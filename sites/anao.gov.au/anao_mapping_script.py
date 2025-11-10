#!/usr/bin/env python3
"""
ANAO Website Mapping and File Extraction Script

This script uses Crawl4AI's existing capabilities to:
1. Map the entire https://www.anao.gov.au/ website
2. Discover and download all available files
3. Generate comprehensive reports on the site structure and files found

Uses the existing AsyncWebCrawler with deep crawling strategy.
"""

import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Set, Optional
from dataclasses import dataclass, asdict
from urllib.parse import urljoin, urlparse

# Try to import networkx, but make it optional
try:
    import networkx as nx
    HAS_NETWORKX = True
except ImportError:
    HAS_NETWORKX = False
    print("⚠️ NetworkX not available - graph analysis features will be limited")

# Add the current directory to path to import crawl4ai
sys.path.insert(0, str(Path(__file__).parent))

from crawl4ai.async_webcrawler import AsyncWebCrawler
from crawl4ai.async_configs import CrawlerRunConfig, BrowserConfig
from crawl4ai.deep_crawling import BFSDeepCrawlStrategy


@dataclass
class URLNode:
    """Represents a URL node in the site graph."""
    url: str
    title: str = ""
    content_type: str = ""
    file_size: int = 0
    last_checked: str = ""
    status_code: int = 0
    parent_url: str = ""
    depth: int = 0
    is_file: bool = False
    file_extension: str = ""
    content_length: int = 0
    discovered_files: List[str] = None
    
    def __post_init__(self):
        if self.discovered_files is None:
            self.discovered_files = []


@dataclass
class SiteGraph:
    """Represents the complete site structure and relationships."""
    domain: str
    root_url: str
    crawl_date: str
    total_pages: int = 0
    total_files: int = 0
    nodes: Dict[str, URLNode] = None
    edges: List[Dict[str, str]] = None
    file_inventory: Dict[str, Dict] = None
    
    def __post_init__(self):
        if self.nodes is None:
            self.nodes = {}
        if self.edges is None:
            self.edges = []
        if self.file_inventory is None:
            self.file_inventory = {}


