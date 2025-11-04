"""
Exhaustive Crawling Analytics Module

This module provides dead-end detection and URL discovery analytics for exhaustive crawling.
It extends the existing AsyncWebCrawler analytics infrastructure to support "crawl until dead ends" behavior.
"""

import asyncio
import time
from typing import Dict, List, Set, Optional, Tuple
from dataclasses import dataclass, field
from collections import defaultdict, deque
from datetime import datetime, timedelta

from .models import CrawlResult
from .async_logger import AsyncLoggerBase


@dataclass
class DeadEndMetrics:
    """Metrics for tracking dead-end detection"""
    consecutive_dead_pages: int = 0
    total_urls_discovered: int = 0
    new_urls_last_batch: int = 0
    revisit_count: int = 0
    total_crawl_attempts: int = 0
    discovery_rate_history: List[int] = field(default_factory=list)
    last_discovery_time: Optional[datetime] = None
    crawl_start_time: Optional[datetime] = None
    
    @property
    def revisit_ratio(self) -> float:
        """Calculate the ratio of revisited URLs to total crawl attempts"""
        if self.total_crawl_attempts == 0:
            return 0.0
        return self.revisit_count / self.total_crawl_attempts
    
    @property
    def average_discovery_rate(self) -> float:
        """Calculate average URL discovery rate over recent batches"""
        if not self.discovery_rate_history:
            return 0.0
        # Use last 5 batches for average
        recent_history = self.discovery_rate_history[-5:]
        return sum(recent_history) / len(recent_history)
    
    @property
    def time_since_last_discovery(self) -> Optional[timedelta]:
        """Time elapsed since last URL discovery"""
        if not self.last_discovery_time:
            return None
        return datetime.now() - self.last_discovery_time


@dataclass
class URLTrackingState:
    """State for tracking URL discovery and revisits"""
    discovered_urls: Set[str] = field(default_factory=set)
    crawled_urls: Set[str] = field(default_factory=set)
    failed_urls: Set[str] = field(default_factory=set)
    url_discovery_source: Dict[str, str] = field(default_factory=dict)  # url -> source_url
    url_discovery_time: Dict[str, datetime] = field(default_factory=dict)  # url -> discovery_time
    url_depth: Dict[str, int] = field(default_factory=dict)  # url -> depth
    pending_urls: deque = field(default_factory=deque)  # Queue of URLs to crawl
    
    def add_discovered_url(self, url: str, source_url: str, depth: int = 0) -> bool:
        """Add a newly discovered URL. Returns True if URL is new, False if already known."""
        if url in self.discovered_urls:
            return False
        
        self.discovered_urls.add(url)
        self.url_discovery_source[url] = source_url
        self.url_discovery_time[url] = datetime.now()
        self.url_depth[url] = depth
        self.pending_urls.append(url)
        return True
    
    def mark_crawled(self, url: str, success: bool = True) -> None:
        """Mark a URL as crawled"""
        self.crawled_urls.add(url)
        if not success:
            self.failed_urls.add(url)
        
        # Remove from pending queue if present
        try:
            self.pending_urls.remove(url)
        except ValueError:
            pass  # URL not in queue
    
    def get_next_url(self) -> Optional[str]:
        """Get the next URL to crawl from the queue"""
        if self.pending_urls:
            return self.pending_urls.popleft()
        return None
    
    def has_pending_urls(self) -> bool:
        """Check if there are URLs pending to be crawled"""
        return len(self.pending_urls) > 0
    
    def get_stats(self) -> Dict:
        """Get current tracking statistics"""
        return {
            'total_discovered': len(self.discovered_urls),
            'total_crawled': len(self.crawled_urls),
            'total_failed': len(self.failed_urls),
            'pending_count': len(self.pending_urls),
            'success_rate': (len(self.crawled_urls) - len(self.failed_urls)) / max(1, len(self.crawled_urls))
        }


