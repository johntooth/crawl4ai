"""
Domain Intelligence Dashboard Server

Thin FastAPI wrapper around Crawl4AI's ExhaustiveAsyncWebCrawler.
Provides REST API for the dashboard to start crawls and monitor progress.
"""

import asyncio
import uuid
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, List
from enum import Enum
import aiohttp

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, HttpUrl

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import Crawl4AI components
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from crawl4ai import BrowserConfig, AsyncWebCrawler
from crawl4ai.async_configs import CrawlerRunConfig
from crawl4ai.exhaustive_strategy_config import create_exhaustive_bfs_strategy


# ============================================================================
# Data Models
# ============================================================================

class CrawlStatus(str, Enum):
    """Crawl session status"""
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


class CrawlOptions(BaseModel):
    """Options for starting a crawl"""
    max_depth: int = Field(default=100, ge=1, le=1000, description="Maximum crawl depth")
    max_pages: int = Field(default=1000, ge=1, le=10000, description="Maximum pages to crawl")
    file_types: List[str] = Field(
        default_factory=lambda: ["pdf", "doc", "docx", "xls", "xlsx", "ppt", "pptx"],
        description="Target file extensions to discover"
    )


class StartCrawlRequest(BaseModel):
    """Request to start a new crawl"""
    url: HttpUrl = Field(..., description="Starting URL for the crawl")
    options: CrawlOptions = Field(default_factory=CrawlOptions)


class PageInfo(BaseModel):
    """Information about a discovered page"""
    id: str
    url: str
    title: str = ""
    depth: int
    status: str = "pending"
    parent_id: Optional[str] = None
    error: Optional[str] = None


class DocumentInfo(BaseModel):
    """Information about a discovered document"""
    id: str
    url: str
    filename: str
    file_type: str
    file_size: int = 0
    source_page: str
    download_status: str = "pending"


class CrawlProgress(BaseModel):
    """Current progress of a crawl session"""
    pages_discovered: int = 0
    pages_crawled: int = 0
    pages_failed: int = 0
    documents_found: int = 0
    current_page: Optional[str] = None
    current_depth: int = 0
    max_depth_reached: int = 0
    errors: List[str] = Field(default_factory=list)
    elapsed_seconds: float = 0
    pages_per_second: float = 0


class CrawlSession(BaseModel):
    """Complete crawl session data"""
    id: str
    start_url: str
    status: CrawlStatus
    start_time: datetime
    end_time: Optional[datetime] = None
    options: CrawlOptions
    progress: CrawlProgress
    pages: List[PageInfo] = Field(default_factory=list)
    documents: List[DocumentInfo] = Field(default_factory=list)


class CrawlStatusResponse(BaseModel):
    """Response for crawl status endpoint"""
    session_id: str
    status: CrawlStatus
    progress: CrawlProgress
    pages: List[PageInfo]
    documents: List[DocumentInfo]


class StartCrawlResponse(BaseModel):
    """Response when starting a crawl"""
    session_id: str
    status: CrawlStatus
    message: str


# ============================================================================
# Global State
# ============================================================================

crawl_sessions: Dict[str, CrawlSession] = {}
crawl_tasks: Dict[str, asyncio.Task] = {}


# ============================================================================
# FastAPI Application
# ============================================================================

app = FastAPI(
    title="Domain Intelligence Dashboard API",
    description="Thin API wrapper around Crawl4AI ExhaustiveAsyncWebCrawler",
    version="1.0.0"
)

# Mount static files directory
static_path = Path(__file__).parent / "static"
if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")


# ============================================================================
# Helper Functions
# ============================================================================

def get_session(session_id: str) -> CrawlSession:
    """Get a crawl session or raise 404"""
    if session_id not in crawl_sessions:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    return crawl_sessions[session_id]