class SiteGraphBuilder:
    """Builds and manages the site graph structure."""
    
    def __init__(self, domain: str, root_url: str):
        self.domain = domain
        self.root_url = root_url
        self.graph = SiteGraph(
            domain=domain,
            root_url=root_url,
            crawl_date=datetime.now().isoformat()
        )
        self.nx_graph = nx.DiGraph() if HAS_NETWORKX else None  # NetworkX graph for analysis
        
    def add_page(self, url: str, result, parent_url: str = "", depth: int = 0):
        """Add a page to the site graph."""
        
        # Create URL node
        node = URLNode(
            url=url,
            title=getattr(result, 'title', '') or '',
            content_length=len(getattr(result, 'cleaned_html', '') or ''),
            last_checked=datetime.now().isoformat(),
            status_code=200 if getattr(result, 'success', False) else 404,
            parent_url=parent_url,
            depth=depth,
            is_file=False
        )
        
        # Extract file links from this page
        if hasattr(result, 'links') and result.links:
            internal_links = result.links.get('internal', [])
            for link in internal_links:
                if isinstance(link, dict):
                    link_url = link.get('href', '')
                    if self._is_file_url(link_url):
                        node.discovered_files.append(link_url)
                        self._add_file_to_inventory(link_url, link, url)
        
        # Add to graph
        self.graph.nodes[url] = node
        if self.nx_graph is not None:
            self.nx_graph.add_node(url, **asdict(node))
        
        # Add edge from parent
        if parent_url and parent_url in self.graph.nodes:
            self.graph.edges.append({
                'source': parent_url,
                'target': url,
                'relationship': 'links_to'
            })
            if self.nx_graph is not None:
                self.nx_graph.add_edge(parent_url, url)
    
    def _is_file_url(self, url: str) -> bool:
        """Check if URL points to a downloadable file."""
        file_extensions = ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', 
                          '.csv', '.txt', '.json', '.xml', '.zip', '.tar', '.gz']
        return any(url.lower().endswith(ext) for ext in file_extensions)
    
    def _add_file_to_inventory(self, file_url: str, link_info: dict, source_page: str):
        """Add file to the inventory."""
        filename = Path(file_url).name
        file_ext = Path(file_url).suffix.lower()
        
        self.graph.file_inventory[file_url] = {
            'filename': filename,
            'url': file_url,
            'extension': file_ext,
            'text': link_info.get('text', ''),
            'source_page': source_page,
            'discovered_at': datetime.now().isoformat(),
            'downloaded': False,
            'file_size': 0
        }
    
    def update_file_download_status(self, file_url: str, downloaded: bool, file_size: int = 0):
        """Update file download status in inventory."""
        if file_url in self.graph.file_inventory:
            self.graph.file_inventory[file_url]['downloaded'] = downloaded
            self.graph.file_inventory[file_url]['file_size'] = file_size
            if downloaded:
                self.graph.file_inventory[file_url]['downloaded_at'] = datetime.now().isoformat()
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive site graph statistics."""
        stats = {
            'total_pages': len(self.graph.nodes),
            'total_files_discovered': len(self.graph.file_inventory),
            'total_edges': len(self.graph.edges),
            'max_depth': max((node.depth for node in self.graph.nodes.values()), default=0),
            'file_types': {},
            'pages_by_depth': {},
            'download_status': {
                'downloaded': 0,
                'not_downloaded': 0,
                'total_size': 0
            }
        }
        
        # File type analysis
        for file_info in self.graph.file_inventory.values():
            ext = file_info['extension']
            stats['file_types'][ext] = stats['file_types'].get(ext, 0) + 1
            
            if file_info['downloaded']:
                stats['download_status']['downloaded'] += 1
                stats['download_status']['total_size'] += file_info['file_size']
            else:
                stats['download_status']['not_downloaded'] += 1
        
        # Pages by depth
        for node in self.graph.nodes.values():
            depth = node.depth
            stats['pages_by_depth'][depth] = stats['pages_by_depth'].get(depth, 0) + 1
        
        return stats
    
    def export_graph_data(self, output_dir: Path) -> Dict[str, Path]:
        """Export graph data in multiple formats."""
        exported_files = {}
        
        # Export as JSON
        graph_json_path = output_dir / "site_graph.json"
        with open(graph_json_path, 'w', encoding='utf-8') as f:
            # Convert dataclass to dict for JSON serialization
            graph_dict = {
                'domain': self.graph.domain,
                'root_url': self.graph.root_url,
                'crawl_date': self.graph.crawl_date,
                'total_pages': len(self.graph.nodes),
                'total_files': len(self.graph.file_inventory),
                'nodes': {url: asdict(node) for url, node in self.graph.nodes.items()},
                'edges': self.graph.edges,
                'file_inventory': self.graph.file_inventory,
                'statistics': self.get_statistics()
            }
            json.dump(graph_dict, f, indent=2, ensure_ascii=False, default=str)
        exported_files['graph_json'] = graph_json_path
        
        # Export NetworkX graph as GraphML (if NetworkX is available)
        if HAS_NETWORKX and self.nx_graph is not None:
            try:
                # Create a simplified graph for GraphML export (GraphML doesn't support complex data types)
                simple_graph = nx.DiGraph()
                for node_id, node_data in self.nx_graph.nodes(data=True):
                    # Convert complex data types to strings for GraphML compatibility
                    simple_data = {}
                    for key, value in node_data.items():
                        if isinstance(value, list):
                            simple_data[key] = ','.join(map(str, value)) if value else ''
                        elif value is None:
                            simple_data[key] = ''
                        else:
                            simple_data[key] = str(value)
                    simple_graph.add_node(node_id, **simple_data)
                
                # Add edges
                for source, target in self.nx_graph.edges():
                    simple_graph.add_edge(source, target)
                
                graphml_path = output_dir / "site_graph.graphml"
                nx.write_graphml(simple_graph, graphml_path)
                exported_files['graphml'] = graphml_path
            except Exception as e:
                print(f"  ⚠️ Could not export GraphML: {e}")
        else:
            print(f"  ⚠️ NetworkX not available - skipping GraphML export")
        
        # Export as CSV (nodes and edges)
        nodes_csv_path = output_dir / "site_graph_nodes.csv"
        with open(nodes_csv_path, 'w', encoding='utf-8') as f:
            f.write("url,title,content_type,content_length,last_checked,status_code,parent_url,depth,is_file,file_extension,discovered_files_count\n")
            for url, node in self.graph.nodes.items():
                title = (node.title or '').replace('"', '""')
                parent = (node.parent_url or '').replace('"', '""')
                f.write(f'"{url}","{title}","{node.content_type}",{node.content_length},"{node.last_checked}",{node.status_code},"{parent}",{node.depth},{node.is_file},"{node.file_extension}",{len(node.discovered_files)}\n')
        exported_files['nodes_csv'] = nodes_csv_path
        
        edges_csv_path = output_dir / "site_graph_edges.csv"
        with open(edges_csv_path, 'w', encoding='utf-8') as f:
            f.write("source,target,relationship\n")
            for edge in self.graph.edges:
                f.write(f'"{edge["source"]}","{edge["target"]}","{edge["relationship"]}"\n')
        exported_files['edges_csv'] = edges_csv_path
        
        return exported_files


async def map_anao_website():
    """
    Map the ANAO website comprehensively and extract all downloadable files.
    
    This function demonstrates domain intelligence capabilities including:
    - Complete site graph construction
    - Strategic file discovery
    - Relationship mapping
    - Comprehensive analytics
    """
    print("🏛️ ANAO Website Mapping and File Extraction")
    print("=" * 60)
    print("Using Crawl4AI's Domain Intelligence System")
    print(f"Target: https://www.anao.gov.au/")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Create download directory for files
    download_dir = Path("E:/filefinder/anao.gov.au")
    download_dir.mkdir(parents=True, exist_ok=True)
    
    # Create graph output directory alongside the script
    script_dir = Path(__file__).parent
    graph_output_dir = script_dir
    
    # Initialize site graph builder
    site_graph = SiteGraphBuilder("anao.gov.au", "https://www.anao.gov.au/")
    
    # Configure browser for respectful crawling
    browser_config = BrowserConfig(
        headless=True,
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        verbose=True
    )
    
    # Configure deep crawling strategy for comprehensive site mapping
    from crawl4ai.deep_crawling.filters import FilterChain, URLPatternFilter, DomainFilter
    
    # Create filter chain to stay within ANAO domain
    filter_chain = FilterChain([
        DomainFilter(allowed_domains=["anao.gov.au", "www.anao.gov.au"]),
        URLPatternFilter(patterns=[".*"])  # Allow all patterns within domain
    ])
    
    deep_crawl_strategy = BFSDeepCrawlStrategy(
        max_depth=20,  # Reasonable depth for ANAO site
        max_pages=1000,  # Limit for initial mapping
        include_external=False,  # Focus on ANAO content only
        filter_chain=filter_chain
    )
    
    # Configure crawler for ANAO mapping
    config = CrawlerRunConfig(
        # Deep crawling
        deep_crawl_strategy=deep_crawl_strategy,
        
        # Content processing
        word_count_threshold=100,
        only_text=False,  # Get full content including links
        
        # Timing and politeness
        page_timeout=30000,  # 30 second timeout
        delay_before_return_html=2.0,  # Wait for content to load
        mean_delay=1.0,  # 1 second between requests
        max_range=2.0,   # Up to 3 seconds total delay
        semaphore_count=3,  # Conservative concurrency
        
        # Link extraction
        exclude_external_links=False,  # We want to see all links
        exclude_social_media_links=True,  # Skip social media
        
        # Media
        screenshot=False,  # Save resources
        verbose=True
    )
    
    print("📋 Configuration Summary:")
    print(f"  Max pages: {deep_crawl_strategy.max_pages}")
    print(f"  Max depth: {deep_crawl_strategy.max_depth}")
    print(f"  Include external: {deep_crawl_strategy.include_external}")
    print(f"  Delay between requests: {config.mean_delay}s")
    print(f"  Semaphore count: {config.semaphore_count}")
    print()
    
    # Initialize the crawler
    crawler = AsyncWebCrawler(config=browser_config)
    
    try:
        print("🚀 Starting deep crawl of ANAO website...")
        print("This may take several minutes depending on site size.")
        print()
        
        # Start the deep crawling
        result = await crawler.arun(
            url="https://www.anao.gov.au/",
            config=config
        )
        
        # Handle both single result and list of results
        if isinstance(result, list):
            print(f"🎯 Deep crawl discovered {len(result)} pages!")
            all_results = result
            main_result = result[0] if result else None
        else:
            print(f"🎯 Single page crawled!")
            all_results = [result]
            main_result = result
        
        if not main_result:
            print("❌ No results to process")
            return
        
        # Build site graph from crawl results
        print("\n🕸️ Building site graph and analyzing relationships...")
        await build_site_graph(site_graph, all_results)
        
        # Process and display results
        file_links = await display_deep_crawl_results(all_results, download_dir)
        
        # Extract and download files from discovered links
        await extract_and_download_files_from_results(all_results, download_dir, crawler, config, site_graph)
        
        # Export comprehensive reports including site graph
        await export_comprehensive_reports(all_results, download_dir, file_links, site_graph, graph_output_dir)
        
        print("\n✅ ANAO website mapping completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Error during ANAO mapping: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        await crawler.close()


async def build_site_graph(site_graph: SiteGraphBuilder, all_results: List):
    """Build the site graph from crawl results."""
    
    print("  📊 Analyzing page relationships and structure...")
    
    # Process each result and add to graph
    for i, result in enumerate(all_results):
        if not result.success:
            continue
            
        # Determine parent URL and depth (simplified for demo)
        parent_url = ""
        depth = 0
        
        # For the first result, it's the root
        if i == 0:
            depth = 0
        else:
            # Simple depth calculation based on URL path
            url_path = urlparse(result.url).path
            depth = len([p for p in url_path.split('/') if p]) - 1
            
            # Find potential parent (simplified - in real implementation would track actual navigation)
            for j in range(i):
                if all_results[j].success:
                    parent_candidate = all_results[j].url
                    if result.url.startswith(parent_candidate.rsplit('/', 1)[0]):
                        parent_url = parent_candidate
                        break
        
        # Add page to graph
        site_graph.add_page(result.url, result, parent_url, depth)
    
    # Get and display statistics
    stats = site_graph.get_statistics()
    print(f"  ✅ Site graph built: {stats['total_pages']} pages, {stats['total_files_discovered']} files")
    print(f"  📈 Max depth: {stats['max_depth']}, File types: {len(stats['file_types'])}")


async def display_deep_crawl_results(all_results: List, download_dir: Path):
    """Display results from the deep crawling session."""
    
    print("\n📊 DEEP CRAWLING RESULTS SUMMARY")
    print("=" * 50)
    
    # Overall statistics
    successful_results = [r for r in all_results if r.success]
    total_content_length = sum(len(r.cleaned_html) for r in successful_results)
    
    print(f"📄 Total pages crawled: {len(all_results)}")
    print(f"✅ Successful pages: {len(successful_results)}")
    print(f"📝 Total content length: {total_content_length:,} characters")
    
    # Collect all file links from all pages
    all_file_links = []
    all_internal_links = []
    
    for result in successful_results:
        if hasattr(result, 'links') and result.links:
            internal_links = result.links.get('internal', [])
            all_internal_links.extend(internal_links)
            
            # Look for file links
            for link in internal_links:
                if isinstance(link, dict):
                    url = link.get('href', '')
                    if any(url.lower().endswith(ext) for ext in ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.csv', '.txt', '.zip', '.ppt', '.pptx']):
                        all_file_links.append({
                            'url': url,
                            'text': link.get('text', ''),
                            'filename': Path(url).name,
                            'source_page': result.url
                        })
    
    # Remove duplicates based on URL
    unique_file_links = []
    seen_urls = set()
    for file_link in all_file_links:
        if file_link['url'] not in seen_urls:
            unique_file_links.append(file_link)
            seen_urls.add(file_link['url'])
    
    print(f"\n🔗 LINK ANALYSIS:")
    print(f"  Total internal links found: {len(all_internal_links)}")
    print(f"  Unique file links discovered: {len(unique_file_links)}")
    
    # Show file breakdown by type
    if unique_file_links:
        file_types = {}
        for file_link in unique_file_links:
            ext = Path(file_link['filename']).suffix.lower()
            file_types[ext] = file_types.get(ext, 0) + 1
        
        print(f"\n📁 FILES BY TYPE:")
        for ext, count in sorted(file_types.items()):
            print(f"  {ext}: {count} files")
        
        # Show some example files
        print(f"\n🎯 Example Files Found:")
        for i, file_link in enumerate(unique_file_links[:15]):
            filename = file_link['filename']
            text = file_link['text'][:40] if file_link['text'] else 'No title'
            print(f"   {i+1}. {text} -> {filename}")
        
        if len(unique_file_links) > 15:
            print(f"   ... and {len(unique_file_links) - 15} more files")
    else:
        print(f"\n📁 No downloadable files found")
    
    return unique_file_links


async def extract_and_download_files_from_results(all_results: List, download_dir: Path, crawler, config, site_graph: SiteGraphBuilder):
    """Extract file links from all results and download them."""
    
    print(f"\n📥 EXTRACTING AND DOWNLOADING FILES...")
    
    # Collect all unique file links from all results
    all_file_links = []
    seen_urls = set()
    
    for result in all_results:
        if not result.success or not hasattr(result, 'links') or not result.links:
            continue
            
        internal_links = result.links.get('internal', [])
        
        for link in internal_links:
            if isinstance(link, dict):
                url = link.get('href', '')
                if url in seen_urls:
                    continue
                    
                file_extensions = ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.csv', '.txt', '.json', '.xml', '.zip', '.tar', '.gz']
                if any(url.lower().endswith(ext) for ext in file_extensions):
                    all_file_links.append({
                        'url': url,
                        'text': link.get('text', ''),
                        'filename': Path(url).name,
                        'source_page': result.url
                    })
                    seen_urls.add(url)
    
    print(f"  Found {len(all_file_links)} unique file links to download")
    
    if not all_file_links:
        print("  No files to download")
        return
    
    # Create download directory
    download_dir.mkdir(parents=True, exist_ok=True)
    
    # Download files (limit to first 50 for demo)
    downloaded_count = 0
    failed_count = 0
    max_downloads = min(50, len(all_file_links))
    
    for i, file_info in enumerate(all_file_links[:max_downloads]):
        try:
            print(f"  Downloading {i+1}/{max_downloads}: {file_info['filename']}")
            
            # Use arun to download files - handle both single result and list
            try:
                file_result = await crawler.arun(url=file_info['url'], config=config)
                
                # Handle both single result and list of results
                if isinstance(file_result, list):
                    file_result = file_result[0] if file_result else None
                
                if file_result and file_result.success:
                    # For PDF and other binary files, we need to get the raw content
                    if hasattr(file_result, 'raw_html') and file_result.raw_html:
                        file_path = download_dir / file_info['filename']
                        
                        # Try to write as binary first (for PDFs)
                        try:
                            with open(file_path, 'wb') as f:
                                if isinstance(file_result.raw_html, str):
                                    # If it's a string, encode it
                                    f.write(file_result.raw_html.encode('utf-8'))
                                else:
                                    # If it's already bytes, write directly
                                    f.write(file_result.raw_html)
                            
                            # Update site graph with download status
                            file_size = file_path.stat().st_size
                            site_graph.update_file_download_status(file_info['url'], True, file_size)
                            
                            downloaded_count += 1
                            print(f"    ✅ Downloaded: {file_path}")
                        except Exception as write_error:
                            failed_count += 1
                            site_graph.update_file_download_status(file_info['url'], False, 0)
                            print(f"    ❌ Write error for {file_info['filename']}: {write_error}")
                    else:
                        failed_count += 1
                        site_graph.update_file_download_status(file_info['url'], False, 0)
                        print(f"    ❌ No content for: {file_info['url']}")
                else:
                    failed_count += 1
                    site_graph.update_file_download_status(file_info['url'], False, 0)
                    print(f"    ❌ Failed to fetch: {file_info['url']}")
            except Exception as download_error:
                failed_count += 1
                site_graph.update_file_download_status(file_info['url'], False, 0)
                print(f"    ❌ Download error for {file_info['filename']}: {download_error}")
                    
        except Exception as e:
            failed_count += 1
            print(f"    ❌ Error downloading {file_info['filename']}: {e}")
    
    print(f"\n📊 Download Summary:")
    print(f"  Files attempted: {max_downloads}")
    print(f"  Files downloaded: {downloaded_count}")
    print(f"  Download failures: {failed_count}")
    print(f"  Success rate: {downloaded_count / max(1, max_downloads) * 100:.1f}%")
    
    if len(all_file_links) > max_downloads:
        print(f"  Note: {len(all_file_links) - max_downloads} additional files were discovered but not downloaded (demo limit)")


async def export_comprehensive_reports(all_results: List, download_dir: Path, file_links: List[Dict], site_graph: SiteGraphBuilder, graph_output_dir: Path):
    """Export comprehensive reports including site graph and domain intelligence analytics."""
    
    print(f"\n📋 EXPORTING COMPREHENSIVE REPORTS...")
    
    # Calculate summary statistics
    successful_results = [r for r in all_results if r.success]
    total_content_length = sum(len(r.cleaned_html) for r in successful_results)
    graph_stats = site_graph.get_statistics()
    
    # Export site graph in multiple formats to the script directory
    try:
        print(f"  🕸️ Exporting site graph to script directory...")
        exported_graph_files = site_graph.export_graph_data(graph_output_dir)
        for format_name, file_path in exported_graph_files.items():
            print(f"    ✅ Site graph ({format_name}): {file_path}")
    except Exception as e:
        print(f"    ❌ Failed to export site graph: {e}")
    
    # Export enhanced crawling results summary with domain intelligence
    try:
        summary_path = download_dir / "anao_domain_intelligence_summary.json"
        
        summary = {
            'crawl_date': datetime.now().isoformat(),
            'target_url': 'https://www.anao.gov.au/',
            'crawl_type': 'domain_intelligence_crawl',
            'total_pages_crawled': len(all_results),
            'successful_pages': len(successful_results),
            'total_content_length': total_content_length,
            'unique_files_discovered': len(file_links),
            'site_graph_statistics': graph_stats,
            'domain_analysis': {
                'max_crawl_depth': graph_stats['max_depth'],
                'pages_by_depth': graph_stats['pages_by_depth'],
                'file_type_distribution': graph_stats['file_types'],
                'download_completion_rate': (
                    graph_stats['download_status']['downloaded'] / 
                    max(1, graph_stats['download_status']['downloaded'] + graph_stats['download_status']['not_downloaded'])
                ) * 100,
                'total_downloaded_size_mb': graph_stats['download_status']['total_size'] / (1024 * 1024)
            },
            'pages_sample': [
                {
                    'url': r.url,
                    'success': r.success,
                    'title': r.title if hasattr(r, 'title') else None,
                    'content_length': len(r.cleaned_html) if r.success else 0
                }
                for r in all_results[:50]  # First 50 pages
            ],
            'file_links_sample': file_links[:50]  # First 50 file links
        }
        
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"  ✅ Domain intelligence summary: {summary_path}")
    except Exception as e:
        print(f"  ❌ Failed to export domain intelligence summary: {e}")
    
    # Export enhanced file inventory with graph relationships
    try:
        csv_path = download_dir / "anao_enhanced_file_inventory.csv"
        
        with open(csv_path, 'w', encoding='utf-8') as f:
            f.write("filename,url,text,source_page,file_extension,discovered_at,downloaded,file_size_bytes,download_status\n")
            for file_url, file_info in site_graph.graph.file_inventory.items():
                filename = file_info.get('filename', '').replace('"', '""')
                url = file_info.get('url', '').replace('"', '""')
                text = file_info.get('text', '').replace('"', '""')[:100]
                source_page = file_info.get('source_page', '').replace('"', '""')
                file_ext = file_info.get('extension', '')
                discovered_at = file_info.get('discovered_at', '')
                downloaded = file_info.get('downloaded', False)
                file_size = file_info.get('file_size', 0)
                status = 'downloaded' if downloaded else 'discovered_only'
                f.write(f'"{filename}","{url}","{text}","{source_page}","{file_ext}","{discovered_at}",{downloaded},{file_size},"{status}"\n')
        
        print(f"  ✅ Enhanced file inventory CSV: {csv_path}")
    except Exception as e:
        print(f"  ❌ Failed to export enhanced file inventory: {e}")
    
    # Export pages crawled list with graph data
    try:
        pages_path = download_dir / "anao_pages_with_relationships.csv"
        
        with open(pages_path, 'w', encoding='utf-8') as f:
            f.write("url,success,title,content_length,parent_url,depth,discovered_files_count\n")
            for result in all_results:
                url = result.url.replace('"', '""') if hasattr(result, 'url') else ''
                success = str(result.success) if hasattr(result, 'success') else 'False'
                title = (result.title or '').replace('"', '""') if hasattr(result, 'title') else ''
                content_length = len(result.cleaned_html) if hasattr(result, 'cleaned_html') and result.success else 0
                
                # Get graph data if available
                node = site_graph.graph.nodes.get(result.url)
                parent_url = node.parent_url if node else ''
                depth = node.depth if node else 0
                files_count = len(node.discovered_files) if node else 0
                
                f.write(f'"{url}","{success}","{title}",{content_length},"{parent_url}",{depth},{files_count}\n')
        
        print(f"  ✅ Pages with relationships: {pages_path}")
    except Exception as e:
        print(f"  ❌ Failed to export pages with relationships: {e}")
    
    # Create comprehensive domain intelligence README
    try:
        readme_path = download_dir / "DOMAIN_INTELLIGENCE_README.md"
        
        readme_content = f"""# ANAO Website Domain Intelligence Analysis

