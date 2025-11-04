"""
Tests for FileDiscoveryFilter implementation.

This test suite verifies that the FileDiscoveryFilter correctly identifies
and catalogs downloadable files according to the requirements.
"""

import pytest
from unittest.mock import Mock, patch
from crawl4ai.file_discovery_filter import (
    FileDiscoveryFilter, FileType, FileMetadata, FileDiscoveryStats,
    create_document_filter, create_data_filter, create_media_filter,
    create_comprehensive_filter
)


class TestFileDiscoveryFilter:
    """Test cases for FileDiscoveryFilter functionality."""
    
    def test_filter_initialization_default(self):
        """Test filter initialization with default settings."""
        filter_instance = FileDiscoveryFilter()
        
        assert filter_instance.name == "FileDiscoveryFilter"
        assert filter_instance.enable_mime_validation is True
        assert filter_instance.track_repository_paths is True
        assert len(filter_instance.target_extensions) > 0
        assert len(filter_instance.repository_patterns) > 0
    
    def test_filter_initialization_custom(self):
        """Test filter initialization with custom settings."""
        target_extensions = ['.pdf', '.doc', '.xls']
        exclude_extensions = ['.tmp']
        
        filter_instance = FileDiscoveryFilter(
            target_extensions=target_extensions,
            exclude_extensions=exclude_extensions,
            max_file_size_mb=50,
            enable_mime_validation=False,
            name="CustomFilter"
        )
        
        assert filter_instance.name == "CustomFilter"
        assert filter_instance.enable_mime_validation is False
        assert filter_instance.max_file_size_mb == 50
        assert '.pdf' in filter_instance.target_extensions
        assert '.tmp' in filter_instance.exclude_extensions
    
    def test_filter_initialization_by_file_types(self):
        """Test filter initialization using file types."""
        filter_instance = FileDiscoveryFilter(
            target_file_types=[FileType.DOCUMENT, FileType.SPREADSHEET]
        )
        
        # Should include document and spreadsheet extensions
        assert '.pdf' in filter_instance.target_extensions
        assert '.doc' in filter_instance.target_extensions
        assert '.xls' in filter_instance.target_extensions
        assert '.xlsx' in filter_instance.target_extensions
        
        # Should not include other types
        assert '.mp3' not in filter_instance.target_extensions
        assert '.jpg' not in filter_instance.target_extensions
    
    def test_apply_valid_document_file(self):
        """Test filter application on valid document files."""
        filter_instance = FileDiscoveryFilter(
            target_file_types=[FileType.DOCUMENT]
        )
        
        test_urls = [
            "https://example.com/document.pdf",
            "https://example.com/files/report.doc",
            "https://example.com/downloads/manual.docx",
            "https://example.com/attachments/guide.txt"
        ]
        
        for url in test_urls:
            result = filter_instance.apply(url)
            assert result is True, f"Failed to identify file: {url}"
        
        # Check that files were discovered
        assert len(filter_instance.discovered_files) == len(test_urls)
        assert filter_instance.discovery_stats.total_files_discovered == len(test_urls)
    
    def test_apply_invalid_files(self):
        """Test filter application on invalid or non-target files."""
        filter_instance = FileDiscoveryFilter(
            target_file_types=[FileType.DOCUMENT]
        )
        
        test_urls = [
            "https://example.com/page.html",  # HTML page, not a file
            "https://example.com/image.jpg",  # Image, not in target types
            "https://example.com/script.js",  # Script, not in target types
            "https://example.com/noextension",  # No extension
            "https://example.com/",  # Root path
        ]
        
        for url in test_urls:
            result = filter_instance.apply(url)
            assert result is False, f"Incorrectly identified as file: {url}"
        
        # Check that no files were discovered
        assert len(filter_instance.discovered_files) == 0
        assert filter_instance.discovery_stats.total_files_discovered == 0
    
    def test_apply_excluded_extensions(self):
        """Test that excluded extensions are properly filtered out."""
        filter_instance = FileDiscoveryFilter(
            target_extensions=['.pdf', '.doc', '.tmp'],
            exclude_extensions=['.tmp']
        )
        
        # Should accept PDF and DOC
        assert filter_instance.apply("https://example.com/file.pdf") is True
        assert filter_instance.apply("https://example.com/file.doc") is True
        
        # Should reject TMP (excluded)
        assert filter_instance.apply("https://example.com/file.tmp") is False
        
        assert len(filter_instance.discovered_files) == 2
    
    def test_repository_path_extraction(self):
        """Test extraction of repository paths from URLs."""
        filter_instance = FileDiscoveryFilter(
            target_file_types=[FileType.DOCUMENT],
            track_repository_paths=True
        )
        
        test_cases = [
            ("https://example.com/downloads/file.pdf", "/downloads"),
            ("https://example.com/files/docs/report.doc", "/files"),
            ("https://example.com/attachments/manual.pdf", "/attachments"),
            ("https://example.com/other/path/file.pdf", None),
        ]
        
        for url, expected_repo in test_cases:
            filter_instance.apply(url)
        
        discovered = filter_instance.discovered_files
        assert len(discovered) == 4
        
        # Check repository paths
        repo_paths = [f.repository_path for f in discovered]
        assert "/downloads" in repo_paths
        assert "/files" in repo_paths
        assert "/attachments" in repo_paths
        assert None in repo_paths  # For the path that doesn't match patterns
    
    def test_file_metadata_creation(self):
        """Test that file metadata is correctly created."""
        filter_instance = FileDiscoveryFilter(
            target_file_types=[FileType.DOCUMENT]
        )
        
        url = "https://example.com/downloads/report.pdf"
        result = filter_instance.apply(url)
        
        assert result is True
        assert len(filter_instance.discovered_files) == 1
        
        file_metadata = filter_instance.discovered_files[0]
        assert file_metadata.url == url
        assert file_metadata.filename == "report.pdf"
        assert file_metadata.extension == ".pdf"
        assert file_metadata.file_type == FileType.DOCUMENT
        assert file_metadata.repository_path == "/downloads"
        assert file_metadata.mime_type == "application/pdf"
    
    def test_discovery_statistics(self):
        """Test that discovery statistics are correctly maintained."""
        filter_instance = FileDiscoveryFilter(
            target_file_types=[FileType.DOCUMENT, FileType.SPREADSHEET]
        )
        
        test_files = [
            "https://example.com/file1.pdf",
            "https://example.com/file2.pdf",
            "https://example.com/file3.doc",
            "https://example.com/file4.xls",
            "https://example.com/downloads/file5.xlsx",
        ]
        
        for url in test_files:
            filter_instance.apply(url)
        
        stats = filter_instance.discovery_stats
        assert stats.total_files_discovered == 5
        assert stats.files_by_type[FileType.DOCUMENT] == 3  # 2 PDF + 1 DOC
        assert stats.files_by_type[FileType.SPREADSHEET] == 2  # 1 XLS + 1 XLSX
        assert stats.files_by_extension['.pdf'] == 2
        assert stats.files_by_extension['.doc'] == 1
        assert stats.files_by_extension['.xls'] == 1
        assert stats.files_by_extension['.xlsx'] == 1
    
    def test_get_discovered_files_filtered(self):
        """Test getting discovered files filtered by type."""
        filter_instance = FileDiscoveryFilter(
            target_file_types=[FileType.DOCUMENT, FileType.SPREADSHEET]
        )
        
        test_files = [
            "https://example.com/file1.pdf",  # DOCUMENT
            "https://example.com/file2.doc",  # DOCUMENT
            "https://example.com/file3.xls",  # SPREADSHEET
        ]
        
        for url in test_files:
            filter_instance.apply(url)
        
        # Get all files
        all_files = filter_instance.get_discovered_files()
        assert len(all_files) == 3
        
        # Get only documents
        documents = filter_instance.get_discovered_files(FileType.DOCUMENT)
        assert len(documents) == 2
        assert all(f.file_type == FileType.DOCUMENT for f in documents)
        
        # Get only spreadsheets
        spreadsheets = filter_instance.get_discovered_files(FileType.SPREADSHEET)
        assert len(spreadsheets) == 1
        assert spreadsheets[0].file_type == FileType.SPREADSHEET
    
    def test_repository_inventory(self):
        """Test getting repository inventory."""
        filter_instance = FileDiscoveryFilter(
            target_file_types=[FileType.DOCUMENT]
        )
        
        test_files = [
            "https://example.com/downloads/file1.pdf",
            "https://example.com/downloads/file2.doc",
            "https://example.com/files/file3.pdf",
            "https://example.com/other/file4.pdf",  # No matching repo pattern
        ]
        
        for url in test_files:
            filter_instance.apply(url)
        
        inventory = filter_instance.get_repository_inventory()
        
        assert "/downloads" in inventory
        assert "/files" in inventory
        assert "unknown" in inventory  # For files without matching repo pattern
        
        assert len(inventory["/downloads"]) == 2
        assert len(inventory["/files"]) == 1
        assert len(inventory["unknown"]) == 1
    
    def test_export_file_inventory(self):
        """Test exporting file inventory in different formats."""
        filter_instance = FileDiscoveryFilter(
            target_file_types=[FileType.DOCUMENT]
        )
        
        filter_instance.apply("https://example.com/file.pdf")
        
        # Test dict export
        dict_export = filter_instance.export_file_inventory("dict")
        assert isinstance(dict_export, dict)
        assert "discovered_files" in dict_export
        assert "statistics" in dict_export
        assert len(dict_export["discovered_files"]) == 1
        
        # Test JSON export
        json_export = filter_instance.export_file_inventory("json")
        assert isinstance(json_export, str)
        assert "discovered_files" in json_export
        
        # Test CSV export
        csv_export = filter_instance.export_file_inventory("csv")
        assert isinstance(csv_export, str)
        assert "URL,Filename,Extension" in csv_export
        assert "file.pdf" in csv_export
    
    def test_clear_discovered_files(self):
        """Test clearing discovered files and statistics."""
        filter_instance = FileDiscoveryFilter(
            target_file_types=[FileType.DOCUMENT]
        )
        
        # Add some files
        filter_instance.apply("https://example.com/file1.pdf")
        filter_instance.apply("https://example.com/file2.doc")
        
        assert len(filter_instance.discovered_files) == 2
        assert filter_instance.discovery_stats.total_files_discovered == 2
        
        # Clear files
        filter_instance.clear_discovered_files()
        
        assert len(filter_instance.discovered_files) == 0
        assert filter_instance.discovery_stats.total_files_discovered == 0
    
    def test_mime_type_validation(self):
        """Test MIME type validation functionality."""
        filter_instance = FileDiscoveryFilter(
            target_extensions=['.pdf'],
            enable_mime_validation=True
        )
        
        # Test valid MIME type
        with patch('mimetypes.guess_type') as mock_guess:
            mock_guess.return_value = ('application/pdf', None)
            result = filter_instance.apply("https://example.com/file.pdf")
            assert result is True
        
        # Test invalid MIME type (should still pass for now as we're lenient)
        with patch('mimetypes.guess_type') as mock_guess:
            mock_guess.return_value = ('text/html', None)
            result = filter_instance.apply("https://example.com/file.pdf")
            # Current implementation is lenient with MIME validation
            assert result is True
    
    def test_convenience_functions(self):
        """Test convenience functions for creating specialized filters."""
        # Test document filter
        doc_filter = create_document_filter()
        assert isinstance(doc_filter, FileDiscoveryFilter)
        assert doc_filter.name == "DocumentFilter"
        assert '.pdf' in doc_filter.target_extensions
        assert '.doc' in doc_filter.target_extensions
        
        # Test data filter
        data_filter = create_data_filter()
        assert isinstance(data_filter, FileDiscoveryFilter)
        assert data_filter.name == "DataFilter"
        assert '.json' in data_filter.target_extensions
        assert '.csv' in data_filter.target_extensions
        
        # Test media filter
        media_filter = create_media_filter()
        assert isinstance(media_filter, FileDiscoveryFilter)
        assert media_filter.name == "MediaFilter"
        assert '.jpg' in media_filter.target_extensions
        assert '.mp3' in media_filter.target_extensions
        
        # Test comprehensive filter
        comp_filter = create_comprehensive_filter()
        assert isinstance(comp_filter, FileDiscoveryFilter)
        assert comp_filter.name == "ComprehensiveFileFilter"
        # Should include extensions from all file types
        assert '.pdf' in comp_filter.target_extensions
        assert '.jpg' in comp_filter.target_extensions
        assert '.mp3' in comp_filter.target_extensions


