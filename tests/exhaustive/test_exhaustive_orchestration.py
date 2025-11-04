"""
Test suite for exhaustive crawling orchestration functionality.

This module tests the arun_exhaustive method and related orchestration features
including URL queue management, dead-end detection, and progress tracking.
"""

import pytest
import asyncio
import sys
from pathlib import Path

# Add the project root directory to the path to import crawl4ai
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from crawl4ai import BrowserConfig
from crawl4ai.exhaustive_webcrawler import ExhaustiveAsyncWebCrawler
from crawl4ai import ExhaustiveCrawlConfig, create_exhaustive_preset_config


@pytest.mark.asyncio
async def test_basic_exhaustive_orchestration():
    """Test basic exhaustive crawling orchestration functionality."""
    
    # Create configuration for testing
    config = ExhaustiveCrawlConfig(
        dead_end_threshold=3,  # Low threshold for quick testing
        revisit_ratio_threshold=0.80,
        max_pages=10
    )
    
    # Add orchestration parameters
    config.batch_size = 2
    config.continue_on_dead_ends = True
    config.log_discovery_stats = False  # Reduce test noise
    
    # Create crawler
    browser_config = BrowserConfig(headless=True)
    crawler = ExhaustiveAsyncWebCrawler(config=browser_config)
    
    try:
        # Test HTML with links
        test_html = """
        <html>
        <head><title>Test Page</title></head>
        <body>
            <h1>Test Hub</h1>
            <a href="https://example.com/page1">Page 1</a>
            <a href="https://example.com/page2">Page 2</a>
            <a href="https://example.com/page3">Page 3</a>
        </body>
        </html>
        """
        
        # Run exhaustive crawling
        result = await crawler.arun_exhaustive(f"raw:{test_html}", config=config)
        
        # Verify basic results structure
        assert 'results' in result
        assert 'analytics' in result
        assert 'stop_reason' in result
        assert 'total_pages_crawled' in result
        assert 'successful_pages' in result
        assert 'total_urls_discovered' in result
        
        # Verify we crawled some pages
        assert result['total_pages_crawled'] > 0
        assert result['successful_pages'] > 0
        assert result['total_urls_discovered'] >= 3  # At least the 3 links we provided
        
        # Verify analytics structure
        analytics = result['analytics']
        assert 'session_stats' in analytics
        assert 'url_tracking' in analytics
        
        # Verify session stats
        session_stats = analytics['session_stats']
        assert 'crawl_duration' in session_stats
        assert 'total_crawl_attempts' in session_stats
        assert 'total_urls_discovered' in session_stats
        
        # Verify URL tracking
        url_tracking = analytics['url_tracking']
        assert 'total_discovered' in url_tracking
        assert 'total_crawled' in url_tracking
        assert 'success_rate' in url_tracking
        
        return True
        
    finally:
        if hasattr(crawler, 'close'):
            await crawler.close()


@pytest.mark.asyncio
async def test_dead_end_detection():
    """Test that dead-end detection stops crawling appropriately."""
    
    # Configuration with very low dead-end threshold
    config = ExhaustiveCrawlConfig(
        dead_end_threshold=2,  # Stop after 2 consecutive dead pages
        revisit_ratio_threshold=0.95,
        max_pages=20
    )
    
    config.batch_size = 1
    config.log_discovery_stats = False
    
    browser_config = BrowserConfig(headless=True)
    crawler = ExhaustiveAsyncWebCrawler(config=browser_config)
    
    try:
        # HTML with no additional links (should hit dead end quickly)
        dead_end_html = """
        <html>
        <head><title>Dead End</title></head>
        <body>
            <h1>No Links Here</h1>
            <p>This page has no outbound links.</p>
        </body>
        </html>
        """
        
        result = await crawler.arun_exhaustive(f"raw:{dead_end_html}", config=config)
        
        # Should stop due to dead end
        assert "dead end" in result['stop_reason'].lower() or "no more urls" in result['stop_reason'].lower()
        
        # Should have crawled minimal pages
        assert result['total_pages_crawled'] <= 5
        
        # Analytics should show dead-end detection
        analytics = result['analytics']
        session_stats = analytics['session_stats']
        # The consecutive_dead_pages might be less than threshold if stopped for other reasons
        assert session_stats['consecutive_dead_pages'] >= 1
        
        return True
        
    finally:
        if hasattr(crawler, 'close'):
            await crawler.close()


