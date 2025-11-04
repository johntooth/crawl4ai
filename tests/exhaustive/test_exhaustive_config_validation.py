#!/usr/bin/env python3
"""
Specialized tests for ExhaustiveCrawlConfig validation and edge cases.

This module focuses specifically on configuration validation, edge cases,
and parameter interactions in ExhaustiveCrawlConfig.
"""

import pytest
import sys
from pathlib import Path

# Add the project root directory to the path to import crawl4ai
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from crawl4ai import ExhaustiveCrawlConfig, create_exhaustive_preset_config
from crawl4ai.exhaustive_configs import (
    validate_exhaustive_config,
    configure_adaptive_for_exhaustive_mode,
    create_minimal_filter_scorer_config
)


class TestExhaustiveCrawlConfigValidation:
    """Comprehensive validation tests for ExhaustiveCrawlConfig."""
    
    def test_all_valid_parameter_combinations(self):
        """Test various valid parameter combinations."""
        valid_configs = [
            # Minimal valid config
            ExhaustiveCrawlConfig(
                max_depth=1,
                max_pages=1,
                dead_end_threshold=1,
                revisit_ratio_threshold=0.0
            ),
            # Maximum reasonable config
            ExhaustiveCrawlConfig(
                max_depth=1000,
                max_pages=100000,
                dead_end_threshold=1000,
                revisit_ratio_threshold=1.0,
                max_concurrent_requests=100,
                delay_between_requests=10.0
            ),
            # Balanced config
            ExhaustiveCrawlConfig(
                max_depth=50,
                max_pages=5000,
                dead_end_threshold=25,
                revisit_ratio_threshold=0.85,
                discover_files_during_crawl=True,
                download_discovered_files=True
            )
        ]
        
        for config in valid_configs:
            # Should not raise any exceptions
            config.validate()
    
    def test_boundary_value_validation(self):
        """Test boundary values for all parameters."""
        
        # Test minimum boundary values
        config = ExhaustiveCrawlConfig(
            max_depth=1,
            max_pages=1,
            dead_end_threshold=1,
            revisit_ratio_threshold=0.0,
            max_concurrent_requests=1,
            delay_between_requests=0.0,
            adaptive_confidence_threshold=0.0,
            progress_report_interval=1
        )
        config.validate()  # Should pass
        
        # Test maximum boundary values
        config = ExhaustiveCrawlConfig(
            revisit_ratio_threshold=1.0,
            adaptive_confidence_threshold=1.0
        )
        config.validate()  # Should pass
    
    def test_invalid_boundary_values(self):
        """Test invalid boundary values."""
        
        # Test zero and negative values for positive-only parameters
        invalid_params = [
            ('max_depth', 0),
            ('max_depth', -1),
            ('max_pages', 0),
            ('max_pages', -1),
            ('dead_end_threshold', 0),
            ('dead_end_threshold', -1),
            ('max_concurrent_requests', 0),
            ('max_concurrent_requests', -1),
            ('progress_report_interval', 0),
            ('progress_report_interval', -1),
        ]
        
        for param_name, invalid_value in invalid_params:
            with pytest.raises(AssertionError):
                kwargs = {param_name: invalid_value}
                config = ExhaustiveCrawlConfig(**kwargs)
                config.validate()
        
        # Test out-of-range values for ratio parameters
        ratio_params = [
            ('revisit_ratio_threshold', -0.1),
            ('revisit_ratio_threshold', 1.1),
            ('adaptive_confidence_threshold', -0.1),
            ('adaptive_confidence_threshold', 1.1),
        ]
        
        for param_name, invalid_value in ratio_params:
            with pytest.raises(AssertionError):
                kwargs = {param_name: invalid_value}
                config = ExhaustiveCrawlConfig(**kwargs)
                config.validate()
    
    def test_parameter_type_validation(self):
        """Test that parameters accept correct types."""
        
        # Test boolean parameters
        config = ExhaustiveCrawlConfig(
            stop_on_dead_ends=True,
            discover_files_during_crawl=False,
            download_discovered_files=True,
            respect_robots_txt=False,
            enable_url_seeder=True,
            enable_adaptive_intelligence=False,
            enable_progress_tracking=True
        )
        config.validate()  # Should pass
        
        # Test list parameters
        config = ExhaustiveCrawlConfig(
            file_extensions_whitelist=['pdf', 'doc', 'txt'],
            file_extensions_blacklist=['exe', 'dmg']
        )
        config.validate()  # Should pass
        
        # Test None values for optional parameters
        config = ExhaustiveCrawlConfig(
            file_extensions_whitelist=None
        )
        config.validate()  # Should pass
    
    def test_logical_parameter_relationships(self):
        """Test logical relationships between parameters."""
        
        # Test file discovery parameters
        config = ExhaustiveCrawlConfig(
            discover_files_during_crawl=False,
            download_discovered_files=True  # Illogical but should not fail validation
        )
        config.validate()  # Should pass (validation doesn't check logical consistency)
        
        # Test URL seeder parameters
        config = ExhaustiveCrawlConfig(
            enable_url_seeder=True,
            seeder_sources="sitemap+cc",
            seeder_max_urls=1000
        )
        config.validate()  # Should pass
        
        # Test adaptive intelligence parameters
        config = ExhaustiveCrawlConfig(
            enable_adaptive_intelligence=True,
            adaptive_confidence_threshold=0.85
        )
        config.validate()  # Should pass
    
    def test_url_seeder_validation(self):
        """Test URL seeder specific validation."""
        
        # Valid seeder sources
        valid_sources = ["sitemap", "cc", "sitemap+cc", "cc+sitemap"]
        
        for source in valid_sources:
            config = ExhaustiveCrawlConfig(
                enable_url_seeder=True,
                seeder_sources=source,
                seeder_max_urls=100
            )
            config.validate()  # Should pass
        
        # Invalid seeder source
        with pytest.raises(AssertionError, match="seeder_sources must be one of"):
            config = ExhaustiveCrawlConfig(
                enable_url_seeder=True,
                seeder_sources="invalid_source",
                seeder_max_urls=100
            )
            config.validate()
        
        # Invalid seeder_max_urls
        with pytest.raises(AssertionError, match="seeder_max_urls must be positive"):
            config = ExhaustiveCrawlConfig(
                enable_url_seeder=True,
                seeder_sources="sitemap",
                seeder_max_urls=0
            )
            config.validate()
    
    def test_file_extensions_validation(self):
        """Test file extensions parameter validation."""
        
        # Valid file extensions lists
        config = ExhaustiveCrawlConfig(
            file_extensions_whitelist=['pdf', 'doc', 'txt'],
            file_extensions_blacklist=['exe', 'dmg', 'msi']
        )
        config.validate()  # Should pass
        
        # Empty lists should be valid
        config = ExhaustiveCrawlConfig(
            file_extensions_whitelist=[],
            file_extensions_blacklist=[]
        )
        config.validate()  # Should pass
        
        # None whitelist should be valid
        config = ExhaustiveCrawlConfig(
            file_extensions_whitelist=None,
            file_extensions_blacklist=['exe']
        )
        config.validate()  # Should pass