async def run_exhaustive_crawl(session_id: str):
    """
    Run exhaustive crawl using Crawl4AI's ExhaustiveAsyncWebCrawler.
    This is a thin wrapper that just calls the existing functionality.
    """
    session = crawl_sessions[session_id]
    logger.info(f"[{session_id}] Starting exhaustive crawl for: {session.start_url}")
    
    try:
        session.status = CrawlStatus.RUNNING
        
        # Calculate reasonable max_pages based on depth
        # Lower depths should have lower page limits to respect the depth setting
        depth_based_max_pages = {
            1: 50,      # Just the start page and its direct links
            2: 200,     # Two levels deep
            3: 500,     # Three levels
            4: 800,     # Four levels
            5: 1000,    # Five levels (full site)
        }
        effective_max_pages = min(
            session.options.max_pages,
            depth_based_max_pages.get(session.options.max_depth, session.options.max_pages)
        )
        
        logger.info(f"[{session_id}] Depth={session.options.max_depth}, effective max_pages={effective_max_pages}")
        
        # Create BFS strategy for deep crawling with human-like delays
        bfs_strategy = create_exhaustive_bfs_strategy(
            max_depth=session.options.max_depth,
            max_pages=effective_max_pages,
            max_concurrent_requests=2,  # Conservative for human-like behavior
            delay_between_requests=5.0,  # 5 second delay between requests
            file_extensions=session.options.file_types,
            include_external=False,
            respect_robots_txt=False
        )
        
        # Create CrawlerRunConfig with the BFS strategy attached
        config = CrawlerRunConfig(
            deep_crawl_strategy=bfs_strategy,
            stream=True,  # Streaming mode for real-time progress
            verbose=True,
            mean_delay=5.0,  # 5 second base delay between requests
            max_range=3.0,   # Add 0-3 second random delay (total: 5-8 seconds)
            semaphore_count=2  # Limit concurrent requests to 2 (more conservative)
        )
        
        logger.info(f"[{session_id}] Config: max_depth={session.options.max_depth}, max_pages={effective_max_pages}, strategy={type(bfs_strategy).__name__}")
        
        # Create browser config
        browser_config = BrowserConfig(headless=True, verbose=False)
        
        # Create crawler and run deep crawl with streaming
        results_list = []
        url_to_page_id = {}
        seen_doc_urls = set()
        
        async with AsyncWebCrawler(config=browser_config) as crawler:
            logger.info(f"[{session_id}] Starting deep crawl with BFS strategy (streaming mode)...")
            
            # arun with stream=True returns AsyncGenerator[CrawlResult]
            async for crawl_result in await crawler.arun(session.start_url, config=config):
                results_list.append(crawl_result)
                
                # Real-time page processing
                page_id = str(uuid.uuid4())
                metadata = getattr(crawl_result, 'metadata', {}) or {}
                depth = metadata.get('depth', 0)
                parent_url = metadata.get('parent_url', None)
                
                page = PageInfo(
                    id=page_id,
                    url=crawl_result.url,
                    title=getattr(crawl_result, 'title', '') or crawl_result.url,
                    depth=depth,
                    status="crawled" if crawl_result.success else "failed",
                    parent_id=None,  # Will be set after we have all pages
                    error=getattr(crawl_result, 'error_message', None)
                )
                
                url_to_page_id[crawl_result.url] = {
                    'page_id': page_id,
                    'parent_url': parent_url,
                    'page': page
                }
                session.pages.append(page)
                
                # Real-time document discovery
                if crawl_result.success and hasattr(crawl_result, 'links') and crawl_result.links:
                    all_links = []
                    if isinstance(crawl_result.links, dict):
                        all_links.extend(crawl_result.links.get('internal', []))
                        all_links.extend(crawl_result.links.get('external', []))
                    
                    for link in all_links:
                        link_url = link.get('href', '') if isinstance(link, dict) else str(link)
                        
                        # Skip if already seen (deduplication)
                        if link_url in seen_doc_urls:
                            continue
                        
                        if link_url and any(link_url.lower().endswith(f'.{ft}') for ft in session.options.file_types):
                            seen_doc_urls.add(link_url)
                            
                            filename = link_url.split('/')[-1].split('?')[0]
                            file_type = filename.split('.')[-1] if '.' in filename else 'unknown'
                            file_size = 0
                            if isinstance(link, dict):
                                file_size = link.get('size', 0) or link.get('file_size', 0)
                            
                            doc = DocumentInfo(
                                id=str(uuid.uuid4()),
                                url=link_url,
                                filename=filename,
                                file_type=file_type,
                                file_size=file_size,
                                source_page=crawl_result.url,
                                download_status="discovered"
                            )
                            session.documents.append(doc)
                
                # Update progress in real-time with detailed metrics
                session.progress.pages_discovered = len(session.pages)
                session.progress.pages_crawled = len([p for p in session.pages if p.status == "crawled"])
                session.progress.pages_failed = len([p for p in session.pages if p.status == "failed"])
                session.progress.documents_found = len(session.documents)
                session.progress.current_page = crawl_result.url
                session.progress.current_depth = depth
                session.progress.max_depth_reached = max(session.progress.max_depth_reached, depth)
                
                # Calculate pages per second
                elapsed = (datetime.now() - session.start_time).total_seconds()
                session.progress.elapsed_seconds = elapsed
                if elapsed > 0:
                    session.progress.pages_per_second = session.progress.pages_crawled / elapsed
                
                # Log progress every 10 pages
                if len(session.pages) % 10 == 0:
                    logger.info(f"[{session_id}] Progress: {session.progress.pages_crawled} pages (depth {depth}), {session.progress.documents_found} docs, {session.progress.pages_per_second:.2f} pages/sec")
            
            logger.info(f"[{session_id}] Deep crawl completed: {len(results_list)} pages")
            
            # Create result dict for compatibility
            result = {
                'results': results_list,
                'total_pages_crawled': len(results_list),
                'successful_pages': len([r for r in results_list if r.success])
            }
        
        logger.info(f"[{session_id}] Crawl completed. Setting parent relationships...")
        
        # Set parent_id relationships (pages and docs already created in real-time)
        for url, info in url_to_page_id.items():
            parent_url = info['parent_url']
            if parent_url and parent_url in url_to_page_id:
                info['page'].parent_id = url_to_page_id[parent_url]['page_id']
        
        # Final progress update (already updated in real-time, but ensure it's current)
        session.progress.pages_discovered = len(session.pages)
        session.progress.pages_crawled = len([p for p in session.pages if p.status == "crawled"])
        session.progress.documents_found = len(session.documents)
        session.progress.current_page = None  # Clear current page
        
        # Mark as completed
        session.status = CrawlStatus.COMPLETED
        session.end_time = datetime.now()
        
        logger.info(f"[{session_id}] Completed: {session.progress.pages_crawled} pages, {session.progress.documents_found} documents")
        
    except asyncio.CancelledError:
        session.status = CrawlStatus.COMPLETED
        session.end_time = datetime.now()
        logger.info(f"[{session_id}] Cancelled by user")
        
    except Exception as e:
        session.status = CrawlStatus.FAILED
        session.progress.errors.append(f"Crawl failed: {str(e)}")
        session.end_time = datetime.now()
        logger.error(f"[{session_id}] Failed: {str(e)}", exc_info=True)
    
    finally:
        # Cleanup
        if session_id in crawl_tasks:
            del crawl_tasks[session_id]


