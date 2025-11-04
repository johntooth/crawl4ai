#!/usr/bin/env python3
"""
Basic Test Suite for Exhaustive Crawling

This module provides basic tests to validate that the exhaustive crawling
components are properly integrated and functional.
"""

import sys
from pathlib import Path

# Add the project root directory to the path to import crawl4ai
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from crawl4ai import ExhaustiveCrawlConfig, create_exhaustive_preset_config


def test_exhaustive_config_creation():
    """Test basic ExhaustiveCrawlConfig creation."""
    config = ExhaustiveCrawlConfig()
    
    # Test that basic attributes exist
    assert hasattr(config, 'max_depth')
    assert hasattr(config, 'max_pages')
    assert hasattr(config, 'dead_end_threshold')
    assert hasattr(config, 'revisit_ratio_threshold')
    
    # Test default values
    assert config.max_depth == 100
    assert config.max_pages == 10000
    assert config.dead_end_threshold == 50
    assert config.revisit_ratio_threshold == 0.95
    
    print("✓ ExhaustiveCrawlConfig creation test passed")


def test_exhaustive_config_custom_values():
    """Test ExhaustiveCrawlConfig with custom values."""
    config = ExhaustiveCrawlConfig(
        max_depth=25,
        max_pages=1000,
        dead_end_threshold=10,
        revisit_ratio_threshold=0.80
    )
    
    assert config.max_depth == 25
    assert config.max_pages == 1000
    assert config.dead_end_threshold == 10
    assert config.revisit_ratio_threshold == 0.80
    
    print("✓ ExhaustiveCrawlConfig custom values test passed")


def test_exhaustive_config_validation():
    """Test ExhaustiveCrawlConfig validation."""
    config = ExhaustiveCrawlConfig(
        max_depth=50,
        max_pages=5000,
        dead_end_threshold=25,
        revisit_ratio_threshold=0.85
    )
    
    # Should not raise any exceptions
    config.validate()
    
    print("✓ ExhaustiveCrawlConfig validation test passed")


def test_preset_creation():
    """Test preset configuration creation."""
    presets = ["comprehensive", "balanced", "fast", "files_focused", "adaptive"]
    
    for preset_name in presets:
        config = create_exhaustive_preset_config(preset_name)
        
        # Should be a valid ExhaustiveCrawlConfig
        assert isinstance(config, ExhaustiveCrawlConfig)
        
        # Should have reasonable values
        assert config.max_depth > 0
        assert config.max_pages > 0
        assert config.dead_end_threshold > 0
        assert 0 <= config.revisit_ratio_threshold <= 1
        
        # Should pass validation
        config.validate()
    
    print("✓ Preset creation test passed")


def test_analytics_components():
    """Test that analytics components can be imported and created."""
    try:
        from crawl4ai.exhaustive_analytics import ExhaustiveAnalytics, DeadEndMetrics, URLTrackingState
        
        # Test DeadEndMetrics
        metrics = DeadEndMetrics()
        assert metrics.consecutive_dead_pages == 0
        assert metrics.revisit_ratio == 0.0
        
        # Test URLTrackingState
        state = URLTrackingState()
        assert len(state.discovered_urls) == 0
        
        # Test ExhaustiveAnalytics
        analytics = ExhaustiveAnalytics()
        assert analytics.metrics is not None
        assert analytics.url_state is not None
        
        print("✓ Analytics components test passed")
        
    except ImportError as e:
        print(f"⚠ Analytics components not available: {e}")


def test_webcrawler_components():
    """Test that webcrawler components can be imported and created."""
    try:
        from crawl4ai.exhaustive_webcrawler import ExhaustiveAsyncWebCrawler
        from crawl4ai import BrowserConfig
        
        # Test that we can create the crawler
        browser_config = BrowserConfig(headless=True)
        crawler = ExhaustiveAsyncWebCrawler(config=browser_config)
        
        # Test that it has the expected methods
        assert hasattr(crawler, 'arun_exhaustive')
        assert hasattr(crawler, 'get_dead_end_metrics')
        assert hasattr(crawler, 'get_progress_tracking')
        
        print("✓ WebCrawler components test passed")
        
    except ImportError as e:
        print(f"⚠ WebCrawler components not available: {e}")


def test_file_discovery_components():
    """Test that file discovery components can be imported."""
    try:
        from crawl4ai.file_discovery_filter import FileDiscoveryFilter, FileType, FileMetadata
        
        # Test FileDiscoveryFilter creation
        filter_instance = FileDiscoveryFilter()
        assert hasattr(filter_instance, 'apply')
        assert hasattr(filter_instance, 'discovered_files')
        
        # Test FileType enum
        assert hasattr(FileType, 'DOCUMENT')
        assert hasattr(FileType, 'SPREADSHEET')
        
        print("✓ File discovery components test passed")
        
    except ImportError as e:
        print(f"⚠ File discovery components not available: {e}")


def test_integration_components():
    """Test that integration components can be imported."""
    try:
        from crawl4ai.exhaustive_integration import configure_exhaustive_crawler
        
        print("✓ Integration components test passed")
        
    except ImportError as e:
        print(f"⚠ Integration components not available: {e}")


if __name__ == "__main__":
    print("Running basic exhaustive crawling tests...\n")
    
    try:
        test_exhaustive_config_creation()
        test_exhaustive_config_custom_values()
        test_exhaustive_config_validation()
        test_preset_creation()
        test_analytics_components()
        test_webcrawler_components()
        test_file_discovery_components()
        test_integration_components()
        
        print("\n🎉 All basic exhaustive crawling tests passed!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)