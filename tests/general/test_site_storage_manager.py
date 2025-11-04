#!/usr/bin/env python3
"""
Tests for Site Storage Manager

Comprehensive tests for the dual storage architecture system.
"""

import pytest
import asyncio
import tempfile
import json
import shutil
from pathlib import Path
from datetime import datetime
from unittest.mock import patch, AsyncMock

from crawl4ai.site_storage_manager import (
    SiteStorageManager,
    StorageConfig,
    SiteStorageInfo,
    StorageType,
    get_site_storage_manager,
    initialize_site_for_crawling,
    store_crawl_file,
    store_analysis_result
)


class TestStorageConfig:
    """Test StorageConfig data class."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = StorageConfig()
        
        assert config.files_root == r"E:\filefinder"
        assert config.analysis_root == r"D:\Repo\FileFinder-a Crawl4AI mod\sites"
        assert 'documents' in config.files_subdirs
        assert 'graphs' in config.analysis_subdirs
    
    def test_custom_config(self):
        """Test custom configuration."""
        custom_config = StorageConfig(
            files_root="/custom/files",
            analysis_root="/custom/analysis",
            files_subdirs={'pdfs': 'pdf_files'},
            analysis_subdirs={'reports': 'custom_reports'}
        )
        
        assert custom_config.files_root == "/custom/files"
        assert custom_config.analysis_root == "/custom/analysis"
        assert custom_config.files_subdirs == {'pdfs': 'pdf_files'}
        assert custom_config.analysis_subdirs == {'reports': 'custom_reports'}


class TestSiteStorageManager:
    """Test SiteStorageManager main functionality."""
    
    def setup_method(self):
        """Set up test fixtures with temporary directories."""
        self.temp_dir = tempfile.mkdtemp()
        self.files_root = Path(self.temp_dir) / "files"
        self.analysis_root = Path(self.temp_dir) / "analysis"
        
        self.config = StorageConfig(
            files_root=str(self.files_root),
            analysis_root=str(self.analysis_root)
        )
        
        self.manager = SiteStorageManager(self.config)
    
    def teardown_method(self):
        """Clean up temporary directories."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_normalize_domain(self):
        """Test domain normalization."""
        # Test URL normalization
        assert self.manager._normalize_domain("https://example.com") == "example.com"
        assert self.manager._normalize_domain("http://www.example.com") == "example.com"
        assert self.manager._normalize_domain("https://sub.example.com:8080") == "sub.example.com_8080"
        
        # Test domain normalization
        assert self.manager._normalize_domain("example.com") == "example.com"
        assert self.manager._normalize_domain("WWW.EXAMPLE.COM") == "example.com"
    
    @pytest.mark.asyncio
    async def test_initialize_site_storage(self):
        """Test site storage initialization."""
        site_url = "https://example.com"
        
        site_info = await self.manager.initialize_site_storage(site_url)
        
        # Check site info
        assert site_info.domain == "example.com"
        assert site_info.files_path.exists()
        assert site_info.analysis_path.exists()
        assert isinstance(site_info.created_at, datetime)
        
        # Check subdirectories were created
        for subdir in self.config.files_subdirs.values():
            assert (site_info.files_path / subdir).exists()
        
        for subdir in self.config.analysis_subdirs.values():
            assert (site_info.analysis_path / subdir).exists()
        
        # Check metadata file was created
        metadata_path = site_info.analysis_path / "metadata" / "site_info.json"
        assert metadata_path.exists()
    
    @pytest.mark.asyncio
    async def test_get_site_storage_existing(self):
        """Test getting storage info for existing site."""
        site_url = "https://example.com"
        
        # Initialize first
        original_info = await self.manager.initialize_site_storage(site_url)
        
        # Get existing
        retrieved_info = await self.manager.get_site_storage(site_url)
        
        assert retrieved_info is not None
        assert retrieved_info.domain == original_info.domain
        assert retrieved_info.files_path == original_info.files_path
    
    @pytest.mark.asyncio
    async def test_get_site_storage_nonexistent(self):
        """Test getting storage info for non-existent site."""
        site_url = "https://nonexistent.com"
        
        retrieved_info = await self.manager.get_site_storage(site_url)
        assert retrieved_info is None
    
    @pytest.mark.asyncio
    async def test_get_file_storage_path(self):
        """Test getting file storage paths."""
        site_url = "https://example.com"
        
        # Test with auto-creation
        documents_path = await self.manager.get_file_storage_path(
            site_url, "documents", create_if_missing=True
        )
        
        assert documents_path.exists()
        assert documents_path.name == "documents"
        
        # Test with specific file type
        images_path = await self.manager.get_file_storage_path(
            site_url, "images", create_if_missing=False
        )
        
        assert images_path.exists()
        assert images_path.name == "images"
    
    @pytest.mark.asyncio
    async def test_get_analysis_storage_path(self):
        """Test getting analysis storage paths."""
        site_url = "https://example.com"
        
        # Test with auto-creation
        graphs_path = await self.manager.get_analysis_storage_path(
            site_url, "graphs", create_if_missing=True
        )
        
        assert graphs_path.exists()
        assert graphs_path.name == "graphs"
        
        # Test with specific analysis type
        reports_path = await self.manager.get_analysis_storage_path(
            site_url, "reports", create_if_missing=False
        )
        
        assert reports_path.exists()
        assert reports_path.name == "reports"
    
    @pytest.mark.asyncio
    async def test_store_downloaded_file(self):
        """Test storing downloaded files."""
        site_url = "https://example.com"
        file_url = "https://example.com/document.pdf"
        file_content = b"Mock PDF content for testing"
        
        metadata = {
            'title': 'Test Document',
            'content_type': 'application/pdf',
            'size': len(file_content)
        }
        
        stored_path = await self.manager.store_downloaded_file(
            site_url, file_url, file_content, "documents", metadata
        )
        
        # Check file was stored
        stored_file = Path(stored_path)
        assert stored_file.exists()
        assert stored_file.read_bytes() == file_content
        
        # Check metadata was stored
        metadata_file = stored_file.with_suffix(stored_file.suffix + '.meta.json')
        assert metadata_file.exists()
        
        with open(metadata_file, 'r') as f:
            stored_metadata = json.load(f)
            assert stored_metadata['title'] == 'Test Document'
            assert stored_metadata['original_url'] == file_url
    
    @pytest.mark.asyncio
    async def test_store_downloaded_file_duplicate_names(self):
        """Test handling duplicate file names."""
        site_url = "https://example.com"
        file_url = "https://example.com/document.pdf"
        file_content1 = b"First document content"
        file_content2 = b"Second document content"
        
        # Store first file
        path1 = await self.manager.store_downloaded_file(
            site_url, file_url, file_content1, "documents"
        )
        
        # Store second file with same name
        path2 = await self.manager.store_downloaded_file(
            site_url, file_url, file_content2, "documents"
        )
        
        # Check both files exist with different names
        assert Path(path1).exists()
        assert Path(path2).exists()
        assert path1 != path2
        
        # Check content is different
        assert Path(path1).read_bytes() == file_content1
        assert Path(path2).read_bytes() == file_content2
    
    @pytest.mark.asyncio
    async def test_store_analysis_output_json(self):
        """Test storing JSON analysis output."""
        site_url = "https://example.com"
        output_name = "test_analysis"
        
        content = {
            'nodes': 100,
            'edges': 200,
            'analysis_date': datetime.now().isoformat()
        }
        
        stored_path = await self.manager.store_analysis_output(
            site_url, output_name, content, "graphs", ".json"
        )
        
        # Check file was stored
        stored_file = Path(stored_path)
        assert stored_file.exists()
        assert stored_file.suffix == ".json"
        
        # Check content
        with open(stored_file, 'r') as f:
            stored_content = json.load(f)
            assert stored_content['nodes'] == 100
            assert stored_content['edges'] == 200
    
    @pytest.mark.asyncio
    async def test_store_analysis_output_text(self):
        """Test storing text analysis output."""
        site_url = "https://example.com"
        output_name = "test_report"
        content = "This is a test report with analysis results."
        
        stored_path = await self.manager.store_analysis_output(
            site_url, output_name, content, "reports", ".txt"
        )
        
        # Check file was stored
        stored_file = Path(stored_path)
        assert stored_file.exists()
        assert stored_file.read_text() == content
    
    @pytest.mark.asyncio
    async def test_store_analysis_output_binary(self):
        """Test storing binary analysis output."""
        site_url = "https://example.com"
        output_name = "test_binary"
        content = b"Binary data for testing"
        
        stored_path = await self.manager.store_analysis_output(
            site_url, output_name, content, "exports", ".bin"
        )
        
        # Check file was stored
        stored_file = Path(stored_path)
        assert stored_file.exists()
        assert stored_file.read_bytes() == content
    
    @pytest.mark.asyncio
    async def test_get_site_file_list(self):
        """Test getting list of stored files."""
        site_url = "https://example.com"
        
        # Store some test files
        files_to_store = [
            ("https://example.com/doc1.pdf", b"PDF content 1", "documents"),
            ("https://example.com/image1.png", b"PNG content 1", "images"),
            ("https://example.com/doc2.pdf", b"PDF content 2", "documents")
        ]
        
        for file_url, content, file_type in files_to_store:
            await self.manager.store_downloaded_file(
                site_url, file_url, content, file_type
            )
        
        # Get all files
        all_files = await self.manager.get_site_file_list(site_url)
        assert len(all_files) == 3
        
        # Get documents only
        doc_files = await self.manager.get_site_file_list(site_url, "documents")
        assert len(doc_files) == 2
        
        # Check file info structure
        file_info = all_files[0]
        assert 'path' in file_info
        assert 'name' in file_info
        assert 'size' in file_info
        assert 'modified' in file_info
        assert 'type' in file_info
    
    @pytest.mark.asyncio
    async def test_get_site_analysis_outputs(self):
        """Test getting list of analysis outputs."""
        site_url = "https://example.com"
        
        # Store some analysis outputs
        outputs_to_store = [
            ("graph_analysis", {"nodes": 50}, "graphs"),
            ("crawl_report", {"pages": 100}, "reports"),
            ("site_map", "XML content", "exports")
        ]
        
        for name, content, analysis_type in outputs_to_store:
            await self.manager.store_analysis_output(
                site_url, name, content, analysis_type
            )
        
        # Get all outputs
        all_outputs = await self.manager.get_site_analysis_outputs(site_url)
        assert len(all_outputs) == 3
        
        # Get graphs only
        graph_outputs = await self.manager.get_site_analysis_outputs(site_url, "graphs")
        assert len(graph_outputs) == 1
        
        # Check output info structure
        output_info = all_outputs[0]
        assert 'path' in output_info
        assert 'name' in output_info
        assert 'analysis_type' in output_info
    
    @pytest.mark.asyncio
    async def test_get_storage_statistics_single_site(self):
        """Test getting statistics for a single site."""
        site_url = "https://example.com"
        
        # Store some files and outputs
        await self.manager.store_downloaded_file(
            site_url, "https://example.com/test.pdf", b"Test content", "documents"
        )
        await self.manager.store_analysis_output(
            site_url, "test_analysis", {"test": "data"}, "reports"
        )
        
        stats = await self.manager.get_storage_statistics(site_url)
        
        assert stats['domain'] == "example.com"
        assert stats['files_count'] == 1
        assert stats['analysis_outputs_count'] == 1
        assert stats['total_file_size'] > 0
        assert 'created_at' in stats
    
    @pytest.mark.asyncio
    async def test_get_storage_statistics_all_sites(self):
        """Test getting statistics for all sites."""
        # Create multiple sites
        sites = ["https://site1.com", "https://site2.com"]
        
        for site in sites:
            await self.manager.store_downloaded_file(
                site, f"{site}/test.pdf", b"Test content", "documents"
            )
        
        stats = await self.manager.get_storage_statistics()
        
        assert stats['total_sites'] >= 2
        assert stats['total_files'] >= 2
        assert len(stats['sites']) >= 2