class TestFileMetadata:
    """Test cases for FileMetadata class."""
    
    def test_file_metadata_creation(self):
        """Test FileMetadata creation and post-initialization."""
        metadata = FileMetadata(
            url="https://example.com/file.pdf",
            filename="file.pdf",
            extension=".pdf",
            file_type=FileType.DOCUMENT
        )
        
        assert metadata.url == "https://example.com/file.pdf"
        assert metadata.filename == "file.pdf"
        assert metadata.extension == ".pdf"
        assert metadata.file_type == FileType.DOCUMENT
        assert metadata.mime_type == "application/pdf"  # Set by post_init


class TestFileDiscoveryStats:
    """Test cases for FileDiscoveryStats class."""
    
    def test_stats_initialization(self):
        """Test FileDiscoveryStats initialization."""
        stats = FileDiscoveryStats()
        
        assert stats.total_files_discovered == 0
        assert len(stats.files_by_type) == 0
        assert len(stats.files_by_extension) == 0
        assert len(stats.repository_paths) == 0
    
    def test_add_file_to_stats(self):
        """Test adding files to statistics."""
        stats = FileDiscoveryStats()
        
        metadata1 = FileMetadata(
            url="https://example.com/file1.pdf",
            filename="file1.pdf",
            extension=".pdf",
            file_type=FileType.DOCUMENT,
            repository_path="/downloads"
        )
        
        metadata2 = FileMetadata(
            url="https://example.com/file2.pdf",
            filename="file2.pdf",
            extension=".pdf",
            file_type=FileType.DOCUMENT,
            repository_path="/files"
        )
        
        stats.add_file(metadata1)
        stats.add_file(metadata2)
        
        assert stats.total_files_discovered == 2
        assert stats.files_by_type[FileType.DOCUMENT] == 2
        assert stats.files_by_extension['.pdf'] == 2
        assert len(stats.repository_paths) == 2
        assert "/downloads" in stats.repository_paths
        assert "/files" in stats.repository_paths


if __name__ == "__main__":
    pytest.main([__file__])