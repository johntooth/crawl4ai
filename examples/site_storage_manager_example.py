#!/usr/bin/env python3
"""
Site Storage Manager Example

Demonstrates the dual storage architecture for the Domain Intelligence Crawler:
- Downloaded files: E:\filefinder\{domain}\
- Analysis outputs: D:\Repo\FileFinder-a Crawl4AI mod\sites\{domain}\
"""

import asyncio
import sys
from pathlib import Path
import json
from datetime import datetime

# Add the parent directory to the path to import crawl4ai
sys.path.append(str(Path(__file__).parent.parent))

from crawl4ai.site_storage_manager import (
    SiteStorageManager,
    StorageConfig,
    get_site_storage_manager,
    initialize_site_for_crawling,
    store_crawl_file,
    store_analysis_result
)


async def basic_storage_setup_example():
    """Demonstrate basic storage setup for a new site."""
    print("=== Basic Storage Setup Example ===")
    
    # Initialize storage manager
    manager = SiteStorageManager()
    
    # Initialize storage for a new site
    site_url = "https://anao.gov.au"
    print(f"Initializing storage for: {site_url}")
    
    site_info = await manager.initialize_site_storage(site_url)
    
    print(f"✅ Storage initialized:")
    print(f"   Domain: {site_info.domain}")
    print(f"   Files Path: {site_info.files_path}")
    print(f"   Analysis Path: {site_info.analysis_path}")
    print(f"   Created: {site_info.created_at}")
    
    # Verify directory structure
    print(f"\n📁 Directory structure created:")
    print(f"   Files root: {site_info.files_path}")
    for subdir in ['documents', 'images', 'archives', 'data', 'other']:
        subdir_path = site_info.files_path / subdir
        exists = "✅" if subdir_path.exists() else "❌"
        print(f"     {exists} {subdir}/")
    
    print(f"   Analysis root: {site_info.analysis_path}")
    for subdir in ['graphs', 'reports', 'databases', 'exports', 'visualizations', 'logs', 'cache', 'metadata']:
        subdir_path = site_info.analysis_path / subdir
        exists = "✅" if subdir_path.exists() else "❌"
        print(f"     {exists} {subdir}/")
    
    return manager, site_info


async def file_storage_example(manager: SiteStorageManager):
    """Demonstrate storing downloaded files."""
    print("\n=== File Storage Example ===")
    
    site_url = "https://anao.gov.au"
    
    # Simulate downloading different types of files
    files_to_store = [
        {
            'url': 'https://anao.gov.au/reports/annual-report-2023.pdf',
            'content': b'%PDF-1.4 Mock PDF content for annual report...',
            'type': 'documents',
            'metadata': {
                'title': 'Annual Report 2023',
                'file_type': 'pdf',
                'content_length': 1024000,
                'last_modified': '2023-12-01'
            }
        },
        {
            'url': 'https://anao.gov.au/images/logo.png',
            'content': b'\x89PNG\r\n\x1a\n Mock PNG content...',
            'type': 'images',
            'metadata': {
                'title': 'ANAO Logo',
                'file_type': 'png',
                'dimensions': '200x100'
            }
        },
        {
            'url': 'https://anao.gov.au/data/financial-data.xlsx',
            'content': b'PK\x03\x04 Mock Excel content...',
            'type': 'data',
            'metadata': {
                'title': 'Financial Data',
                'file_type': 'xlsx',
                'sheets': ['Summary', 'Details']
            }
        }
    ]
    
    stored_files = []
    
    for file_info in files_to_store:
        print(f"📥 Storing: {file_info['url']}")
        
        stored_path = await manager.store_downloaded_file(
            url_or_domain=site_url,
            file_url=file_info['url'],
            file_content=file_info['content'],
            file_type=file_info['type'],
            metadata=file_info['metadata']
        )
        
        stored_files.append(stored_path)
        print(f"   ✅ Stored at: {stored_path}")
    
    # List stored files
    print(f"\n📋 Files stored for {site_url}:")
    file_list = await manager.get_site_file_list(site_url)
    
    for file_info in file_list:
        print(f"   📄 {file_info['name']}")
        print(f"      Size: {file_info['size']:,} bytes")
        print(f"      Type: {file_info['type']}")
        print(f"      Path: {file_info['relative_path']}")
        if 'metadata' in file_info:
            print(f"      Title: {file_info['metadata'].get('title', 'N/A')}")
    
    return stored_files