# ============================================================================
# API Endpoints
# ============================================================================

@app.get("/", response_class=HTMLResponse)
async def serve_dashboard():
    """Serve the dashboard HTML"""
    dashboard_path = Path(__file__).parent / "dashboard.html"
    if not dashboard_path.exists():
        raise HTTPException(status_code=404, detail="Dashboard not found")
    return FileResponse(dashboard_path)


@app.get("/favicon.ico")
async def favicon():
    """Return a simple favicon to avoid 404 errors"""
    # Return a 204 No Content response - browser won't show error
    from fastapi import Response
    return Response(status_code=204)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "active_sessions": len(crawl_sessions),
        "running_crawls": len([s for s in crawl_sessions.values() if s.status == CrawlStatus.RUNNING])
    }


@app.post("/api/start-crawl", response_model=StartCrawlResponse)
async def start_crawl(request: StartCrawlRequest):
    """Start a new exhaustive crawl session"""
    session_id = str(uuid.uuid4())
    
    logger.info(f"[{session_id}] New crawl: {request.url}")
    
    session = CrawlSession(
        id=session_id,
        start_url=str(request.url),
        status=CrawlStatus.PENDING,
        start_time=datetime.now(),
        options=request.options,
        progress=CrawlProgress()
    )
    
    crawl_sessions[session_id] = session
    
    # Start background task
    task = asyncio.create_task(run_exhaustive_crawl(session_id))
    crawl_tasks[session_id] = task
    
    return StartCrawlResponse(
        session_id=session_id,
        status=CrawlStatus.PENDING,
        message=f"Crawl started"
    )


@app.get("/api/crawl-status/{session_id}", response_model=CrawlStatusResponse)
async def get_crawl_status(session_id: str):
    """Get current crawl status and progress"""
    session = get_session(session_id)
    
    # Calculate elapsed time
    if session.end_time:
        elapsed = (session.end_time - session.start_time).total_seconds()
    else:
        elapsed = (datetime.now() - session.start_time).total_seconds()
    
    session.progress.elapsed_seconds = elapsed
    
    return CrawlStatusResponse(
        session_id=session.id,
        status=session.status,
        progress=session.progress,
        pages=session.pages,
        documents=session.documents
    )


