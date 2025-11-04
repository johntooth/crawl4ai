"""
Exhaustive Crawling Integration Module

This module provides integration hooks for existing AsyncWebCrawler event system
to enable real-time dead-end detection and URL discovery analytics during normal crawling.
"""

from typing import Dict, Any, Optional, Callable, List
from functools import wraps
import asyncio

from .models import CrawlResult
from .exhaustive_analytics import ExhaustiveAnalytics
from .async_logger import AsyncLoggerBase


class ExhaustiveCrawlIntegration:
    """
    Integration layer that hooks into existing AsyncWebCrawler events
    to provide real-time dead-end detection and analytics.
    """
    
    def __init__(self, logger: Optional[AsyncLoggerBase] = None):
        self.analytics = ExhaustiveAnalytics(logger=logger)
        self.logger = logger
        self._event_handlers: Dict[str, List[Callable]] = {
            'on_page_processed': [],
            'on_crawl_completed': [],
            'on_url_discovered': []
        }
        self._integration_active = False
    
    def enable_integration(self, crawler) -> None:
        """
        Enable exhaustive crawling integration with an AsyncWebCrawler instance.
        
        This method hooks into the crawler's event system to provide real-time
        dead-end detection and URL discovery analytics.
        
        Args:
            crawler: AsyncWebCrawler instance to integrate with
        """
        if self._integration_active:
            return
        
        # Hook into existing crawler events if they exist
        self._setup_event_hooks(crawler)
        self._integration_active = True
        
        if self.logger:
            self.logger.info("Exhaustive crawling integration enabled", tag="INTEGRATE")
    
    def disable_integration(self) -> None:
        """Disable the integration and clean up event handlers."""
        self._integration_active = False
        self._event_handlers = {
            'on_page_processed': [],
            'on_crawl_completed': [],
            'on_url_discovered': []
        }
        
        if self.logger:
            self.logger.info("Exhaustive crawling integration disabled", tag="INTEGRATE")
    
    def _setup_event_hooks(self, crawler) -> None:
        """Set up event hooks with the crawler."""
        # Check if crawler has event system (some crawlers might not)
        if hasattr(crawler, 'add_event_handler'):
            # Use existing event system
            crawler.add_event_handler('page_processed', self._handle_page_processed)
            crawler.add_event_handler('crawl_completed', self._handle_crawl_completed)
        else:
            # Monkey patch methods to add our hooks
            self._monkey_patch_crawler_methods(crawler)
    
    def _monkey_patch_crawler_methods(self, crawler) -> None:
        """
        Monkey patch crawler methods to add exhaustive analytics hooks.
        This is used when the crawler doesn't have a built-in event system.
        """
        # Patch arun method to capture individual page results
        original_arun = crawler.arun
        
        @wraps(original_arun)
        async def patched_arun(*args, **kwargs):
            result = await original_arun(*args, **kwargs)
            if self._integration_active and hasattr(result, 'url'):
                await self._handle_page_processed(result)
            return result
        
        crawler.arun = patched_arun
        
        # Patch arun_many method to capture batch results
        original_arun_many = crawler.arun_many
        
        @wraps(original_arun_many)
        async def patched_arun_many(*args, **kwargs):
            results = await original_arun_many(*args, **kwargs)
            if self._integration_active and results:
                await self._handle_crawl_completed(list(results))
            return results
        
        crawler.arun_many = patched_arun_many
    
    async def _handle_page_processed(self, result: CrawlResult) -> None:
        """
        Handle individual page processing events.
        
        This method is called whenever a single page is crawled and processed.
        It updates the analytics with URL discovery information from the page.
        
        Args:
            result: CrawlResult from the processed page
        """
        if not self._integration_active:
            return
        
        try:
            # Analyze the single result for URL discovery
            analysis = self.analytics.analyze_crawl_results([result], result.url)
            
            # Check for dead-end conditions
            should_stop, reason = self.analytics.should_stop_crawling()
            
            if should_stop and self.logger:
                self.logger.warning(f"Dead-end detected: {reason}", tag="DEADEND")
            
            # Call registered event handlers
            for handler in self._event_handlers['on_page_processed']:
                try:
                    if asyncio.iscoroutinefunction(handler):
                        await handler(result, analysis)
                    else:
                        handler(result, analysis)
                except Exception as e:
                    if self.logger:
                        self.logger.error(f"Error in page processed handler: {e}", tag="ERROR")
        
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error handling page processed event: {e}", tag="ERROR")
    
    async def _handle_crawl_completed(self, results: List[CrawlResult]) -> None:
        """
        Handle crawl completion events.
        
        This method is called when a batch of URLs has been crawled.
        It provides comprehensive analysis of the batch results.
        
        Args:
            results: List of CrawlResult objects from the completed crawl
        """
        if not self._integration_active or not results:
            return
        
        try:
            # Analyze all results in the batch
            analysis = self.analytics.analyze_crawl_results(results)
            
            # Get comprehensive statistics
            stats = self.analytics.get_comprehensive_stats()
            
            # Check continuation logic
            should_stop, reason = self.analytics.should_stop_crawling()
            
            # Prepare event data
            event_data = {
                'results': results,
                'analysis': analysis,
                'stats': stats,
                'should_stop': should_stop,
                'stop_reason': reason,
                'next_url': self.analytics.get_next_crawl_url()
            }
            
            # Call registered event handlers
            for handler in self._event_handlers['on_crawl_completed']:
                try:
                    if asyncio.iscoroutinefunction(handler):
                        await handler(event_data)
                    else:
                        handler(event_data)
                except Exception as e:
                    if self.logger:
                        self.logger.error(f"Error in crawl completed handler: {e}", tag="ERROR")
        
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error handling crawl completed event: {e}", tag="ERROR")
    
    def add_event_handler(self, event_type: str, handler: Callable) -> None:
        """
        Add an event handler for exhaustive crawling events.
        
        Args:
            event_type: Type of event ('on_page_processed', 'on_crawl_completed', 'on_url_discovered')
            handler: Callable to handle the event
        """
        if event_type in self._event_handlers:
            self._event_handlers[event_type].append(handler)
        else:
            raise ValueError(f"Unknown event type: {event_type}")
    
    def remove_event_handler(self, event_type: str, handler: Callable) -> None:
        """Remove an event handler."""
        if event_type in self._event_handlers:
            try:
                self._event_handlers[event_type].remove(handler)
            except ValueError:
                pass  # Handler not found
    
    def get_analytics(self) -> ExhaustiveAnalytics:
        """Get the analytics engine instance."""
        return self.analytics
    
    def get_current_metrics(self) -> Dict[str, Any]:
        """Get current exhaustive crawling metrics."""
        return self.analytics.get_comprehensive_stats()
    
    def reset_analytics(self) -> None:
        """Reset analytics state for a new crawling session."""
        self.analytics.reset_session()


