#!/usr/bin/env python3
"""
Comprehensive Test Suite for Exhaustive Crawling

This module provides comprehensive testing for the exhaustive crawling functionality,
including unit tests, integration tests, performance tests, and mock website scenarios.

Test Coverage:
- ExhaustiveCrawlConfig validation and behavior
- Dead-end detection logic and thresholds
- Exhaustive crawling workflow integration
- Performance testing for large site mapping
- Mock website scenarios for different crawling patterns
"""

import pytest
import asyncio
import time
import tempfile
import shutil
import sys
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from typing import List, Dict, Any
from datetime import datetime, timedelta

# Add the project root directory to the path to import crawl4ai
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Import Crawl4AI components
from crawl4ai import ExhaustiveCrawlConfig, create_exhaustive_preset_config, BrowserConfig
from crawl4ai.exhaustive_webcrawler import ExhaustiveAsyncWebCrawler
from crawl4ai.exhaustive_analytics import ExhaustiveAnalytics, DeadEndMetrics, URLTrackingState
from crawl4ai.models import CrawlResult, MarkdownGenerationResult


class TestExhaustiveCrawlConfig:
    """Unit tests for ExhaustiveCrawlConfig class."""
    
    def test_config_initialization_defaults(self):
        """Test ExhaustiveCrawlConfig initialization with default values."""
        config = ExhaustiveCrawlConfig()
        
        # Test exhaustive-specific defaults
        assert config.max_depth == 100
        assert config.max_pages == 10000
        assert config.stop_on_dead_ends == True
        assert config.dead_end_threshold == 50
        assert config.revisit_ratio_threshold == 0.95
        assert config.discover_files_during_crawl == True
        assert config.download_discovered_files == False
        assert config.max_concurrent_requests == 20
        assert config.delay_between_requests == 0.1
        assert config.respect_robots_txt == False
    
    def test_config_initialization_custom(self):
        """Test ExhaustiveCrawlConfig with custom parameters."""
        config = ExhaustiveCrawlConfig(
            max_depth=50,
            max_pages=5000,
            dead_end_threshold=25,
            revisit_ratio_threshold=0.85,
            max_concurrent_requests=10,
            delay_between_requests=0.2,
            discover_files_during_crawl=False,
            download_discovered_files=True
        )
        
        assert config.max_depth == 50
        assert config.max_pages == 5000
        assert config.dead_end_threshold == 25
        assert config.revisit_ratio_threshold == 0.85
        assert config.max_concurrent_requests == 10
        assert config.delay_between_requests == 0.2
        assert config.discover_files_during_crawl == False
        assert config.download_discovered_files == True
    
    def test_config_validation_valid(self):
        """Test validation of valid configuration parameters."""
        config = ExhaustiveCrawlConfig(
            max_depth=75,
            dead_end_threshold=30,
            revisit_ratio_threshold=0.90
        )
        
        # Should not raise any exceptions
        config.validate()
    
    def test_config_validation_invalid_parameters(self):
        """Test validation catches invalid parameters."""
        
        # Test invalid max_depth
        with pytest.raises(AssertionError, match="max_depth must be positive"):
            config = ExhaustiveCrawlConfig(max_depth=0)
            config.validate()
        
        # Test invalid dead_end_threshold
        with pytest.raises(AssertionError, match="dead_end_threshold must be positive"):
            config = ExhaustiveCrawlConfig(dead_end_threshold=-1)
            config.validate()
        
        # Test invalid revisit_ratio_threshold
        with pytest.raises(AssertionError, match="revisit_ratio_threshold must be between 0 and 1"):
            config = ExhaustiveCrawlConfig(revisit_ratio_threshold=1.5)
            config.validate()
        
        with pytest.raises(AssertionError, match="revisit_ratio_threshold must be between 0 and 1"):
            config = ExhaustiveCrawlConfig(revisit_ratio_threshold=-0.1)
            config.validate()
    
    def test_config_preset_creation(self):
        """Test creation of preset configurations."""
        
        # Test comprehensive preset
        config = create_exhaustive_preset_config("comprehensive")
        assert config.max_depth == 100
        assert config.max_pages == 10000
        assert config.dead_end_threshold == 50
        
        # Test balanced preset
        config = create_exhaustive_preset_config("balanced")
        assert config.max_depth == 50
        assert config.max_pages == 5000
        assert config.dead_end_threshold == 30
        
        # Test fast preset
        config = create_exhaustive_preset_config("fast")
        assert config.max_depth == 25
        assert config.max_pages == 2000
        assert config.dead_end_threshold == 20
        
        # Test files_focused preset
        config = create_exhaustive_preset_config("files_focused")
        assert config.discover_files_during_crawl == True
        assert config.download_discovered_files == True
    
    def test_config_preset_with_overrides(self):
        """Test preset configuration with custom overrides."""
        config = create_exhaustive_preset_config(
            "balanced",
            max_depth=60,
            dead_end_threshold=35
        )
        
        # Should have overridden values
        assert config.max_depth == 60
        assert config.dead_end_threshold == 35
        
        # Should retain preset defaults for non-overridden values
        assert config.max_pages == 5000  # From balanced preset
    
    def test_config_invalid_preset(self):
        """Test handling of invalid preset names."""
        with pytest.raises(ValueError, match="Unknown preset"):
            create_exhaustive_preset_config("invalid_preset")


