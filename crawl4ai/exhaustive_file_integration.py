"""
Exhaustive File Discovery Integration Module

This module integrates file discovery capabilities with the exhaustive crawling workflow,
combining the FileDiscoveryFilter with exhaustive BFS strategy and providing concurrent
file downloading during crawling operations.

Features:
- Integration of FileDiscoveryFilter with exhaustive BFS strategy
- File download queue management during crawling
- Concurrent file downloading using existing concurrency patterns
- File organization and metadata extraction during download process
- Real-time file discovery analytics and progress tracking
"""

import asyncio
import os
from typing import Dict, List, Optional, Any, Set, Union
from pathlib import Path
from dataclasses import dataclass, field
from datetime import datetime
import time

from .file_discovery_filter import FileDiscoveryFilter, FileMetadata, FileType, FileDiscoveryStats
from .exhaustive_webcrawler import ExhaustiveAsyncWebCrawler
from .exhaustive_configs import ExhaustiveCrawlConfig
from .exhaustive_strategy_config import create_exhaustive_bfs_strategy, create_minimal_filter_chain
from .models import CrawlResult
from .async_logger import AsyncLoggerBase
from .deep_crawling import FilterChain


@dataclass
class FileDownloadTask:
    """Represents a file download task in the queue."""
    file_metadata: FileMetadata
    priority: int = 0  # Higher numbers = higher priority
    retry_count: int = 0
    max_retries: int = 3
    created_at: datetime = field(default_factory=datetime.now)
    source_page_url: Optional[str] = None
    
    def __lt__(self, other):
        """For priority queue ordering (higher priority first)."""
        return self.priority > other.priority


