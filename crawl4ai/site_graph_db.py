"""
Site Graph Database Extension for Crawl4AI

This module extends the existing AsyncDatabaseManager to support site graph persistence,
URL tracking, and file metadata storage for exhaustive crawling capabilities.

Follows existing Crawl4AI patterns:
- Uses existing async_database.py patterns
- Integrates with existing AsyncDatabaseManager
- Uses existing logging and error handling
- Follows existing database schema patterns
"""

import os
import json
import aiosqlite
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from .async_database import AsyncDatabaseManager
from .async_logger import AsyncLogger


@dataclass
class URLNode:
    """Represents a discovered URL in the site graph"""
    url: str
    source_url: Optional[str] = None
    discovered_at: Optional[datetime] = None
    last_checked: Optional[datetime] = None
    status_code: Optional[int] = None
    content_type: Optional[str] = None
    file_size: Optional[int] = None
    is_file: bool = False
    file_extension: Optional[str] = None
    download_status: str = "not_attempted"  # not_attempted, downloading, completed, failed
    local_path: Optional[str] = None
    checksum: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    retry_count: int = 0


@dataclass
class SiteGraphStats:
    """Statistics for site graph crawling"""
    base_url: str
    total_urls_discovered: int = 0
    total_files_discovered: int = 0
    total_files_downloaded: int = 0
    crawl_start_time: Optional[datetime] = None
    crawl_end_time: Optional[datetime] = None
    last_activity: Optional[datetime] = None
    dead_end_count: int = 0
    revisit_ratio: float = 0.0