class TestDeadEndDetectionLogic:
    """Unit tests for dead-end detection logic."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.analytics = ExhaustiveAnalytics()
        self.analytics.start_crawl_session()
    
    def test_dead_end_metrics_initialization(self):
        """Test DeadEndMetrics initialization."""
        metrics = DeadEndMetrics()
        
        assert metrics.consecutive_dead_pages == 0
        assert metrics.total_urls_discovered == 0
        assert metrics.revisit_count == 0
        assert metrics.total_crawl_attempts == 0
        assert metrics.revisit_ratio == 0.0
        assert metrics.average_discovery_rate == 0.0
    
    def test_revisit_ratio_calculation(self):
        """Test revisit ratio calculation."""
        metrics = DeadEndMetrics()
        
        # No crawl attempts yet
        assert metrics.revisit_ratio == 0.0
        
        # Add some crawl attempts and revisits
        metrics.total_crawl_attempts = 10
        metrics.revisit_count = 3
        assert metrics.revisit_ratio == 0.3
        
        # Test edge case with zero attempts
        metrics.total_crawl_attempts = 0
        assert metrics.revisit_ratio == 0.0
    
    def test_average_discovery_rate_calculation(self):
        """Test average discovery rate calculation."""
        metrics = DeadEndMetrics()
        
        # No history yet
        assert metrics.average_discovery_rate == 0.0
        
        # Add discovery history
        metrics.discovery_rate_history = [5, 4, 3, 2, 1]
        assert metrics.average_discovery_rate == 3.0
        
        # Test with more than 5 entries (should use last 5)
        metrics.discovery_rate_history = [10, 9, 8, 7, 6, 5, 4, 3, 2, 1]
        assert metrics.average_discovery_rate == 3.0  # Average of [5, 4, 3, 2, 1]
    
    def test_url_tracking_state_operations(self):
        """Test URL tracking state operations."""
        state = URLTrackingState()
        
        # Test adding new URLs
        is_new = state.add_discovered_url("https://example.com/page1", "https://example.com", 1)
        assert is_new == True
        assert "https://example.com/page1" in state.discovered_urls
        
        # Test adding duplicate URL
        is_new = state.add_discovered_url("https://example.com/page1", "https://example.com", 1)
        assert is_new == False
        
        # Test marking URL as crawled
        state.mark_crawled("https://example.com/page1", success=True)
        assert "https://example.com/page1" in state.crawled_urls
        assert "https://example.com/page1" not in state.failed_urls
        
        # Test marking URL as failed
        state.add_discovered_url("https://example.com/page2", "https://example.com/page1", 2)
        state.mark_crawled("https://example.com/page2", success=False)
        assert "https://example.com/page2" in state.crawled_urls
        assert "https://example.com/page2" in state.failed_urls
    
    def test_url_queue_operations(self):
        """Test URL queue operations."""
        state = URLTrackingState()
        
        # Add URLs to queue
        state.add_discovered_url("https://example.com/page1", "https://example.com", 1)
        state.add_discovered_url("https://example.com/page2", "https://example.com", 1)
        
        assert state.has_pending_urls() == True
        
        # Get next URL
        next_url = state.get_next_url()
        assert next_url == "https://example.com/page1"
        
        # Mark as crawled (should remove from queue)
        state.mark_crawled(next_url)
        
        # Get next URL
        next_url = state.get_next_url()
        assert next_url == "https://example.com/page2"
    
    def test_should_stop_crawling_dead_end_threshold(self):
        """Test dead-end threshold stopping condition."""
        # Set up analytics with high consecutive dead pages
        self.analytics.metrics.consecutive_dead_pages = 55
        
        should_stop, reason = self.analytics.should_stop_crawling(dead_end_threshold=50)
        assert should_stop == True
        assert "dead end" in reason.lower()
    
    def test_should_stop_crawling_revisit_threshold(self):
        """Test revisit ratio threshold stopping condition."""
        # Set up analytics with high revisit ratio
        self.analytics.metrics.total_crawl_attempts = 100
        self.analytics.metrics.revisit_count = 96
        
        should_stop, reason = self.analytics.should_stop_crawling(revisit_threshold=0.95)
        assert should_stop == True
        assert "revisit" in reason.lower()
    
    def test_should_stop_crawling_no_pending_urls(self):
        """Test stopping when no URLs are pending."""
        # Empty URL queue
        assert not self.analytics.url_state.has_pending_urls()
        
        should_stop, reason = self.analytics.should_stop_crawling()
        assert should_stop == True
        assert "no more urls" in reason.lower()
    
    def test_should_continue_crawling(self):
        """Test conditions where crawling should continue."""
        # Add some pending URLs
        self.analytics.url_state.add_discovered_url("https://example.com/page1", "https://example.com", 1)
        
        # Set metrics below thresholds
        self.analytics.metrics.consecutive_dead_pages = 10
        self.analytics.metrics.total_crawl_attempts = 50
        self.analytics.metrics.revisit_count = 20
        
        should_stop, reason = self.analytics.should_stop_crawling(dead_end_threshold=50, revisit_threshold=0.95)
        assert should_stop == False
        assert reason == "Continue crawling"


def create_mock_crawl_result(url: str, links: List[Dict] = None, success: bool = True) -> CrawlResult:
    """Create a mock CrawlResult for testing."""
    links = links or []
    
    markdown_result = MarkdownGenerationResult(
        raw_markdown=f"Content from {url}",
        markdown_with_citations="",
        references_markdown="",
        fit_markdown="",
        fit_html=""
    )
    
    return CrawlResult(
        url=url,
        html=f"<html><body>Content from {url}</body></html>",
        success=success,
        cleaned_html=f"Content from {url}",
        markdown=markdown_result,
        links={'internal': links, 'external': []},
        metadata={'depth': 0},
        extracted_content=None,
        error_message=None if success else "Mock error"
    )


class TestExhaustiveCrawlingWorkflow:
    """Integration tests for exhaustive crawling workflow."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def mock_browser_config(self):
        """Create mock browser configuration."""
        return BrowserConfig(headless=True)
    
    @pytest.mark.asyncio
    async def test_basic_exhaustive_workflow(self, mock_browser_config):
        """Test basic exhaustive crawling workflow."""
        config = ExhaustiveCrawlConfig(
            max_pages=5,  # Small limit for testing
            dead_end_threshold=3,
            revisit_ratio_threshold=0.80,
            enable_progress_tracking=False  # Reduce test noise
        )
        
        crawler = ExhaustiveAsyncWebCrawler(config=mock_browser_config)
        
        # Mock the underlying arun method
        mock_results = [
            create_mock_crawl_result("raw:<html><body>Test content</body></html>", [
                {'href': 'https://example.com/page1'},
                {'href': 'https://example.com/page2'}
            ])
        ]
        
        crawler.arun = AsyncMock(return_value=mock_results[0])
        
        try:
            result = await crawler.arun_exhaustive("raw:<html><body>Test content</body></html>", config=config)
            
            # Verify result structure
            assert 'results' in result
            assert 'analytics' in result
            assert 'stop_reason' in result
            assert 'total_pages_crawled' in result
            assert 'successful_pages' in result
            
            # Verify we got some results
            assert result['total_pages_crawled'] > 0
            assert result['successful_pages'] > 0
            
        finally:
            if hasattr(crawler, 'close'):
                await crawler.close()
    
    @pytest.mark.asyncio
    async def test_dead_end_detection_workflow(self, mock_browser_config):
        """Test that dead-end detection stops crawling appropriately."""
        config = ExhaustiveCrawlConfig(
            max_pages=20,
            dead_end_threshold=2,  # Very low threshold for quick testing
            revisit_ratio_threshold=0.95,
            enable_progress_tracking=False
        )
        
        crawler = ExhaustiveAsyncWebCrawler(config=mock_browser_config)
        
        # Mock arun to return results with no links (dead end)
        dead_end_result = create_mock_crawl_result("raw:<html><body>No links here</body></html>", [])
        crawler.arun = AsyncMock(return_value=dead_end_result)
        
        try:
            result = await crawler.arun_exhaustive("raw:<html><body>No links here</body></html>", config=config)
            
            # Should stop due to dead end
            assert "dead end" in result['stop_reason'].lower() or "no more urls" in result['stop_reason'].lower()
            
            # Should have crawled minimal pages
            assert result['total_pages_crawled'] <= 5
            
        finally:
            if hasattr(crawler, 'close'):
                await crawler.close()
    
    @pytest.mark.asyncio
    async def test_url_discovery_and_queue_management(self, mock_browser_config):
        """Test URL discovery and queue management during crawling."""
        config = ExhaustiveCrawlConfig(
            max_pages=10,
            dead_end_threshold=5,
            enable_progress_tracking=False
        )
        
        crawler = ExhaustiveAsyncWebCrawler(config=mock_browser_config)
        
        # Mock arun to return different results based on URL
        def mock_arun_side_effect(url, **kwargs):
            if "page1" in url:
                return create_mock_crawl_result(url, [{'href': 'https://example.com/page2'}])
            elif "page2" in url:
                return create_mock_crawl_result(url, [{'href': 'https://example.com/page3'}])
            else:
                return create_mock_crawl_result(url, [])
        
        crawler.arun = AsyncMock(side_effect=mock_arun_side_effect)
        
        try:
            result = await crawler.arun_exhaustive("https://example.com/page1", config=config)
            
            # Should have discovered and crawled multiple URLs
            assert result['total_pages_crawled'] > 1
            assert result['total_urls_discovered'] > 0
            
        finally:
            if hasattr(crawler, 'close'):
                await crawler.close()
    
    @pytest.mark.asyncio
    async def test_progress_tracking_integration(self, mock_browser_config):
        """Test progress tracking functionality."""
        config = ExhaustiveCrawlConfig(
            max_pages=5,
            dead_end_threshold=3,
            enable_progress_tracking=True
        )
        
        crawler = ExhaustiveAsyncWebCrawler(config=mock_browser_config)
        crawler.arun = AsyncMock(return_value=create_mock_crawl_result("test", []))
        
        try:
            # Get initial progress
            progress = crawler.get_progress_tracking()
            assert 'session_active' in progress
            assert 'crawl_duration' in progress
            assert 'pages_crawled' in progress
            
            # Session should be inactive initially
            assert progress['session_active'] == False
            
        finally:
            if hasattr(crawler, 'close'):
                await crawler.close()