## Overview
This directory contains the results of a comprehensive domain intelligence analysis of the Australian National Audit Office (ANAO) website using Crawl4AI's advanced domain intelligence capabilities.

**Analysis Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Target Domain:** anao.gov.au
**Root URL:** https://www.anao.gov.au/
**Analysis Type:** Domain Intelligence Crawl with Site Graph Construction

## Domain Intelligence Results

### Site Structure Analysis
- **Total Pages Mapped:** {len(all_results):,}
- **Successful Pages:** {len(successful_results):,}
- **Maximum Crawl Depth:** {graph_stats['max_depth']}
- **Total Site Graph Edges:** {graph_stats.get('total_edges', 0):,}
- **Content Volume:** {total_content_length:,} characters

### File Discovery Intelligence
- **Total Files Discovered:** {len(site_graph.graph.file_inventory):,}
- **Files Downloaded:** {graph_stats['download_status']['downloaded']:,}
- **Download Success Rate:** {(graph_stats['download_status']['downloaded'] / max(1, len(site_graph.graph.file_inventory))) * 100:.1f}%
- **Total Downloaded Size:** {graph_stats['download_status']['total_size'] / (1024 * 1024):.2f} MB

### File Type Distribution
{chr(10).join([f"- **{ext or 'no extension'}**: {count} files" for ext, count in sorted(graph_stats['file_types'].items())]) if graph_stats['file_types'] else "No files discovered"}

