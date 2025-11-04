"""
Site Graph Database Example

This example demonstrates how to use the site graph database functionality
to track discovered URLs, file metadata, and crawling progress.
"""

import asyncio
from datetime import datetime
from crawl4ai.async_database import async_db_manager
from crawl4ai.site_graph_db import URLNode, SiteGraphStats, create_site_graph_manager


async def main():
    """Demonstrate site graph database functionality"""
    
    # Initialize the database manager
    await async_db_manager.initialize()
    
    # Create site graph manager
    site_graph_manager = create_site_graph_manager()
    
    # Example base URL
    base_url = "https://example.com"
    
    print("=== Site Graph Database Example ===\n")
    
    # 1. Store discovered URLs
    print("1. Storing discovered URLs...")
    
    # Store a regular page URL
    page_url = URLNode(
        url=f"{base_url}/about",
        source_url=base_url,
        discovered_at=datetime.now(),
        status_code=200,
        content_type="text/html",
        is_file=False
    )
    await site_graph_manager.store_discovered_url(page_url)
    
    # Store a file URL
    file_url = URLNode(
        url=f"{base_url}/documents/report.pdf",
        source_url=f"{base_url}/about",
        discovered_at=datetime.now(),
        status_code=200,
        content_type="application/pdf",
        file_size=1024000,  # 1MB
        is_file=True,
        file_extension=".pdf",
        download_status="not_attempted"
    )
    await site_graph_manager.store_discovered_url(file_url)
    
    print("✓ URLs stored successfully")
    
    # 2. Retrieve discovered URL
    print("\n2. Retrieving discovered URL...")
    retrieved_url = await site_graph_manager.get_discovered_url(f"{base_url}/about")
    if retrieved_url:
        print(f"✓ Retrieved URL: {retrieved_url.url}")
        print(f"  Status: {retrieved_url.status_code}")
        print(f"  Content Type: {retrieved_url.content_type}")
    
    # 3. Update URL status
    print("\n3. Updating URL status...")
    await site_graph_manager.update_url_status(
        url=f"{base_url}/about",
        status_code=200,
        content_type="text/html",
        file_size=5000
    )
    print("✓ URL status updated")
    
    # 4. Update file download status
    print("\n4. Updating file download status...")
    await site_graph_manager.update_file_download_status(
        url=f"{base_url}/documents/report.pdf",
        download_status="completed",
        local_path="/downloads/report.pdf",
        checksum="abc123def456"
    )
    print("✓ File download status updated")
    
    # 5. Get files by status
    print("\n5. Getting files by download status...")
    completed_files = await site_graph_manager.get_files_by_status("completed", base_url)
    print(f"✓ Found {len(completed_files)} completed files")
    for file in completed_files:
        print(f"  - {file.url} -> {file.local_path}")
    
    # 6. Store site graph statistics
    print("\n6. Storing site graph statistics...")
    stats = SiteGraphStats(
        base_url=base_url,
        total_urls_discovered=10,
        total_files_discovered=3,
        total_files_downloaded=1,
        crawl_start_time=datetime.now(),
        dead_end_count=2,
        revisit_ratio=0.15
    )
    await site_graph_manager.store_site_graph_stats(stats)
    print("✓ Site graph statistics stored")
    
    # 7. Retrieve site graph
    print("\n7. Retrieving complete site graph...")
    site_graph = await site_graph_manager.get_site_graph(base_url)
    print(f"✓ Site graph retrieved:")
    print(f"  Total URLs: {site_graph['total_urls']}")
    print(f"  Total Files: {site_graph['total_files']}")
    
    # 8. Get crawl progress
    print("\n8. Getting crawl progress...")
    progress = await site_graph_manager.get_crawl_progress(base_url)
    print(f"✓ Crawl progress:")
    print(f"  Base URL: {progress['base_url']}")
    if progress.get('file_progress'):
        fp = progress['file_progress']
        print(f"  File Progress: {fp['completed']}/{fp['total_files']} ({fp['progress_percentage']:.1f}%)")
    
    # 9. Get site statistics
    print("\n9. Retrieving site statistics...")
    retrieved_stats = await site_graph_manager.get_site_graph_stats(base_url)
    if retrieved_stats:
        print(f"✓ Site statistics:")
        print(f"  URLs discovered: {retrieved_stats.total_urls_discovered}")
        print(f"  Files discovered: {retrieved_stats.total_files_discovered}")
        print(f"  Files downloaded: {retrieved_stats.total_files_downloaded}")
        print(f"  Dead end count: {retrieved_stats.dead_end_count}")
        print(f"  Revisit ratio: {retrieved_stats.revisit_ratio:.2f}")
    
    print("\n=== Site Graph Database Example Complete ===")


if __name__ == "__main__":
    asyncio.run(main())