class TestUtilityFunctions:
    """Test utility functions."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.config = StorageConfig(
            files_root=str(Path(self.temp_dir) / "files"),
            analysis_root=str(Path(self.temp_dir) / "analysis")
        )
    
    def teardown_method(self):
        """Clean up temporary directories."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @pytest.mark.asyncio
    async def test_get_site_storage_manager(self):
        """Test getting storage manager instance."""
        manager = await get_site_storage_manager(self.config)
        assert isinstance(manager, SiteStorageManager)
        assert manager.config == self.config
    
    @pytest.mark.asyncio
    async def test_initialize_site_for_crawling(self):
        """Test convenience function for site initialization."""
        site_url = "https://example.com"
        
        files_path, analysis_path = await initialize_site_for_crawling(
            site_url, self.config
        )
        
        assert files_path.exists()
        assert analysis_path.exists()
        assert files_path.name == "example.com"
        assert analysis_path.name == "example.com"
    
    @pytest.mark.asyncio
    async def test_store_crawl_file(self):
        """Test convenience function for storing files."""
        site_url = "https://example.com"
        file_url = "https://example.com/test.pdf"
        content = b"Test file content"
        
        stored_path = await store_crawl_file(
            site_url, file_url, content, "documents", config=self.config
        )
        
        assert Path(stored_path).exists()
        assert Path(stored_path).read_bytes() == content
    
    @pytest.mark.asyncio
    async def test_store_analysis_result(self):
        """Test convenience function for storing analysis results."""
        site_url = "https://example.com"
        analysis_name = "test_analysis"
        result = {"test": "result", "value": 42}
        
        stored_path = await store_analysis_result(
            site_url, analysis_name, result, "reports", self.config
        )
        
        assert Path(stored_path).exists()
        
        with open(stored_path, 'r') as f:
            stored_result = json.load(f)
            assert stored_result == result