@dataclass
class FileDownloadResult:
    """Result of a file download operation."""
    task: FileDownloadTask
    success: bool
    file_path: Optional[str] = None
    file_size: int = 0
    checksum: Optional[str] = None
    error_message: Optional[str] = None
    download_time: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class FileDownloadQueue:
    """
    Manages file download queue with priority and concurrency control.
    
    This class provides queue management for discovered files during exhaustive
    crawling, with support for prioritization, retry logic, and concurrent downloads.
    """
    
    def __init__(
        self,
        max_concurrent_downloads: int = 5,
        max_queue_size: int = 1000,
        logger: Optional[AsyncLoggerBase] = None
    ):
        self.max_concurrent_downloads = max_concurrent_downloads
        self.max_queue_size = max_queue_size
        self.logger = logger
        
        # Queue management
        self._download_queue: asyncio.PriorityQueue = asyncio.PriorityQueue(maxsize=max_queue_size)
        self._queued_urls: Set[str] = set()  # URLs currently in queue
        self._active_downloads: Set[str] = set()  # URLs currently being downloaded
        self._completed_downloads: Dict[str, FileDownloadResult] = {}
        self._failed_downloads: Dict[str, FileDownloadResult] = {}
        
        # Concurrency control
        self._download_semaphore = asyncio.Semaphore(max_concurrent_downloads)
        self._download_tasks: Set[asyncio.Task] = set()
        
        # Statistics
        self._stats = {
            'queued': 0,
            'completed': 0,
            'failed': 0,
            'active': 0,
            'total_bytes_downloaded': 0
        }
    
    async def add_file_task(
        self,
        file_metadata: FileMetadata,
        priority: int = 0,
        source_page_url: Optional[str] = None
    ) -> bool:
        """
        Add a file download task to the queue.
        
        Args:
            file_metadata: Metadata of the file to download
            priority: Priority level (higher = more important)
            source_page_url: URL of the page where file was discovered
            
        Returns:
            bool: True if task was added, False if queue is full or URL already queued
        """
        # Check if already queued, active, or completed
        if file_metadata.url in self._queued_urls:
            return False
            
        if file_metadata.url in self._active_downloads:
            return False
        
        if file_metadata.url in self._completed_downloads:
            return False
        
        try:
            task = FileDownloadTask(
                file_metadata=file_metadata,
                priority=priority,
                source_page_url=source_page_url
            )
            
            # Add to queue (will block if queue is full)
            await self._download_queue.put((task.priority, time.time(), task))
            self._queued_urls.add(file_metadata.url)
            self._stats['queued'] += 1
            
            if self.logger:
                self.logger.info(
                    f"Added file to download queue: {file_metadata.filename} (priority: {priority})",
                    tag="FILE_QUEUE"
                )
            
            return True
            
        except asyncio.QueueFull:
            if self.logger:
                self.logger.warning(
                    f"Download queue full, skipping file: {file_metadata.filename}",
                    tag="FILE_QUEUE"
                )
            return False
    
    async def start_download_workers(self, crawler: ExhaustiveAsyncWebCrawler) -> None:
        """
        Start concurrent download workers.
        
        Args:
            crawler: ExhaustiveAsyncWebCrawler instance for downloading files
        """
        for i in range(self.max_concurrent_downloads):
            task = asyncio.create_task(self._download_worker(crawler, f"worker-{i}"))
            self._download_tasks.add(task)
            task.add_done_callback(self._download_tasks.discard)
    
    async def _download_worker(self, crawler: ExhaustiveAsyncWebCrawler, worker_name: str) -> None:
        """
        Worker coroutine for processing download queue.
        
        Args:
            crawler: Crawler instance for downloading files
            worker_name: Name of the worker for logging
        """
        while True:
            try:
                # Get next download task
                _, _, task = await self._download_queue.get()
                
                # Mark as active
                self._queued_urls.discard(task.file_metadata.url)
                self._active_downloads.add(task.file_metadata.url)
                self._stats['active'] += 1
                self._stats['queued'] -= 1
                
                if self.logger:
                    self.logger.info(
                        f"[{worker_name}] Starting download: {task.file_metadata.filename}",
                        tag="FILE_DOWNLOAD"
                    )
                
                # Perform download with semaphore control
                async with self._download_semaphore:
                    result = await self._download_file(crawler, task)
                
                # Process result
                await self._process_download_result(result)
                
                # Mark task as done
                self._download_queue.task_done()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                if self.logger:
                    self.logger.error(f"[{worker_name}] Download worker error: {e}", tag="ERROR")
    
    async def _download_file(
        self,
        crawler: ExhaustiveAsyncWebCrawler,
        task: FileDownloadTask
    ) -> FileDownloadResult:
        """
        Download a single file using the crawler's adownload_file method.
        
        Args:
            crawler: Crawler instance for downloading
            task: Download task to process
            
        Returns:
            FileDownloadResult: Result of the download operation
        """
        try:
            # Use existing adownload_file method with proper configuration
            download_result = await crawler.adownload_file(
                url=task.file_metadata.url,
                validate_integrity=True,
                max_retries=task.max_retries
            )
            
            # Create result object
            result = FileDownloadResult(
                task=task,
                success=download_result.get('success', False),
                file_path=download_result.get('file_path'),
                file_size=download_result.get('file_size', 0),
                checksum=download_result.get('checksum'),
                error_message=download_result.get('error_message'),
                download_time=datetime.now(),
                metadata=download_result.get('metadata', {})
            )
            
            return result
            
        except Exception as e:
            return FileDownloadResult(
                task=task,
                success=False,
                error_message=f"Download exception: {str(e)}",
                download_time=datetime.now()
            )
    
    async def _process_download_result(self, result: FileDownloadResult) -> None:
        """
        Process the result of a download operation.
        
        Args:
            result: Download result to process
        """
        url = result.task.file_metadata.url
        
        # Remove from active downloads
        self._active_downloads.discard(url)
        self._stats['active'] -= 1
        
        if result.success:
            # Success - store result and update stats
            self._completed_downloads[url] = result
            self._stats['completed'] += 1
            self._stats['total_bytes_downloaded'] += result.file_size
            
            if self.logger:
                self.logger.success(
                    f"Downloaded: {result.task.file_metadata.filename} ({result.file_size} bytes)",
                    tag="FILE_DOWNLOAD"
                )
        else:
            # Failure - check if we should retry
            result.task.retry_count += 1
            
            if result.task.retry_count < result.task.max_retries:
                # Retry - add back to queue with lower priority
                retry_priority = max(0, result.task.priority - 1)
                # Create new task with updated retry count
                retry_task = FileDownloadTask(
                    file_metadata=result.task.file_metadata,
                    priority=retry_priority,
                    retry_count=result.task.retry_count,
                    max_retries=result.task.max_retries,
                    source_page_url=result.task.source_page_url
                )
                
                try:
                    await self._download_queue.put((retry_task.priority, time.time(), retry_task))
                    self._queued_urls.add(result.task.file_metadata.url)
                    self._stats['queued'] += 1
                except asyncio.QueueFull:
                    # Queue is full, mark as failed
                    self._failed_downloads[url] = result
                    self._stats['failed'] += 1
                
                if self.logger:
                    self.logger.warning(
                        f"Retrying download ({result.task.retry_count}/{result.task.max_retries}): "
                        f"{result.task.file_metadata.filename}",
                        tag="FILE_DOWNLOAD"
                    )
            else:
                # Max retries reached - mark as failed
                self._failed_downloads[url] = result
                self._stats['failed'] += 1
                
                if self.logger:
                    self.logger.error(
                        f"Download failed after {result.task.max_retries} retries: "
                        f"{result.task.file_metadata.filename} - {result.error_message}",
                        tag="FILE_DOWNLOAD"
                    )
    
    def get_stats(self) -> Dict[str, Any]:
        """Get current download queue statistics."""
        return {
            **self._stats,
            'queue_size': self._download_queue.qsize(),
            'success_rate': (
                self._stats['completed'] / max(1, self._stats['completed'] + self._stats['failed'])
            ) * 100
        }
    
    async def wait_for_completion(self, timeout: Optional[float] = None) -> None:
        """
        Wait for all downloads to complete.
        
        Args:
            timeout: Maximum time to wait in seconds
        """
        try:
            await asyncio.wait_for(self._download_queue.join(), timeout=timeout)
        except asyncio.TimeoutError:
            if self.logger:
                self.logger.warning("Download queue completion timeout", tag="FILE_QUEUE")
    
    async def stop_workers(self) -> None:
        """Stop all download workers."""
        for task in self._download_tasks:
            task.cancel()
        
        if self._download_tasks:
            await asyncio.gather(*self._download_tasks, return_exceptions=True)
        
        self._download_tasks.clear()