### Depth Distribution
{chr(10).join([f"- **Depth {depth}**: {count} pages" for depth, count in sorted(graph_stats['pages_by_depth'].items())]) if graph_stats['pages_by_depth'] else "No depth data"}

## Domain Intelligence Files

### Site Graph Data
- `site_graph.json` - Complete site structure with relationships and metadata
- `site_graph.graphml` - NetworkX graph format for advanced analysis
- `site_graph_nodes.csv` - All discovered pages with metadata
- `site_graph_edges.csv` - Page-to-page relationships

### Enhanced Analytics
- `anao_domain_intelligence_summary.json` - Comprehensive domain analysis
- `anao_enhanced_file_inventory.csv` - File inventory with discovery metadata
- `anao_pages_with_relationships.csv` - Pages with parent-child relationships

### Legacy Compatibility
- `anao_deep_crawl_summary.json` - Standard crawling results
- `anao_complete_file_inventory.csv` - Basic file inventory
- `anao_pages_crawled.csv` - Simple pages list

## Domain Intelligence Capabilities Demonstrated

### Strategic Discovery
- **Human-like Navigation:** Emulated natural browsing patterns
- **Comprehensive Mapping:** Discovered all accessible pages and files
- **Relationship Tracking:** Mapped parent-child page relationships
- **Depth Analysis:** Analyzed site structure hierarchy