@pytest.mark.asyncio
async def test_url_queue_management():
    """Test URL queue management during orchestration."""
    
    config = ExhaustiveCrawlConfig(
        dead_end_threshold=5,
        revisit_ratio_threshold=0.90,
        max_pages=15
    )
    
    config.batch_size = 3  # Process multiple URLs per batch
    config.log_discovery_stats = False
    
    browser_config = BrowserConfig(headless=True)
    crawler = ExhaustiveAsyncWebCrawler(config=browser_config)
    
    try:
        # HTML with multiple levels of links
        multi_level_html = """
        <html>
        <head><title>Multi-Level Site</title></head>
        <body>
            <h1>Root Page</h1>
            <div class="nav">
                <a href="https://example.com/section1">Section 1</a>
                <a href="https://example.com/section2">Section 2</a>
                <a href="https://example.com/section3">Section 3</a>
                <a href="https://example.com/section4">Section 4</a>
            </div>
        </body>
        </html>
        """
        
        result = await crawler.arun_exhaustive(f"raw:{multi_level_html}", config=config)
        
        # Verify URL discovery and queue processing
        assert result['total_urls_discovered'] >= 4  # At least the 4 sections
        assert result['total_pages_crawled'] > 1     # Should crawl multiple pages
        
        # Check URL tracking details
        url_tracking = result['analytics']['url_tracking']
        assert url_tracking['total_discovered'] >= 4
        assert url_tracking['total_crawled'] >= 1
        assert url_tracking['success_rate'] > 0
        
        return True
        
    finally:
        if hasattr(crawler, 'close'):
            await crawler.close()


@pytest.mark.asyncio
async def test_progress_tracking():
    """Test progress tracking functionality during orchestration."""
    
    config = ExhaustiveCrawlConfig(
        dead_end_threshold=4,
        revisit_ratio_threshold=0.85,
        max_pages=12
    )
    
    config.batch_size = 2
    config.log_discovery_stats = False
    
    browser_config = BrowserConfig(headless=True)
    crawler = ExhaustiveAsyncWebCrawler(config=browser_config)
    
    try:
        test_html = """
        <html>
        <head><title>Progress Test</title></head>
        <body>
            <h1>Progress Tracking Test</h1>
            <a href="https://example.com/track1">Track 1</a>
            <a href="https://example.com/track2">Track 2</a>
        </body>
        </html>
        """
        
        result = await crawler.arun_exhaustive(f"raw:{test_html}", config=config)
        
        # Get progress tracking information
        progress = crawler.get_progress_tracking()
        
        # Verify progress tracking structure
        assert 'session_active' in progress
        assert 'crawl_duration' in progress
        assert 'pages_crawled' in progress
        assert 'urls_discovered' in progress
        assert 'urls_pending' in progress
        assert 'success_rate' in progress
        assert 'dead_end_status' in progress
        assert 'discovery_trend' in progress
        
        # Verify dead-end status structure
        dead_end_status = progress['dead_end_status']
        assert 'consecutive_dead_pages' in dead_end_status
        assert 'revisit_ratio' in dead_end_status
        assert 'average_discovery_rate' in dead_end_status
        
        # Session should be inactive after completion
        assert progress['session_active'] == False
        
        return True
        
    finally:
        if hasattr(crawler, 'close'):
            await crawler.close()


