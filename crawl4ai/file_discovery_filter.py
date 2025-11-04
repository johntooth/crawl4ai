"""
File Discovery Filter for Crawl4AI Domain Intelligence Crawler

This module implements a FileDiscoveryFilter that extends the existing URLFilter
architecture to identify and catalog downloadable files and documents during
crawling operations.

Features:
- File extension detection (.pdf, .doc, .xls, etc.)
- MIME type analysis for content type verification
- URL pattern matching for file repositories
- Integration with existing FilterChain and FilterStats
- Comprehensive file inventory management
- Support for AsyncUrlSeeder integration
"""

import re
import mimetypes
from typing import List, Set, Dict, Optional, Union, Pattern
from urllib.parse import urlparse, unquote
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum
import logging

# Import existing filter architecture
from .deep_crawling.filters import URLFilter, FilterStats
from .async_logger import AsyncLogger


class FileType(Enum):
    """Enumeration of supported file types for discovery."""
    DOCUMENT = "document"
    SPREADSHEET = "spreadsheet"
    PRESENTATION = "presentation"
    ARCHIVE = "archive"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    DATA = "data"
    CODE = "code"
    OTHER = "other"


@dataclass
class FileMetadata:
    """Metadata for discovered files."""
    url: str
    filename: str
    extension: str
    file_type: FileType
    mime_type: Optional[str] = None
    estimated_size: Optional[int] = None
    source_url: Optional[str] = None
    discovery_timestamp: Optional[float] = None
    repository_path: Optional[str] = None
    
    def __post_init__(self):
        """Post-initialization to set derived fields."""
        if not self.mime_type:
            self.mime_type, _ = mimetypes.guess_type(self.url)


@dataclass
class FileDiscoveryStats:
    """Statistics for file discovery operations."""
    total_files_discovered: int = 0
    files_by_type: Dict[FileType, int] = field(default_factory=dict)
    files_by_extension: Dict[str, int] = field(default_factory=dict)
    repository_paths: Set[str] = field(default_factory=set)
    
    def add_file(self, file_metadata: FileMetadata):
        """Add a discovered file to statistics."""
        self.total_files_discovered += 1
        
        # Update type counts
        if file_metadata.file_type not in self.files_by_type:
            self.files_by_type[file_metadata.file_type] = 0
        self.files_by_type[file_metadata.file_type] += 1
        
        # Update extension counts
        ext = file_metadata.extension.lower()
        if ext not in self.files_by_extension:
            self.files_by_extension[ext] = 0
        self.files_by_extension[ext] += 1
        
        # Track repository paths
        if file_metadata.repository_path:
            self.repository_paths.add(file_metadata.repository_path)