class ExhaustiveAnalytics:
    """
    Analytics engine for exhaustive crawling with dead-end detection.
    
    This class extends existing AsyncWebCrawler analytics to provide:
    - Dead-end detection based on URL discovery rate
    - Revisit ratio calculation
    - URL tracking and queue management
    - Crawl continuation logic
    """
    
    def __init__(self, logger: Optional[AsyncLoggerBase] = None):
        self.logger = logger
        self.metrics = DeadEndMetrics()
        self.url_state = URLTrackingState()
        self._batch_start_time: Optional[float] = None
        self._last_batch_size = 0
        
    def start_crawl_session(self) -> None:
        """Initialize a new crawl session"""
        self.metrics = DeadEndMetrics()
        self.metrics.crawl_start_time = datetime.now()
        self.url_state = URLTrackingState()
        self._batch_start_time = time.time()
        
        if self.logger:
            self.logger.info("Started exhaustive crawl session", tag="EXHAUST")
    
    def analyze_crawl_results(self, results: List[CrawlResult], source_url: str = None) -> Dict:
        """
        Analyze crawl results to update dead-end detection metrics.
        
        Args:
            results: List of CrawlResult objects from recent crawling
            source_url: The URL that was crawled to produce these results
            
        Returns:
            Dictionary with analysis results and recommendations
        """
        if not results:
            return self._handle_empty_results()
        
        # Track the crawled URL
        if source_url:
            success = any(r.success for r in results if r.url == source_url)
            self.url_state.mark_crawled(source_url, success)
            self.metrics.total_crawl_attempts += 1
        
        # Analyze URL discovery from results
        new_urls_discovered = 0
        total_links_found = 0
        
        for result in results:
            if not result.success:
                continue
                
            # Extract links from the result
            internal_links = result.links.get('internal', []) if result.links else []
            external_links = result.links.get('external', []) if result.links else []
            
            all_links = internal_links + external_links
            total_links_found += len(all_links)
            
            # Track new URL discoveries
            current_depth = result.metadata.get('depth', 0) if result.metadata else 0
            
            for link in all_links:
                url = link.get('href', '')
                if url and self.url_state.add_discovered_url(url, result.url, current_depth + 1):
                    new_urls_discovered += 1
        
        # Update metrics
        self.metrics.new_urls_last_batch = new_urls_discovered
        self.metrics.total_urls_discovered += new_urls_discovered
        self.metrics.discovery_rate_history.append(new_urls_discovered)
        
        # Keep only recent history (last 10 batches)
        if len(self.metrics.discovery_rate_history) > 10:
            self.metrics.discovery_rate_history = self.metrics.discovery_rate_history[-10:]
        
        # Update discovery time if new URLs found
        if new_urls_discovered > 0:
            self.metrics.last_discovery_time = datetime.now()
            self.metrics.consecutive_dead_pages = 0
        else:
            self.metrics.consecutive_dead_pages += 1
        
        # Calculate revisit ratio
        if source_url and source_url in self.url_state.crawled_urls:
            self.metrics.revisit_count += 1
        
        # Log analysis results
        if self.logger:
            self.logger.info(
                f"Analyzed {len(results)} results: {new_urls_discovered} new URLs, "
                f"{total_links_found} total links, {self.metrics.consecutive_dead_pages} consecutive dead pages",
                tag="ANALYZE"
            )
        
        return {
            'new_urls_discovered': new_urls_discovered,
            'total_links_found': total_links_found,
            'consecutive_dead_pages': self.metrics.consecutive_dead_pages,
            'revisit_ratio': self.metrics.revisit_ratio,
            'discovery_rate': self.metrics.average_discovery_rate,
            'should_continue': self._should_continue_crawling(),
            'url_stats': self.url_state.get_stats()
        }
    
    def _handle_empty_results(self) -> Dict:
        """Handle case where no results were returned"""
        self.metrics.consecutive_dead_pages += 1
        self.metrics.discovery_rate_history.append(0)
        
        if self.logger:
            self.logger.warning("No results returned from crawl batch", tag="ANALYZE")
        
        return {
            'new_urls_discovered': 0,
            'total_links_found': 0,
            'consecutive_dead_pages': self.metrics.consecutive_dead_pages,
            'revisit_ratio': self.metrics.revisit_ratio,
            'discovery_rate': 0.0,
            'should_continue': self._should_continue_crawling(),
            'url_stats': self.url_state.get_stats()
        }
    
    def should_stop_crawling(self, dead_end_threshold: int = 50, revisit_threshold: float = 0.95) -> Tuple[bool, str]:
        """
        Determine if crawling should stop based on dead-end detection criteria.
        
        Args:
            dead_end_threshold: Number of consecutive pages with no new URLs before stopping
            revisit_threshold: Ratio of revisited URLs that triggers stopping
            
        Returns:
            Tuple of (should_stop, reason)
        """
        # Check consecutive dead pages
        if self.metrics.consecutive_dead_pages >= dead_end_threshold:
            return True, f"Hit dead end: {self.metrics.consecutive_dead_pages} consecutive pages with no new URLs"
        
        # Check revisit ratio
        if self.metrics.revisit_ratio >= revisit_threshold and self.metrics.total_crawl_attempts > 10:
            return True, f"High revisit ratio: {self.metrics.revisit_ratio:.2%} of URLs are revisits"
        
        # Check if no pending URLs
        if not self.url_state.has_pending_urls():
            return True, "No more URLs to crawl"
        
        # Check discovery rate trend (if consistently low for extended period)
        if len(self.metrics.discovery_rate_history) >= 5:
            recent_avg = sum(self.metrics.discovery_rate_history[-5:]) / 5
            if recent_avg < 0.5 and self.metrics.consecutive_dead_pages > 20:
                return True, f"Very low discovery rate: {recent_avg:.1f} URLs/batch over last 5 batches"
        
        return False, "Continue crawling"
    
    def _should_continue_crawling(self) -> bool:
        """Internal method to determine if crawling should continue"""
        should_stop, _ = self.should_stop_crawling()
        return not should_stop
    
    def get_next_crawl_url(self) -> Optional[str]:
        """Get the next URL to crawl from the discovery queue"""
        return self.url_state.get_next_url()
    
    def get_comprehensive_stats(self) -> Dict:
        """Get comprehensive statistics about the crawl session"""
        crawl_duration = None
        if self.metrics.crawl_start_time:
            crawl_duration = datetime.now() - self.metrics.crawl_start_time
        
        return {
            'session_stats': {
                'crawl_duration': str(crawl_duration) if crawl_duration else None,
                'total_crawl_attempts': self.metrics.total_crawl_attempts,
                'total_urls_discovered': self.metrics.total_urls_discovered,
                'consecutive_dead_pages': self.metrics.consecutive_dead_pages,
                'revisit_ratio': self.metrics.revisit_ratio,
                'average_discovery_rate': self.metrics.average_discovery_rate,
                'time_since_last_discovery': str(self.metrics.time_since_last_discovery) if self.metrics.time_since_last_discovery else None
            },
            'url_tracking': self.url_state.get_stats(),
            'discovery_history': self.metrics.discovery_rate_history.copy(),
            'pending_urls_sample': list(self.url_state.pending_urls)[:10]  # First 10 pending URLs
        }
    
    def reset_session(self) -> None:
        """Reset all analytics state for a new crawl session"""
        self.start_crawl_session()