@pytest.mark.asyncio
async def test_exhaustive_config_presets():
    """Test exhaustive crawling with different configuration presets."""
    
    browser_config = BrowserConfig(headless=True)
    
    # Test with fast preset
    fast_config = create_exhaustive_preset_config("fast")
    fast_config.max_pages = 5  # Limit for testing
    
    crawler = ExhaustiveAsyncWebCrawler(config=browser_config)
    
    try:
        simple_html = """
        <html>
        <head><title>Preset Test</title></head>
        <body>
            <h1>Testing Presets</h1>
            <a href="https://example.com/preset1">Preset 1</a>
        </body>
        </html>
        """
        
        result = await crawler.arun_exhaustive(f"raw:{simple_html}", config=fast_config)
        
        # Should complete successfully with fast preset
        assert result['total_pages_crawled'] > 0
        assert result['successful_pages'] > 0
        assert 'stop_reason' in result
        
        return True
        
    finally:
        if hasattr(crawler, 'close'):
            await crawler.close()


@pytest.mark.asyncio
async def test_batch_processing():
    """Test batch processing functionality in orchestration."""
    
    config = ExhaustiveCrawlConfig(
        dead_end_threshold=6,
        revisit_ratio_threshold=0.90,
        max_pages=20
    )
    
    # Test different batch sizes
    config.batch_size = 4  # Larger batch size
    config.log_discovery_stats = False
    
    browser_config = BrowserConfig(headless=True)
    crawler = ExhaustiveAsyncWebCrawler(config=browser_config)
    
    try:
        batch_html = """
        <html>
        <head><title>Batch Test</title></head>
        <body>
            <h1>Batch Processing Test</h1>
            <a href="https://example.com/batch1">Batch 1</a>
            <a href="https://example.com/batch2">Batch 2</a>
            <a href="https://example.com/batch3">Batch 3</a>
            <a href="https://example.com/batch4">Batch 4</a>
            <a href="https://example.com/batch5">Batch 5</a>
        </body>
        </html>
        """
        
        result = await crawler.arun_exhaustive(f"raw:{batch_html}", config=config)
        
        # Should process multiple URLs
        assert result['total_urls_discovered'] >= 5
        assert result['total_pages_crawled'] > 1
        
        # Verify analytics captured batch processing
        analytics = result['analytics']
        assert analytics['session_stats']['total_crawl_attempts'] > 0
        
        return True
        
    finally:
        if hasattr(crawler, 'close'):
            await crawler.close()


def test_exhaustive_analytics_integration():
    """Test integration with ExhaustiveAnalytics."""
    
    browser_config = BrowserConfig(headless=True)
    crawler = ExhaustiveAsyncWebCrawler(config=browser_config)
    
    # Test analytics methods are available
    assert hasattr(crawler, 'analytics')
    assert hasattr(crawler, 'get_dead_end_metrics')
    assert hasattr(crawler, 'get_url_tracking_state')
    assert hasattr(crawler, 'get_exhaustive_stats')
    assert hasattr(crawler, 'get_progress_tracking')
    assert hasattr(crawler, 'reset_exhaustive_session')
    
    # Test analytics initialization
    assert crawler.analytics is not None
    
    # Test metrics objects
    metrics = crawler.get_dead_end_metrics()
    assert hasattr(metrics, 'consecutive_dead_pages')
    assert hasattr(metrics, 'revisit_ratio')
    
    url_state = crawler.get_url_tracking_state()
    assert hasattr(url_state, 'discovered_urls')
    assert hasattr(url_state, 'crawled_urls')


if __name__ == "__main__":
    # Run tests manually for debugging
    async def run_tests():
        print("Running exhaustive orchestration tests...")
        
        try:
            await test_basic_exhaustive_orchestration()
            print("✓ Basic orchestration test passed")
            
            await test_dead_end_detection()
            print("✓ Dead-end detection test passed")
            
            await test_url_queue_management()
            print("✓ URL queue management test passed")
            
            await test_progress_tracking()
            print("✓ Progress tracking test passed")
            
            await test_exhaustive_config_presets()
            print("✓ Config presets test passed")
            
            await test_batch_processing()
            print("✓ Batch processing test passed")
            
            test_exhaustive_analytics_integration()
            print("✓ Analytics integration test passed")
            
            print("\n🎉 All exhaustive orchestration tests passed!")
            
        except Exception as e:
            print(f"❌ Test failed: {e}")
            import traceback
            traceback.print_exc()
    
    asyncio.run(run_tests())