class SiteGraphDatabaseManager:
    """
    Extension to AsyncDatabaseManager for site graph persistence.
    
    Integrates with existing database infrastructure while adding
    site mapping and file discovery capabilities.
    """
    
    def __init__(self, db_manager: AsyncDatabaseManager):
        self.db_manager = db_manager
        self.logger = AsyncLogger(
            log_file=os.path.join(os.path.dirname(db_manager.db_path), "site_graph.log"),
            verbose=False,
            tag_width=12,
        )
        self._schema_initialized = False

    async def initialize_site_graph_schema(self):
        """Initialize site graph database schema using existing patterns"""
        if self._schema_initialized:
            return
            
        try:
            async with self.db_manager.get_connection() as db:
                # Create discovered_urls table
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS discovered_urls (
                        url TEXT PRIMARY KEY,
                        source_url TEXT,
                        discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_checked TIMESTAMP,
                        status_code INTEGER,
                        content_type TEXT,
                        file_size INTEGER,
                        is_file BOOLEAN DEFAULT FALSE,
                        file_extension TEXT,
                        download_status TEXT DEFAULT 'not_attempted',
                        local_path TEXT,
                        checksum TEXT,
                        metadata TEXT DEFAULT '{}',
                        error_message TEXT,
                        retry_count INTEGER DEFAULT 0,
                        FOREIGN KEY (source_url) REFERENCES discovered_urls(url)
                    )
                """)
                
                # Create site_graph_stats table
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS site_graph_stats (
                        base_url TEXT PRIMARY KEY,
                        total_urls_discovered INTEGER DEFAULT 0,
                        total_files_discovered INTEGER DEFAULT 0,
                        total_files_downloaded INTEGER DEFAULT 0,
                        crawl_start_time TIMESTAMP,
                        crawl_end_time TIMESTAMP,
                        last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        dead_end_count INTEGER DEFAULT 0,
                        revisit_ratio REAL DEFAULT 0.0
                    )
                """)
                
                # Create indexes for performance
                await db.execute("""
                    CREATE INDEX IF NOT EXISTS idx_discovered_urls_source 
                    ON discovered_urls(source_url)
                """)
                
                await db.execute("""
                    CREATE INDEX IF NOT EXISTS idx_discovered_urls_is_file 
                    ON discovered_urls(is_file)
                """)
                
                await db.execute("""
                    CREATE INDEX IF NOT EXISTS idx_discovered_urls_status 
                    ON discovered_urls(download_status)
                """)
                
                await db.execute("""
                    CREATE INDEX IF NOT EXISTS idx_discovered_urls_discovered_at 
                    ON discovered_urls(discovered_at)
                """)
                
                await db.commit()
                
            self._schema_initialized = True
            self.logger.success("Site graph schema initialized successfully", tag="INIT")
            
        except Exception as e:
            self.logger.error(
                message="Failed to initialize site graph schema: {error}",
                tag="ERROR",
                params={"error": str(e)}
            )
            raise

    async def store_discovered_url(self, url_node: URLNode) -> None:
        """Store a discovered URL in the site graph using existing database patterns"""
        await self.initialize_site_graph_schema()
        
        async def _store(db):
            # Convert datetime objects to ISO format strings for storage
            discovered_at = url_node.discovered_at.isoformat() if url_node.discovered_at else None
            last_checked = url_node.last_checked.isoformat() if url_node.last_checked else None
            metadata_json = json.dumps(url_node.metadata or {})
            
            await db.execute("""
                INSERT INTO discovered_urls (
                    url, source_url, discovered_at, last_checked, status_code,
                    content_type, file_size, is_file, file_extension, download_status,
                    local_path, checksum, metadata, error_message, retry_count
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(url) DO UPDATE SET
                    last_checked = excluded.last_checked,
                    status_code = excluded.status_code,
                    content_type = excluded.content_type,
                    file_size = excluded.file_size,
                    download_status = excluded.download_status,
                    local_path = excluded.local_path,
                    checksum = excluded.checksum,
                    metadata = excluded.metadata,
                    error_message = excluded.error_message,
                    retry_count = excluded.retry_count
            """, (
                url_node.url,
                url_node.source_url,
                discovered_at,
                last_checked,
                url_node.status_code,
                url_node.content_type,
                url_node.file_size,
                url_node.is_file,
                url_node.file_extension,
                url_node.download_status,
                url_node.local_path,
                url_node.checksum,
                metadata_json,
                url_node.error_message,
                url_node.retry_count
            ))

        try:
            await self.db_manager.execute_with_retry(_store)
            self.logger.debug(
                message="Stored URL in site graph: {url}",
                tag="STORE",
                params={"url": url_node.url}
            )
        except Exception as e:
            self.logger.error(
                message="Failed to store discovered URL: {error}",
                tag="ERROR",
                params={"error": str(e)}
            )
            raise

    async def get_discovered_url(self, url: str) -> Optional[URLNode]:
        """Retrieve a discovered URL from the site graph"""
        await self.initialize_site_graph_schema()
        
        async def _get(db):
            async with db.execute(
                "SELECT * FROM discovered_urls WHERE url = ?", (url,)
            ) as cursor:
                row = await cursor.fetchone()
                if not row:
                    return None
                
                # Get column names for proper mapping
                columns = [description[0] for description in cursor.description]
                row_dict = dict(zip(columns, row))
                
                # Convert timestamp strings back to datetime objects
                if row_dict['discovered_at']:
                    row_dict['discovered_at'] = datetime.fromisoformat(row_dict['discovered_at'])
                if row_dict['last_checked']:
                    row_dict['last_checked'] = datetime.fromisoformat(row_dict['last_checked'])
                
                # Parse metadata JSON
                try:
                    row_dict['metadata'] = json.loads(row_dict['metadata'] or '{}')
                except json.JSONDecodeError:
                    row_dict['metadata'] = {}
                
                return URLNode(**row_dict)

        try:
            return await self.db_manager.execute_with_retry(_get)
        except Exception as e:
            self.logger.error(
                message="Failed to retrieve discovered URL: {error}",
                tag="ERROR",
                params={"error": str(e)}
            )
            return None

    async def get_site_graph(self, base_url: str, include_files: bool = True) -> Dict[str, List[URLNode]]:
        """Retrieve complete site graph for a base URL"""
        await self.initialize_site_graph_schema()
        
        async def _get_graph(db):
            # Build query based on parameters
            query = "SELECT * FROM discovered_urls WHERE url LIKE ? OR source_url LIKE ?"
            params = [f"{base_url}%", f"{base_url}%"]
            
            if not include_files:
                query += " AND is_file = FALSE"
            
            query += " ORDER BY discovered_at ASC"
            
            async with db.execute(query, params) as cursor:
                rows = await cursor.fetchall()
                columns = [description[0] for description in cursor.description]
                
                urls = []
                files = []
                
                for row in rows:
                    row_dict = dict(zip(columns, row))
                    
                    # Convert timestamps
                    if row_dict['discovered_at']:
                        row_dict['discovered_at'] = datetime.fromisoformat(row_dict['discovered_at'])
                    if row_dict['last_checked']:
                        row_dict['last_checked'] = datetime.fromisoformat(row_dict['last_checked'])
                    
                    # Parse metadata
                    try:
                        row_dict['metadata'] = json.loads(row_dict['metadata'] or '{}')
                    except json.JSONDecodeError:
                        row_dict['metadata'] = {}
                    
                    url_node = URLNode(**row_dict)
                    
                    if url_node.is_file:
                        files.append(url_node)
                    else:
                        urls.append(url_node)
                
                return {
                    'urls': urls,
                    'files': files,
                    'total_urls': len(urls),
                    'total_files': len(files)
                }

        try:
            return await self.db_manager.execute_with_retry(_get_graph)
        except Exception as e:
            self.logger.error(
                message="Failed to retrieve site graph: {error}",
                tag="ERROR",
                params={"error": str(e)}
            )
            return {'urls': [], 'files': [], 'total_urls': 0, 'total_files': 0}

    async def update_url_status(self, url: str, status_code: int, 
                               content_type: str = None, file_size: int = None,
                               error_message: str = None) -> None:
        """Update URL status after checking/crawling"""
        await self.initialize_site_graph_schema()
        
        async def _update(db):
            await db.execute("""
                UPDATE discovered_urls 
                SET last_checked = ?, status_code = ?, content_type = ?, 
                    file_size = ?, error_message = ?
                WHERE url = ?
            """, (
                datetime.now().isoformat(),
                status_code,
                content_type,
                file_size,
                error_message,
                url
            ))

        try:
            await self.db_manager.execute_with_retry(_update)
        except Exception as e:
            self.logger.error(
                message="Failed to update URL status: {error}",
                tag="ERROR",
                params={"error": str(e)}
            )
            raise

    async def update_file_download_status(self, url: str, download_status: str,
                                        local_path: str = None, checksum: str = None,
                                        error_message: str = None) -> None:
        """Update file download status and metadata"""
        await self.initialize_site_graph_schema()
        
        async def _update(db):
            await db.execute("""
                UPDATE discovered_urls 
                SET download_status = ?, local_path = ?, checksum = ?, 
                    error_message = ?, last_checked = ?
                WHERE url = ?
            """, (
                download_status,
                local_path,
                checksum,
                error_message,
                datetime.now().isoformat(),
                url
            ))

        try:
            await self.db_manager.execute_with_retry(_update)
        except Exception as e:
            self.logger.error(
                message="Failed to update file download status: {error}",
                tag="ERROR",
                params={"error": str(e)}
            )
            raise

    async def get_files_by_status(self, download_status: str, base_url: str = None) -> List[URLNode]:
        """Get files filtered by download status"""
        await self.initialize_site_graph_schema()
        
        async def _get_files(db):
            query = "SELECT * FROM discovered_urls WHERE is_file = TRUE AND download_status = ?"
            params = [download_status]
            
            if base_url:
                query += " AND url LIKE ?"
                params.append(f"{base_url}%")
            
            async with db.execute(query, params) as cursor:
                rows = await cursor.fetchall()
                columns = [description[0] for description in cursor.description]
                
                files = []
                for row in rows:
                    row_dict = dict(zip(columns, row))
                    
                    # Convert timestamps
                    if row_dict['discovered_at']:
                        row_dict['discovered_at'] = datetime.fromisoformat(row_dict['discovered_at'])
                    if row_dict['last_checked']:
                        row_dict['last_checked'] = datetime.fromisoformat(row_dict['last_checked'])
                    
                    # Parse metadata
                    try:
                        row_dict['metadata'] = json.loads(row_dict['metadata'] or '{}')
                    except json.JSONDecodeError:
                        row_dict['metadata'] = {}
                    
                    files.append(URLNode(**row_dict))
                
                return files

        try:
            return await self.db_manager.execute_with_retry(_get_files)
        except Exception as e:
            self.logger.error(
                message="Failed to get files by status: {error}",
                tag="ERROR",
                params={"error": str(e)}
            )
            return []

    async def store_site_graph_stats(self, stats: SiteGraphStats) -> None:
        """Store or update site graph statistics"""
        await self.initialize_site_graph_schema()
        
        async def _store_stats(db):
            # Convert datetime objects to ISO format strings
            crawl_start = stats.crawl_start_time.isoformat() if stats.crawl_start_time else None
            crawl_end = stats.crawl_end_time.isoformat() if stats.crawl_end_time else None
            last_activity = stats.last_activity.isoformat() if stats.last_activity else datetime.now().isoformat()
            
            await db.execute("""
                INSERT INTO site_graph_stats (
                    base_url, total_urls_discovered, total_files_discovered,
                    total_files_downloaded, crawl_start_time, crawl_end_time,
                    last_activity, dead_end_count, revisit_ratio
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(base_url) DO UPDATE SET
                    total_urls_discovered = excluded.total_urls_discovered,
                    total_files_discovered = excluded.total_files_discovered,
                    total_files_downloaded = excluded.total_files_downloaded,
                    crawl_end_time = excluded.crawl_end_time,
                    last_activity = excluded.last_activity,
                    dead_end_count = excluded.dead_end_count,
                    revisit_ratio = excluded.revisit_ratio
            """, (
                stats.base_url,
                stats.total_urls_discovered,
                stats.total_files_discovered,
                stats.total_files_downloaded,
                crawl_start,
                crawl_end,
                last_activity,
                stats.dead_end_count,
                stats.revisit_ratio
            ))

        try:
            await self.db_manager.execute_with_retry(_store_stats)
        except Exception as e:
            self.logger.error(
                message="Failed to store site graph stats: {error}",
                tag="ERROR",
                params={"error": str(e)}
            )
            raise

    async def get_site_graph_stats(self, base_url: str) -> Optional[SiteGraphStats]:
        """Retrieve site graph statistics"""
        await self.initialize_site_graph_schema()
        
        async def _get_stats(db):
            async with db.execute(
                "SELECT * FROM site_graph_stats WHERE base_url = ?", (base_url,)
            ) as cursor:
                row = await cursor.fetchone()
                if not row:
                    return None
                
                columns = [description[0] for description in cursor.description]
                row_dict = dict(zip(columns, row))
                
                # Convert timestamp strings back to datetime objects
                if row_dict['crawl_start_time']:
                    row_dict['crawl_start_time'] = datetime.fromisoformat(row_dict['crawl_start_time'])
                if row_dict['crawl_end_time']:
                    row_dict['crawl_end_time'] = datetime.fromisoformat(row_dict['crawl_end_time'])
                if row_dict['last_activity']:
                    row_dict['last_activity'] = datetime.fromisoformat(row_dict['last_activity'])
                
                return SiteGraphStats(**row_dict)

        try:
            return await self.db_manager.execute_with_retry(_get_stats)
        except Exception as e:
            self.logger.error(
                message="Failed to get site graph stats: {error}",
                tag="ERROR",
                params={"error": str(e)}
            )
            return None

    async def get_crawl_progress(self, base_url: str) -> Dict[str, Any]:
        """Get comprehensive crawl progress information"""
        await self.initialize_site_graph_schema()
        
        try:
            # Get basic stats
            stats = await self.get_site_graph_stats(base_url)
            
            # Get file download progress
            files_pending = await self.get_files_by_status("not_attempted", base_url)
            files_downloading = await self.get_files_by_status("downloading", base_url)
            files_completed = await self.get_files_by_status("completed", base_url)
            files_failed = await self.get_files_by_status("failed", base_url)
            
            # Calculate progress metrics
            total_files = len(files_pending) + len(files_downloading) + len(files_completed) + len(files_failed)
            download_progress = len(files_completed) / total_files if total_files > 0 else 0.0
            
            return {
                'base_url': base_url,
                'stats': asdict(stats) if stats else None,
                'file_progress': {
                    'total_files': total_files,
                    'pending': len(files_pending),
                    'downloading': len(files_downloading),
                    'completed': len(files_completed),
                    'failed': len(files_failed),
                    'progress_percentage': download_progress * 100
                },
                'last_updated': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(
                message="Failed to get crawl progress: {error}",
                tag="ERROR",
                params={"error": str(e)}
            )
            return {
                'base_url': base_url,
                'error': str(e),
                'last_updated': datetime.now().isoformat()
            }

    async def cleanup_old_entries(self, base_url: str, days_old: int = 30) -> int:
        """Clean up old site graph entries"""
        await self.initialize_site_graph_schema()
        
        async def _cleanup(db):
            cutoff_date = datetime.now().replace(day=datetime.now().day - days_old)
            
            # Delete old discovered URLs
            async with db.execute("""
                DELETE FROM discovered_urls 
                WHERE (url LIKE ? OR source_url LIKE ?) 
                AND discovered_at < ?
            """, (f"{base_url}%", f"{base_url}%", cutoff_date.isoformat())) as cursor:
                deleted_count = cursor.rowcount
            
            return deleted_count

        try:
            deleted = await self.db_manager.execute_with_retry(_cleanup)
            self.logger.info(
                message="Cleaned up {count} old site graph entries",
                tag="CLEANUP",
                params={"count": deleted}
            )
            return deleted
        except Exception as e:
            self.logger.error(
                message="Failed to cleanup old entries: {error}",
                tag="ERROR",
                params={"error": str(e)}
            )
            return 0


# Create a factory function to integrate with existing database manager
def create_site_graph_manager(db_manager: AsyncDatabaseManager = None) -> SiteGraphDatabaseManager:
    """
    Factory function to create SiteGraphDatabaseManager with existing database manager.
    
    If no db_manager is provided, uses the global async_db_manager instance.
    """
    if db_manager is None:
        from .async_database import async_db_manager
        db_manager = async_db_manager
    
    return SiteGraphDatabaseManager(db_manager)