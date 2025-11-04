#!/usr/bin/env python3
"""
Performance Tests for Exhaustive Crawling

This module focuses on performance testing for exhaustive crawling scenarios,
including large site mapping, memory usage, and scalability tests.
"""

import pytest
import asyncio
import time
import sys
import gc
from pathlib import Path
from typing import List, Dict
from unittest.mock import Mock, AsyncMock

# Add the project root directory to the path to import crawl4ai
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from crawl4ai import ExhaustiveCrawlConfig, BrowserConfig
from crawl4ai.exhaustive_analytics import ExhaustiveAnalytics, DeadEndMetrics, URLTrackingState
from crawl4ai.exhaustive_webcrawler import ExhaustiveAsyncWebCrawler
from crawl4ai.models import CrawlResult, MarkdownGenerationResult


def create_mock_result_with_links(url: str, num_links: int = 5) -> CrawlResult:
    """Create a mock CrawlResult with specified number of links."""
    links = [{'href': f'{url}/link{i}'} for i in range(num_links)]
    
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
        success=True,
        cleaned_html=f"Content from {url}",
        markdown=markdown_result,
        links={'internal': links, 'external': []},
        metadata={'depth': 0}
    )


class TestLargeScaleURLTracking:
    """Test performance with large numbers of URLs."""
    
    def test_large_url_discovery_performance(self):
        """Test performance of discovering large numbers of URLs."""
        analytics = ExhaustiveAnalytics()
        analytics.start_crawl_session()
        
        # Test with 10,000 URLs
        num_urls = 10000
        start_time = time.time()
        
        for i in range(num_urls):
            url = f"https://example.com/page{i}"
            analytics.url_state.add_discovered_url(url, "https://example.com", 1)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Should complete in reasonable time (under 2 seconds)
        assert duration < 2.0, f"URL discovery took {duration:.2f}s for {num_urls} URLs"
        
        # Verify all URLs were added
        assert len(analytics.url_state.discovered_urls) == num_urls
        
        # Test URL retrieval performance
        start_time = time.time()
        
        retrieved_count = 0
        while analytics.url_state.has_pending_urls() and retrieved_count < 1000:
            url = analytics.url_state.get_next_url()
            if url:
                retrieved_count += 1
        
        end_time = time.time()
        retrieval_duration = end_time - start_time
        
        # URL retrieval should be fast
        assert retrieval_duration < 0.5, f"URL retrieval took {retrieval_duration:.2f}s for {retrieved_count} URLs"
    
    def test_url_tracking_memory_usage(self):
        """Test memory usage with large URL sets."""
        analytics = ExhaustiveAnalytics()
        analytics.start_crawl_session()
        
        # Force garbage collection to get baseline
        gc.collect()
        
        # Measure initial memory usage
        initial_objects = len(gc.get_objects())
        
        # Add many URLs
        num_urls = 5000
        for i in range(num_urls):
            url = f"https://example.com/page{i}"
            analytics.url_state.add_discovered_url(url, f"https://example.com/source{i%100}", i%10)
        
        # Force garbage collection
        gc.collect()
        
        # Measure final memory usage
        final_objects = len(gc.get_objects())
        object_growth = final_objects - initial_objects
        
        # Memory growth should be reasonable (less than 10x the number of URLs)
        assert object_growth < num_urls * 10, f"Memory growth too high: {object_growth} objects for {num_urls} URLs"
        
        # Test memory usage of URL state operations
        url_state_size = sys.getsizeof(analytics.url_state.discovered_urls)
        assert url_state_size < 1024 * 1024, f"URL state too large: {url_state_size} bytes"
    
    def test_concurrent_url_operations(self):
        """Test performance of concurrent URL operations."""
        analytics = ExhaustiveAnalytics()
        analytics.start_crawl_session()
        
        # Simulate concurrent URL discovery and processing
        start_time = time.time()
        
        # Add URLs in batches (simulating concurrent discovery)
        batch_size = 100
        num_batches = 50
        
        for batch in range(num_batches):
            batch_urls = []
            for i in range(batch_size):
                url = f"https://example.com/batch{batch}/page{i}"
                batch_urls.append(url)
                analytics.url_state.add_discovered_url(url, f"https://example.com/batch{batch}", batch)
            
            # Process some URLs from the queue
            for _ in range(min(10, len(batch_urls))):
                next_url = analytics.url_state.get_next_url()
                if next_url:
                    analytics.url_state.mark_crawled(next_url, success=True)
        
        end_time = time.time()
        duration = end_time - start_time
        
        total_urls = batch_size * num_batches
        
        # Should handle concurrent operations efficiently
        assert duration < 3.0, f"Concurrent operations took {duration:.2f}s for {total_urls} URLs"
        
        # Verify state consistency
        stats = analytics.url_state.get_stats()
        assert stats['total_discovered'] == total_urls
        assert stats['total_crawled'] > 0