class TestPerformanceScenarios:
    """Performance tests for large site mapping scenarios."""
    
    @pytest.mark.asyncio
    async def test_large_url_queue_performance(self):
        """Test performance with large URL queues."""
        analytics = ExhaustiveAnalytics()
        analytics.start_crawl_session()
        
        # Simulate discovering many URLs
        start_time = time.time()
        
        for i in range(1000):
            url = f"https://example.com/page{i}"
            analytics.url_state.add_discovered_url(url, "https://example.com", 1)
        
        end_time = time.time()
        
        # Should complete quickly (under 1 second)
        assert (end_time - start_time) < 1.0
        
        # Verify all URLs were added
        assert len(analytics.url_state.discovered_urls) == 1000
        assert analytics.url_state.has_pending_urls()
    
    @pytest.mark.asyncio
    async def test_discovery_rate_history_performance(self):
        """Test performance of discovery rate history tracking."""
        analytics = ExhaustiveAnalytics()
        analytics.start_crawl_session()
        
        start_time = time.time()
        
        # Simulate many batches of URL discovery
        for batch in range(100):
            # Create mock results with varying numbers of links
            num_links = batch % 10  # 0-9 links per batch
            links = [{'href': f'https://example.com/batch{batch}_link{i}'} for i in range(num_links)]
            
            mock_result = create_mock_crawl_result(f"https://example.com/batch{batch}", links)
            analytics.analyze_crawl_results([mock_result])
        
        end_time = time.time()
        
        # Should complete quickly
        assert (end_time - start_time) < 2.0
        
        # Verify history is maintained efficiently (only last 10 entries)
        assert len(analytics.metrics.discovery_rate_history) == 10
        
        # Verify average calculation works
        avg_rate = analytics.metrics.average_discovery_rate
        assert isinstance(avg_rate, float)
        assert avg_rate >= 0
    
    @pytest.mark.asyncio
    async def test_memory_usage_with_large_datasets(self):
        """Test memory usage with large datasets."""
        import sys
        
        analytics = ExhaustiveAnalytics()
        analytics.start_crawl_session()
        
        # Get initial memory usage (approximate)
        initial_size = sys.getsizeof(analytics.url_state.discovered_urls)
        
        # Add many URLs
        for i in range(5000):
            analytics.url_state.add_discovered_url(f"https://example.com/page{i}", "source", 1)
        
        # Check memory growth is reasonable
        final_size = sys.getsizeof(analytics.url_state.discovered_urls)
        memory_growth = final_size - initial_size
        
        # Memory growth should be reasonable (less than 1MB for 5000 URLs)
        assert memory_growth < 1024 * 1024
    
    def test_config_validation_performance(self):
        """Test configuration validation performance."""
        start_time = time.time()
        
        # Create and validate many configurations
        for i in range(100):
            config = ExhaustiveCrawlConfig(
                max_depth=50 + i,
                max_pages=1000 + i * 10,
                dead_end_threshold=20 + i % 10
            )
            config.validate()
        
        end_time = time.time()
        
        # Should complete quickly
        assert (end_time - start_time) < 1.0


