"""
Exhaustive Crawling Monitoring Module

This module provides event-based monitoring for exhaustive crawling using the existing
AsyncWebCrawler event system. It hooks into page_processed and crawl_completed events
to provide real-time dead-end detection and URL discovery analytics.
"""

import asyncio
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime

from .models import CrawlResult
from .exhaustive_analytics import ExhaustiveAnalytics, DeadEndMetrics, URLTrackingState
from .async_logger import AsyncLoggerBase


class ExhaustiveMonitor:
    """
    Event-based monitor for exhaustive crawling that hooks into AsyncWebCrawler events.
    
    This class provides:
    - Real-time dead-end detection using existing page analytics
    - URL discovery rate analysis using existing crawl analytics
    - Progress reporting using existing logger patterns
    - Continuation logic for exhaustive crawling
    """
    
    def __init__(
        self,
        logger: Optional[AsyncLoggerBase] = None,
        dead_end_threshold: int = 50,
        revisit_threshold: float = 0.95,
        log_discovery_stats: bool = True
    ):
        """
        Initialize the exhaustive monitor.
        
        Args:
            logger: Logger for monitoring events
            dead_end_threshold: Consecutive dead pages before stopping
            revisit_threshold: Revisit ratio threshold for stopping
            log_discovery_stats: Whether to log URL discovery statistics
        """
        self.logger = logger
        self.analytics = ExhaustiveAnalytics(logger=logger)
        self.dead_end_threshold = dead_end_threshold
        self.revisit_threshold = revisit_threshold
        self.log_discovery_stats = log_discovery_stats
        
        # Monitoring state
        self._monitoring_active = False
        self._session_start_time: Optional[datetime] = None
        self._last_progress_log: Optional[datetime] = None
        
        # Callbacks for external handling
        self._dead_end_callbacks: List[Callable] = []
        self._progress_callbacks: List[Callable] = []
    
    def start_monitoring(self, crawler) -> None:
        """
        Start monitoring by hooking into crawler events.
        
        Args:
            crawler: AsyncWebCrawler instance to monitor
        """
        if self._monitoring_active:
            return
        
        # Hook into existing event system
        crawler.add_event_handler('page_processed', self._handle_page_processed)
        crawler.add_event_handler('crawl_completed', self._handle_crawl_completed)
        
        # Initialize monitoring session
        self.analytics.start_crawl_session()
        self._monitoring_active = True
        self._session_start_time = datetime.now()
        
        if self.logger:
            self.logger.info(
                "Started exhaustive crawling monitoring",
                tag="MONITOR"
            )
    
    def stop_monitoring(self, crawler) -> None:
        """
        Stop monitoring and clean up event handlers.
        
        Args:
            crawler: AsyncWebCrawler instance to stop monitoring
        """
        if not self._monitoring_active:
            return
        
        # Remove event handlers
        crawler.remove_event_handler('page_processed', self._handle_page_processed)
        crawler.remove_event_handler('crawl_completed', self._handle_crawl_completed)
        
        self._monitoring_active = False
        
        if self.logger:
            self.logger.info(
                "Stopped exhaustive crawling monitoring",
                tag="MONITOR"
            )
    
    async def _handle_page_processed(self, result: CrawlResult) -> None:
        """
        Handle page_processed events for dead-end detection.
        
        This method analyzes individual page results for URL discovery
        and updates dead-end detection metrics.
        
        Args:
            result: CrawlResult from the processed page
        """
        if not self._monitoring_active:
            return
        
        try:
            # Analyze the page result for URL discovery
            analysis = self.analytics.analyze_crawl_results([result], result.url)
            
            # Log URL discovery if enabled
            if self.log_discovery_stats and self.logger:
                self.logger.info(
                    f"Page processed: {result.url} | "
                    f"New URLs: {analysis['new_urls_discovered']} | "
                    f"Total links: {analysis['total_links_found']} | "
                    f"Dead pages: {analysis['consecutive_dead_pages']}",
                    tag="PAGE_STATS"
                )
            
            # Check for dead-end conditions
            should_stop, reason = self.analytics.should_stop_crawling(
                dead_end_threshold=self.dead_end_threshold,
                revisit_threshold=self.revisit_threshold
            )
            
            if should_stop:
                await self._handle_dead_end_detected(reason, analysis)
            
            # Call progress callbacks
            await self._call_progress_callbacks(analysis)
            
        except Exception as e:
            if self.logger:
                self.logger.error(
                    f"Error handling page processed event: {str(e)}",
                    tag="MONITOR_ERROR"
                )
    
    async def _handle_crawl_completed(self, results: List[CrawlResult]) -> None:
        """
        Handle crawl_completed events for continuation logic.
        
        This method analyzes batch results and provides comprehensive
        analytics for exhaustive crawling continuation decisions.
        
        Args:
            results: List of CrawlResult objects from completed crawl
        """
        if not self._monitoring_active or not results:
            return
        
        try:
            # Analyze all results in the batch
            batch_analysis = self.analytics.analyze_crawl_results(results)
            
            # Get comprehensive statistics
            comprehensive_stats = self.analytics.get_comprehensive_stats()
            
            # Log batch completion with progress reporting
            if self.log_discovery_stats and self.logger:
                self._log_batch_progress(results, batch_analysis, comprehensive_stats)
            
            # Check continuation logic
            should_stop, reason = self.analytics.should_stop_crawling(
                dead_end_threshold=self.dead_end_threshold,
                revisit_threshold=self.revisit_threshold
            )
            
            if should_stop:
                await self._handle_dead_end_detected(reason, batch_analysis)
            
            # Call progress callbacks with batch data
            await self._call_progress_callbacks(batch_analysis, results)
            
        except Exception as e:
            if self.logger:
                self.logger.error(
                    f"Error handling crawl completed event: {str(e)}",
                    tag="MONITOR_ERROR"
                )
    
    def _log_batch_progress(
        self,
        results: List[CrawlResult],
        analysis: Dict[str, Any],
        stats: Dict[str, Any]
    ) -> None:
        """
        Log batch progress using existing logger patterns.
        
        Args:
            results: Batch results
            analysis: Batch analysis data
            stats: Comprehensive statistics
        """
        successful_results = [r for r in results if r.success]
        
        # Calculate session duration
        session_duration = "Unknown"
        if self._session_start_time:
            duration = datetime.now() - self._session_start_time
            session_duration = str(duration).split('.')[0]  # Remove microseconds
        
        self.logger.info(
            f"Batch completed: {len(successful_results)}/{len(results)} successful | "
            f"New URLs: {analysis['new_urls_discovered']} | "
            f"Total discovered: {stats['session_stats']['total_urls_discovered']} | "
            f"Dead pages: {analysis['consecutive_dead_pages']} | "
            f"Revisit ratio: {analysis['revisit_ratio']:.2%} | "
            f"Session time: {session_duration}",
            tag="BATCH_STATS"
        )
        
        # Log detailed URL tracking stats
        url_stats = analysis.get('url_stats', {})
        if url_stats:
            self.logger.info(
                f"URL tracking: {url_stats.get('total_discovered', 0)} discovered, "
                f"{url_stats.get('total_crawled', 0)} crawled, "
                f"{url_stats.get('pending_count', 0)} pending, "
                f"success rate: {url_stats.get('success_rate', 0):.2%}",
                tag="URL_STATS"
            )
    
    async def _handle_dead_end_detected(self, reason: str, analysis: Dict[str, Any]) -> None:
        """
        Handle dead-end detection events.
        
        Args:
            reason: Reason for dead-end detection
            analysis: Current analysis data
        """
        if self.logger:
            self.logger.warning(
                f"Dead-end detected: {reason}",
                tag="DEADEND"
            )
        
        # Call dead-end callbacks
        for callback in self._dead_end_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(reason, analysis)
                else:
                    callback(reason, analysis)
            except Exception as e:
                if self.logger:
                    self.logger.error(
                        f"Error in dead-end callback: {str(e)}",
                        tag="CALLBACK_ERROR"
                    )
    
    async def _call_progress_callbacks(
        self,
        analysis: Dict[str, Any],
        results: Optional[List[CrawlResult]] = None
    ) -> None:
        """
        Call registered progress callbacks.
        
        Args:
            analysis: Current analysis data
            results: Optional batch results
        """
        for callback in self._progress_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(analysis, results)
                else:
                    callback(analysis, results)
            except Exception as e:
                if self.logger:
                    self.logger.error(
                        f"Error in progress callback: {str(e)}",
                        tag="CALLBACK_ERROR"
                    )
    
    def add_dead_end_callback(self, callback: Callable) -> None:
        """
        Add a callback for dead-end detection events.
        
        Args:
            callback: Function to call when dead-end is detected
                     Signature: callback(reason: str, analysis: Dict[str, Any])
        """
        self._dead_end_callbacks.append(callback)
    
    def add_progress_callback(self, callback: Callable) -> None:
        """
        Add a callback for progress updates.
        
        Args:
            callback: Function to call on progress updates
                     Signature: callback(analysis: Dict[str, Any], results: Optional[List[CrawlResult]])
        """
        self._progress_callbacks.append(callback)
    
    def get_current_metrics(self) -> DeadEndMetrics:
        """Get current dead-end detection metrics."""
        return self.analytics.metrics
    
    def get_url_tracking_state(self) -> URLTrackingState:
        """Get current URL tracking state."""
        return self.analytics.url_state
    
    def get_comprehensive_stats(self) -> Dict[str, Any]:
        """Get comprehensive monitoring statistics."""
        stats = self.analytics.get_comprehensive_stats()
        
        # Add monitoring-specific information
        stats['monitoring'] = {
            'active': self._monitoring_active,
            'session_start_time': str(self._session_start_time) if self._session_start_time else None,
            'dead_end_threshold': self.dead_end_threshold,
            'revisit_threshold': self.revisit_threshold,
            'log_discovery_stats': self.log_discovery_stats
        }
        
        return stats
    
    def should_continue_crawling(self) -> tuple[bool, str]:
        """
        Check if crawling should continue based on current metrics.
        
        Returns:
            Tuple of (should_continue, reason)
        """
        should_stop, reason = self.analytics.should_stop_crawling(
            dead_end_threshold=self.dead_end_threshold,
            revisit_threshold=self.revisit_threshold
        )
        return not should_stop, reason
    
    def reset_monitoring_session(self) -> None:
        """Reset the monitoring session state."""
        self.analytics.reset_session()
        self._session_start_time = datetime.now()
        self._last_progress_log = None
        
        if self.logger:
            self.logger.info(
                "Reset exhaustive monitoring session",
                tag="MONITOR"
            )


