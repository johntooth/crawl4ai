#!/usr/bin/env python3
"""
Example demonstrating the AsyncWebCrawler.adownload_file method.

This example shows how to use the adownload_file method to download files
with integrity validation, retry mechanisms, and proper error handling.

The adownload_file method implements all requirements from task 5:
- Leverages existing session management
- Uses existing proxy rotation and rate limiting  
- Implements file integrity validation using checksums and size verification
- Integrates with existing retry mechanisms
"""

import asyncio
import os
import tempfile
import shutil
from pathlib import Path

from crawl4ai.async_webcrawler import AsyncWebCrawler
from crawl4ai.async_configs import CrawlerRunConfig


async def demonstrate_adownload_file():
    """Demonstrate various adownload_file capabilities"""
    
    # Create temporary directory for downloads
    temp_dir = tempfile.mkdtemp(prefix="crawl4ai_download_demo_")
    download_path = os.path.join(temp_dir, "downloads")
    
    try:
        print("🚀 AsyncWebCrawler adownload_file Method Demo")
        print("=" * 50)
        
        async with AsyncWebCrawler() as crawler:
            
            # Example 1: Basic file download with integrity validation
            print("\n📥 Example 1: Basic file download with integrity validation")
            
            result = await crawler.adownload_file(
                url="https://httpbin.org/json",
                download_path=download_path,
                validate_integrity=True,
                max_retries=3
            )
            
            if result["success"]:
                print(f"   ✅ Successfully downloaded: {os.path.basename(result['file_path'])}")
                print(f"   📊 File size: {result['file_size']} bytes")
                print(f"   🔒 SHA256 checksum: {result['checksum'][:16]}...")
                print(f"   📄 Content type: {result['content_type']}")
                print(f"   🔄 Retries needed: {result['retry_count']}")
            else:
                print(f"   ❌ Download failed: {result['error_message']}")
            
            # Example 2: Download with custom filename and configuration
            print("\n📥 Example 2: Download with custom filename and configuration")
            
            config = CrawlerRunConfig(
                page_timeout=15000,  # 15 seconds timeout
                verbose=True
            )
            
            result = await crawler.adownload_file(
                url="https://httpbin.org/robots.txt",
                download_path=download_path,
                filename="custom_robots.txt",
                config=config,
                validate_integrity=True
            )
            
            if result["success"]:
                print(f"   ✅ Downloaded with custom name: {os.path.basename(result['file_path'])}")
                print(f"   📊 File size: {result['file_size']} bytes")
                
                # Show file metadata
                metadata = result["metadata"]
                print(f"   📅 Download time: {metadata.get('download_time', 'N/A')}")
                print(f"   🌐 Original URL: {metadata.get('url', 'N/A')}")
            else:
                print(f"   ❌ Download failed: {result['error_message']}")
            
            # Example 3: Error handling demonstration
            print("\n📥 Example 3: Error handling demonstration")
            
            result = await crawler.adownload_file(
                url="https://httpbin.org/status/404",  # This will return 404
                download_path=download_path,
                validate_integrity=True,
                max_retries=2
            )
            
            if not result["success"]:
                print(f"   ✅ Error correctly handled: {result['error_message']}")
                print(f"   🔄 Retry attempts made: {result['retry_count']}")
            else:
                print(f"   ❌ Unexpected success for 404 URL")
            
            # Example 4: Download different file types
            print("\n📥 Example 4: Download different file types")
            
            file_urls = [
                ("https://httpbin.org/json", "JSON data"),
                ("https://httpbin.org/xml", "XML data"),
                ("https://httpbin.org/html", "HTML content")
            ]
            
            for url, description in file_urls:
                result = await crawler.adownload_file(
                    url=url,
                    download_path=download_path,
                    validate_integrity=True
                )
                
                if result["success"]:
                    filename = os.path.basename(result['file_path'])
                    print(f"   ✅ {description}: {filename} ({result['file_size']} bytes)")
                else:
                    print(f"   ❌ Failed to download {description}: {result['error_message']}")
            
            # Example 5: Show integrity validation in action
            print("\n📥 Example 5: Integrity validation features")
            
            result = await crawler.adownload_file(
                url="https://httpbin.org/json",
                download_path=download_path,
                filename="integrity_test.json",
                validate_integrity=True
            )
            
            if result["success"]:
                print(f"   ✅ File downloaded and validated")
                print(f"   🔒 Checksum calculated: {result['checksum'][:16]}...")
                print(f"   📏 Size verified: {result['file_size']} bytes")
                
                # Verify the file actually exists and matches reported size
                actual_size = os.path.getsize(result['file_path'])
                print(f"   ✓ Actual file size matches: {actual_size == result['file_size']}")
            
        print("\n🎉 Demo completed successfully!")
        print(f"\n📁 Downloaded files are in: {download_path}")
        
        # List all downloaded files
        if os.path.exists(download_path):
            files = os.listdir(download_path)
            if files:
                print("\n📋 Downloaded files:")
                for file in files:
                    file_path = os.path.join(download_path, file)
                    size = os.path.getsize(file_path)
                    print(f"   • {file} ({size} bytes)")
            else:
                print("\n📋 No files were downloaded")
        
    except Exception as e:
        print(f"❌ Demo failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        
    finally:
        # Cleanup
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
            print(f"\n🧹 Cleaned up temporary directory")


async def demonstrate_advanced_features():
    """Demonstrate advanced adownload_file features"""
    
    print("\n🔧 Advanced Features Demo")
    print("=" * 30)
    
    temp_dir = tempfile.mkdtemp(prefix="crawl4ai_advanced_demo_")
    download_path = os.path.join(temp_dir, "downloads")
    
    try:
        async with AsyncWebCrawler() as crawler:
            
            # Demonstrate chunked download with progress
            print("\n📥 Chunked download with integrity validation")
            
            result = await crawler.adownload_file(
                url="https://httpbin.org/json",
                download_path=download_path,
                validate_integrity=True,
                chunk_size=1024,  # Small chunks for demonstration
                max_retries=3
            )
            
            if result["success"]:
                print(f"   ✅ Chunked download completed")
                print(f"   📊 Total size: {result['file_size']} bytes")
                print(f"   🔒 Integrity verified: SHA256 checksum calculated")
            
            # Demonstrate retry mechanism with timeout
            print("\n🔄 Retry mechanism demonstration")
            
            # Use a delay endpoint to test timeout and retry
            config = CrawlerRunConfig(page_timeout=2000)  # Very short timeout
            
            result = await crawler.adownload_file(
                url="https://httpbin.org/delay/1",  # 1 second delay
                download_path=download_path,
                config=config,
                max_retries=2,
                validate_integrity=True
            )
            
            print(f"   🔄 Retry attempts: {result['retry_count']}")
            if result["success"]:
                print(f"   ✅ Download succeeded after retries")
            else:
                print(f"   ⚠️ Download failed as expected: {result['error_message']}")
            
    finally:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)


if __name__ == "__main__":
    # Run the basic demonstration
    asyncio.run(demonstrate_adownload_file())
    
    # Run advanced features demonstration
    asyncio.run(demonstrate_advanced_features())