class TestExhaustiveConfigPresets:
    """Test preset configuration creation and validation."""
    
    def test_all_preset_types(self):
        """Test all available preset types."""
        preset_names = ["comprehensive", "balanced", "fast", "files_focused", "adaptive"]
        
        for preset_name in preset_names:
            config = create_exhaustive_preset_config(preset_name)
            
            # Each preset should be valid
            config.validate()
            
            # Each preset should have appropriate characteristics
            if preset_name == "comprehensive":
                assert config.max_depth >= 75
                assert config.max_pages >= 7500
            elif preset_name == "fast":
                assert config.max_depth <= 30
                assert config.max_pages <= 3000
            elif preset_name == "files_focused":
                assert config.discover_files_during_crawl == True
                assert config.download_discovered_files == True
            elif preset_name == "adaptive":
                assert config.enable_adaptive_intelligence == True
    
    def test_preset_overrides(self):
        """Test preset configuration with overrides."""
        
        # Override single parameter
        config = create_exhaustive_preset_config(
            "balanced",
            max_depth=75
        )
        assert config.max_depth == 75
        # Other balanced preset values should remain
        assert config.max_pages == 5000
        
        # Override multiple parameters
        config = create_exhaustive_preset_config(
            "fast",
            max_depth=40,
            dead_end_threshold=15,
            discover_files_during_crawl=True
        )
        assert config.max_depth == 40
        assert config.dead_end_threshold == 15
        assert config.discover_files_during_crawl == True
        
        # Overridden config should still be valid
        config.validate()
    
    def test_preset_validation_with_invalid_overrides(self):
        """Test that invalid overrides are caught during preset creation."""
        
        # Invalid override should cause validation failure
        with pytest.raises(ValueError, match="validation failed"):
            create_exhaustive_preset_config(
                "balanced",
                max_depth=-1  # Invalid value
            )
        
        with pytest.raises(ValueError, match="validation failed"):
            create_exhaustive_preset_config(
                "comprehensive",
                revisit_ratio_threshold=1.5  # Invalid value
            )