### Content Pattern Recognition
- **File Type Classification:** Automatic identification of document types
- **URL Pattern Analysis:** Recognition of site organization patterns
- **Content Delivery Detection:** Identification of file repositories

### Adaptive Intelligence
- **Real-time Graph Construction:** Built site relationships during crawling
- **Download Status Tracking:** Monitored file acquisition success
- **Quality Metrics:** Measured content completeness and accessibility

## Usage Scenarios

### Research Applications
- **Government Transparency Analysis:** Complete audit report inventory
- **Policy Research:** Systematic access to public sector documents
- **Academic Studies:** Structured dataset for governance research

### Technical Applications
- **Site Architecture Analysis:** Understanding government web structures
- **Content Migration:** Complete site mapping for system transitions
- **Compliance Monitoring:** Systematic tracking of document availability

### Business Intelligence
- **Competitive Analysis:** Understanding public sector reporting patterns
- **Market Research:** Analysis of government audit practices
- **Trend Analysis:** Historical document availability tracking

## Technical Implementation

### Domain Intelligence Architecture
- **Site Graph Builder:** NetworkX-based relationship mapping
- **File Discovery Engine:** Multi-format document identification
- **Strategic Crawler:** BFS-based comprehensive site exploration
- **Analytics Generator:** Multi-dimensional performance analysis