class TestErrorHandling:
    """Test error handling scenarios."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.config = StorageConfig(
            files_root=str(Path(self.temp_dir) / "files"),
            analysis_root=str(Path(self.temp_dir) / "analysis")
        )
        self.manager = SiteStorageManager(self.config)
    
    def teardown_method(self):
        """Clean up temporary directories."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @pytest.mark.asyncio
    async def test_get_storage_path_nonexistent_site(self):
        """Test getting storage path for non-existent site with create_if_missing=False."""
        site_url = "https://nonexistent.com"
        
        with pytest.raises(ValueError, match="No storage found"):
            await self.manager.get_file_storage_path(
                site_url, "documents", create_if_missing=False
            )
    
    @pytest.mark.asyncio
    async def test_store_analysis_output_invalid_content_type(self):
        """Test storing analysis output with invalid content type."""
        site_url = "https://example.com"
        
        # Initialize storage first
        await self.manager.initialize_site_storage(site_url)
        
        # Try to store invalid content type
        with pytest.raises(ValueError, match="Unsupported content type"):
            await self.manager.store_analysis_output(
                site_url, "test", [1, 2, 3], "reports"  # List is not supported
            )


class TestIntegration:
    """Integration tests."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.config = StorageConfig(
            files_root=str(Path(self.temp_dir) / "files"),
            analysis_root=str(Path(self.temp_dir) / "analysis")
        )
    
    def teardown_method(self):
        """Clean up temporary directories."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @pytest.mark.asyncio
    async def test_complete_workflow(self):
        """Test complete storage workflow."""
        manager = SiteStorageManager(self.config)
        site_url = "https://integration-test.com"
        
        # Step 1: Initialize storage
        site_info = await manager.initialize_site_storage(site_url)
        assert site_info.domain == "integration-test.com"
        
        # Step 2: Store multiple files
        files = [
            ("https://integration-test.com/doc1.pdf", b"PDF 1", "documents"),
            ("https://integration-test.com/doc2.pdf", b"PDF 2", "documents"),
            ("https://integration-test.com/data.xlsx", b"Excel data", "data")
        ]
        
        stored_files = []
        for file_url, content, file_type in files:
            path = await manager.store_downloaded_file(
                site_url, file_url, content, file_type
            )
            stored_files.append(path)
        
        # Step 3: Store analysis outputs
        analyses = [
            ("site_graph", {"nodes": 50, "edges": 100}, "graphs"),
            ("crawl_report", {"status": "complete"}, "reports")
        ]
        
        stored_analyses = []
        for name, content, analysis_type in analyses:
            path = await manager.store_analysis_output(
                site_url, name, content, analysis_type
            )
            stored_analyses.append(path)
        
        # Step 4: Verify everything was stored
        file_list = await manager.get_site_file_list(site_url)
        assert len(file_list) == 3
        
        analysis_list = await manager.get_site_analysis_outputs(site_url)
        assert len(analysis_list) == 2
        
        # Step 5: Check statistics
        stats = await manager.get_storage_statistics(site_url)
        assert stats['files_count'] == 3
        assert stats['analysis_outputs_count'] == 2
        
        # Step 6: Verify all files exist and have correct content
        for stored_path in stored_files:
            assert Path(stored_path).exists()
        
        for stored_path in stored_analyses:
            assert Path(stored_path).exists()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])