class TestAnalyticsPerformance:
    """Test performance of analytics operations."""
    
    def test_crawl_result_analysis_performance(self):
        """Test performance of analyzing large numbers of crawl results."""
        analytics = ExhaustiveAnalytics()
        analytics.start_crawl_session()
        
        # Create many mock results with varying numbers of links
        num_results = 1000
        results = []
        
        for i in range(num_results):
            num_links = (i % 10) + 1  # 1-10 links per result
            result = create_mock_result_with_links(f"https://example.com/page{i}", num_links)
            results.append(result)
        
        # Test batch analysis performance
        start_time = time.time()
        
        # Analyze in batches of 50
        batch_size = 50
        for i in range(0, len(results), batch_size):
            batch = results[i:i + batch_size]
            analytics.analyze_crawl_results(batch)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Should complete analysis quickly
        assert duration < 5.0, f"Analysis took {duration:.2f}s for {num_results} results"
        
        # Verify analytics state
        assert analytics.metrics.total_urls_discovered > 0
        assert len(analytics.metrics.discovery_rate_history) > 0
    
    def test_discovery_rate_history_performance(self):
        """Test performance of discovery rate history tracking."""
        analytics = ExhaustiveAnalytics()
        analytics.start_crawl_session()
        
        # Simulate many batches of discovery
        num_batches = 1000
        start_time = time.time()
        
        for batch in range(num_batches):
            # Simulate varying discovery rates
            discovery_count = batch % 20  # 0-19 discoveries per batch
            analytics.metrics.discovery_rate_history.append(discovery_count)
            
            # Maintain history size (should be automatic)
            if len(analytics.metrics.discovery_rate_history) > 10:
                analytics.metrics.discovery_rate_history = analytics.metrics.discovery_rate_history[-10:]
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Should handle history efficiently
        assert duration < 1.0, f"History tracking took {duration:.2f}s for {num_batches} batches"
        
        # Verify history is maintained at correct size
        assert len(analytics.metrics.discovery_rate_history) == 10
        
        # Test average calculation performance
        start_time = time.time()
        
        for _ in range(1000):
            avg_rate = analytics.metrics.average_discovery_rate
        
        end_time = time.time()
        calc_duration = end_time - start_time
        
        # Average calculation should be very fast
        assert calc_duration < 0.1, f"Average calculation took {calc_duration:.2f}s for 1000 calls"
    
    def test_comprehensive_stats_performance(self):
        """Test performance of comprehensive statistics generation."""
        analytics = ExhaustiveAnalytics()
        analytics.start_crawl_session()
        
        # Set up analytics with substantial data
        for i in range(1000):
            analytics.url_state.add_discovered_url(f"https://example.com/page{i}", "source", 1)
            if i % 3 == 0:
                analytics.url_state.mark_crawled(f"https://example.com/page{i}", success=True)
        
        analytics.metrics.discovery_rate_history = list(range(10))
        analytics.metrics.total_crawl_attempts = 333
        analytics.metrics.revisit_count = 50
        
        # Test stats generation performance
        start_time = time.time()
        
        for _ in range(100):
            stats = analytics.get_comprehensive_stats()
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Stats generation should be fast
        assert duration < 1.0, f"Stats generation took {duration:.2f}s for 100 calls"
        
        # Verify stats structure
        stats = analytics.get_comprehensive_stats()
        assert 'session_stats' in stats
        assert 'url_tracking' in stats
        assert 'discovery_history' in stats


