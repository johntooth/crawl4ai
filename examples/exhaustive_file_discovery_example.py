#!/usr/bin/env python3
"""
Exhaustive File Discovery Integration Example

This example demonstrates how to use the integrated file discovery and exhaustive
crawling workflow to comprehensively map a website while discovering and downloading
all available files.

Features demonstrated:
- Exhaustive site crawling with file discovery
- Concurrent file downloading during crawling
- File organization and metadata extraction
- Real-time progress monitoring
- Comprehensive reporting of discovered files
"""

import asyncio
import json
from pathlib import Path
from typing import Dict, Any

from crawl4ai.exhaustive_file_integration import (
    ExhaustiveFileDiscoveryCrawler,
    create_document_focused_crawler,
    create_comprehensive_file_crawler
)
from crawl4ai.exhaustive_configs import ExhaustiveCrawlConfig
from crawl4ai.file_discovery_filter import FileType
from crawl4ai.async_logger import AsyncLogger


async def basic_file_discovery_example():
    """
    Basic example of exhaustive crawling with file discovery.
    
    This example shows how to crawl a website exhaustively while discovering
    and downloading files in real-time.
    """
    print("🔍 Basic File Discovery Example")
    print("=" * 50)
    
    # Create a document-focused crawler
    crawler = create_document_focused_crawler(
        download_directory="./downloads/basic_example",
        max_concurrent_downloads=3
    )
    
    try:
        # Configure exhaustive crawling
        config = ExhaustiveCrawlConfig(
            exhaustive_max_pages=100,  # Limit for example
            dead_end_threshold=10,
            revisit_ratio=0.9,
            log_discovery_stats=True
        )
        
        # Run exhaustive crawling with file discovery
        print("Starting exhaustive crawl with file discovery...")
        results = await crawler.arun_exhaustive_with_files(
            start_url="https://example.com",  # Replace with actual URL
            config=config,
            enable_file_discovery=True,
            enable_file_download=True
        )
        
        # Display results
        print(f"\n📊 Crawling Results:")
        print(f"  Pages crawled: {results['total_pages_crawled']}")
        print(f"  URLs discovered: {results['total_urls_discovered']}")
        print(f"  Stop reason: {results['stop_reason']}")
        
        # Display file discovery results
        file_stats = results['file_discovery']['discovery_stats']
        print(f"\n📁 File Discovery Results:")
        print(f"  Total files discovered: {file_stats['total_files_discovered']}")
        print(f"  Files by type: {file_stats['files_by_type']}")
        print(f"  Repository paths found: {len(file_stats['repository_paths'])}")
        
        # Display download results
        if results['download_stats']:
            download_stats = results['download_stats']
            print(f"\n⬇️ Download Results:")
            print(f"  Files downloaded: {download_stats['completed']}")
            print(f"  Download failures: {download_stats['failed']}")
            print(f"  Success rate: {download_stats['success_rate']:.1f}%")
            print(f"  Total bytes downloaded: {download_stats['total_bytes_downloaded']:,}")
        
    finally:
        await crawler.close()


