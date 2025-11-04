#!/usr/bin/env python3
"""
Tests for Exhaustive File Discovery Integration

This module tests the integration of file discovery capabilities with exhaustive
crawling workflow, including file download queue management and concurrent downloading.
"""

import pytest
import asyncio
import tempfile
import shutil
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
from typing import List, Dict, Any

from crawl4ai.exhaustive_file_integration import (
    ExhaustiveFileDiscoveryCrawler,
    FileDownloadQueue,
    FileDownloadTask,
    FileDownloadResult,
    create_document_focused_crawler,
    create_comprehensive_file_crawler
)
from crawl4ai.file_discovery_filter import FileMetadata, FileType
from crawl4ai.exhaustive_configs import ExhaustiveCrawlConfig
from crawl4ai.models import CrawlResult


class TestFileDownloadQueue:
    """Test the FileDownloadQueue functionality."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def mock_logger(self):
        """Create a mock logger."""
        return MagicMock()
    
    @pytest.fixture
    def download_queue(self, mock_logger):
        """Create a FileDownloadQueue for testing."""
        return FileDownloadQueue(
            max_concurrent_downloads=2,
            max_queue_size=10,
            logger=mock_logger
        )
    
    @pytest.fixture
    def sample_file_metadata(self):
        """Create sample file metadata for testing."""
        return FileMetadata(
            url="https://example.com/test.pdf",
            filename="test.pdf",
            extension=".pdf",
            file_type=FileType.DOCUMENT,
            repository_path="/documents"
        )
    
    @pytest.mark.asyncio
    async def test_add_file_task(self, download_queue, sample_file_metadata):
        """Test adding file tasks to the download queue."""
        # Test successful addition
        result = await download_queue.add_file_task(sample_file_metadata, priority=5)
        assert result is True
        
        # Check stats
        stats = download_queue.get_stats()
        assert stats['queued'] == 1
        
        # Test duplicate addition (should fail)
        result = await download_queue.add_file_task(sample_file_metadata, priority=3)
        assert result is False
        
        # Stats should remain the same
        stats = download_queue.get_stats()
        assert stats['queued'] == 1
    
    @pytest.mark.asyncio
    async def test_download_queue_stats(self, download_queue, sample_file_metadata):
        """Test download queue statistics tracking."""
        # Initial stats
        stats = download_queue.get_stats()
        assert stats['queued'] == 0
        assert stats['completed'] == 0
        assert stats['failed'] == 0
        assert stats['active'] == 0
        
        # Add a task
        await download_queue.add_file_task(sample_file_metadata)
        stats = download_queue.get_stats()
        assert stats['queued'] == 1
        assert stats['success_rate'] == 0.0  # No completed downloads yet
    
    @pytest.mark.asyncio
    async def test_queue_full_handling(self, mock_logger):
        """Test handling of full download queue."""
        # Create queue with very small size
        small_queue = FileDownloadQueue(
            max_concurrent_downloads=1,
            max_queue_size=2,
            logger=mock_logger
        )
        
        # Fill the queue
        file1 = FileMetadata("https://example.com/file1.pdf", "file1.pdf", ".pdf", FileType.DOCUMENT)
        file2 = FileMetadata("https://example.com/file2.pdf", "file2.pdf", ".pdf", FileType.DOCUMENT)
        file3 = FileMetadata("https://example.com/file3.pdf", "file3.pdf", ".pdf", FileType.DOCUMENT)
        
        # First two should succeed
        assert await small_queue.add_file_task(file1) is True
        assert await small_queue.add_file_task(file2) is True
        
        # Third should fail due to queue being full
        # Note: This test might need adjustment based on actual queue behavior
        # as asyncio.Queue might block rather than immediately fail


class TestExhaustiveFileDiscoveryCrawler:
    """Test the ExhaustiveFileDiscoveryCrawler functionality."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def mock_crawler(self, temp_dir):
        """Create a mock ExhaustiveFileDiscoveryCrawler."""
        download_config = {
            'download_directory': temp_dir,
            'max_concurrent_downloads': 2
        }
        
        crawler = ExhaustiveFileDiscoveryCrawler(
            download_config=download_config
        )
        
        # Mock the underlying methods
        crawler.start = AsyncMock()
        crawler.close = AsyncMock()
        crawler.arun_exhaustive = AsyncMock()
        
        return crawler
    
    @pytest.fixture
    def sample_crawl_result(self):
        """Create a sample CrawlResult for testing."""
        return CrawlResult(
            url="https://example.com/page1",
            html="<html><body><a href='/test.pdf'>Test PDF</a></body></html>",
            success=True,
            links={
                'internal': [
                    {'href': 'https://example.com/test.pdf', 'text': 'Test PDF'},
                    {'href': 'https://example.com/document.docx', 'text': 'Document'}
                ],
                'external': []
            }
        )
    
    def test_crawler_initialization(self, temp_dir):
        """Test crawler initialization with file discovery configuration."""
        file_config = {
            'target_file_types': [FileType.DOCUMENT, FileType.DATA],
            'max_file_size_mb': 10
        }
        
        download_config = {
            'download_directory': temp_dir,
            'max_concurrent_downloads': 3,
            'organize_by_type': True
        }
        
        crawler = ExhaustiveFileDiscoveryCrawler(
            file_discovery_config=file_config,
            download_config=download_config
        )
        
        # Check file filter configuration
        assert crawler.file_filter is not None
        assert crawler.file_filter.target_extensions  # Should have extensions for documents and data
        
        # Check download queue configuration
        assert crawler.download_queue is not None
        assert crawler.download_queue.max_concurrent_downloads == 3
        
        # Check organization settings
        assert crawler.organize_by_type is True
        assert crawler.download_directory == temp_dir
    
    def test_file_priority_calculation(self, mock_crawler):
        """Test file priority calculation logic."""
        # Test document file (high priority)
        doc_file = FileMetadata(
            url="https://example.com/important.pdf",
            filename="important.pdf",
            extension=".pdf",
            file_type=FileType.DOCUMENT,
            repository_path="/documents"
        )
        
        priority = mock_crawler._calculate_file_priority(doc_file)
        assert priority > 10  # Should have high priority
        
        # Test image file (lower priority)
        image_file = FileMetadata(
            url="https://example.com/image.jpg",
            filename="image.jpg",
            extension=".jpg",
            file_type=FileType.IMAGE
        )
        
        image_priority = mock_crawler._calculate_file_priority(image_file)
        assert image_priority < priority  # Should be lower than document
    
    @pytest.mark.asyncio
    async def test_crawl_result_file_processing(self, mock_crawler, sample_crawl_result):
        """Test processing crawl results for file discovery."""
        # Enable file discovery
        mock_crawler._file_discovery_active = True
        
        # Mock the file filter to return discovered files
        mock_crawler.file_filter.apply = MagicMock(return_value=True)
        mock_crawler.file_filter.get_discovered_files = MagicMock(return_value=[
            FileMetadata(
                url="https://example.com/test.pdf",
                filename="test.pdf",
                extension=".pdf",
                file_type=FileType.DOCUMENT
            )
        ])
        
        # Mock the download queue
        mock_crawler.download_queue.add_file_task = AsyncMock(return_value=True)
        
        # Process the crawl result
        await mock_crawler._process_crawl_result_for_files(sample_crawl_result)
        
        # Verify file filter was called
        assert mock_crawler.file_filter.apply.called
        
        # Verify download task was added
        assert mock_crawler.download_queue.add_file_task.called
    
    def test_filter_chain_creation(self, mock_crawler):
        """Test creation of file discovery filter chain."""
        filter_chain = mock_crawler._create_file_discovery_filter_chain()
        
        # Should have filters including the file discovery filter
        assert filter_chain is not None
        assert hasattr(filter_chain, 'filters') or len(filter_chain.filters) > 0
    
    @pytest.mark.asyncio
    async def test_exhaustive_config_modification(self, mock_crawler):
        """Test modification of exhaustive crawl config for file discovery."""
        config = ExhaustiveCrawlConfig()
        
        # Configure for file discovery
        modified_config = mock_crawler._configure_file_discovery_strategy(config)
        
        # Should have deep crawl strategy configured
        assert hasattr(modified_config, 'deep_crawl_strategy')
    
    def test_file_results_compilation(self, mock_crawler):
        """Test compilation of file discovery results."""
        # Mock file filter with sample data
        mock_crawler.file_filter.get_discovery_stats = MagicMock()
        mock_crawler.file_filter.get_discovery_stats.return_value = MagicMock(
            total_files_discovered=5,
            files_by_type={FileType.DOCUMENT: 3, FileType.DATA: 2},
            files_by_extension={'.pdf': 3, '.csv': 2},
            repository_paths={'/documents', '/data'}
        )
        
        mock_crawler.file_filter.get_discovered_files = MagicMock(return_value=[
            FileMetadata("https://example.com/test.pdf", "test.pdf", ".pdf", FileType.DOCUMENT)
        ])
        
        mock_crawler.file_filter.get_repository_inventory = MagicMock(return_value={
            '/documents': [
                FileMetadata("https://example.com/test.pdf", "test.pdf", ".pdf", FileType.DOCUMENT)
            ]
        })
        
        # Compile results
        results = mock_crawler._compile_file_results()
        
        # Verify structure
        assert 'discovery_stats' in results
        assert 'discovered_files' in results
        assert 'repository_inventory' in results
        
        # Verify content
        assert results['discovery_stats']['total_files_discovered'] == 5