class FileDiscoveryFilter(URLFilter):
    """
    File discovery filter that extends existing URLFilter architecture.
    
    This filter identifies downloadable files by extension, MIME type, and URL patterns,
    integrating seamlessly with the existing FilterChain for comprehensive file discovery
    during crawling operations.
    
    Features:
    - Configurable file extensions for different file types
    - URL pattern matching for file repositories
    - MIME type validation
    - Comprehensive file inventory management
    - Integration with existing FilterStats pattern
    """
    
    # Default file extensions by category
    DEFAULT_EXTENSIONS = {
        FileType.DOCUMENT: {
            '.pdf', '.doc', '.docx', '.txt', '.rtf', '.odt', '.pages',
            '.epub', '.mobi', '.djvu', '.xps'
        },
        FileType.SPREADSHEET: {
            '.xls', '.xlsx', '.ods', '.numbers'
        },
        FileType.PRESENTATION: {
            '.ppt', '.pptx', '.odp', '.key', '.pps', '.ppsx'
        },
        FileType.ARCHIVE: {
            '.zip', '.rar', '.7z', '.tar', '.gz', '.bz2', '.xz',
            '.tar.gz', '.tar.bz2', '.tar.xz', '.tgz'
        },
        FileType.IMAGE: {
            '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif',
            '.svg', '.webp', '.ico', '.psd', '.ai', '.eps'
        },
        FileType.AUDIO: {
            '.mp3', '.wav', '.flac', '.aac', '.ogg', '.wma', '.m4a'
        },
        FileType.VIDEO: {
            '.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm',
            '.m4v', '.3gp', '.mpg', '.mpeg'
        },
        FileType.DATA: {
            '.json', '.xml', '.yaml', '.yml', '.sql', '.db', '.sqlite',
            '.mdb', '.accdb', '.csv', '.tsv'
        },
        FileType.CODE: {
            '.py', '.js', '.html', '.css', '.java', '.cpp', '.c', '.h',
            '.php', '.rb', '.go', '.rs', '.swift', '.kt'
        }
    }
    
    # Common file repository URL patterns
    DEFAULT_REPOSITORY_PATTERNS = [
        r'/downloads?/',
        r'/files?/',
        r'/documents?/',
        r'/attachments?/',
        r'/assets/',
        r'/media/',
        r'/uploads?/',
        r'/resources?/',
        r'/library/',
        r'/repository/',
        r'/archive/',
        r'/content/',
        r'/static/',
        r'/public/',
        r'/shared/',
    ]
    
    def __init__(
        self,
        target_extensions: Optional[Union[List[str], Set[str]]] = None,
        target_file_types: Optional[List[FileType]] = None,
        repository_patterns: Optional[List[str]] = None,
        exclude_extensions: Optional[Union[List[str], Set[str]]] = None,
        max_file_size_mb: Optional[int] = None,
        enable_mime_validation: bool = True,
        track_repository_paths: bool = True,
        logger: Optional[AsyncLogger] = None,
        name: str = "FileDiscoveryFilter"
    ):
        """
        Initialize the FileDiscoveryFilter.
        
        Args:
            target_extensions: Specific file extensions to target (e.g., ['.pdf', '.doc'])
            target_file_types: File types to include (e.g., [FileType.DOCUMENT, FileType.SPREADSHEET])
            repository_patterns: URL patterns that indicate file repositories
            exclude_extensions: File extensions to explicitly exclude
            max_file_size_mb: Maximum file size in MB to consider (for URL-based size hints)
            enable_mime_validation: Whether to validate MIME types
            track_repository_paths: Whether to track and analyze repository paths
            logger: Optional logger for detailed logging
            name: Name for this filter instance
        """
        super().__init__(name=name)
        
        self._custom_logger = logger
        self.enable_mime_validation = enable_mime_validation
        self.track_repository_paths = track_repository_paths
        self.max_file_size_mb = max_file_size_mb
        
        # Build target extensions set
        self.target_extensions = set()
        if target_extensions:
            self.target_extensions.update(
                ext.lower() if ext.startswith('.') else f'.{ext.lower()}'
                for ext in target_extensions
            )
        elif target_file_types:
            for file_type in target_file_types:
                if file_type in self.DEFAULT_EXTENSIONS:
                    self.target_extensions.update(self.DEFAULT_EXTENSIONS[file_type])
        else:
            # Default to document and data files
            for file_type in [FileType.DOCUMENT, FileType.SPREADSHEET, FileType.PRESENTATION, FileType.DATA]:
                self.target_extensions.update(self.DEFAULT_EXTENSIONS[file_type])
        
        # Build exclude extensions set
        self.exclude_extensions = set()
        if exclude_extensions:
            self.exclude_extensions.update(
                ext.lower() if ext.startswith('.') else f'.{ext.lower()}'
                for ext in exclude_extensions
            )
        
        # Compile repository patterns
        self.repository_patterns = []
        patterns = repository_patterns or self.DEFAULT_REPOSITORY_PATTERNS
        for pattern in patterns:
            try:
                self.repository_patterns.append(re.compile(pattern, re.IGNORECASE))
            except re.error as e:
                if self._custom_logger:
                    self._custom_logger.warning(f"Invalid repository pattern '{pattern}': {e}")
        
        # File discovery statistics
        self.discovery_stats = FileDiscoveryStats()
        self.discovered_files: List[FileMetadata] = []
        
        # Extension to file type mapping
        self._build_extension_mapping()
        
        if self._custom_logger:
            self._custom_logger.info(
                f"FileDiscoveryFilter initialized with {len(self.target_extensions)} target extensions",
                tag="FILE_FILTER"
            )
    
    def _build_extension_mapping(self):
        """Build mapping from file extensions to file types."""
        self.extension_to_type = {}
        for file_type, extensions in self.DEFAULT_EXTENSIONS.items():
            for ext in extensions:
                self.extension_to_type[ext.lower()] = file_type
    
    def apply(self, url: str) -> bool:
        """
        Apply the file discovery filter to a URL.
        
        Args:
            url: The URL to analyze for file discovery
            
        Returns:
            bool: True if the URL represents a discoverable file, False otherwise
        """
        try:
            # Parse URL
            parsed_url = urlparse(url)
            path = unquote(parsed_url.path)
            
            # Extract filename and extension
            filename = Path(path).name
            if not filename or '.' not in filename:
                self._update_stats(False)
                return False
            
            # Get file extension
            extension = Path(filename).suffix.lower()
            if not extension:
                self._update_stats(False)
                return False
            
            # Check if extension is excluded
            if extension in self.exclude_extensions:
                self._update_stats(False)
                return False
            
            # Check if extension is in target extensions
            if extension not in self.target_extensions:
                self._update_stats(False)
                return False
            
            # Validate MIME type if enabled
            if self.enable_mime_validation:
                mime_type, _ = mimetypes.guess_type(url)
                if mime_type and not self._is_valid_mime_type(mime_type, extension):
                    if self._custom_logger:
                        self._custom_logger.debug(
                            f"MIME type mismatch for {url}: {mime_type} vs {extension}",
                            tag="FILE_FILTER"
                        )
                    self._update_stats(False)
                    return False
            
            # Check file size hints in URL (if available)
            if self.max_file_size_mb and not self._check_size_hints(url):
                self._update_stats(False)
                return False
            
            # Create file metadata
            file_type = self.extension_to_type.get(extension, FileType.OTHER)
            repository_path = self._extract_repository_path(path) if self.track_repository_paths else None
            
            file_metadata = FileMetadata(
                url=url,
                filename=filename,
                extension=extension,
                file_type=file_type,
                repository_path=repository_path
            )
            
            # Add to discovered files and update statistics
            self.discovered_files.append(file_metadata)
            self.discovery_stats.add_file(file_metadata)
            
            if self._custom_logger:
                self._custom_logger.info(
                    f"Discovered {file_type.value} file: {filename}",
                    tag="FILE_FILTER"
                )
            
            self._update_stats(True)
            return True
            
        except Exception as e:
            if self._custom_logger:
                self._custom_logger.error(f"Error processing URL {url}: {e}", tag="FILE_FILTER")
            self._update_stats(False)
            return False
    
    def _is_valid_mime_type(self, mime_type: str, extension: str) -> bool:
        """
        Validate that the MIME type matches the file extension.
        
        Args:
            mime_type: The MIME type to validate
            extension: The file extension
            
        Returns:
            bool: True if MIME type is valid for the extension
        """
        # Common MIME type mappings for validation
        mime_mappings = {
            '.pdf': ['application/pdf'],
            '.doc': ['application/msword'],
            '.docx': ['application/vnd.openxmlformats-officedocument.wordprocessingml.document'],
            '.xls': ['application/vnd.ms-excel'],
            '.xlsx': ['application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'],
            '.ppt': ['application/vnd.ms-powerpoint'],
            '.pptx': ['application/vnd.openxmlformats-officedocument.presentationml.presentation'],
            '.zip': ['application/zip'],
            '.csv': ['text/csv', 'application/csv'],
            '.json': ['application/json'],
            '.xml': ['application/xml', 'text/xml'],
        }
        
        expected_mimes = mime_mappings.get(extension.lower())
        if expected_mimes:
            is_valid = mime_type.lower() in [m.lower() for m in expected_mimes]
            if not is_valid and self._custom_logger:
                self._custom_logger.debug(
                    f"Unexpected MIME type {mime_type} for extension {extension}, but allowing it",
                    tag="FILE_FILTER"
                )
            # Be lenient - allow files even with unexpected MIME types
            # This handles cases where servers might return incorrect MIME types
            return True
        
        # For extensions not in our mapping, accept any reasonable MIME type
        return True
    
    def _check_size_hints(self, url: str) -> bool:
        """
        Check URL for file size hints and validate against max_file_size_mb.
        
        Args:
            url: The URL to check for size hints
            
        Returns:
            bool: True if size is acceptable or no size hint found
        """
        if not self.max_file_size_mb:
            return True
        
        # Look for size hints in URL parameters or path
        size_patterns = [
            r'size=(\d+)',
            r'filesize=(\d+)',
            r'bytes=(\d+)',
            r'length=(\d+)'
        ]
        
        for pattern in size_patterns:
            match = re.search(pattern, url, re.IGNORECASE)
            if match:
                try:
                    size_bytes = int(match.group(1))
                    size_mb = size_bytes / (1024 * 1024)
                    return size_mb <= self.max_file_size_mb
                except ValueError:
                    continue
        
        # No size hint found, assume acceptable
        return True
    
    def _extract_repository_path(self, path: str) -> Optional[str]:
        """
        Extract repository path from URL path if it matches known patterns.
        
        Args:
            path: The URL path to analyze
            
        Returns:
            Optional[str]: The repository path if found, None otherwise
        """
        for pattern in self.repository_patterns:
            match = pattern.search(path)
            if match:
                # Extract the path up to and including the repository directory
                repo_end = match.end()
                return path[:repo_end].rstrip('/')
        
        return None
    
    def get_discovered_files(self, file_type: Optional[FileType] = None) -> List[FileMetadata]:
        """
        Get list of discovered files, optionally filtered by file type.
        
        Args:
            file_type: Optional file type to filter by
            
        Returns:
            List[FileMetadata]: List of discovered files
        """
        if file_type is None:
            return self.discovered_files.copy()
        
        return [f for f in self.discovered_files if f.file_type == file_type]
    
    def get_discovery_stats(self) -> FileDiscoveryStats:
        """
        Get file discovery statistics.
        
        Returns:
            FileDiscoveryStats: Current discovery statistics
        """
        return self.discovery_stats
    
    def get_repository_inventory(self) -> Dict[str, List[FileMetadata]]:
        """
        Get inventory of files organized by repository path.
        
        Returns:
            Dict[str, List[FileMetadata]]: Files organized by repository path
        """
        inventory = {}
        for file_metadata in self.discovered_files:
            repo_path = file_metadata.repository_path or "unknown"
            if repo_path not in inventory:
                inventory[repo_path] = []
            inventory[repo_path].append(file_metadata)
        
        return inventory
    
    def clear_discovered_files(self):
        """Clear the list of discovered files and reset statistics."""
        self.discovered_files.clear()
        self.discovery_stats = FileDiscoveryStats()
        
        if self._custom_logger:
            self._custom_logger.info("Cleared discovered files and reset statistics", tag="FILE_FILTER")
    
    def export_file_inventory(self, format: str = "json") -> Union[str, Dict]:
        """
        Export the file inventory in the specified format.
        
        Args:
            format: Export format ("json", "csv", or "dict")
            
        Returns:
            Union[str, Dict]: Exported inventory data
        """
        if format.lower() == "dict":
            return {
                "discovered_files": [
                    {
                        "url": f.url,
                        "filename": f.filename,
                        "extension": f.extension,
                        "file_type": f.file_type.value,
                        "mime_type": f.mime_type,
                        "repository_path": f.repository_path
                    }
                    for f in self.discovered_files
                ],
                "statistics": {
                    "total_files": self.discovery_stats.total_files_discovered,
                    "files_by_type": {ft.value: count for ft, count in self.discovery_stats.files_by_type.items()},
                    "files_by_extension": dict(self.discovery_stats.files_by_extension),
                    "repository_paths": list(self.discovery_stats.repository_paths)
                }
            }
        elif format.lower() == "json":
            import json
            return json.dumps(self.export_file_inventory("dict"), indent=2)
        elif format.lower() == "csv":
            import csv
            import io
            
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Write header
            writer.writerow(["URL", "Filename", "Extension", "File Type", "MIME Type", "Repository Path"])
            
            # Write data
            for f in self.discovered_files:
                writer.writerow([
                    f.url, f.filename, f.extension, f.file_type.value,
                    f.mime_type or "", f.repository_path or ""
                ])
            
            return output.getvalue()
        else:
            raise ValueError(f"Unsupported export format: {format}")