def configure_exhaustive_monitoring(
    crawler,
    logger: Optional[AsyncLoggerBase] = None,
    dead_end_threshold: int = 50,
    revisit_threshold: float = 0.95,
    log_discovery_stats: bool = True
) -> ExhaustiveMonitor:
    """
    Configure exhaustive monitoring for an AsyncWebCrawler.
    
    This function creates and starts an ExhaustiveMonitor that hooks into
    the crawler's event system for real-time monitoring.
    
    Args:
        crawler: AsyncWebCrawler instance to monitor
        logger: Logger for monitoring events
        dead_end_threshold: Consecutive dead pages before stopping
        revisit_threshold: Revisit ratio threshold for stopping
        log_discovery_stats: Whether to log URL discovery statistics
        
    Returns:
        ExhaustiveMonitor instance for managing monitoring
    """
    monitor = ExhaustiveMonitor(
        logger=logger,
        dead_end_threshold=dead_end_threshold,
        revisit_threshold=revisit_threshold,
        log_discovery_stats=log_discovery_stats
    )
    
    monitor.start_monitoring(crawler)
    return monitor


def analyze_url_discovery_rate_from_events(
    results: List[CrawlResult],
    logger: Optional[AsyncLoggerBase] = None
) -> Dict[str, Any]:
    """
    Analyze URL discovery rate from crawl results using existing page analytics.
    
    This function provides standalone URL discovery analysis that can be used
    independently of the monitoring system.
    
    Args:
        results: List of CrawlResult objects to analyze
        logger: Optional logger for analysis events
        
    Returns:
        Dictionary with URL discovery analysis
    """
    analytics = ExhaustiveAnalytics(logger=logger)
    return analytics.analyze_crawl_results(results)