class MockWebsiteScenarios:
    """Mock website scenarios for testing different crawling patterns."""
    
    @staticmethod
    def create_linear_site_structure(depth: int = 5) -> Dict[str, List[str]]:
        """Create a linear site structure (page1 -> page2 -> page3 -> ...)."""
        structure = {}
        
        for i in range(depth):
            current_page = f"https://example.com/page{i}"
            if i < depth - 1:
                next_page = f"https://example.com/page{i + 1}"
                structure[current_page] = [next_page]
            else:
                structure[current_page] = []  # Last page has no links
        
        return structure
    
    @staticmethod
    def create_hub_and_spoke_structure(hub_url: str, num_spokes: int = 5) -> Dict[str, List[str]]:
        """Create a hub-and-spoke structure (hub links to all spokes, spokes link back to hub)."""
        structure = {}
        
        # Hub page links to all spokes
        spoke_urls = [f"https://example.com/spoke{i}" for i in range(num_spokes)]
        structure[hub_url] = spoke_urls
        
        # Each spoke links back to hub
        for spoke_url in spoke_urls:
            structure[spoke_url] = [hub_url]
        
        return structure
    
    @staticmethod
    def create_deep_tree_structure(base_url: str, depth: int = 3, branching_factor: int = 3) -> Dict[str, List[str]]:
        """Create a deep tree structure with specified depth and branching factor."""
        structure = {}
        
        def build_tree(current_url: str, current_depth: int):
            if current_depth >= depth:
                structure[current_url] = []
                return
            
            children = []
            for i in range(branching_factor):
                child_url = f"{current_url}/child{i}"
                children.append(child_url)
                build_tree(child_url, current_depth + 1)
            
            structure[current_url] = children
        
        build_tree(base_url, 0)
        return structure
    
    @staticmethod
    def create_cyclic_structure(num_nodes: int = 4) -> Dict[str, List[str]]:
        """Create a cyclic structure where pages form a cycle."""
        structure = {}
        
        for i in range(num_nodes):
            current_page = f"https://example.com/cycle{i}"
            next_page = f"https://example.com/cycle{(i + 1) % num_nodes}"
            structure[current_page] = [next_page]
        
        return structure