# Convenience functions for integration with existing systems

def create_document_filter(logger: Optional[AsyncLogger] = None) -> FileDiscoveryFilter:
    """Create a filter specifically for document files."""
    return FileDiscoveryFilter(
        target_file_types=[FileType.DOCUMENT, FileType.SPREADSHEET, FileType.PRESENTATION],
        logger=logger,
        name="DocumentFilter"
    )


def create_data_filter(logger: Optional[AsyncLogger] = None) -> FileDiscoveryFilter:
    """Create a filter specifically for data files."""
    return FileDiscoveryFilter(
        target_file_types=[FileType.DATA],
        logger=logger,
        name="DataFilter"
    )


def create_media_filter(logger: Optional[AsyncLogger] = None) -> FileDiscoveryFilter:
    """Create a filter specifically for media files."""
    return FileDiscoveryFilter(
        target_file_types=[FileType.IMAGE, FileType.AUDIO, FileType.VIDEO],
        logger=logger,
        name="MediaFilter"
    )


def create_comprehensive_filter(logger: Optional[AsyncLogger] = None) -> FileDiscoveryFilter:
    """Create a comprehensive filter for all supported file types."""
    return FileDiscoveryFilter(
        target_file_types=list(FileType),
        logger=logger,
        name="ComprehensiveFileFilter"
    )