@app.post("/api/pause-crawl/{session_id}")
async def pause_crawl(session_id: str):
    """Pause/resume a crawl (not fully supported by exhaustive crawler yet)"""
    session = get_session(session_id)
    
    if session.status == CrawlStatus.PAUSED:
        session.status = CrawlStatus.RUNNING
        return {"message": "Resumed", "status": session.status.value}
    
    if session.status == CrawlStatus.RUNNING:
        session.status = CrawlStatus.PAUSED
        return {"message": "Paused", "status": session.status.value}
    
    raise HTTPException(status_code=400, detail=f"Cannot pause in {session.status.value} state")


@app.post("/api/stop-crawl/{session_id}")
async def stop_crawl(session_id: str):
    """Stop a running crawl gracefully"""
    session = get_session(session_id)
    
    if session.status not in [CrawlStatus.RUNNING, CrawlStatus.PAUSED, CrawlStatus.PENDING]:
        raise HTTPException(status_code=400, detail=f"Cannot stop in {session.status.value} state")
    
    logger.info(f"[{session_id}] Stop requested - cancelling crawl task")
    
    # Cancel the background task
    if session_id in crawl_tasks:
        task = crawl_tasks[session_id]
        task.cancel()
        logger.info(f"[{session_id}] Crawl task cancelled")
    
    # Update session status
    session.status = CrawlStatus.COMPLETED
    session.end_time = datetime.now()
    
    return {"message": "Crawl stopped", "status": "completed"}


@app.get("/api/export-pdf/{session_id}")
async def export_pdf(session_id: str):
    """Export site map as PDF"""
    from fastapi.responses import StreamingResponse
    from io import BytesIO
    
    session = get_session(session_id)
    
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.units import inch
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.enums import TA_CENTER, TA_LEFT
        from reportlab.lib import colors
        
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
        elements = []
        styles = getSampleStyleSheet()
        
        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1e40af'),
            spaceAfter=30,
            alignment=TA_CENTER
        )
        
        elements.append(Paragraph("Site Map Report", title_style))
        elements.append(Spacer(1, 0.2*inch))
        
        # Summary
        summary_data = [
            ["URL:", session.start_url],
            ["Status:", session.status.value],
            ["Pages Crawled:", str(session.progress.pages_crawled)],
            ["Documents Found:", str(session.progress.documents_found)],
            ["Crawl Time:", f"{session.progress.elapsed_seconds:.1f}s"],
        ]
        
        summary_table = Table(summary_data, colWidths=[1.5*inch, 5*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e5e7eb')),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('PADDING', (0, 0), (-1, -1), 8),
        ]))
        
        elements.append(summary_table)
        elements.append(Spacer(1, 0.3*inch))
        
        # Documents section
        if session.documents:
            elements.append(Paragraph("Documents Found", styles['Heading2']))
            elements.append(Spacer(1, 0.1*inch))
            
            # Group documents by type
            doc_by_type = {}
            for doc in session.documents:
                doc_type = doc.file_type.upper()
                if doc_type not in doc_by_type:
                    doc_by_type[doc_type] = []
                doc_by_type[doc_type].append(doc)
            
            # Summary by type
            type_data = [["File Type", "Count"]]
            for doc_type, docs in sorted(doc_by_type.items()):
                type_data.append([doc_type, str(len(docs))])
            
            type_table = Table(type_data, colWidths=[2*inch, 1*inch])
            type_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e40af')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('PADDING', (0, 0), (-1, -1), 6),
            ]))
            elements.append(type_table)
        
        # Build PDF
        doc.build(elements)
        buffer.seek(0)
        
        return StreamingResponse(
            buffer,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=site-map-{session_id}.pdf"}
        )
        
    except ImportError as e:
        logger.error(f"PDF export failed - reportlab not installed: {e}")
        raise HTTPException(status_code=500, detail="PDF export requires reportlab. Install with: pip install reportlab")
    except Exception as e:
        logger.error(f"PDF export failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"PDF generation error: {str(e)}")


@app.get("/api/export-csv/{session_id}")
async def export_csv(session_id: str):
    """Export document list as CSV"""
    from fastapi.responses import StreamingResponse
    from io import StringIO
    import csv
    
    session = get_session(session_id)
    
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["URL", "Filename", "Type", "Size", "Status", "Source"])
    
    for doc in session.documents:
        writer.writerow([
            doc.url,
            doc.filename,
            doc.file_type.upper(),
            doc.file_size,
            doc.download_status,
            doc.source_page
        ])
    
    output.seek(0)
    
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=documents-{session_id}.csv"}
    )