async def analysis_storage_example(manager: SiteStorageManager):
    """Demonstrate storing analysis outputs."""
    print("\n=== Analysis Storage Example ===")
    
    site_url = "https://anao.gov.au"
    
    # Store different types of analysis outputs
    analysis_outputs = [
        {
            'name': 'site_graph_analysis',
            'type': 'graphs',
            'content': {
                'nodes': 150,
                'edges': 300,
                'density': 0.027,
                'components': 1,
                'analysis_date': datetime.now().isoformat(),
                'top_pages': [
                    {'url': 'https://anao.gov.au/', 'pagerank': 0.15},
                    {'url': 'https://anao.gov.au/reports/', 'pagerank': 0.12}
                ]
            },
            'extension': '.json'
        },
        {
            'name': 'crawl_report',
            'type': 'reports',
            'content': {
                'summary': {
                    'total_pages': 150,
                    'files_found': 45,
                    'errors': 3,
                    'duration_minutes': 25
                },
                'file_types': {
                    'pdf': 30,
                    'xlsx': 10,
                    'docx': 5
                },
                'generated_at': datetime.now().isoformat()
            },
            'extension': '.json'
        },
        {
            'name': 'site_map',
            'type': 'exports',
            'content': '''<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
    <url>
        <loc>https://anao.gov.au/</loc>
        <lastmod>2024-01-15</lastmod>
        <priority>1.0</priority>
    </url>
    <url>
        <loc>https://anao.gov.au/reports/</loc>
        <lastmod>2024-01-14</lastmod>
        <priority>0.8</priority>
    </url>
</urlset>''',
            'extension': '.xml'
        }
    ]
    
    stored_outputs = []
    
    for output in analysis_outputs:
        print(f"📊 Storing analysis: {output['name']}")
        
        stored_path = await manager.store_analysis_output(
            url_or_domain=site_url,
            output_name=output['name'],
            content=output['content'],
            analysis_type=output['type'],
            file_extension=output['extension']
        )
        
        stored_outputs.append(stored_path)
        print(f"   ✅ Stored at: {stored_path}")
    
    # List analysis outputs
    print(f"\n📋 Analysis outputs for {site_url}:")
    output_list = await manager.get_site_analysis_outputs(site_url)
    
    for output_info in output_list:
        print(f"   📈 {output_info['name']}")
        print(f"      Size: {output_info['size']:,} bytes")
        print(f"      Type: {output_info['analysis_type']}")
        print(f"      Path: {output_info['relative_path']}")
    
    return stored_outputs


async def storage_statistics_example(manager: SiteStorageManager):
    """Demonstrate storage statistics and monitoring."""
    print("\n=== Storage Statistics Example ===")
    
    site_url = "https://anao.gov.au"
    
    # Get statistics for specific site
    print(f"📊 Statistics for {site_url}:")
    site_stats = await manager.get_storage_statistics(site_url)
    
    if site_stats:
        print(f"   Files: {site_stats['files_count']}")
        print(f"   Total file size: {site_stats['total_file_size']:,} bytes")
        print(f"   Analysis outputs: {site_stats['analysis_outputs_count']}")
        print(f"   Total analysis size: {site_stats['total_analysis_size']:,} bytes")
        print(f"   Created: {site_stats['created_at']}")
        print(f"   Files path: {site_stats['files_path']}")
        print(f"   Analysis path: {site_stats['analysis_path']}")
    
    # Get overall statistics
    print(f"\n📊 Overall storage statistics:")
    overall_stats = await manager.get_storage_statistics()
    
    print(f"   Total sites: {overall_stats['total_sites']}")
    print(f"   Total files: {overall_stats['total_files']}")
    print(f"   Total size: {overall_stats['total_size']:,} bytes")
    
    if overall_stats['sites']:
        print(f"   Sites managed:")
        for site in overall_stats['sites']:
            print(f"     - {site['domain']}: {site['files_count']} files")


async def convenience_functions_example():
    """Demonstrate convenience functions for easy integration."""
    print("\n=== Convenience Functions Example ===")
    
    site_url = "https://example.gov.au"
    
    # Initialize storage using convenience function
    print(f"🚀 Initializing storage for: {site_url}")
    files_path, analysis_path = await initialize_site_for_crawling(site_url)
    
    print(f"   Files path: {files_path}")
    print(f"   Analysis path: {analysis_path}")
    
    # Store a file using convenience function
    print(f"\n📥 Storing file using convenience function:")
    file_content = b"Mock document content for testing..."
    file_metadata = {
        'title': 'Test Document',
        'content_type': 'application/pdf'
    }
    
    stored_file_path = await store_crawl_file(
        url=site_url,
        file_url="https://example.gov.au/test-document.pdf",
        content=file_content,
        file_type="documents",
        metadata=file_metadata
    )
    
    print(f"   ✅ File stored: {stored_file_path}")
    
    # Store analysis result using convenience function
    print(f"\n📊 Storing analysis result:")
    analysis_result = {
        'pages_crawled': 25,
        'files_discovered': 8,
        'analysis_timestamp': datetime.now().isoformat(),
        'summary': 'Successful crawl of government site'
    }
    
    stored_analysis_path = await store_analysis_result(
        url=site_url,
        analysis_name="crawl_summary",
        result=analysis_result,
        analysis_type="reports"
    )
    
    print(f"   ✅ Analysis stored: {stored_analysis_path}")