async def comprehensive_file_discovery_example():
    """
    Comprehensive example with all file types and advanced configuration.
    
    This example demonstrates advanced file discovery with custom configuration,
    priority handling, and detailed monitoring.
    """
    print("\n🔍 Comprehensive File Discovery Example")
    print("=" * 50)
    
    # Create comprehensive file crawler with custom configuration
    file_config = {
        'target_file_types': list(FileType),  # All file types
        'max_file_size_mb': 50,  # Limit file size
        'enable_mime_validation': True,
        'track_repository_paths': True
    }
    
    download_config = {
        'download_directory': "./downloads/comprehensive_example",
        'max_concurrent_downloads': 5,
        'max_queue_size': 500,
        'organize_by_type': True,
        'organize_by_source': True
    }
    
    crawler = ExhaustiveFileDiscoveryCrawler(
        file_discovery_config=file_config,
        download_config=download_config
    )
    
    try:
        # Configure for comprehensive crawling
        config = ExhaustiveCrawlConfig(
            exhaustive_max_pages=500,
            exhaustive_max_depth=50,
            dead_end_threshold=25,
            revisit_ratio=0.95,
            log_discovery_stats=True,
            batch_size=10
        )
        
        print("Starting comprehensive file discovery crawl...")
        
        # Monitor progress during crawling
        async def monitor_progress():
            """Monitor crawling and download progress."""
            while True:
                await asyncio.sleep(10)  # Check every 10 seconds
                
                # Get current stats
                file_stats = crawler.get_file_discovery_stats()
                download_stats = crawler.get_download_stats()
                progress = crawler.get_progress_tracking()
                
                print(f"\n📈 Progress Update:")
                print(f"  Pages crawled: {progress['pages_crawled']}")
                print(f"  Files discovered: {file_stats.total_files_discovered}")
                print(f"  Downloads completed: {download_stats['completed']}")
                print(f"  Downloads active: {download_stats['active']}")
                print(f"  Queue size: {download_stats['queue_size']}")
                
                # Stop monitoring if crawling is complete
                if not progress['session_active']:
                    break
        
        # Start monitoring task
        monitor_task = asyncio.create_task(monitor_progress())
        
        # Run crawling
        results = await crawler.arun_exhaustive_with_files(
            start_url="https://example.com",  # Replace with actual URL
            config=config,
            enable_file_discovery=True,
            enable_file_download=True
        )
        
        # Stop monitoring
        monitor_task.cancel()
        
        # Display comprehensive results
        print(f"\n🎯 Final Results:")
        print(f"  Total pages crawled: {results['total_pages_crawled']}")
        print(f"  Successful pages: {results['successful_pages']}")
        print(f"  URLs discovered: {results['total_urls_discovered']}")
        print(f"  Crawl duration: {results['analytics']['session_stats']['crawl_duration']}")
        
        # File discovery breakdown
        file_discovery = results['file_discovery']
        print(f"\n📂 File Discovery Breakdown:")
        for file_type, count in file_discovery['discovery_stats']['files_by_type'].items():
            print(f"  {file_type}: {count} files")
        
        # Repository analysis
        repositories = file_discovery['repository_inventory']
        print(f"\n🗂️ Repository Analysis:")
        for repo_path, files in repositories.items():
            print(f"  {repo_path}: {len(files)} files")
        
        # Download performance
        download_stats = results['download_stats']
        if download_stats:
            print(f"\n⚡ Download Performance:")
            print(f"  Success rate: {download_stats['success_rate']:.1f}%")
            print(f"  Total data downloaded: {download_stats['total_bytes_downloaded']:,} bytes")
            print(f"  Average file size: {download_stats['total_bytes_downloaded'] // max(1, download_stats['completed']):,} bytes")
        
        # Export file inventory
        inventory = crawler.export_file_inventory("dict")
        inventory_path = Path("./downloads/comprehensive_example/file_inventory.json")
        inventory_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(inventory_path, 'w') as f:
            json.dump(inventory, f, indent=2)
        
        print(f"\n💾 File inventory exported to: {inventory_path}")
        
    finally:
        await crawler.close()


async def targeted_file_discovery_example():
    """
    Example of targeted file discovery for specific file types and patterns.
    
    This example shows how to configure the crawler for specific file types
    and repository patterns, useful for focused data collection.
    """
    print("\n🎯 Targeted File Discovery Example")
    print("=" * 50)
    
    # Configure for specific file types only
    file_config = {
        'target_file_types': [FileType.DOCUMENT, FileType.DATA],
        'repository_patterns': [
            r'/documents?/',
            r'/files?/',
            r'/downloads?/',
            r'/reports?/',
            r'/publications?/'
        ],
        'exclude_extensions': ['.exe', '.dmg', '.msi'],  # Security exclusions
        'max_file_size_mb': 25
    }
    
    download_config = {
        'download_directory': "./downloads/targeted_example",
        'max_concurrent_downloads': 3,
        'organize_by_type': True
    }
    
    crawler = ExhaustiveFileDiscoveryCrawler(
        file_discovery_config=file_config,
        download_config=download_config
    )
    
    try:
        # Configure for focused crawling
        config = ExhaustiveCrawlConfig(
            exhaustive_max_pages=200,
            dead_end_threshold=15,
            revisit_ratio=0.9,
            log_discovery_stats=True
        )
        
        print("Starting targeted file discovery...")
        results = await crawler.arun_exhaustive_with_files(
            start_url="https://example.com",  # Replace with actual URL
            config=config,
            enable_file_discovery=True,
            enable_file_download=True
        )
        
        # Analyze targeted results
        file_discovery = results['file_discovery']
        
        print(f"\n🎯 Targeted Discovery Results:")
        print(f"  Documents found: {file_discovery['discovery_stats']['files_by_type'].get('document', 0)}")
        print(f"  Data files found: {file_discovery['discovery_stats']['files_by_type'].get('data', 0)}")
        
        # Show repository-specific results
        repositories = file_discovery['repository_inventory']
        print(f"\n📁 Repository-Specific Results:")
        for repo_path, files in repositories.items():
            if repo_path != "unknown":
                print(f"  {repo_path}:")
                for file_info in files[:5]:  # Show first 5 files
                    print(f"    - {file_info['filename']} ({file_info['file_type']})")
                if len(files) > 5:
                    print(f"    ... and {len(files) - 5} more files")
        
        # Export targeted inventory
        csv_inventory = crawler.export_file_inventory("csv")
        csv_path = Path("./downloads/targeted_example/targeted_inventory.csv")
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(csv_path, 'w') as f:
            f.write(csv_inventory)
        
        print(f"\n💾 Targeted inventory exported to: {csv_path}")
        
    finally:
        await crawler.close()