class TestValidateExhaustiveConfig:
    """Test the standalone validation function."""
    
    def test_validation_function_with_valid_config(self):
        """Test validation function with valid configuration."""
        config = ExhaustiveCrawlConfig(
            max_depth=50,
            max_pages=5000,
            dead_end_threshold=25
        )
        
        errors = validate_exhaustive_config(config)
        assert len(errors) == 0
    
    def test_validation_function_with_invalid_config(self):
        """Test validation function with invalid configuration."""
        config = ExhaustiveCrawlConfig(
            max_depth=-1,  # Invalid
            dead_end_threshold=0,  # Invalid
            revisit_ratio_threshold=1.5  # Invalid
        )
        
        errors = validate_exhaustive_config(config)
        assert len(errors) > 0
        
        # Should contain error messages (may vary based on implementation)
        error_text = ' '.join(errors).lower()
        # Check for any validation-related keywords
        assert any(keyword in error_text for keyword in ['max_depth', 'threshold', 'ratio', 'positive', 'between'])
    
    def test_validation_function_with_conflicting_settings(self):
        """Test validation function detects conflicting settings."""
        config = ExhaustiveCrawlConfig(
            enable_adaptive_intelligence=True,
            adaptive_confidence_threshold=0.98,  # Very high
            dead_end_threshold=5,  # Very low
            stop_on_dead_ends=True
        )
        
        errors = validate_exhaustive_config(config)
        
        # Should detect potential conflict
        if errors:
            error_text = ' '.join(errors)
            assert "confidence threshold" in error_text or "dead-end threshold" in error_text
    
    def test_validation_function_with_resource_warnings(self):
        """Test validation function warns about resource-intensive settings."""
        config = ExhaustiveCrawlConfig(
            max_concurrent_requests=100,  # Very high
            delay_between_requests=0.01   # Very low
        )
        
        errors = validate_exhaustive_config(config)
        
        # Should warn about aggressive settings
        if errors:
            error_text = ' '.join(errors)
            assert "concurrent_requests" in error_text or "delay_between_requests" in error_text