def create_dead_end_detection_handler(
    dead_end_threshold: int = 50,
    revisit_threshold: float = 0.95,
    logger: Optional[AsyncLoggerBase] = None
) -> Callable:
    """
    Create a dead-end detection event handler.
    
    This function creates a handler that can be registered with the crawler's
    event system to detect dead-end conditions.
    
    Args:
        dead_end_threshold: Consecutive dead pages before detection
        revisit_threshold: Revisit ratio threshold for detection
        logger: Optional logger for detection events
        
    Returns:
        Event handler function for dead-end detection
    """
    analytics = ExhaustiveAnalytics(logger=logger)
    
    async def handle_dead_end_detection(results: List[CrawlResult]) -> bool:
        """
        Event handler for dead-end detection.
        
        Args:
            results: CrawlResult objects from crawl completion
            
        Returns:
            True if dead-end detected, False otherwise
        """
        # Analyze results for dead-end conditions
        analysis = analytics.analyze_crawl_results(results)
        
        # Check if we should stop crawling
        should_stop, reason = analytics.should_stop_crawling(
            dead_end_threshold=dead_end_threshold,
            revisit_threshold=revisit_threshold
        )
        
        if should_stop and logger:
            logger.warning(f"Dead-end detected: {reason}", tag="DEADEND")
        
        return should_stop
    
    return handle_dead_end_detection


def create_progress_reporting_handler(
    logger: AsyncLoggerBase,
    log_interval_seconds: int = 30
) -> Callable:
    """
    Create a progress reporting event handler using existing logger patterns.
    
    Args:
        logger: Logger for progress reporting
        log_interval_seconds: Minimum interval between progress logs
        
    Returns:
        Event handler function for progress reporting
    """
    last_log_time = [0]  # Use list to allow modification in nested function
    
    async def handle_progress_reporting(results: List[CrawlResult]) -> None:
        """
        Event handler for progress reporting.
        
        Args:
            results: CrawlResult objects from crawl completion
        """
        import time
        
        current_time = time.time()
        if current_time - last_log_time[0] < log_interval_seconds:
            return
        
        last_log_time[0] = current_time
        
        # Analyze results for progress reporting
        analytics = ExhaustiveAnalytics(logger=logger)
        analysis = analytics.analyze_crawl_results(results)
        
        successful_results = [r for r in results if r.success]
        
        logger.info(
            f"Progress update: {len(successful_results)}/{len(results)} successful | "
            f"New URLs: {analysis['new_urls_discovered']} | "
            f"Dead pages: {analysis['consecutive_dead_pages']} | "
            f"Revisit ratio: {analysis['revisit_ratio']:.2%}",
            tag="PROGRESS"
        )
    
    return handle_progress_reporting