@app.post("/api/download-documents/{session_id}")
async def download_documents(session_id: str):
    """
    Download all discovered documents to E:\\filefinder\\{domain}\\
    Uses batched downloads with the existing SiteStorageManager
    """
    import aiohttp
    from urllib.parse import urlparse
    
    session = get_session(session_id)
    
    # Import storage manager
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from crawl4ai.site_storage_manager import SiteStorageManager, StorageConfig
    
    # Extract domain from start URL
    parsed = urlparse(session.start_url)
    domain = parsed.netloc.replace('www.', '')
    
    # Initialize storage manager
    storage_config = StorageConfig(files_root=r"E:\filefinder")
    storage_manager = SiteStorageManager(config=storage_config)
    
    # Deduplicate documents by URL
    seen_urls = set()
    unique_documents = []
    for doc in session.documents:
        if doc.url not in seen_urls:
            seen_urls.add(doc.url)
            unique_documents.append(doc)
    
    duplicates_removed = len(session.documents) - len(unique_documents)
    
    # Prepare download stats
    download_stats = {
        "total": len(unique_documents),
        "duplicates_removed": duplicates_removed,
        "successful": 0,
        "failed": 0,
        "skipped": 0,
        "download_path": f"E:\\filefinder\\{domain}",
        "errors": []
    }
    
    logger.info(f"[{session_id}] Starting batch download of {len(unique_documents)} documents ({duplicates_removed} duplicates removed) to E:\\filefinder\\{domain}")
    
    # Download documents in batches
    batch_size = 3  # Match concurrent request limit
    
    async with aiohttp.ClientSession() as http_session:
        for i in range(0, len(unique_documents), batch_size):
            batch = unique_documents[i:i+batch_size]
            tasks = []
            
            for doc in batch:
                tasks.append(download_single_document(
                    http_session, 
                    storage_manager, 
                    domain, 
                    doc, 
                    download_stats
                ))
            
            # Execute batch
            await asyncio.gather(*tasks, return_exceptions=True)
            
            # Add delay between batches (human-like)
            if i + batch_size < len(session.documents):
                await asyncio.sleep(2.0)
    
    logger.info(f"[{session_id}] Download complete: {download_stats['successful']} successful, {download_stats['failed']} failed")
    
    return {
        "session_id": session_id,
        "domain": domain,
        "stats": download_stats
    }


async def download_single_document(http_session, storage_manager, domain, doc, stats):
    """Download a single document and store it"""
    try:
        # Determine file type category for storage
        file_type_map = {
            'pdf': 'documents',
            'doc': 'documents',
            'docx': 'documents',
            'xls': 'documents',
            'xlsx': 'documents',
            'ppt': 'documents',
            'pptx': 'documents',
            'txt': 'documents',
            'csv': 'data',
            'json': 'data',
            'xml': 'data',
            'zip': 'archives',
            'tar': 'archives',
            'gz': 'archives',
            'rar': 'archives',
            '7z': 'archives',
        }
        
        file_category = file_type_map.get(doc.file_type.lower(), 'other')
        
        # Download file
        async with http_session.get(doc.url, timeout=aiohttp.ClientTimeout(total=60)) as response:
            if response.status == 200:
                content = await response.read()
                
                # Store using storage manager
                metadata = {
                    'source_page': doc.source_page,
                    'file_type': doc.file_type,
                    'original_filename': doc.filename
                }
                
                stored_path = await storage_manager.store_downloaded_file(
                    url_or_domain=domain,
                    file_url=doc.url,
                    file_content=content,
                    file_type=file_category,
                    metadata=metadata
                )
                
                # Update document info
                doc.file_size = len(content)
                doc.download_status = "completed"
                
                stats["successful"] += 1
                logger.info(f"Downloaded: {doc.filename} -> {stored_path}")
                
            else:
                doc.download_status = "failed"
                stats["failed"] += 1
                error_msg = f"HTTP {response.status}"
                stats["errors"].append(f"{doc.filename}: {error_msg}")
                logger.warning(f"Failed to download {doc.filename}: {error_msg}")
                
    except asyncio.TimeoutError:
        doc.download_status = "failed"
        stats["failed"] += 1
        stats["errors"].append(f"{doc.filename}: Timeout")
        logger.warning(f"Timeout downloading {doc.filename}")
        
    except Exception as e:
        doc.download_status = "failed"
        stats["failed"] += 1
        error_msg = str(e)
        stats["errors"].append(f"{doc.filename}: {error_msg}")
        logger.error(f"Error downloading {doc.filename}: {error_msg}")


# ============================================================================
# Application Entry Point
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    print("Starting Domain Intelligence Dashboard Server...")
    print("Dashboard: http://localhost:8080")
    print("API docs: http://localhost:8080/docs")
    
    uvicorn.run(app, host="0.0.0.0", port=8080, log_level="info")