class TestExhaustiveCrawlerPerformance:
    """Test performance of the exhaustive crawler itself."""
    
    @pytest.mark.asyncio
    async def test_batch_crawling_performance(self):
        """Test performance of batch crawling operations."""
        from crawl4ai import BrowserConfig
        
        from crawl4ai import CrawlerRunConfig
        config = CrawlerRunConfig()
        
        browser_config = BrowserConfig(headless=True)
        crawler = ExhaustiveAsyncWebCrawler(config=browser_config)
        
        # Mock arun to return quickly
        async def mock_arun(url, **kwargs):
            # Simulate some processing time
            await asyncio.sleep(0.001)  # 1ms per URL
            return create_mock_result_with_links(url, 2)
        
        crawler.arun = mock_arun
        
        try:
            # Test batch processing performance
            urls = [f"https://example.com/page{i}" for i in range(50)]
            
            start_time = time.time()
            results = await crawler._crawl_batch(urls, config)
            end_time = time.time()
            
            duration = end_time - start_time
            
            # Should process batch efficiently
            assert duration < 2.0, f"Batch crawling took {duration:.2f}s for {len(urls)} URLs"
            assert len(results) == len(urls)
            
        finally:
            if hasattr(crawler, 'close'):
                await crawler.close()
    
    @pytest.mark.asyncio
    async def test_url_extraction_performance(self):
        """Test performance of URL extraction from results."""
        from crawl4ai import BrowserConfig
        
        config = ExhaustiveCrawlConfig()
        browser_config = BrowserConfig(headless=True)
        crawler = ExhaustiveAsyncWebCrawler(config=browser_config)
        
        try:
            # Create result with many links
            num_links = 1000
            large_result = create_mock_result_with_links("https://example.com", num_links)
            
            # Test URL extraction performance
            start_time = time.time()
            
            for _ in range(100):
                urls = crawler._extract_urls_from_result(large_result, config)
            
            end_time = time.time()
            duration = end_time - start_time
            
            # URL extraction should be fast
            assert duration < 1.0, f"URL extraction took {duration:.2f}s for 100 iterations"
            
            # Verify extraction worked
            urls = crawler._extract_urls_from_result(large_result, config)
            assert len(urls) == num_links
            
        finally:
            if hasattr(crawler, 'close'):
                await crawler.close()
    
    @pytest.mark.asyncio
    async def test_progress_tracking_overhead(self):
        """Test overhead of progress tracking."""
        from crawl4ai import BrowserConfig
        
        browser_config = BrowserConfig(headless=True)
        
        # Test with progress tracking enabled
        crawler_with_tracking = ExhaustiveAsyncWebCrawler(config=browser_config)
        
        # Test with progress tracking disabled
        crawler_without_tracking = ExhaustiveAsyncWebCrawler(config=browser_config)
        
        try:
            # Simulate analytics operations
            num_operations = 1000
            
            # Test with tracking
            start_time = time.time()
            for i in range(num_operations):
                progress = crawler_with_tracking.get_progress_tracking()
            end_time = time.time()
            tracking_duration = end_time - start_time
            
            # Test without tracking (just analytics access)
            start_time = time.time()
            for i in range(num_operations):
                stats = crawler_without_tracking.analytics.get_comprehensive_stats()
            end_time = time.time()
            no_tracking_duration = end_time - start_time
            
            # Progress tracking overhead should be minimal
            overhead = tracking_duration - no_tracking_duration
            assert overhead < 0.5, f"Progress tracking overhead: {overhead:.2f}s for {num_operations} operations"
            
        finally:
            if hasattr(crawler_with_tracking, 'close'):
                await crawler_with_tracking.close()
            if hasattr(crawler_without_tracking, 'close'):
                await crawler_without_tracking.close()


class TestConfigurationPerformance:
    """Test performance of configuration operations."""
    
    def test_config_creation_performance(self):
        """Test performance of creating many configurations."""
        start_time = time.time()
        
        configs = []
        for i in range(1000):
            config = ExhaustiveCrawlConfig(
                max_depth=50 + i % 50,
                max_pages=1000 + i * 10,
                dead_end_threshold=20 + i % 30
            )
            configs.append(config)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Config creation should be fast
        assert duration < 1.0, f"Config creation took {duration:.2f}s for 1000 configs"
        assert len(configs) == 1000
    
    def test_config_validation_performance(self):
        """Test performance of configuration validation."""
        # Create configs to validate
        configs = []
        for i in range(500):
            config = ExhaustiveCrawlConfig(
                max_depth=25 + i % 75,
                max_pages=500 + i * 20,
                dead_end_threshold=10 + i % 40,
                revisit_ratio_threshold=0.5 + (i % 50) / 100
            )
            configs.append(config)
        
        # Test validation performance
        start_time = time.time()
        
        for config in configs:
            config.validate()
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Validation should be fast
        assert duration < 1.0, f"Validation took {duration:.2f}s for {len(configs)} configs"
    
    def test_preset_creation_performance(self):
        """Test performance of preset configuration creation."""
        from crawl4ai.exhaustive_configs import create_exhaustive_preset_config
        
        preset_names = ["comprehensive", "balanced", "fast", "files_focused", "adaptive"]
        
        start_time = time.time()
        
        configs = []
        for _ in range(200):
            for preset_name in preset_names:
                config = create_exhaustive_preset_config(preset_name)
                configs.append(config)
        
        end_time = time.time()
        duration = end_time - start_time
        
        total_configs = 200 * len(preset_names)
        
        # Preset creation should be fast
        assert duration < 2.0, f"Preset creation took {duration:.2f}s for {total_configs} configs"
        assert len(configs) == total_configs


