"""
Example demonstrating FileDiscoveryFilter integration with existing filter architecture.

This example shows how to use the FileDiscoveryFilter with the existing FilterChain
to discover and catalog downloadable files during crawling operations.
"""

import asyncio
import crawl4ai
from crawl4ai.file_discovery_filter import (
    FileDiscoveryFilter, FileType, 
    create_document_filter, create_data_filter, create_comprehensive_filter
)
from crawl4ai.deep_crawling.filters import FilterChain, URLPatternFilter, DomainFilter
from crawl4ai.async_logger import AsyncLogger


async def main():
    """Demonstrate FileDiscoveryFilter usage and integration."""
    
    # Create a logger for detailed output
    logger = AsyncLogger(verbose=True)
    
    print("=== FileDiscoveryFilter Integration Example ===\n")
    
    # Example 1: Basic file discovery filter
    print("1. Basic Document Filter:")
    doc_filter = create_document_filter(logger=logger)
    
    test_urls = [
        "https://example.com/documents/report.pdf",
        "https://example.com/files/manual.doc",
        "https://example.com/downloads/presentation.pptx",
        "https://example.com/page.html",  # Should be rejected
        "https://example.com/image.jpg",  # Should be rejected (not document)
    ]
    
    for url in test_urls:
        result = doc_filter.apply(url)
        print(f"  {url} -> {'✓ Accepted' if result else '✗ Rejected'}")
    
    print(f"\nDiscovered {len(doc_filter.discovered_files)} document files")
    
    # Example 2: Custom filter with specific extensions
    print("\n2. Custom Filter (PDF and Excel only):")
    custom_filter = FileDiscoveryFilter(
        target_extensions=['.pdf', '.xlsx'],
        logger=logger,
        name="PDFExcelFilter"
    )
    
    custom_urls = [
        "https://example.com/report.pdf",
        "https://example.com/data.xlsx", 
        "https://example.com/document.doc",  # Should be rejected
        "https://example.com/presentation.pptx",  # Should be rejected
    ]
    
    for url in custom_urls:
        result = custom_filter.apply(url)
        print(f"  {url} -> {'✓ Accepted' if result else '✗ Rejected'}")
    
    # Example 3: Integration with FilterChain
    print("\n3. Integration with FilterChain:")
    
    # Create a comprehensive filter chain
    filter_chain = FilterChain([
        DomainFilter(allowed_domains=["example.com", "docs.example.com"]),
        URLPatternFilter(patterns=["*/downloads/*", "*/files/*", "*/documents/*"]),
        create_comprehensive_filter(logger=logger)
    ])
    
    chain_test_urls = [
        "https://example.com/downloads/report.pdf",  # Should pass all filters
        "https://docs.example.com/files/manual.doc",  # Should pass all filters
        "https://other.com/downloads/file.pdf",  # Should fail domain filter
        "https://example.com/other/file.pdf",  # Should fail pattern filter
        "https://example.com/downloads/page.html",  # Should fail file filter
    ]
    
    for url in chain_test_urls:
        result = await filter_chain.apply(url)
        print(f"  {url} -> {'✓ Passed chain' if result else '✗ Failed chain'}")
    
    # Example 4: Repository analysis
    print("\n4. Repository Analysis:")
    repo_filter = FileDiscoveryFilter(
        target_file_types=[FileType.DOCUMENT, FileType.DATA],
        track_repository_paths=True,
        logger=logger
    )
    
    repo_urls = [
        "https://example.com/downloads/report1.pdf",
        "https://example.com/downloads/report2.pdf", 
        "https://example.com/files/data.json",
        "https://example.com/attachments/manual.doc",
        "https://example.com/other/path/file.csv",
    ]
    
    for url in repo_urls:
        repo_filter.apply(url)
    
    # Show repository inventory
    inventory = repo_filter.get_repository_inventory()
    print("Repository inventory:")
    for repo_path, files in inventory.items():
        print(f"  {repo_path}: {len(files)} files")
        for file_meta in files:
            print(f"    - {file_meta.filename} ({file_meta.file_type.value})")
    
    # Example 5: Statistics and export
    print("\n5. Discovery Statistics:")
    stats = repo_filter.get_discovery_stats()
    print(f"Total files discovered: {stats.total_files_discovered}")
    print("Files by type:")
    for file_type, count in stats.files_by_type.items():
        print(f"  {file_type.value}: {count}")
    
    print("Files by extension:")
    for ext, count in stats.files_by_extension.items():
        print(f"  {ext}: {count}")
    
    # Example 6: Export inventory
    print("\n6. Export Inventory (JSON format):")
    json_export = repo_filter.export_file_inventory("json")
    print("JSON export preview (first 200 chars):")
    print(json_export[:200] + "..." if len(json_export) > 200 else json_export)
    
    print("\n=== Example Complete ===")


if __name__ == "__main__":
    asyncio.run(main())