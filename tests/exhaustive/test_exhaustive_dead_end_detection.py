#!/usr/bin/env python3
"""
Test script for exhaustive crawling dead-end detection functionality.

This script tests the implementation of task 3: dead-end detection using existing AsyncWebCrawler analytics.
"""

import asyncio
import sys
import os

# Add the crawl4ai directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'crawl4ai'))

from crawl4ai.exhaustive_analytics import ExhaustiveAnalytics, DeadEndMetrics, URLTrackingState
from crawl4ai.exhaustive_webcrawler import ExhaustiveAsyncWebCrawler, ExhaustiveCrawlConfig
from crawl4ai.exhaustive_integration import configure_exhaustive_crawler, analyze_url_discovery_rate
from crawl4ai.models import CrawlResult, MarkdownGenerationResult
from crawl4ai.async_logger import AsyncLogger


def create_mock_crawl_result(url: str, links: list = None, success: bool = True) -> CrawlResult:
    """Create a mock CrawlResult for testing."""
    links = links or []
    
    # Create mock markdown result
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


async def test_dead_end_metrics():
    """Test DeadEndMetrics functionality."""
    print("Testing DeadEndMetrics...")
    
    metrics = DeadEndMetrics()
    
    # Test initial state
    assert metrics.consecutive_dead_pages == 0
    assert metrics.total_urls_discovered == 0
    assert metrics.revisit_ratio == 0.0
    
    # Test metrics updates
    metrics.consecutive_dead_pages = 5
    metrics.total_crawl_attempts = 10
    metrics.revisit_count = 3
    
    assert metrics.revisit_ratio == 0.3
    
    # Test discovery rate history
    metrics.discovery_rate_history = [5, 3, 2, 1, 0]
    assert metrics.average_discovery_rate == 2.2
    
    print("✓ DeadEndMetrics tests passed")


async def test_url_tracking_state():
    """Test URLTrackingState functionality."""
    print("Testing URLTrackingState...")
    
    state = URLTrackingState()
    
    # Test URL discovery
    is_new = state.add_discovered_url("https://example.com/page1", "https://example.com", 1)
    assert is_new == True
    assert "https://example.com/page1" in state.discovered_urls
    
    # Test duplicate URL
    is_new = state.add_discovered_url("https://example.com/page1", "https://example.com", 1)
    assert is_new == False
    
    # Test URL crawling
    state.mark_crawled("https://example.com/page1", success=True)
    assert "https://example.com/page1" in state.crawled_urls
    
    # Test queue operations
    state.add_discovered_url("https://example.com/page2", "https://example.com/page1", 2)
    next_url = state.get_next_url()
    assert next_url == "https://example.com/page2"
    
    # Test statistics
    stats = state.get_stats()
    assert stats['total_discovered'] == 2
    assert stats['total_crawled'] == 1
    
    print("✓ URLTrackingState tests passed")


async def test_exhaustive_analytics():
    """Test ExhaustiveAnalytics functionality."""
    print("Testing ExhaustiveAnalytics...")
    
    logger = AsyncLogger(verbose=True)
    analytics = ExhaustiveAnalytics(logger=logger)
    
    # Start session
    analytics.start_crawl_session()
    assert analytics.metrics.crawl_start_time is not None
    
    # Test with results that have new URLs
    results_with_links = [
        create_mock_crawl_result("https://example.com", [
            {'href': 'https://example.com/page1'},
            {'href': 'https://example.com/page2'}
        ])
    ]
    
    analysis = analytics.analyze_crawl_results(results_with_links, "https://example.com")
    assert analysis['new_urls_discovered'] == 2
    assert analysis['consecutive_dead_pages'] == 0
    
    # Test with results that have no new URLs (dead end)
    results_no_links = [create_mock_crawl_result("https://example.com/page1", [])]
    
    analysis = analytics.analyze_crawl_results(results_no_links, "https://example.com/page1")
    assert analysis['new_urls_discovered'] == 0
    assert analysis['consecutive_dead_pages'] == 1
    
    # Test dead-end detection
    # Simulate multiple dead pages
    for i in range(5):
        analytics.analyze_crawl_results([create_mock_crawl_result(f"https://example.com/dead{i}", [])], f"https://example.com/dead{i}")
    
    should_stop, reason = analytics.should_stop_crawling(dead_end_threshold=5)
    assert should_stop == True
    assert "dead end" in reason.lower()
    
    print("✓ ExhaustiveAnalytics tests passed")


async def test_exhaustive_webcrawler():
    """Test ExhaustiveAsyncWebCrawler functionality."""
    print("Testing ExhaustiveAsyncWebCrawler...")
    
    # Note: This is a basic test of the class structure
    # Full integration testing would require a running web server
    
    try:
        from crawl4ai.async_configs import BrowserConfig
        
        config = BrowserConfig(headless=True)
        crawler = ExhaustiveAsyncWebCrawler(config=config)
        
        # Test configuration
        exhaustive_config = ExhaustiveCrawlConfig(
            dead_end_threshold=10,
            revisit_ratio_threshold=0.8,
            max_pages=100
        )
        
        # Test analytics access
        metrics = crawler.get_dead_end_metrics()
        assert isinstance(metrics, DeadEndMetrics)
        
        url_state = crawler.get_url_tracking_state()
        assert isinstance(url_state, URLTrackingState)
        
        # Test revisit ratio calculation
        ratio = crawler.calculate_revisit_ratio()
        assert isinstance(ratio, float)
        assert 0.0 <= ratio <= 1.0
        
        print("✓ ExhaustiveAsyncWebCrawler tests passed")
        
    except ImportError as e:
        print(f"⚠ Skipping ExhaustiveAsyncWebCrawler test due to import error: {e}")


async def test_integration_functions():
    """Test integration utility functions."""
    print("Testing integration functions...")
    
    # Test analyze_url_discovery_rate function
    results = [
        create_mock_crawl_result("https://example.com", [
            {'href': 'https://example.com/page1'},
            {'href': 'https://example.com/page2'}
        ])
    ]
    
    analysis = analyze_url_discovery_rate(results)
    assert 'new_urls_discovered' in analysis
    assert 'consecutive_dead_pages' in analysis
    assert 'revisit_ratio' in analysis
    
    print("✓ Integration function tests passed")


async def main():
    """Run all tests."""
    print("Running exhaustive crawling dead-end detection tests...\n")
    
    try:
        await test_dead_end_metrics()
        await test_url_tracking_state()
        await test_exhaustive_analytics()
        await test_exhaustive_webcrawler()
        await test_integration_functions()
        
        print("\n🎉 All tests passed! Dead-end detection implementation is working correctly.")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)