def configure_exhaustive_crawler(crawler, logger: Optional[AsyncLoggerBase] = None) -> ExhaustiveCrawlIntegration:
    """
    Configure an existing AsyncWebCrawler for exhaustive crawling with dead-end detection.
    
    This function sets up the integration layer and returns the integration object
    for further configuration and event handling.
    
    Args:
        crawler: AsyncWebCrawler instance to configure
        logger: Optional logger for integration events
        
    Returns:
        ExhaustiveCrawlIntegration instance for managing the integration
    """
    integration = ExhaustiveCrawlIntegration(logger=logger)
    integration.enable_integration(crawler)
    return integration


def create_dead_end_detector(
    dead_end_threshold: int = 50,
    revisit_threshold: float = 0.95,
    logger: Optional[AsyncLoggerBase] = None
) -> Callable:
    """
    Create a dead-end detection function that can be used as an event handler.
    
    Args:
        dead_end_threshold: Number of consecutive dead pages before stopping
        revisit_threshold: Revisit ratio threshold for stopping
        logger: Optional logger for detection events
        
    Returns:
        Callable that can be used as an event handler for dead-end detection
    """
    analytics = ExhaustiveAnalytics(logger=logger)
    
    async def detect_dead_end(event_data: Dict[str, Any]) -> bool:
        """
        Dead-end detection handler.
        
        Args:
            event_data: Event data from crawl completion
            
        Returns:
            True if dead-end detected, False otherwise
        """
        should_stop, reason = analytics.should_stop_crawling(
            dead_end_threshold=dead_end_threshold,
            revisit_threshold=revisit_threshold
        )
        
        if should_stop and logger:
            logger.warning(f"Dead-end detected: {reason}", tag="DEADEND")
        
        return should_stop
    
    return detect_dead_end


def analyze_url_discovery_rate(results: List[CrawlResult], logger: Optional[AsyncLoggerBase] = None) -> Dict[str, Any]:
    """
    Standalone function to analyze URL discovery rate from crawl results.
    
    This function can be used independently of the integration system
    to analyze URL discovery patterns in crawl results.
    
    Args:
        results: List of CrawlResult objects to analyze
        logger: Optional logger for analysis events
        
    Returns:
        Dictionary with URL discovery analysis
    """
    analytics = ExhaustiveAnalytics(logger=logger)
    return analytics.analyze_crawl_results(results)