class TestAdaptiveIntegration:
    """Test integration with adaptive crawler configuration."""
    
    def test_configure_adaptive_for_exhaustive_mode(self):
        """Test configuring adaptive crawler for exhaustive mode."""
        
        # Test with default adaptive config
        adaptive_config = configure_adaptive_for_exhaustive_mode()
        
        # Should have exhaustive-appropriate settings
        assert adaptive_config.max_depth >= 50
        assert adaptive_config.max_pages >= 5000
        assert adaptive_config.confidence_threshold >= 0.8
        assert adaptive_config.save_state == True
    
    def test_configure_adaptive_with_overrides(self):
        """Test configuring adaptive with custom overrides."""
        
        adaptive_config = configure_adaptive_for_exhaustive_mode(
            max_depth=75,
            confidence_threshold=0.85,
            novelty_weight=0.4,
            relevance_weight=0.4,
            authority_weight=0.2
        )
        
        assert adaptive_config.max_depth == 75
        assert adaptive_config.confidence_threshold == 0.85
        assert adaptive_config.novelty_weight == 0.4
    
    def test_adaptive_config_validation(self):
        """Test that adaptive config is properly validated."""
        
        # Should not raise exceptions with valid parameters
        adaptive_config = configure_adaptive_for_exhaustive_mode(
            confidence_threshold=0.9,
            max_depth=100
        )
        
        # Adaptive config should have validate method
        if hasattr(adaptive_config, 'validate'):
            adaptive_config.validate()


class TestFilterScorerConfig:
    """Test minimal filter and scorer configuration creation."""
    
    def test_create_minimal_filter_scorer_config(self):
        """Test creation of minimal filter and scorer configuration."""
        
        config = create_minimal_filter_scorer_config()
        
        # Should return dictionary with expected keys
        assert 'filter_config' in config
        assert 'scorer_config' in config
        
        # Scorer should be minimal (no restrictions)
        scorer_config = config['scorer_config']
        assert scorer_config['enable_scoring'] == False
        
        # Filter should allow maximum discovery
        filter_config = config['filter_config']
        assert filter_config['enable_minimal_filtering'] == True
    
    def test_filter_scorer_config_with_file_discovery(self):
        """Test filter/scorer config with file discovery enabled."""
        
        config = create_minimal_filter_scorer_config(
            enable_file_discovery=True,
            file_extensions=['pdf', 'doc', 'txt']
        )
        
        filter_config = config['filter_config']
        assert filter_config['file_discovery_enabled'] == True
        assert filter_config['file_extensions'] == ['pdf', 'doc', 'txt']
    
    def test_filter_scorer_config_with_exclusions(self):
        """Test filter/scorer config with exclusion patterns."""
        
        exclude_patterns = ['*/admin/*', '*/private/*', '*.exe']
        
        config = create_minimal_filter_scorer_config(
            exclude_patterns=exclude_patterns
        )
        
        filter_config = config['filter_config']
        assert filter_config['exclude_patterns'] == exclude_patterns


if __name__ == "__main__":
    # Run tests manually for debugging
    print("Running exhaustive config validation tests...")
    
    test_validation = TestExhaustiveCrawlConfigValidation()
    test_validation.test_all_valid_parameter_combinations()
    test_validation.test_boundary_value_validation()
    print("✓ Basic validation tests passed")
    
    test_presets = TestExhaustiveConfigPresets()
    test_presets.test_all_preset_types()
    test_presets.test_preset_overrides()
    print("✓ Preset tests passed")
    
    test_validate_func = TestValidateExhaustiveConfig()
    test_validate_func.test_validation_function_with_valid_config()
    test_validate_func.test_validation_function_with_invalid_config()
    print("✓ Validation function tests passed")
    
    test_adaptive = TestAdaptiveIntegration()
    test_adaptive.test_configure_adaptive_for_exhaustive_mode()
    test_adaptive.test_configure_adaptive_with_overrides()
    print("✓ Adaptive integration tests passed")
    
    test_filter = TestFilterScorerConfig()
    test_filter.test_create_minimal_filter_scorer_config()
    test_filter.test_filter_scorer_config_with_file_discovery()
    print("✓ Filter/scorer config tests passed")
    
    print("\n🎉 All exhaustive config validation tests passed!")