class ExhaustiveFileDiscoveryCrawler(ExhaustiveAsyncWebCrawler):
    """
    Extended ExhaustiveAsyncWebCrawler with integrated file discovery and downloading.
    
    This class combines exhaustive crawling with real-time file discovery and downloading,
    providing a complete solution for comprehensive site mapping with file acquisition.
    """
    
    def __init__(
        self,
        file_discovery_config: Optional[Dict[str, Any]] = None,
        download_config: Optional[Dict[str, Any]] = None,
        *args,
        **kwargs
    ):
        super().__init__(*args, **kwargs)
        
        # Initialize file discovery filter
        file_config = file_discovery_config or {}
        self.file_filter = FileDiscoveryFilter(
            logger=self.logger,
            **file_config
        )
        
        # Initialize download queue
        download_config = download_config or {}
        self.download_queue = FileDownloadQueue(
            max_concurrent_downloads=download_config.get('max_concurrent_downloads', 5),
            max_queue_size=download_config.get('max_queue_size', 1000),
            logger=self.logger
        )
        
        # File organization settings
        self.download_directory = download_config.get('download_directory', './downloads')
        self.organize_by_type = download_config.get('organize_by_type', True)
        self.organize_by_source = download_config.get('organize_by_source', False)
        
        # Integration state
        self._file_discovery_active = False
    
    async def arun_exhaustive_with_files(
        self,
        start_url: str,
        config: Optional[ExhaustiveCrawlConfig] = None,
        enable_file_discovery: bool = True,
        enable_file_download: bool = True,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Run exhaustive crawling with integrated file discovery and downloading.
        
        This method extends the base exhaustive crawling to include real-time file
        discovery and concurrent downloading of discovered files.
        
        Args:
            start_url: URL to start crawling from
            config: Exhaustive crawl configuration
            enable_file_discovery: Whether to discover files during crawling
            enable_file_download: Whether to download discovered files
            **kwargs: Additional arguments for crawling
            
        Returns:
            Dictionary containing crawl results, file discovery stats, and download results
        """
        config = config or ExhaustiveCrawlConfig()
        
        # Configure BFS strategy with file discovery integration
        if enable_file_discovery:
            config = self._configure_file_discovery_strategy(config)
        
        # Start download workers if downloading is enabled
        if enable_file_download:
            await self.download_queue.start_download_workers(self)
        
        self._file_discovery_active = enable_file_discovery
        
        try:
            # Run exhaustive crawling with file discovery hooks
            crawl_results = await self.arun_exhaustive(start_url, config, **kwargs)
            
            # Wait for remaining downloads to complete
            if enable_file_download:
                await self.download_queue.wait_for_completion(timeout=300)  # 5 minute timeout
            
            # Compile comprehensive results
            file_results = self._compile_file_results()
            
            return {
                **crawl_results,
                'file_discovery': file_results,
                'download_stats': self.download_queue.get_stats() if enable_file_download else None
            }
            
        finally:
            self._file_discovery_active = False
            if enable_file_download:
                await self.download_queue.stop_workers()
    
    def _configure_file_discovery_strategy(self, config: ExhaustiveCrawlConfig) -> ExhaustiveCrawlConfig:
        """
        Configure the exhaustive crawl strategy to include file discovery.
        
        Args:
            config: Base exhaustive crawl configuration
            
        Returns:
            Modified configuration with file discovery integration
        """
        # Create enhanced filter chain that includes file discovery
        enhanced_filter_chain = self._create_file_discovery_filter_chain()
        
        # If config has a deep_crawl_strategy, enhance it
        if hasattr(config, 'deep_crawl_strategy') and config.deep_crawl_strategy:
            # Replace the filter chain in the existing strategy
            config.deep_crawl_strategy.filter_chain = enhanced_filter_chain
        else:
            # Create new exhaustive BFS strategy with file discovery
            from .exhaustive_strategy_config import create_exhaustive_bfs_strategy
            
            strategy = create_exhaustive_bfs_strategy(
                max_depth=getattr(config, 'exhaustive_max_depth', 100),
                max_pages=getattr(config, 'exhaustive_max_pages', 10000),
                logger=self.logger
            )
            strategy.filter_chain = enhanced_filter_chain
            config.deep_crawl_strategy = strategy
        
        return config
    
    def _create_file_discovery_filter_chain(self) -> FilterChain:
        """
        Create a filter chain that integrates file discovery with exhaustive crawling.
        
        Returns:
            FilterChain with integrated file discovery capabilities
        """
        # Start with minimal filter chain for maximum discovery
        base_chain = create_minimal_filter_chain(enable_filtering=True)
        
        # Add file discovery filter to the chain
        filters = list(base_chain.filters) if hasattr(base_chain, 'filters') else []
        filters.append(self.file_filter)
        
        return FilterChain(filters)
    
    async def _process_crawl_result_for_files(
        self,
        result: CrawlResult,
        source_url: Optional[str] = None
    ) -> None:
        """
        Process a crawl result to discover and queue files for download.
        
        Args:
            result: CrawlResult to process for file discovery
            source_url: URL of the source page
        """
        if not self._file_discovery_active or not result.success:
            return
        
        try:
            # Extract links from the result
            if hasattr(result, 'links') and result.links:
                all_links = []
                
                # Collect internal links
                internal_links = result.links.get('internal', [])
                for link in internal_links:
                    if isinstance(link, dict) and 'href' in link:
                        all_links.append(link['href'])
                    elif isinstance(link, str):
                        all_links.append(link)
                
                # Process each link through file discovery filter
                for link_url in all_links:
                    if self.file_filter.apply(link_url):
                        # Get the discovered file metadata
                        discovered_files = self.file_filter.get_discovered_files()
                        if discovered_files:
                            # Get the most recently discovered file
                            latest_file = discovered_files[-1]
                            
                            # Determine priority based on file type
                            priority = self._calculate_file_priority(latest_file)
                            
                            # Add to download queue
                            await self.download_queue.add_file_task(
                                latest_file,
                                priority=priority,
                                source_page_url=source_url or result.url
                            )
        
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error processing crawl result for files: {e}", tag="FILE_DISCOVERY")
    
    def _calculate_file_priority(self, file_metadata: FileMetadata) -> int:
        """
        Calculate download priority for a discovered file.
        
        Args:
            file_metadata: Metadata of the discovered file
            
        Returns:
            Priority score (higher = more important)
        """
        # Base priority by file type
        type_priorities = {
            FileType.DOCUMENT: 10,
            FileType.SPREADSHEET: 9,
            FileType.PRESENTATION: 8,
            FileType.DATA: 7,
            FileType.ARCHIVE: 6,
            FileType.IMAGE: 3,
            FileType.AUDIO: 2,
            FileType.VIDEO: 1,
            FileType.CODE: 5,
            FileType.OTHER: 1
        }
        
        priority = type_priorities.get(file_metadata.file_type, 1)
        
        # Boost priority for certain extensions
        high_value_extensions = {'.pdf', '.docx', '.xlsx', '.pptx', '.csv', '.json', '.xml'}
        if file_metadata.extension.lower() in high_value_extensions:
            priority += 5
        
        # Boost priority for files in repository paths
        if file_metadata.repository_path:
            priority += 3
        
        return priority
    
    def _compile_file_results(self) -> Dict[str, Any]:
        """
        Compile comprehensive file discovery and download results.
        
        Returns:
            Dictionary with file discovery statistics and results
        """
        discovery_stats = self.file_filter.get_discovery_stats()
        repository_inventory = self.file_filter.get_repository_inventory()
        
        return {
            'discovery_stats': {
                'total_files_discovered': discovery_stats.total_files_discovered,
                'files_by_type': {ft.value: count for ft, count in discovery_stats.files_by_type.items()},
                'files_by_extension': dict(discovery_stats.files_by_extension),
                'repository_paths': list(discovery_stats.repository_paths)
            },
            'discovered_files': [
                {
                    'url': f.url,
                    'filename': f.filename,
                    'extension': f.extension,
                    'file_type': f.file_type.value,
                    'repository_path': f.repository_path
                }
                for f in self.file_filter.get_discovered_files()
            ],
            'repository_inventory': {
                path: [
                    {
                        'url': f.url,
                        'filename': f.filename,
                        'file_type': f.file_type.value
                    }
                    for f in files
                ]
                for path, files in repository_inventory.items()
            }
        }
    
    # Override the batch crawling method to include file processing
    async def _crawl_batch(self, urls: List[str], config: ExhaustiveCrawlConfig, **kwargs) -> List[CrawlResult]:
        """
        Enhanced batch crawling with file discovery integration.
        
        Args:
            urls: URLs to crawl
            config: Crawl configuration
            **kwargs: Additional arguments
            
        Returns:
            List of crawl results
        """
        # Call parent method to get results
        results = await super()._crawl_batch(urls, config, **kwargs)
        
        # Process each result for file discovery
        if self._file_discovery_active:
            for i, result in enumerate(results):
                source_url = urls[i] if i < len(urls) else None
                await self._process_crawl_result_for_files(result, source_url)
        
        return results
    
    def get_file_discovery_stats(self) -> Dict[str, Any]:
        """Get current file discovery statistics."""
        return self.file_filter.get_discovery_stats()
    
    def get_download_stats(self) -> Dict[str, Any]:
        """Get current download queue statistics."""
        return self.download_queue.get_stats()
    
    def export_file_inventory(self, format: str = "json") -> Union[str, Dict]:
        """Export discovered file inventory in specified format."""
        return self.file_filter.export_file_inventory(format)


# Convenience functions for creating integrated crawlers

def create_file_discovery_crawler(
    file_types: Optional[List[FileType]] = None,
    download_directory: str = "./downloads",
    max_concurrent_downloads: int = 5,
    **crawler_kwargs
) -> ExhaustiveFileDiscoveryCrawler:
    """
    Create an ExhaustiveFileDiscoveryCrawler with file discovery configuration.
    
    Args:
        file_types: List of file types to discover
        download_directory: Directory for downloaded files
        max_concurrent_downloads: Maximum concurrent downloads
        **crawler_kwargs: Additional arguments for crawler
        
    Returns:
        Configured ExhaustiveFileDiscoveryCrawler
    """
    file_config = {}
    if file_types:
        file_config['target_file_types'] = file_types
    
    download_config = {
        'download_directory': download_directory,
        'max_concurrent_downloads': max_concurrent_downloads,
        'organize_by_type': True
    }
    
    return ExhaustiveFileDiscoveryCrawler(
        file_discovery_config=file_config,
        download_config=download_config,
        **crawler_kwargs
    )


def create_document_focused_crawler(**kwargs) -> ExhaustiveFileDiscoveryCrawler:
    """Create a crawler focused on document discovery and download."""
    return create_file_discovery_crawler(
        file_types=[FileType.DOCUMENT, FileType.SPREADSHEET, FileType.PRESENTATION, FileType.DATA],
        **kwargs
    )


def create_comprehensive_file_crawler(**kwargs) -> ExhaustiveFileDiscoveryCrawler:
    """Create a crawler for comprehensive file discovery across all types."""
    return create_file_discovery_crawler(
        file_types=list(FileType),
        **kwargs
    )