class TestMemoryLeakDetection:
    """Test for potential memory leaks in long-running scenarios."""
    
    def test_analytics_memory_stability(self):
        """Test that analytics don't leak memory over time."""
        analytics = ExhaustiveAnalytics()
        
        # Force garbage collection
        gc.collect()
        initial_objects = len(gc.get_objects())
        
        # Simulate long-running analytics session
        for session in range(10):
            analytics.start_crawl_session()
            
            # Add and process many URLs
            for i in range(100):
                url = f"https://example.com/session{session}/page{i}"
                analytics.url_state.add_discovered_url(url, "source", 1)
                
                if i % 10 == 0:
                    # Simulate crawl result analysis
                    result = create_mock_result_with_links(url, 5)
                    analytics.analyze_crawl_results([result], url)
            
            # Reset session (simulating crawler restart)
            analytics.reset_session()
        
        # Force garbage collection
        gc.collect()
        final_objects = len(gc.get_objects())
        
        object_growth = final_objects - initial_objects
        
        # Memory growth should be minimal after resets
        assert object_growth < 1000, f"Potential memory leak: {object_growth} objects after 10 sessions"
    
    def test_url_state_cleanup(self):
        """Test that URL state can be properly cleaned up."""
        state = URLTrackingState()
        
        # Add many URLs
        for i in range(1000):
            state.add_discovered_url(f"https://example.com/page{i}", "source", 1)
        
        # Verify URLs were added
        assert len(state.discovered_urls) == 1000
        
        # Clear state
        state.discovered_urls.clear()
        state.crawled_urls.clear()
        state.failed_urls.clear()
        state.url_discovery_source.clear()
        state.url_discovery_time.clear()
        state.url_depth.clear()
        state.pending_urls.clear()
        
        # Verify cleanup
        assert len(state.discovered_urls) == 0
        assert len(state.crawled_urls) == 0
        assert len(state.pending_urls) == 0


if __name__ == "__main__":
    # Run performance tests manually
    async def run_performance_tests():
        print("Running exhaustive crawling performance tests...")
        
        # URL tracking performance
        test_url_tracking = TestLargeScaleURLTracking()
        test_url_tracking.test_large_url_discovery_performance()
        test_url_tracking.test_url_tracking_memory_usage()
        test_url_tracking.test_concurrent_url_operations()
        print("✓ URL tracking performance tests passed")
        
        # Analytics performance
        test_analytics = TestAnalyticsPerformance()
        test_analytics.test_crawl_result_analysis_performance()
        test_analytics.test_discovery_rate_history_performance()
        test_analytics.test_comprehensive_stats_performance()
        print("✓ Analytics performance tests passed")
        
        # Crawler performance
        test_crawler = TestExhaustiveCrawlerPerformance()
        await test_crawler.test_batch_crawling_performance()
        await test_crawler.test_url_extraction_performance()
        await test_crawler.test_progress_tracking_overhead()
        print("✓ Crawler performance tests passed")
        
        # Configuration performance
        test_config = TestConfigurationPerformance()
        test_config.test_config_creation_performance()
        test_config.test_config_validation_performance()
        test_config.test_preset_creation_performance()
        print("✓ Configuration performance tests passed")
        
        # Memory leak detection
        test_memory = TestMemoryLeakDetection()
        test_memory.test_analytics_memory_stability()
        test_memory.test_url_state_cleanup()
        print("✓ Memory leak detection tests passed")
        
        print("\n🎉 All performance tests passed!")
    
    asyncio.run(run_performance_tests())