async def file_discovery_with_custom_organization():
    """
    Example showing custom file organization and metadata extraction.
    
    This example demonstrates how to organize downloaded files by source domain,
    file type, and discovery date for better file management.
    """
    print("\n📁 Custom File Organization Example")
    print("=" * 50)
    
    # Custom organization configuration
    download_config = {
        'download_directory': "./downloads/organized_example",
        'max_concurrent_downloads': 4,
        'organize_by_type': True,
        'organize_by_source': True
    }
    
    crawler = create_comprehensive_file_crawler(**download_config)
    
    try:
        config = ExhaustiveCrawlConfig(
            exhaustive_max_pages=150,
            dead_end_threshold=20,
            log_discovery_stats=True
        )
        
        print("Starting crawl with custom file organization...")
        results = await crawler.arun_exhaustive_with_files(
            start_url="https://example.com",  # Replace with actual URL
            config=config,
            enable_file_discovery=True,
            enable_file_download=True
        )
        
        # Analyze organization results
        download_dir = Path("./downloads/organized_example")
        if download_dir.exists():
            print(f"\n📂 File Organization Structure:")
            
            # Walk through organized directories
            for root, dirs, files in download_dir.walk():
                level = len(root.parts) - len(download_dir.parts)
                indent = "  " * level
                print(f"{indent}{root.name}/")
                
                # Show files in directory
                sub_indent = "  " * (level + 1)
                for file in files[:3]:  # Show first 3 files
                    print(f"{sub_indent}- {file}")
                if len(files) > 3:
                    print(f"{sub_indent}... and {len(files) - 3} more files")
        
        print(f"\n📊 Organization Summary:")
        download_stats = results['download_stats']
        if download_stats:
            print(f"  Total files organized: {download_stats['completed']}")
            print(f"  Organization success rate: {download_stats['success_rate']:.1f}%")
        
    finally:
        await crawler.close()


async def main():
    """
    Main function to run all file discovery examples.
    
    This function demonstrates the complete workflow of integrating file discovery
    with exhaustive crawling, showing various configuration options and use cases.
    """
    print("🚀 Exhaustive File Discovery Integration Examples")
    print("=" * 60)
    print("This example demonstrates comprehensive file discovery during exhaustive crawling.")
    print("Note: Replace 'https://example.com' with actual URLs for testing.")
    print()
    
    try:
        # Run basic example
        await basic_file_discovery_example()
        
        # Run comprehensive example
        await comprehensive_file_discovery_example()
        
        # Run targeted example
        await targeted_file_discovery_example()
        
        # Run custom organization example
        await file_discovery_with_custom_organization()
        
        print("\n✅ All file discovery examples completed successfully!")
        print("\nKey Integration Features Demonstrated:")
        print("  ✓ File discovery during exhaustive crawling")
        print("  ✓ Concurrent file downloading with queue management")
        print("  ✓ File organization and metadata extraction")
        print("  ✓ Real-time progress monitoring")
        print("  ✓ Comprehensive file inventory reporting")
        print("  ✓ Custom file type targeting and filtering")
        print("  ✓ Repository-based file organization")
        
    except Exception as e:
        print(f"\n❌ Error running examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Run the examples
    asyncio.run(main())