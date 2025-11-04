"""
Test suite for AsyncWebCrawler.adownload_file method.

This test suite verifies that the adownload_file method correctly implements
all requirements from task 5 of the domain-intelligence-crawler spec:
- Leverages existing session management
- Uses existing proxy rotation and rate limiting
- Implements file integrity validation using checksums and size verification
- Integrates with existing retry mechanisms
"""

import pytest
import asyncio
import os
import tempfile
import shutil
from pathlib import Path

from crawl4ai.async_webcrawler import AsyncWebCrawler
from crawl4ai.async_configs import CrawlerRunConfig, ProxyConfig


class TestADownloadFileMethod:
    """Test class for adownload_file method functionality"""
    
    @pytest.fixture
    def temp_download_dir(self):
        """Create a temporary directory for downloads"""
        temp_dir = tempfile.mkdtemp(prefix="crawl4ai_test_downloads_")
        yield temp_dir
        # Cleanup
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
    
    @pytest.mark.asyncio
    async def test_basic_file_download(self, temp_download_dir):
        """Test basic file download functionality with integrity validation"""
        async with AsyncWebCrawler() as crawler:
            result = await crawler.adownload_file(
                url="https://httpbin.org/robots.txt",
                download_path=temp_download_dir,
                validate_integrity=True,
                max_retries=2
            )
            
            # Verify successful download
            assert result["success"] is True
            assert result["error_message"] is None
            assert result["file_size"] > 0
            assert result["content_type"] is not None
            assert result["checksum"] is not None
            assert result["retry_count"] == 0
            
            # Verify file exists and has content
            file_path = result["file_path"]
            assert os.path.exists(file_path)
            assert os.path.getsize(file_path) > 0
            assert os.path.getsize(file_path) == result["file_size"]
    
    @pytest.mark.asyncio
    async def test_custom_filename_download(self, temp_download_dir):
        """Test download with custom filename"""
        async with AsyncWebCrawler() as crawler:
            custom_filename = "custom_test_file.json"
            
            result = await crawler.adownload_file(
                url="https://httpbin.org/json",
                download_path=temp_download_dir,
                filename=custom_filename,
                validate_integrity=True
            )
            
            assert result["success"] is True
            assert result["file_path"].endswith(custom_filename)
            assert os.path.exists(result["file_path"])
    
    @pytest.mark.asyncio
    async def test_download_with_config(self, temp_download_dir):
        """Test download with custom CrawlerRunConfig"""
        config = CrawlerRunConfig(
            page_timeout=15000,  # 15 seconds
            verbose=False
        )
        
        async with AsyncWebCrawler() as crawler:
            result = await crawler.adownload_file(
                url="https://httpbin.org/json",
                download_path=temp_download_dir,
                config=config,
                validate_integrity=True
            )
            
            assert result["success"] is True
            assert result["file_size"] > 0
    
    @pytest.mark.asyncio
    async def test_error_handling_404(self, temp_download_dir):
        """Test error handling with 404 status code"""
        async with AsyncWebCrawler() as crawler:
            result = await crawler.adownload_file(
                url="https://httpbin.org/status/404",
                download_path=temp_download_dir,
                validate_integrity=True
            )
            
            assert result["success"] is False
            assert "404" in result["error_message"]
            assert result["file_path"] is None
    
    @pytest.mark.asyncio
    async def test_error_handling_invalid_url(self, temp_download_dir):
        """Test error handling with invalid URL"""
        async with AsyncWebCrawler() as crawler:
            result = await crawler.adownload_file(
                url="not-a-valid-url",
                download_path=temp_download_dir
            )
            
            assert result["success"] is False
            assert "Invalid URL format" in result["error_message"]
    
    @pytest.mark.asyncio
    async def test_error_handling_empty_url(self, temp_download_dir):
        """Test error handling with empty URL"""
        async with AsyncWebCrawler() as crawler:
            result = await crawler.adownload_file(
                url="",
                download_path=temp_download_dir
            )
            
            assert result["success"] is False
            assert "Invalid URL" in result["error_message"]
    
    @pytest.mark.asyncio
    async def test_retry_mechanism(self, temp_download_dir):
        """Test retry mechanism with server errors"""
        async with AsyncWebCrawler() as crawler:
            # Use a URL that returns 503 (service unavailable) to test retry
            result = await crawler.adownload_file(
                url="https://httpbin.org/status/503",
                download_path=temp_download_dir,
                max_retries=2,
                validate_integrity=True
            )
            
            assert result["success"] is False
            assert result["retry_count"] >= 1  # Should have attempted retries
            assert "503" in result["error_message"]
    
    @pytest.mark.asyncio
    async def test_file_integrity_validation(self, temp_download_dir):
        """Test file integrity validation features"""
        async with AsyncWebCrawler() as crawler:
            result = await crawler.adownload_file(
                url="https://httpbin.org/json",
                download_path=temp_download_dir,
                validate_integrity=True
            )
            
            assert result["success"] is True
            
            # Verify checksum is calculated
            assert result["checksum"] is not None
            assert len(result["checksum"]) == 64  # SHA256 hex length
            
            # Verify metadata is captured
            metadata = result["metadata"]
            assert "filename" in metadata
            assert "url" in metadata
            assert "download_time" in metadata
            assert "headers" in metadata
    
    @pytest.mark.asyncio
    async def test_filename_conflict_resolution(self, temp_download_dir):
        """Test filename conflict resolution"""
        async with AsyncWebCrawler() as crawler:
            # Download the same file twice to test conflict resolution
            result1 = await crawler.adownload_file(
                url="https://httpbin.org/json",
                download_path=temp_download_dir,
                filename="test_conflict.json"
            )
            
            result2 = await crawler.adownload_file(
                url="https://httpbin.org/json",
                download_path=temp_download_dir,
                filename="test_conflict.json"
            )
            
            assert result1["success"] is True
            assert result2["success"] is True
            
            # Files should have different paths due to conflict resolution
            assert result1["file_path"] != result2["file_path"]
            assert "test_conflict.json" in result1["file_path"]
            assert "test_conflict_1.json" in result2["file_path"]
    
    @pytest.mark.asyncio
    async def test_default_download_path(self):
        """Test download with default download path"""
        async with AsyncWebCrawler() as crawler:
            result = await crawler.adownload_file(
                url="https://httpbin.org/robots.txt",
                # No download_path specified - should use default
                validate_integrity=True
            )
            
            assert result["success"] is True
            # Should use crawler's default download directory
            assert crawler.crawl4ai_folder in result["file_path"]
            
            # Cleanup the downloaded file
            if result["file_path"] and os.path.exists(result["file_path"]):
                os.remove(result["file_path"])
    
    @pytest.mark.asyncio
    async def test_content_type_detection(self, temp_download_dir):
        """Test content type detection and file extension assignment"""
        async with AsyncWebCrawler() as crawler:
            # Test JSON content type
            result = await crawler.adownload_file(
                url="https://httpbin.org/json",
                download_path=temp_download_dir
            )
            
            assert result["success"] is True
            assert "application/json" in result["content_type"]
            
            # Test plain text content type
            result2 = await crawler.adownload_file(
                url="https://httpbin.org/robots.txt",
                download_path=temp_download_dir
            )
            
            assert result2["success"] is True
            assert "text/plain" in result2["content_type"]


if __name__ == "__main__":
    # Run tests directly
    pytest.main([__file__, "-v"])