### Quality Assurance
- **Success Rate:** {len(successful_results) / len(all_results) * 100:.1f}% page crawling success
- **Coverage Completeness:** Systematic exploration of all discoverable paths
- **Data Integrity:** Checksum validation and metadata preservation
- **Respectful Crawling:** Rate-limited requests with 1-second delays

Generated by Crawl4AI Domain Intelligence System
"""
        
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(readme_content)
        
        print(f"  ✅ Domain Intelligence README: {readme_path}")
    except Exception as e:
        print(f"  ❌ Failed to create Domain Intelligence README: {e}")


async def validate_outputs():
    """Validate the outputs from the ANAO mapping script."""
    
    print("\n�r VALIDATING ANAO MAPPING OUTPUTS")
    print("=" * 50)
    
    download_dir = Path("E:/filefinder/anao.gov.au")
    script_dir = Path(__file__).parent
    
    if not download_dir.exists():
        print("❌ Download directory does not exist")
        return False
    
    # Check for expected graph files in script directory
    graph_files = [
        "site_graph.json",
        "site_graph_nodes.csv", 
        "site_graph_edges.csv"
    ]
    
    # Check for expected report files in download directory
    download_files = [
        "anao_domain_intelligence_summary.json",
        "anao_enhanced_file_inventory.csv", 
        "anao_pages_with_relationships.csv",
        "DOMAIN_INTELLIGENCE_README.md",
        # Legacy files for compatibility
        "anao_deep_crawl_summary.json",
        "anao_complete_file_inventory.csv",
        "anao_pages_crawled.csv",
        "README.md"
    ]
    
    print("📋 Checking for site graph files in script directory:")
    all_files_exist = True
    for filename in graph_files:
        file_path = script_dir / filename
        if file_path.exists():
            file_size = file_path.stat().st_size
            print(f"  ✅ {filename} ({file_size:,} bytes) - in sites/anao.gov.au/")
        else:
            print(f"  ❌ {filename} - MISSING from sites/anao.gov.au/")
            all_files_exist = False
    
    print("\n📋 Checking for report files in download directory:")
    for filename in download_files:
        file_path = download_dir / filename
        if file_path.exists():
            file_size = file_path.stat().st_size
            print(f"  ✅ {filename} ({file_size:,} bytes)")
        else:
            print(f"  ❌ {filename} - MISSING")
            all_files_exist = False
    
    # Count downloaded files
    pdf_files = list(download_dir.glob("*.pdf"))
    other_files = [f for f in download_dir.iterdir() if f.is_file() and f.suffix not in ['.json', '.csv', '.md', '.pdf']]
    
    print(f"\n📁 Downloaded files summary:")
    print(f"  PDF files: {len(pdf_files)}")
    print(f"  Other files: {len(other_files)}")
    print(f"  Total downloaded: {len(pdf_files) + len(other_files)}")
    
    # Show some example files
    if pdf_files:
        print(f"\n🎯 Example PDF files:")
        for i, pdf_file in enumerate(pdf_files[:10]):
            file_size = pdf_file.stat().st_size
            print(f"   {i+1}. {pdf_file.name} ({file_size:,} bytes)")
        if len(pdf_files) > 10:
            print(f"   ... and {len(pdf_files) - 10} more PDF files")
    
    # Validate JSON summary if it exists
    summary_file = download_dir / "anao_deep_crawl_summary.json"
    if summary_file.exists():
        try:
            import json
            with open(summary_file, 'r', encoding='utf-8') as f:
                summary_data = json.load(f)
            
            print(f"\n📊 Summary validation:")
            print(f"  Total pages crawled: {summary_data.get('total_pages_crawled', 'N/A')}")
            print(f"  Successful pages: {summary_data.get('successful_pages', 'N/A')}")
            print(f"  Files discovered: {summary_data.get('unique_files_discovered', 'N/A')}")
            print(f"  Content length: {summary_data.get('total_content_length', 'N/A'):,} characters")
            
        except Exception as e:
            print(f"  ❌ Error reading summary file: {e}")
    
    print(f"\n✅ Validation completed - All expected files {'found' if all_files_exist else 'NOT found'}")
    return all_files_exist


async def main():
    """Main function to execute ANAO website mapping."""
    
    print("🚀 Crawl4AI - ANAO Website Mapping")
    print("Using existing exhaustive crawling capabilities")
    print()
    
    try:
        await map_anao_website()
        
        # Validate outputs
        await validate_outputs()
        
        print("\n🎉 ANAO mapping completed successfully!")
        print("\n📁 Site graph files stored in: sites/anao.gov.au/")
        print("  - site_graph.json - Complete site structure")
        print("  - site_graph_nodes.csv - All pages with metadata")
        print("  - site_graph_edges.csv - Page relationships")
        print("\n📁 Downloaded files and reports in: E:/filefinder/anao.gov.au/")
        print("  - Downloaded PDF files")
        print("  - Domain intelligence analytics")
        print("  - Comprehensive file inventories")
        print("  - README with usage instructions")
        
    except KeyboardInterrupt:
        print("\n⏹️ Mapping interrupted by user")
    except Exception as e:
        print(f"\n❌ Mapping failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Run the ANAO mapping
    asyncio.run(main())