async def custom_configuration_example():
    """Demonstrate custom storage configuration."""
    print("\n=== Custom Configuration Example ===")
    
    # Create custom storage configuration
    custom_config = StorageConfig(
        files_root=r"C:\CustomFileFinder\downloads",
        analysis_root=r"C:\CustomFileFinder\analysis",
        files_subdirs={
            'pdfs': 'pdf_documents',
            'spreadsheets': 'excel_files',
            'presentations': 'powerpoint_files',
            'other': 'miscellaneous'
        },
        analysis_subdirs={
            'network_graphs': 'graphs',
            'summary_reports': 'reports',
            'raw_data': 'databases'
        }
    )
    
    print(f"🔧 Custom configuration:")
    print(f"   Files root: {custom_config.files_root}")
    print(f"   Analysis root: {custom_config.analysis_root}")
    print(f"   Custom file subdirs: {list(custom_config.files_subdirs.keys())}")
    print(f"   Custom analysis subdirs: {list(custom_config.analysis_subdirs.keys())}")
    
    # Use custom configuration
    custom_manager = SiteStorageManager(custom_config)
    
    site_url = "https://custom-site.com"
    site_info = await custom_manager.initialize_site_storage(site_url)
    
    print(f"\n✅ Custom storage initialized:")
    print(f"   Domain: {site_info.domain}")
    print(f"   Files path: {site_info.files_path}")
    print(f"   Analysis path: {site_info.analysis_path}")


async def integration_workflow_example():
    """Demonstrate complete integration workflow."""
    print("\n=== Integration Workflow Example ===")
    
    # This simulates how the storage manager would be used
    # in a complete crawling and analysis workflow
    
    site_url = "https://treasury.gov.au"
    
    print(f"🔄 Complete workflow for: {site_url}")
    
    # Step 1: Initialize storage
    print("1️⃣ Initializing storage...")
    manager = await get_site_storage_manager()
    site_info = await manager.initialize_site_storage(site_url)
    
    # Step 2: Simulate crawling and file discovery
    print("2️⃣ Simulating file discovery and download...")
    discovered_files = [
        {
            'url': 'https://treasury.gov.au/budget/budget-2024.pdf',
            'content': b'Mock budget PDF content...',
            'type': 'documents'
        },
        {
            'url': 'https://treasury.gov.au/data/economic-indicators.xlsx',
            'content': b'Mock Excel data...',
            'type': 'data'
        }
    ]
    
    for file_info in discovered_files:
        await manager.store_downloaded_file(
            site_url, 
            file_info['url'], 
            file_info['content'],
            file_info['type']
        )
        print(f"   📥 Downloaded: {Path(file_info['url']).name}")
    
    # Step 3: Generate and store analysis
    print("3️⃣ Generating and storing analysis...")
    
    # Site graph analysis
    graph_analysis = {
        'total_pages': 75,
        'file_links': len(discovered_files),
        'depth_analysis': {
            'max_depth': 4,
            'avg_depth': 2.3
        },
        'generated_at': datetime.now().isoformat()
    }
    
    await manager.store_analysis_output(
        site_url,
        'site_graph_analysis',
        graph_analysis,
        'graphs'
    )
    
    # Crawl report
    crawl_report = {
        'status': 'completed',
        'files_downloaded': len(discovered_files),
        'total_size_mb': 15.7,
        'duration_minutes': 12,
        'errors': 0
    }
    
    await manager.store_analysis_output(
        site_url,
        'crawl_report',
        crawl_report,
        'reports'
    )
    
    print("   📊 Analysis results stored")
    
    # Step 4: Generate summary
    print("4️⃣ Generating summary...")
    stats = await manager.get_storage_statistics(site_url)
    
    print(f"   ✅ Workflow completed:")
    print(f"      Files stored: {stats['files_count']}")
    print(f"      Analysis outputs: {stats['analysis_outputs_count']}")
    print(f"      Total storage used: {(stats['total_file_size'] + stats['total_analysis_size']):,} bytes")


async def main():
    """Run all storage manager examples."""
    print("🗄️ Site Storage Manager Examples")
    print("=" * 60)
    print("Demonstrating dual storage architecture:")
    print("- Files: E:\\filefinder\\{domain}\\")
    print("- Analysis: D:\\Repo\\FileFinder-a Crawl4AI mod\\sites\\{domain}\\")
    print("=" * 60)
    
    try:
        # Run examples
        manager, site_info = await basic_storage_setup_example()
        await file_storage_example(manager)
        await analysis_storage_example(manager)
        await storage_statistics_example(manager)
        await convenience_functions_example()
        await custom_configuration_example()
        await integration_workflow_example()
        
        print("\n" + "=" * 60)
        print("✅ All storage manager examples completed successfully!")
        print("\nKey features demonstrated:")
        print("- Automatic directory structure creation")
        print("- File type-based organization")
        print("- Metadata preservation")
        print("- Analysis output management")
        print("- Storage statistics and monitoring")
        print("- Custom configuration support")
        print("- Integration-ready convenience functions")
        
    except Exception as e:
        print(f"❌ Error running examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())