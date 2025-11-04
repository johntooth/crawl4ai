"""
Tests for Site Graph Database functionality

Tests the site graph database extension that provides URL tracking,
file metadata storage, and crawling progress monitoring.
"""

import pytest
import pytest_asyncio
import asyncio
import tempfile
import os
from datetime import datetime
from crawl4ai.async_database import AsyncDatabaseManager
from crawl4ai.site_graph_db import (
    URLNode, 
    SiteGraphStats, 
    SiteGraphDatabaseManager,
    create_site_graph_manager
)


@pytest_asyncio.fixture
async def temp_db_manager():
    """Create a temporary database manager for testing"""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_file:
        db_path = tmp_file.name
    
    # Create temporary database manager
    db_manager = AsyncDatabaseManager()
    db_manager.db_path = db_path
    
    try:
        await db_manager.initialize()
        yield db_manager
    finally:
        await db_manager.cleanup()
        # Clean up temporary file
        if os.path.exists(db_path):
            os.unlink(db_path)


@pytest_asyncio.fixture
async def site_graph_manager(temp_db_manager):
    """Create site graph manager with temporary database"""
    return SiteGraphDatabaseManager(temp_db_manager)


class TestSiteGraphDatabase:
    """Test suite for site graph database functionality"""
    
    @pytest.mark.asyncio
    async def test_store_and_retrieve_url(self, site_graph_manager):
        """Test storing and retrieving a discovered URL"""
        # Create test URL node
        url_node = URLNode(
            url="https://example.com/test",
            source_url="https://example.com",
            discovered_at=datetime.now(),
            status_code=200,
            content_type="text/html",
            is_file=False
        )
        
        # Store the URL
        await site_graph_manager.store_discovered_url(url_node)
        
        # Retrieve the URL
        retrieved = await site_graph_manager.get_discovered_url("https://example.com/test")
        
        assert retrieved is not None
        assert retrieved.url == url_node.url
        assert retrieved.source_url == url_node.source_url
        assert retrieved.status_code == url_node.status_code
        assert retrieved.content_type == url_node.content_type
        assert retrieved.is_file == url_node.is_file
    
    @pytest.mark.asyncio
    async def test_store_file_url(self, site_graph_manager):
        """Test storing a file URL with metadata"""
        file_node = URLNode(
            url="https://example.com/document.pdf",
            source_url="https://example.com/downloads",
            discovered_at=datetime.now(),
            status_code=200,
            content_type="application/pdf",
            file_size=1024000,
            is_file=True,
            file_extension=".pdf",
            download_status="not_attempted",
            metadata={"title": "Test Document", "category": "reports"}
        )
        
        await site_graph_manager.store_discovered_url(file_node)
        
        retrieved = await site_graph_manager.get_discovered_url("https://example.com/document.pdf")
        
        assert retrieved is not None
        assert retrieved.is_file is True
        assert retrieved.file_extension == ".pdf"
        assert retrieved.file_size == 1024000
        assert retrieved.download_status == "not_attempted"
        assert retrieved.metadata["title"] == "Test Document"
    
    @pytest.mark.asyncio
    async def test_update_url_status(self, site_graph_manager):
        """Test updating URL status after crawling"""
        # Store initial URL
        url_node = URLNode(
            url="https://example.com/page",
            source_url="https://example.com",
            discovered_at=datetime.now()
        )
        await site_graph_manager.store_discovered_url(url_node)
        
        # Update status
        await site_graph_manager.update_url_status(
            url="https://example.com/page",
            status_code=200,
            content_type="text/html",
            file_size=5000
        )
        
        # Verify update
        retrieved = await site_graph_manager.get_discovered_url("https://example.com/page")
        assert retrieved.status_code == 200
        assert retrieved.content_type == "text/html"
        assert retrieved.file_size == 5000
        assert retrieved.last_checked is not None
    
    @pytest.mark.asyncio
    async def test_update_file_download_status(self, site_graph_manager):
        """Test updating file download status"""
        # Store file URL
        file_node = URLNode(
            url="https://example.com/file.pdf",
            source_url="https://example.com",
            discovered_at=datetime.now(),
            is_file=True,
            download_status="not_attempted"
        )
        await site_graph_manager.store_discovered_url(file_node)
        
        # Update download status
        await site_graph_manager.update_file_download_status(
            url="https://example.com/file.pdf",
            download_status="completed",
            local_path="/downloads/file.pdf",
            checksum="abc123"
        )
        
        # Verify update
        retrieved = await site_graph_manager.get_discovered_url("https://example.com/file.pdf")
        assert retrieved.download_status == "completed"
        assert retrieved.local_path == "/downloads/file.pdf"
        assert retrieved.checksum == "abc123"
    
    @pytest.mark.asyncio
    async def test_get_files_by_status(self, site_graph_manager):
        """Test filtering files by download status"""
        base_url = "https://example.com"
        
        # Store multiple files with different statuses
        files = [
            URLNode(url=f"{base_url}/file1.pdf", is_file=True, download_status="completed"),
            URLNode(url=f"{base_url}/file2.doc", is_file=True, download_status="failed"),
            URLNode(url=f"{base_url}/file3.txt", is_file=True, download_status="completed"),
            URLNode(url=f"{base_url}/page.html", is_file=False, download_status="not_attempted")
        ]
        
        for file_node in files:
            await site_graph_manager.store_discovered_url(file_node)
        
        # Get completed files
        completed_files = await site_graph_manager.get_files_by_status("completed", base_url)
        assert len(completed_files) == 2
        assert all(f.download_status == "completed" for f in completed_files)
        assert all(f.is_file for f in completed_files)
        
        # Get failed files
        failed_files = await site_graph_manager.get_files_by_status("failed", base_url)
        assert len(failed_files) == 1
        assert failed_files[0].download_status == "failed"
    
    @pytest.mark.asyncio
    async def test_site_graph_retrieval(self, site_graph_manager):
        """Test retrieving complete site graph"""
        base_url = "https://example.com"
        
        # Store mixed URLs and files
        nodes = [
            URLNode(url=f"{base_url}/page1", is_file=False),
            URLNode(url=f"{base_url}/page2", is_file=False),
            URLNode(url=f"{base_url}/file1.pdf", is_file=True),
            URLNode(url=f"{base_url}/file2.doc", is_file=True),
        ]
        
        for node in nodes:
            await site_graph_manager.store_discovered_url(node)
        
        # Get complete site graph
        site_graph = await site_graph_manager.get_site_graph(base_url)
        
        assert site_graph['total_urls'] == 2
        assert site_graph['total_files'] == 2
        assert len(site_graph['urls']) == 2
        assert len(site_graph['files']) == 2
        
        # Test excluding files
        site_graph_no_files = await site_graph_manager.get_site_graph(base_url, include_files=False)
        assert site_graph_no_files['total_urls'] == 2
        assert site_graph_no_files['total_files'] == 0
    
    @pytest.mark.asyncio
    async def test_site_graph_stats(self, site_graph_manager):
        """Test storing and retrieving site graph statistics"""
        base_url = "https://example.com"
        
        # Create and store stats
        stats = SiteGraphStats(
            base_url=base_url,
            total_urls_discovered=50,
            total_files_discovered=10,
            total_files_downloaded=8,
            crawl_start_time=datetime.now(),
            dead_end_count=5,
            revisit_ratio=0.25
        )
        
        await site_graph_manager.store_site_graph_stats(stats)
        
        # Retrieve stats
        retrieved_stats = await site_graph_manager.get_site_graph_stats(base_url)
        
        assert retrieved_stats is not None
        assert retrieved_stats.base_url == base_url
        assert retrieved_stats.total_urls_discovered == 50
        assert retrieved_stats.total_files_discovered == 10
        assert retrieved_stats.total_files_downloaded == 8
        assert retrieved_stats.dead_end_count == 5
        assert retrieved_stats.revisit_ratio == 0.25
    
    @pytest.mark.asyncio
    async def test_crawl_progress(self, site_graph_manager):
        """Test getting comprehensive crawl progress"""
        base_url = "https://example.com"
        
        # Store stats
        stats = SiteGraphStats(
            base_url=base_url,
            total_urls_discovered=20,
            total_files_discovered=5,
            total_files_downloaded=3
        )
        await site_graph_manager.store_site_graph_stats(stats)
        
        # Store some files with different statuses
        files = [
            URLNode(url=f"{base_url}/file1.pdf", is_file=True, download_status="completed"),
            URLNode(url=f"{base_url}/file2.doc", is_file=True, download_status="completed"),
            URLNode(url=f"{base_url}/file3.txt", is_file=True, download_status="failed"),
            URLNode(url=f"{base_url}/file4.zip", is_file=True, download_status="not_attempted"),
        ]
        
        for file_node in files:
            await site_graph_manager.store_discovered_url(file_node)
        
        # Get progress
        progress = await site_graph_manager.get_crawl_progress(base_url)
        
        assert progress['base_url'] == base_url
        assert progress['stats'] is not None
        assert progress['file_progress']['total_files'] == 4
        assert progress['file_progress']['completed'] == 2
        assert progress['file_progress']['failed'] == 1
        assert progress['file_progress']['pending'] == 1
        assert progress['file_progress']['progress_percentage'] == 50.0
    
    @pytest.mark.asyncio
    async def test_factory_function(self, temp_db_manager):
        """Test the factory function for creating site graph manager"""
        # Test with provided db_manager
        manager = create_site_graph_manager(temp_db_manager)
        assert isinstance(manager, SiteGraphDatabaseManager)
        assert manager.db_manager == temp_db_manager
        
        # Test basic functionality
        url_node = URLNode(url="https://test.com", is_file=False)
        await manager.store_discovered_url(url_node)
        
        retrieved = await manager.get_discovered_url("https://test.com")
        assert retrieved is not None
        assert retrieved.url == "https://test.com"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])