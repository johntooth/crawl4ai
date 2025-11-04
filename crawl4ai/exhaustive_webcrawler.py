"""
Exhaustive Web Crawler Extension

This module extends AsyncWebCrawler with dead-end detection and exhaustive crawling capabilities.
It provides methods for crawling until dead ends are reached, with intelligent URL discovery
and revisit ratio analysis.
"""

import asyncio
from typing import Optional, List, Dict, Any, Union

from .async_webcrawler import AsyncWebCrawler
from .async_configs import CrawlerRunConfig
from .models import CrawlResult, RunManyReturn
from .exhaustive_analytics import ExhaustiveAnalytics, DeadEndMetrics, URLTrackingState
from .exhaustive_configs import ExhaustiveCrawlConfig
from .async_logger import AsyncLoggerBase


class ExhaustiveAsyncWebCrawler(AsyncWebCrawler):
    """
    Extended AsyncWebCrawler with exhaustive crawling and dead-end detection capabilities.
    
    This class adds methods for:
    - Crawling until dead ends are reached
    - Analyzing URL discovery rates
    - Calculating revisit ratios
    - Managing URL queues for continuation
    - Providing detailed analytics
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.analytics = ExhaustiveAnalytics(logger=self.logger)
        self._exhaustive_session_active = False
    
    async def arun_exhaustive(
        self,
        start_url: str,
        config: Optional[ExhaustiveCrawlConfig] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Run exhaustive crawling until dead ends are reached.
        
        This method uses existing arun() as foundation and adds loop logic to continue
        crawling until dead-end threshold is reached. It implements URL queue management
        for continuing from discovered URLs and provides progress tracking using existing
        crawl analytics.
        
        Args:
            start_url: The URL to start crawling from
            config: Configuration for exhaustive crawling behavior
            **kwargs: Additional arguments passed to underlying arun methods
            
        Returns:
            Dictionary containing:
            - results: List of all CrawlResult objects
            - analytics: Comprehensive crawling statistics
            - stop_reason: Why the crawling stopped
        """
        config = config or ExhaustiveCrawlConfig()
        
        # Initialize analytics session
        self.analytics.start_crawl_session()
        self._exhaustive_session_active = True
        
        try:
            # Start with the initial URL
            all_results = []
            crawl_queue = [start_url]  # URL queue for continuing from discovered URLs
            crawled_count = 0
            
            log_stats = getattr(config, 'log_discovery_stats', True)
            if self.logger and log_stats:
                self.logger.info(
                    f"Starting exhaustive crawl from {start_url}",
                    tag="EXHAUST"
                )
            
            while crawl_queue and self._exhaustive_session_active and crawled_count < config.max_pages:
                # Get next batch of URLs to crawl
                batch_urls = []
                batch_size = min(getattr(config, 'batch_size', 5), len(crawl_queue))
                
                for _ in range(batch_size):
                    if crawl_queue:
                        batch_urls.append(crawl_queue.pop(0))
                
                if not batch_urls:
                    break
                
                # Crawl the batch using existing arun() as foundation
                batch_results = await self._crawl_batch(batch_urls, config, **kwargs)
                all_results.extend(batch_results)
                crawled_count += len(batch_results)
                
                # Analyze results for dead-end detection and URL discovery
                for i, result in enumerate(batch_results):
                    source_url = batch_urls[i] if i < len(batch_urls) else None
                    analysis = self.analytics.analyze_crawl_results([result], source_url)
                    
                    # Add newly discovered URLs to the queue
                    if result.success and hasattr(result, 'links') and result.links:
                        new_urls = self._extract_urls_from_result(result, config)
                        for new_url in new_urls:
                            if new_url not in [r.url for r in all_results] and new_url not in crawl_queue:
                                crawl_queue.append(new_url)
                
                # Log progress using existing crawl analytics
                log_stats = getattr(config, 'log_discovery_stats', True)
                if self.logger and log_stats:
                    total_analysis = self.analytics.analyze_crawl_results(batch_results)
                    self.logger.info(
                        f"Batch complete: {len(batch_results)} pages crawled, "
                        f"{total_analysis['new_urls_discovered']} new URLs discovered, "
                        f"{len(crawl_queue)} URLs in queue, "
                        f"dead pages: {total_analysis['consecutive_dead_pages']}, "
                        f"revisit ratio: {total_analysis['revisit_ratio']:.2%}",
                        tag="PROGRESS"
                    )
                
                # Check if we should stop based on dead-end detection
                should_stop, stop_reason = self.analytics.should_stop_crawling(
                    dead_end_threshold=config.dead_end_threshold,
                    revisit_threshold=config.revisit_ratio_threshold
                )
                
                if should_stop:
                    if self.logger:
                        self.logger.info(f"Stopping exhaustive crawl: {stop_reason}", tag="COMPLETE")
                    break
                
                # Continue crawling if we have URLs in queue and haven't hit limits
                continue_on_dead_ends = getattr(config, 'continue_on_dead_ends', True)
                if not continue_on_dead_ends and total_analysis['consecutive_dead_pages'] > 0:
                    if self.logger:
                        self.logger.info("Stopping due to dead end and continue_on_dead_ends=False", tag="COMPLETE")
                    stop_reason = "Dead end reached and continue_on_dead_ends disabled"
                    break
            
            # Determine final stop reason if not already set
            if 'stop_reason' not in locals():
                if crawled_count >= config.max_pages:
                    stop_reason = f"Maximum pages limit reached ({config.max_pages})"
                elif not crawl_queue:
                    stop_reason = "No more URLs to crawl"
                else:
                    stop_reason = "Session ended"
            
            # Get final analytics using existing crawl analytics
            final_stats = self.analytics.get_comprehensive_stats()
            
            if self.logger:
                self.logger.info(
                    f"Exhaustive crawl completed: {len(all_results)} pages crawled, "
                    f"{final_stats['session_stats']['total_urls_discovered']} URLs discovered",
                    tag="COMPLETE"
                )
            
            return {
                'results': all_results,
                'analytics': final_stats,
                'stop_reason': stop_reason,
                'total_pages_crawled': len(all_results),
                'successful_pages': len([r for r in all_results if r.success]),
                'total_urls_discovered': final_stats['session_stats']['total_urls_discovered'],
                'urls_in_queue': len(crawl_queue)
            }
            
        finally:
            self._exhaustive_session_active = False
    
    async def _crawl_batch(self, urls: List[str], config: CrawlerRunConfig, **kwargs) -> List[CrawlResult]:
        """
        Crawl a batch of URLs using the existing arun infrastructure as foundation.
        
        This method uses existing arun() method as the foundation for crawling,
        ensuring compatibility with all existing AsyncWebCrawler functionality.
        
        Args:
            urls: List of URLs to crawl
            config: Crawler configuration
            **kwargs: Additional arguments passed to arun methods
            
        Returns:
            List of CrawlResult objects
        """
        if not urls:
            return []
        
        results = []
        
        try:
            # Create a basic CrawlerRunConfig for batch operations to avoid attribute issues
            from .async_configs import CrawlerRunConfig
            batch_config = CrawlerRunConfig()
            
            for url in urls:
                try:
                    # Use existing arun() as foundation - this ensures all existing
                    # functionality (caching, processing, etc.) works correctly
                    result_container = await self.arun(url, config=batch_config, **kwargs)
                    
                    # Extract CrawlResult from container if needed
                    if hasattr(result_container, 'result'):
                        # It's a CrawlResultContainer
                        crawl_result = result_container.result
                    elif hasattr(result_container, 'url'):
                        # It's already a CrawlResult
                        crawl_result = result_container
                    else:
                        # Handle unexpected return type
                        if self.logger:
                            self.logger.warning(f"Unexpected result type from arun: {type(result_container)}", tag="BATCH")
                        continue
                    
                    results.append(crawl_result)
                    
                except Exception as e:
                    if self.logger:
                        self.logger.error(f"Error crawling URL {url}: {str(e)}", tag="BATCH")
                    
                    # Create a failed result to maintain consistency
                    from .models import CrawlResult
                    failed_result = CrawlResult(
                        url=url,
                        html="",
                        success=False,
                        error_message=str(e)
                    )
                    results.append(failed_result)
                
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error in batch crawling: {str(e)}", tag="BATCH")
        
        return results
    
    def _extract_urls_from_result(self, result: CrawlResult, config: ExhaustiveCrawlConfig) -> List[str]:
        """
        Extract URLs from a crawl result for URL queue management.
        
        This method extracts internal and external links from crawl results
        to continue crawling from discovered URLs.
        
        Args:
            result: CrawlResult object to extract URLs from
            config: Configuration to determine which URLs to include
            
        Returns:
            List of URLs discovered in the result
        """
        urls = []
        
        if not result.success or not hasattr(result, 'links') or not result.links:
            return urls
        
        try:
            # Extract internal links (always included)
            internal_links = result.links.get('internal', [])
            for link in internal_links:
                if isinstance(link, dict) and 'href' in link:
                    url = link['href']
                    if url and url not in urls:
                        urls.append(url)
                elif isinstance(link, str):
                    if link and link not in urls:
                        urls.append(link)
            
            # Extract external links if configured
            include_external = getattr(config, 'include_external_links', False)
            if include_external:
                external_links = result.links.get('external', [])
                for link in external_links:
                    if isinstance(link, dict) and 'href' in link:
                        url = link['href']
                        if url and url not in urls:
                            urls.append(url)
                    elif isinstance(link, str):
                        if link and link not in urls:
                            urls.append(link)
        
        except Exception as e:
            if self.logger:
                self.logger.warning(f"Error extracting URLs from result: {str(e)}", tag="URL_EXTRACT")
        
        return urls
    
    async def analyze_url_discovery_rate(self, results: List[CrawlResult]) -> Dict[str, Any]:
        """
        Analyze URL discovery rate from crawl results.
        
        This method examines the links found in crawl results to determine
        the rate of new URL discovery, which is key for dead-end detection.
        
        Args:
            results: List of CrawlResult objects to analyze
            
        Returns:
            Dictionary with discovery rate analysis
        """
        return self.analytics.analyze_crawl_results(results)
    
    def calculate_revisit_ratio(self) -> float:
        """
        Calculate the current revisit ratio.
        
        Returns:
            Float between 0.0 and 1.0 representing the ratio of revisited URLs
        """
        return self.analytics.metrics.revisit_ratio
    
    def get_dead_end_metrics(self) -> DeadEndMetrics:
        """
        Get current dead-end detection metrics.
        
        Returns:
            DeadEndMetrics object with current statistics
        """
        return self.analytics.metrics
    
    def get_url_tracking_state(self) -> URLTrackingState:
        """
        Get current URL tracking state.
        
        Returns:
            URLTrackingState object with discovered/crawled URL information
        """
        return self.analytics.url_state
    
    async def should_continue_crawling(
        self,
        dead_end_threshold: int = 50,
        revisit_threshold: float = 0.95
    ) -> tuple[bool, str]:
        """
        Determine if crawling should continue based on current metrics.
        
        Args:
            dead_end_threshold: Consecutive dead pages threshold
            revisit_threshold: Revisit ratio threshold
            
        Returns:
            Tuple of (should_continue, reason)
        """
        should_stop, reason = self.analytics.should_stop_crawling(
            dead_end_threshold, revisit_threshold
        )
        return not should_stop, reason
    
    def reset_exhaustive_session(self) -> None:
        """Reset the exhaustive crawling session state."""
        self.analytics.reset_session()
        self._exhaustive_session_active = False
    
    def get_exhaustive_stats(self) -> Dict[str, Any]:
        """
        Get comprehensive exhaustive crawling statistics.
        
        Returns:
            Dictionary with detailed analytics and metrics
        """
        return self.analytics.get_comprehensive_stats()
    
    def get_progress_tracking(self) -> Dict[str, Any]:
        """
        Get real-time progress tracking information using existing crawl analytics.
        
        This method provides progress tracking that integrates with existing
        AsyncWebCrawler analytics infrastructure.
        
        Returns:
            Dictionary with progress tracking information
        """
        stats = self.analytics.get_comprehensive_stats()
        metrics = self.analytics.metrics
        url_state = self.analytics.url_state
        
        return {
            'session_active': self._exhaustive_session_active,
            'crawl_duration': stats['session_stats']['crawl_duration'],
            'pages_crawled': stats['session_stats']['total_crawl_attempts'],
            'urls_discovered': stats['session_stats']['total_urls_discovered'],
            'urls_pending': url_state.get_stats()['pending_count'],
            'success_rate': url_state.get_stats()['success_rate'],
            'dead_end_status': {
                'consecutive_dead_pages': metrics.consecutive_dead_pages,
                'revisit_ratio': metrics.revisit_ratio,
                'average_discovery_rate': metrics.average_discovery_rate,
                'time_since_last_discovery': str(metrics.time_since_last_discovery) if metrics.time_since_last_discovery else None
            },
            'discovery_trend': metrics.discovery_rate_history[-5:] if len(metrics.discovery_rate_history) >= 5 else metrics.discovery_rate_history
        }
    
    async def stop_exhaustive_crawling(self) -> None:
        """Stop the current exhaustive crawling session."""
        self._exhaustive_session_active = False
        if self.logger:
            self.logger.info("Exhaustive crawling session stopped by user", tag="STOP")


# Convenience function to create an exhaustive crawler
def create_exhaustive_crawler(**kwargs) -> ExhaustiveAsyncWebCrawler:
    """
    Create an ExhaustiveAsyncWebCrawler with default configuration.
    
    Args:
        **kwargs: Arguments passed to ExhaustiveAsyncWebCrawler constructor
        
    Returns:
        Configured ExhaustiveAsyncWebCrawler instance
    """
    return ExhaustiveAsyncWebCrawler(**kwargs)