class TestConvenienceFunctions:
    """Test convenience functions for creating specialized crawlers."""
    
    def test_create_document_focused_crawler(self):
        """Test creation of document-focused crawler."""
        crawler = create_document_focused_crawler(
            download_directory="./test_downloads",
            max_concurrent_downloads=3
        )
        
        assert isinstance(crawler, ExhaustiveFileDiscoveryCrawler)
        assert crawler.download_directory == "./test_downloads"
        assert crawler.download_queue.max_concurrent_downloads == 3
    
    def test_create_comprehensive_file_crawler(self):
        """Test creation of comprehensive file crawler."""
        crawler = create_comprehensive_file_crawler(
            download_directory="./comprehensive_downloads"
        )
        
        assert isinstance(crawler, ExhaustiveFileDiscoveryCrawler)
        assert crawler.download_directory == "./comprehensive_downloads"
        
        # Should be configured for all file types
        # This would need to be verified based on the actual implementation


class TestIntegrationWorkflow:
    """Test the complete integration workflow."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.mark.asyncio
    async def test_complete_workflow_mock(self, temp_dir):
        """Test the complete file discovery workflow with mocked components."""
        # Create crawler with test configuration
        crawler = create_document_focused_crawler(
            download_directory=temp_dir,
            max_concurrent_downloads=2
        )
        
        # Mock the underlying crawler methods
        crawler.start = AsyncMock()
        crawler.close = AsyncMock()
        
        # Mock arun_exhaustive to return sample results
        mock_exhaustive_results = {
            'results': [],
            'analytics': {'session_stats': {'crawl_duration': '00:01:30'}},
            'stop_reason': 'Test completed',
            'total_pages_crawled': 10,
            'successful_pages': 8,
            'total_urls_discovered': 25
        }
        crawler.arun_exhaustive = AsyncMock(return_value=mock_exhaustive_results)
        
        # Mock download queue methods
        crawler.download_queue.start_download_workers = AsyncMock()
        crawler.download_queue.wait_for_completion = AsyncMock()
        crawler.download_queue.stop_workers = AsyncMock()
        crawler.download_queue.get_stats = MagicMock(return_value={
            'completed': 5,
            'failed': 1,
            'success_rate': 83.3,
            'total_bytes_downloaded': 1024000
        })
        
        # Mock file discovery results
        crawler._compile_file_results = MagicMock(return_value={
            'discovery_stats': {
                'total_files_discovered': 6,
                'files_by_type': {'document': 4, 'data': 2},
                'files_by_extension': {'.pdf': 4, '.csv': 2},
                'repository_paths': ['/documents', '/data']
            },
            'discovered_files': [],
            'repository_inventory': {}
        })
        
        try:
            # Configure and run
            config = ExhaustiveCrawlConfig(
                max_pages=50,
                dead_end_threshold=10
            )
            
            results = await crawler.arun_exhaustive_with_files(
                start_url="https://example.com",
                config=config,
                enable_file_discovery=True,
                enable_file_download=True
            )
            
            # Verify results structure
            assert 'total_pages_crawled' in results
            assert 'file_discovery' in results
            assert 'download_stats' in results
            
            # Verify file discovery results
            assert results['file_discovery']['discovery_stats']['total_files_discovered'] == 6
            
            # Verify download results
            assert results['download_stats']['completed'] == 5
            assert results['download_stats']['success_rate'] == 83.3
            
            # Verify workflow methods were called
            crawler.download_queue.start_download_workers.assert_called_once()
            crawler.download_queue.wait_for_completion.assert_called_once()
            crawler.download_queue.stop_workers.assert_called_once()
            
        finally:
            await crawler.close()


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])