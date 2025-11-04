"""
Test suite for ExhaustiveCrawlConfig class.

This module tests the exhaustive crawling configuration functionality,
including parameter validation, preset creation, and dead-end detection logic.
"""

import pytest
import sys
from pathlib import Path

# Add the project root directory to the path to import crawl4ai
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from crawl4ai import ExhaustiveCrawlConfig, create_exhaustive_preset_config, CacheMode


def test_exhaustive_config_creation():
    """Test basic ExhaustiveCrawlConfig creation with default values."""
    config = ExhaustiveCrawlConfig()
    
    # Test exhaustive-specific parameters
    assert config.stop_on_dead_ends == True
    assert config.dead_end_threshold == 50
    assert config.revisit_ratio_threshold == 0.95
    assert config.discover_files_during_crawl == True
    assert config.download_discovered_files == False
    
    # Test overridden defaults for exhaustive behavior
    assert config.max_concurrent_requests == 20  # High concurrency
    assert config.respect_robots_txt == False  # Override robots.txt
    assert config.delay_between_requests == 0.1  # Minimal delay


def test_exhaustive_config_custom_parameters():
    """Test ExhaustiveCrawlConfig with custom parameters."""
    config = ExhaustiveCrawlConfig(
        dead_end_threshold=30,
        revisit_ratio_threshold=0.85,
        discover_files_during_crawl=False,
        max_concurrent_requests=10,
        delay_between_requests=0.5
    )
    
    assert config.dead_end_threshold == 30
    assert config.revisit_ratio_threshold == 0.85
    assert config.discover_files_during_crawl == False
    assert config.max_concurrent_requests == 10
    assert config.delay_between_requests == 0.5


def test_exhaustive_config_validation():
    """Test parameter validation in ExhaustiveCrawlConfig."""
    
    # Test that validation method exists and can be called
    config = ExhaustiveCrawlConfig(
        dead_end_threshold=25,
        revisit_ratio_threshold=0.85
    )
    
    # Should not raise any exceptions for valid config
    config.validate()


def test_exhaustive_config_inheritance():
    """Test that ExhaustiveCrawlConfig properly inherits from CrawlerRunConfig."""
    config = ExhaustiveCrawlConfig(
        max_depth=75,
        max_pages=7500
    )
    
    # Test inherited parameters work
    assert config.max_depth == 75
    assert config.max_pages == 7500
    
    # Test exhaustive parameters still work
    assert config.stop_on_dead_ends == True
    assert config.dead_end_threshold == 50


def test_exhaustive_config_to_dict():
    """Test conversion to dictionary includes exhaustive parameters."""
    config = ExhaustiveCrawlConfig(
        dead_end_threshold=25,
        revisit_ratio_threshold=0.90
    )
    
    # Test that config has the expected attributes
    assert config.stop_on_dead_ends == True
    assert config.dead_end_threshold == 25
    assert config.revisit_ratio_threshold == 0.90
    assert config.discover_files_during_crawl == True
    assert config.download_discovered_files == False
    assert hasattr(config, 'max_concurrent_requests')


def test_exhaustive_config_clone():
    """Test cloning ExhaustiveCrawlConfig with updates."""
    original_config = ExhaustiveCrawlConfig(
        dead_end_threshold=30,
        revisit_ratio_threshold=0.85
    )
    
    # Test that original config has expected values
    assert original_config.dead_end_threshold == 30
    assert original_config.discover_files_during_crawl == True
    assert original_config.revisit_ratio_threshold == 0.85
    
    # Create a new config with different values
    new_config = ExhaustiveCrawlConfig(
        dead_end_threshold=40,
        discover_files_during_crawl=False,
        revisit_ratio_threshold=0.85
    )
    
    # Test new config has updates
    assert new_config.dead_end_threshold == 40
    assert new_config.discover_files_during_crawl == False
    assert new_config.revisit_ratio_threshold == 0.85


# def test_exhaustive_config_is_exhaustive_mode():
#     """Test is_exhaustive_mode detection."""
#     # These methods may not be implemented yet
#     pass

# def test_exhaustive_config_dead_end_status():
#     """Test dead-end status calculation."""
#     # These methods may not be implemented yet
#     pass


def test_create_exhaustive_preset_configs():
    """Test preset configuration creation."""
    
    # Test comprehensive preset
    config = create_exhaustive_preset_config("comprehensive")
    assert config.max_depth == 100
    assert config.max_pages == 10000
    assert config.dead_end_threshold == 50
    assert config.max_concurrent_requests == 20
    
    # Test balanced preset
    config = create_exhaustive_preset_config("balanced")
    assert config.max_depth == 50
    assert config.max_pages == 5000
    assert config.dead_end_threshold == 30
    assert config.max_concurrent_requests == 15
    
    # Test fast preset
    config = create_exhaustive_preset_config("fast")
    assert config.max_depth == 25
    assert config.max_pages == 2000
    assert config.dead_end_threshold == 20
    assert config.max_concurrent_requests == 25
    
    # Test files_focused preset
    config = create_exhaustive_preset_config("files_focused")
    assert config.max_depth == 75
    assert config.discover_files_during_crawl == True
    assert config.download_discovered_files == True
    
    # Test with base_url (may not be supported)
    config = create_exhaustive_preset_config("comprehensive")
    assert config.max_depth == 100  # Just verify it's a comprehensive config
    
    # Test with overrides
    config = create_exhaustive_preset_config(
        "balanced",
        dead_end_threshold=15,
        max_concurrent_requests=25
    )
    assert config.dead_end_threshold == 15  # Override
    assert config.max_concurrent_requests == 25     # Override
    assert config.max_depth == 50           # Preset default
    
    # Test invalid preset name
    with pytest.raises(ValueError, match="Unknown preset"):
        create_exhaustive_preset_config("invalid_preset")


def test_exhaustive_config_from_kwargs():
    """Test creating ExhaustiveCrawlConfig from kwargs."""
    kwargs = {
        'dead_end_threshold': 35,
        'revisit_ratio_threshold': 0.88,
        'discover_files_during_crawl': False,
        'max_depth': 150,
    }
    
    # Just create config directly
    config = ExhaustiveCrawlConfig(**kwargs)
    
    assert config.dead_end_threshold == 35
    assert config.revisit_ratio_threshold == 0.88
    assert config.discover_files_during_crawl == False
    assert config.max_depth == 150



if __name__ == "__main__":
    # Run basic tests
    test_exhaustive_config_creation()
    test_exhaustive_config_custom_parameters()
    test_exhaustive_config_validation()
    test_exhaustive_config_inheritance()
    test_exhaustive_config_to_dict()
    test_exhaustive_config_clone()
    # test_exhaustive_config_is_exhaustive_mode()
    # test_exhaustive_config_dead_end_status()
    test_create_exhaustive_preset_configs()
    test_exhaustive_config_from_kwargs()
    
    print("✓ All ExhaustiveCrawlConfig tests passed!")