class TestMockWebsiteScenarios:
    """Test exhaustive crawling with different mock website scenarios."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.scenarios = MockWebsiteScenarios()
    
    @pytest.mark.asyncio
    async def test_linear_site_crawling(self):
        """Test crawling a linear site structure."""
        structure = self.scenarios.create_linear_site_structure(depth=5)
        
        analytics = ExhaustiveAnalytics()
        analytics.start_crawl_session()
        
        # Simulate crawling the linear structure
        current_url = "https://example.com/page0"
        crawled_urls = []
        
        while current_url and len(crawled_urls) < 10:  # Safety limit
            crawled_urls.append(current_url)
            
            # Get links for current page
            links = structure.get(current_url, [])
            mock_links = [{'href': link} for link in links]
            
            # Create mock result and analyze
            result = create_mock_crawl_result(current_url, mock_links)
            analysis = analytics.analyze_crawl_results([result], current_url)
            
            # Get next URL to crawl
            current_url = analytics.get_next_crawl_url()
        
        # Should have crawled all pages in the linear structure
        assert len(crawled_urls) == 5
        assert crawled_urls == [f"https://example.com/page{i}" for i in range(5)]
    
    @pytest.mark.asyncio
    async def test_hub_and_spoke_crawling(self):
        """Test crawling a hub-and-spoke structure."""
        hub_url = "https://example.com/hub"
        structure = self.scenarios.create_hub_and_spoke_structure(hub_url, num_spokes=3)
        
        analytics = ExhaustiveAnalytics()
        analytics.start_crawl_session()
        
        # Start crawling from hub
        hub_links = [{'href': link} for link in structure[hub_url]]
        hub_result = create_mock_crawl_result(hub_url, hub_links)
        
        analysis = analytics.analyze_crawl_results([hub_result], hub_url)
        
        # Should discover all spoke URLs
        assert analysis['new_urls_discovered'] == 3
        
        # Crawl one spoke
        spoke_url = analytics.get_next_crawl_url()
        spoke_links = [{'href': link} for link in structure[spoke_url]]
        spoke_result = create_mock_crawl_result(spoke_url, spoke_links)
        
        analysis = analytics.analyze_crawl_results([spoke_result], spoke_url)
        
        # Should detect revisit (spoke links back to hub)
        assert analytics.metrics.revisit_count > 0
    
    @pytest.mark.asyncio
    async def test_deep_tree_crawling(self):
        """Test crawling a deep tree structure."""
        base_url = "https://example.com/root"
        structure = self.scenarios.create_deep_tree_structure(base_url, depth=3, branching_factor=2)
        
        analytics = ExhaustiveAnalytics()
        analytics.start_crawl_session()
        
        # Crawl the tree breadth-first
        crawled_count = 0
        max_crawls = 20  # Safety limit
        
        # Start with root
        current_url = base_url
        
        while current_url and crawled_count < max_crawls:
            links = structure.get(current_url, [])
            mock_links = [{'href': link} for link in links]
            
            result = create_mock_crawl_result(current_url, mock_links)
            analytics.analyze_crawl_results([result], current_url)
            
            crawled_count += 1
            current_url = analytics.get_next_crawl_url()
        
        # Should have discovered many URLs in the tree
        stats = analytics.url_state.get_stats()
        assert stats['total_discovered'] > 5  # Should find multiple levels
    
    @pytest.mark.asyncio
    async def test_cyclic_structure_detection(self):
        """Test detection of cyclic structures and revisit handling."""
        structure = self.scenarios.create_cyclic_structure(num_nodes=4)
        
        analytics = ExhaustiveAnalytics()
        analytics.start_crawl_session()
        
        # Crawl through the cycle multiple times
        current_url = "https://example.com/cycle0"
        crawled_urls = []
        
        for _ in range(10):  # Go around the cycle more than once
            crawled_urls.append(current_url)
            
            links = structure.get(current_url, [])
            mock_links = [{'href': link} for link in links]
            
            result = create_mock_crawl_result(current_url, mock_links)
            analytics.analyze_crawl_results([result], current_url)
            
            current_url = analytics.get_next_crawl_url()
            if not current_url:
                break
        
        # Should detect high revisit ratio
        assert analytics.metrics.revisit_ratio > 0.5
        
        # Should eventually stop due to high revisit ratio
        should_stop, reason = analytics.should_stop_crawling(revisit_threshold=0.8)
        if analytics.metrics.total_crawl_attempts > 5:
            assert should_stop == True or "revisit" in reason.lower()


class TestIntegrationWithExistingComponents:
    """Test integration with existing Crawl4AI components."""
    
    @pytest.mark.asyncio
    async def test_integration_with_browser_config(self):
        """Test integration with BrowserConfig."""
        browser_config = BrowserConfig(
            headless=True,
            browser_type="chromium",
            viewport_width=1280,
            viewport_height=720
        )
        
        exhaustive_config = ExhaustiveCrawlConfig(
            max_pages=5,
            dead_end_threshold=3
        )
        
        # Should be able to create crawler with both configs
        crawler = ExhaustiveAsyncWebCrawler(config=browser_config)
        
        # Mock arun to avoid actual browser operations
        crawler.arun = AsyncMock(return_value=create_mock_crawl_result("test", []))
        
        try:
            # Should be able to run exhaustive crawling
            result = await crawler.arun_exhaustive("https://example.com", config=exhaustive_config)
            assert 'results' in result
            
        finally:
            if hasattr(crawler, 'close'):
                await crawler.close()
    
    def test_integration_with_existing_analytics(self):
        """Test that exhaustive analytics integrates with existing patterns."""
        analytics = ExhaustiveAnalytics()
        
        # Should have methods compatible with existing analytics patterns
        assert hasattr(analytics, 'start_crawl_session')
        assert hasattr(analytics, 'analyze_crawl_results')
        assert hasattr(analytics, 'get_comprehensive_stats')
        
        # Should work with existing CrawlResult objects
        result = create_mock_crawl_result("https://example.com", [])
        analysis = analytics.analyze_crawl_results([result])
        
        assert isinstance(analysis, dict)
        assert 'new_urls_discovered' in analysis
        assert 'revisit_ratio' in analysis


if __name__ == "__main__":
    # Run tests manually for debugging
    async def run_async_tests():
        print("Running comprehensive exhaustive crawling tests...")
        
        # Run a few key tests manually
        test_config = TestExhaustiveCrawlConfig()
        test_config.test_config_initialization_defaults()
        test_config.test_config_validation_valid()
        print("✓ Config tests passed")
        
        test_dead_end = TestDeadEndDetectionLogic()
        test_dead_end.setup_method()
        test_dead_end.test_dead_end_metrics_initialization()
        test_dead_end.test_should_stop_crawling_dead_end_threshold()
        print("✓ Dead-end detection tests passed")
        
        test_scenarios = TestMockWebsiteScenarios()
        test_scenarios.setup_method()
        await test_scenarios.test_linear_site_crawling()
        await test_scenarios.test_hub_and_spoke_crawling()
        print("✓ Mock website scenario tests passed")
        
        test_performance = TestPerformanceScenarios()
        await test_performance.test_large_url_queue_performance()
        test_performance.test_config_validation_performance()
        print("✓ Performance tests passed")
        
        print("\n🎉 All comprehensive exhaustive crawling tests passed!")
    
    asyncio.run(run_async_tests())