"""
Configuration helpers for exhaustive crawling using existing Crawl4AI infrastructure.

This module provides helper functions to configure existing AdaptiveCrawler and AsyncWebCrawler
for exhaustive mode, create minimal filter and scorer configurations for maximum discovery,
and implement preset configurations for different exhaustive crawling scenarios.
"""

import logging
from typing import Optional, List, Dict, Any, Union
from dataclasses import dataclass, field
from pathlib import Path

from .adaptive_crawler import AdaptiveConfig
from .async_configs import CrawlerRunConfig, BrowserConfig, SeedingConfig
from .async_url_seeder import AsyncUrlSeeder
from .exhaustive_strategy_config import create_exhaustive_bfs_strategy, create_minimal_filter_chain


@dataclass
class ExhaustiveCrawlConfig(CrawlerRunConfig):
    """
    Extended configuration for exhaustive crawling that builds on existing CrawlerRunConfig.
    
    This configuration extends the existing CrawlerRunConfig with parameters optimized
    for "crawl until dead ends" behavior, including dead-end detection, high limits,
    and enhanced URL discovery capabilities.
    
    Requirements addressed:
        - 1.1: Domain knowledge loading and content pattern storage
        - 1.2: Priority target area configuration
        - 1.3: Classification schema application
        - 1.4: Quality criteria evaluation
    """
    
    # Override existing limits for exhaustive behavior
    max_depth: int = 100  # Effectively "infinite" for most sites
    max_pages: int = 10000  # Very high limit for comprehensive coverage
    
    # Dead-end detection parameters
    stop_on_dead_ends: bool = True  # Stop when no new URLs found
    dead_end_threshold: int = 50  # Consecutive pages with no new URLs before stopping
    revisit_ratio_threshold: float = 0.95  # Stop when 95% of URLs are revisits
    
    # Enhanced crawling behavior
    respect_robots_txt: bool = False  # Override for completeness
    delay_between_requests: float = 0.1  # Minimal politeness delay
    max_concurrent_requests: int = 20  # High concurrency for aggressive crawling
    
    # File discovery integration
    discover_files_during_crawl: bool = True
    download_discovered_files: bool = False  # Optional file downloading
    file_extensions_whitelist: Optional[List[str]] = None
    file_extensions_blacklist: List[str] = field(default_factory=lambda: ['.exe', '.dmg', '.msi'])
    
    # URL seeder integration for enhanced discovery
    enable_url_seeder: bool = False  # Optional AsyncUrlSeeder integration
    seeder_sources: str = "sitemap+cc"  # Sources for URL seeder
    seeder_max_urls: int = 1000  # Limit URLs from seeder
    
    # Adaptive crawler integration
    enable_adaptive_intelligence: bool = False  # Optional adaptive crawler features
    adaptive_confidence_threshold: float = 0.8  # Confidence threshold for adaptive mode
    
    # Progress tracking and monitoring
    enable_progress_tracking: bool = True
    progress_report_interval: int = 100  # Report progress every N pages
    
    def validate(self) -> None:
        """
        Validate configuration parameters using existing parameter validation patterns.
        
        Follows the same validation approach as AdaptiveConfig.validate() to ensure
        consistency with existing Crawl4AI patterns.
        """
        # Validate basic parameters
        assert self.max_depth > 0, "max_depth must be positive"
        assert self.max_pages > 0, "max_pages must be positive"
        assert self.max_concurrent_requests > 0, "max_concurrent_requests must be positive"
        assert self.delay_between_requests >= 0, "delay_between_requests must be non-negative"
        
        # Validate dead-end detection parameters
        assert self.dead_end_threshold > 0, "dead_end_threshold must be positive"
        assert 0 <= self.revisit_ratio_threshold <= 1, "revisit_ratio_threshold must be between 0 and 1"
        
        # Validate adaptive parameters
        assert 0 <= self.adaptive_confidence_threshold <= 1, "adaptive_confidence_threshold must be between 0 and 1"
        
        # Validate progress tracking
        assert self.progress_report_interval > 0, "progress_report_interval must be positive"
        
        # Validate seeder parameters
        if self.enable_url_seeder:
            valid_sources = {"sitemap", "cc", "sitemap+cc", "cc+sitemap"}
            assert self.seeder_sources in valid_sources, f"seeder_sources must be one of {valid_sources}"
            assert self.seeder_max_urls > 0, "seeder_max_urls must be positive"
        
        # Validate file discovery parameters
        if self.file_extensions_whitelist is not None:
            assert isinstance(self.file_extensions_whitelist, list), "file_extensions_whitelist must be a list"
        assert isinstance(self.file_extensions_blacklist, list), "file_extensions_blacklist must be a list"


def configure_adaptive_for_exhaustive_mode(
    adaptive_config: Optional[AdaptiveConfig] = None,
    **overrides
) -> AdaptiveConfig:
    """
    Configure existing AdaptiveCrawler for exhaustive mode.
    
    This function takes an existing AdaptiveConfig and modifies it for exhaustive
    crawling behavior, or creates a new one with exhaustive parameters.
    
    Args:
        adaptive_config: Existing AdaptiveConfig to modify (optional)
        **overrides: Additional parameters to override defaults
        
    Returns:
        AdaptiveConfig: Configured for exhaustive crawling behavior
        
    Requirements addressed:
        - 1.1: Configure existing AdaptiveCrawler for exhaustive mode
    """
    # Start with existing config or create new one
    if adaptive_config is None:
        config = AdaptiveConfig()
    else:
        # Create a copy to avoid modifying the original
        config = AdaptiveConfig(
            confidence_threshold=adaptive_config.confidence_threshold,
            max_depth=adaptive_config.max_depth,
            max_pages=adaptive_config.max_pages,
            top_k_links=adaptive_config.top_k_links,
            min_gain_threshold=adaptive_config.min_gain_threshold,
            strategy=adaptive_config.strategy,
            saturation_threshold=adaptive_config.saturation_threshold,
            consistency_threshold=adaptive_config.consistency_threshold,
            coverage_weight=adaptive_config.coverage_weight,
            consistency_weight=adaptive_config.consistency_weight,
            saturation_weight=adaptive_config.saturation_weight,
            relevance_weight=adaptive_config.relevance_weight,
            novelty_weight=adaptive_config.novelty_weight,
            authority_weight=adaptive_config.authority_weight,
            save_state=adaptive_config.save_state,
            state_path=adaptive_config.state_path,
            embedding_model=adaptive_config.embedding_model,
            embedding_llm_config=adaptive_config.embedding_llm_config,
            n_query_variations=adaptive_config.n_query_variations,
            coverage_threshold=adaptive_config.coverage_threshold,
            alpha_shape_alpha=adaptive_config.alpha_shape_alpha,
        )
    
    # Apply exhaustive mode parameters
    exhaustive_defaults = {
        # High limits for "until dead ends" behavior
        'max_depth': 100,
        'max_pages': 10000,
        'top_k_links': 10,  # Consider more links per page
        
        # Lower thresholds to continue crawling longer
        'confidence_threshold': 0.9,  # Higher threshold for stopping
        'saturation_threshold': 0.9,  # Higher saturation before stopping
        'min_gain_threshold': 0.05,  # Lower gain threshold to continue
        
        # Adjust weights for exhaustive discovery
        'coverage_weight': 0.5,  # Emphasize coverage
        'consistency_weight': 0.2,  # Less emphasis on consistency
        'saturation_weight': 0.3,  # Moderate saturation weight
        
        # Link scoring for maximum discovery
        'relevance_weight': 0.4,  # Balanced relevance
        'novelty_weight': 0.4,  # High novelty weight for discovery
        'authority_weight': 0.2,  # Lower authority weight
        
        # Enable state persistence for long crawls
        'save_state': True,
        'state_path': './exhaustive_crawl_state.json',
    }
    
    # Apply defaults and overrides
    for key, value in exhaustive_defaults.items():
        if hasattr(config, key):
            setattr(config, key, value)
    
    for key, value in overrides.items():
        if hasattr(config, key):
            setattr(config, key, value)
    
    # Validate the configuration
    config.validate()
    
    return config


def create_minimal_filter_scorer_config(
    enable_file_discovery: bool = True,
    file_extensions: Optional[List[str]] = None,
    exclude_patterns: Optional[List[str]] = None,
    **filter_overrides
) -> Dict[str, Any]:
    """
    Create minimal filter and scorer configurations for maximum discovery.
    
    This function creates configuration dictionaries for filters and scorers
    that allow maximum URL discovery while providing basic filtering capabilities.
    
    Args:
        enable_file_discovery: Whether to enable file discovery filtering
        file_extensions: File extensions to discover (default: comprehensive list)
        exclude_patterns: URL patterns to exclude (default: minimal exclusions)
        **filter_overrides: Additional filter configuration overrides
        
    Returns:
        Dict containing filter and scorer configurations
        
    Requirements addressed:
        - 1.2: Create minimal filter and scorer configurations for maximum discovery
    """
    # Create minimal filter chain using existing function
    filter_chain = create_minimal_filter_chain(
        enable_filtering=True,
        file_extensions=file_extensions,
        exclude_patterns=exclude_patterns
    )
    
    # Minimal scorer configuration (no scoring restrictions)
    scorer_config = {
        'enable_scoring': False,  # Disable scoring for maximum discovery
        'score_threshold': -float('inf'),  # Accept all URLs
        'use_url_scorer': False,
        'use_content_scorer': False,
    }
    
    # Filter configuration
    filter_config = {
        'filter_chain': filter_chain,
        'enable_minimal_filtering': True,
        'file_discovery_enabled': enable_file_discovery,
        'file_extensions': file_extensions,
        'exclude_patterns': exclude_patterns,
    }
    
    # Apply any overrides
    filter_config.update(filter_overrides)
    
    return {
        'filter_config': filter_config,
        'scorer_config': scorer_config,
    }


def validate_exhaustive_config(config: ExhaustiveCrawlConfig) -> List[str]:
    """
    Validate exhaustive crawling configuration using existing parameter validation patterns.
    
    This function performs comprehensive validation of the exhaustive crawling configuration,
    following the same patterns used in AdaptiveConfig.validate().
    
    Args:
        config: ExhaustiveCrawlConfig to validate
        
    Returns:
        List of validation error messages (empty if valid)
        
    Requirements addressed:
        - 1.3: Add configuration validation using existing parameter validation patterns
    """
    errors = []
    
    try:
        # Use the built-in validate method
        config.validate()
    except AssertionError as e:
        errors.append(str(e))
    except Exception as e:
        errors.append(f"Validation error: {str(e)}")
    
    # Additional validation checks
    try:
        # Check for conflicting settings
        if config.enable_adaptive_intelligence and config.stop_on_dead_ends:
            if config.adaptive_confidence_threshold > 0.95 and config.dead_end_threshold < 10:
                errors.append(
                    "High adaptive confidence threshold with low dead-end threshold may cause premature stopping"
                )
        
        # Validate file discovery settings
        if config.discover_files_during_crawl and config.download_discovered_files:
            # Note: downloads_path is handled by BrowserConfig, not CrawlerRunConfig
            # This validation will be done when creating BrowserConfig
            pass
        
        # Validate URL seeder integration
        if config.enable_url_seeder:
            if config.seeder_max_urls > config.max_pages:
                errors.append("seeder_max_urls should not exceed max_pages")
        
        # Validate resource limits
        if config.max_concurrent_requests > 50:
            errors.append("max_concurrent_requests > 50 may overwhelm target servers")
        
        if config.delay_between_requests < 0.05:
            errors.append("delay_between_requests < 0.05 may be too aggressive for most servers")
        
    except Exception as e:
        errors.append(f"Additional validation error: {str(e)}")
    
    return errors


def create_exhaustive_preset_config(
    preset_name: str = "comprehensive",
    base_url: Optional[str] = None,
    **overrides
) -> ExhaustiveCrawlConfig:
    """
    Create predefined exhaustive crawling configurations for different scenarios.
    
    This function provides preset configurations optimized for common exhaustive
    crawling scenarios, similar to the preset approach in exhaustive_strategy_config.py.
    
    Args:
        preset_name: Name of the preset configuration
                    - "comprehensive": Maximum coverage with high limits
                    - "balanced": Moderate limits with good performance
                    - "fast": Lower limits for quicker completion
                    - "files_focused": Optimized for file discovery
                    - "adaptive": Uses adaptive intelligence features
        base_url: Base URL for the crawl (used for configuration optimization)
        **overrides: Additional parameters to override preset defaults
        
    Returns:
        ExhaustiveCrawlConfig: Configured for the specified preset
        
    Requirements addressed:
        - 1.4: Implement preset configurations for different exhaustive crawling scenarios
    """
    presets = {
        "comprehensive": {
            "max_depth": 100,
            "max_pages": 10000,
            "max_concurrent_requests": 20,
            "delay_between_requests": 0.1,
            "dead_end_threshold": 50,
            "revisit_ratio_threshold": 0.95,
            "discover_files_during_crawl": True,
            "download_discovered_files": False,
            "enable_url_seeder": True,
            "seeder_sources": "sitemap+cc",
            "seeder_max_urls": 1000,
            "enable_adaptive_intelligence": False,
            "enable_progress_tracking": True,
            "progress_report_interval": 100,
        },
        "balanced": {
            "max_depth": 50,
            "max_pages": 5000,
            "max_concurrent_requests": 15,
            "delay_between_requests": 0.2,
            "dead_end_threshold": 30,
            "revisit_ratio_threshold": 0.90,
            "discover_files_during_crawl": True,
            "download_discovered_files": False,
            "enable_url_seeder": True,
            "seeder_sources": "sitemap",
            "seeder_max_urls": 500,
            "enable_adaptive_intelligence": False,
            "enable_progress_tracking": True,
            "progress_report_interval": 50,
        },
        "fast": {
            "max_depth": 25,
            "max_pages": 2000,
            "max_concurrent_requests": 25,
            "delay_between_requests": 0.05,
            "dead_end_threshold": 20,
            "revisit_ratio_threshold": 0.85,
            "discover_files_during_crawl": False,
            "download_discovered_files": False,
            "enable_url_seeder": False,
            "enable_adaptive_intelligence": False,
            "enable_progress_tracking": True,
            "progress_report_interval": 25,
        },
        "files_focused": {
            "max_depth": 75,
            "max_pages": 7500,
            "max_concurrent_requests": 15,
            "delay_between_requests": 0.15,
            "dead_end_threshold": 40,
            "revisit_ratio_threshold": 0.92,
            "discover_files_during_crawl": True,
            "download_discovered_files": True,
            "file_extensions_whitelist": [
                'pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx',
                'zip', 'tar', 'gz', 'rar', '7z', 'txt', 'csv',
                'epub', 'mobi', 'json', 'xml'
            ],
            "enable_url_seeder": True,
            "seeder_sources": "sitemap+cc",
            "seeder_max_urls": 800,
            "enable_adaptive_intelligence": False,
            "enable_progress_tracking": True,
            "progress_report_interval": 75,
        },
        "adaptive": {
            "max_depth": 80,
            "max_pages": 8000,
            "max_concurrent_requests": 18,
            "delay_between_requests": 0.12,
            "dead_end_threshold": 35,
            "revisit_ratio_threshold": 0.88,
            "discover_files_during_crawl": True,
            "download_discovered_files": False,
            "enable_url_seeder": True,
            "seeder_sources": "sitemap+cc",
            "seeder_max_urls": 600,
            "enable_adaptive_intelligence": True,
            "adaptive_confidence_threshold": 0.85,
            "enable_progress_tracking": True,
            "progress_report_interval": 80,
        }
    }
    
    if preset_name not in presets:
        raise ValueError(f"Unknown preset '{preset_name}'. Available: {list(presets.keys())}")
    
    preset_config = presets[preset_name].copy()
    preset_config.update(overrides)
    
    # Create the configuration
    config = ExhaustiveCrawlConfig(**preset_config)
    
    # Validate the configuration
    validation_errors = validate_exhaustive_config(config)
    if validation_errors:
        raise ValueError(f"Preset configuration validation failed: {'; '.join(validation_errors)}")
    
    return config


def integrate_url_seeder_config(
    exhaustive_config: ExhaustiveCrawlConfig,
    domain: str,
    logger: Optional[logging.Logger] = None
) -> SeedingConfig:
    """
    Create SeedingConfig for AsyncUrlSeeder integration with exhaustive crawling.
    
    This function creates a SeedingConfig that integrates AsyncUrlSeeder with
    exhaustive crawling workflow for enhanced URL discovery when appropriate.
    
    Args:
        exhaustive_config: ExhaustiveCrawlConfig containing seeder parameters
        domain: Domain to seed URLs for
        logger: Optional logger instance
        
    Returns:
        SeedingConfig: Configured for integration with exhaustive crawling
        
    Requirements addressed:
        - 1.4: Integrate with existing AsyncUrlSeeder for enhanced URL discovery when appropriate
    """
    if not exhaustive_config.enable_url_seeder:
        raise ValueError("URL seeder integration is not enabled in exhaustive config")
    
    # Create SeedingConfig based on exhaustive config parameters
    seeding_config = SeedingConfig(
        # Source configuration
        source=exhaustive_config.seeder_sources,
        pattern="*",  # Accept all URLs for exhaustive crawling
        
        # Limits and performance
        max_urls=exhaustive_config.seeder_max_urls,
        concurrency=min(exhaustive_config.max_concurrent_requests, 10),  # Reasonable concurrency for seeding
        hits_per_sec=None,  # No rate limiting for seeding
        
        # Content extraction
        extract_head=True,  # Extract head content for better URL analysis
        live_check=False,  # Skip live checks for performance
        
        # Filtering and scoring
        filter_nonsense_urls=True,  # Filter out obvious non-content URLs
        query=None,  # No specific query for exhaustive crawling
        score_threshold=None,  # No score threshold for maximum discovery
        scoring_method="bm25",
        
        # Behavior
        force=False,  # Use cached results when available
        verbose=exhaustive_config.enable_progress_tracking,
    )
    
    return seeding_config


def create_exhaustive_browser_config(
    exhaustive_config: ExhaustiveCrawlConfig,
    **browser_overrides
) -> BrowserConfig:
    """
    Create BrowserConfig optimized for exhaustive crawling.
    
    This function creates a BrowserConfig with settings optimized for exhaustive
    crawling, including appropriate timeouts, concurrency settings, and resource management.
    
    Args:
        exhaustive_config: ExhaustiveCrawlConfig to base browser config on
        **browser_overrides: Additional browser configuration overrides
        
    Returns:
        BrowserConfig: Optimized for exhaustive crawling
    """
    # Base browser configuration for exhaustive crawling
    browser_config = BrowserConfig(
        # Browser type and mode
        browser_type="chromium",
        headless=True,
        browser_mode="dedicated",  # Use dedicated browser for better resource control
        
        # Performance settings
        viewport_width=1280,
        viewport_height=720,
        
        # Network settings
        ignore_https_errors=True,
        java_script_enabled=True,
        
        # Resource management
        accept_downloads=exhaustive_config.download_discovered_files,
        downloads_path="./downloads" if exhaustive_config.download_discovered_files else None,
        
        # Headers and user agent
        user_agent_mode="random" if exhaustive_config.max_concurrent_requests > 10 else "",
        
        # Additional args for performance
        extra_args=[
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--disable-gpu",
            "--disable-background-timer-throttling",
            "--disable-backgrounding-occluded-windows",
            "--disable-renderer-backgrounding",
        ] if exhaustive_config.max_concurrent_requests > 15 else [],
        
        # Verbose logging if progress tracking is enabled
        verbose=exhaustive_config.enable_progress_tracking,
    )
    
    # Apply any overrides
    for key, value in browser_overrides.items():
        if hasattr(browser_config, key):
            setattr(browser_config, key, value)
    
    return browser_config


# Convenience function for complete exhaustive crawling setup
def setup_exhaustive_crawling(
    preset_name: str = "comprehensive",
    domain: Optional[str] = None,
    **config_overrides
) -> Dict[str, Any]:
    """
    Complete setup function for exhaustive crawling with all necessary configurations.
    
    This convenience function creates all necessary configurations for exhaustive crawling
    in a single call, including ExhaustiveCrawlConfig, BrowserConfig, AdaptiveConfig,
    and optional SeedingConfig.
    
    Args:
        preset_name: Preset configuration name
        domain: Domain for URL seeding (optional)
        **config_overrides: Configuration overrides
        
    Returns:
        Dict containing all configured objects for exhaustive crawling
    """
    # Create main exhaustive config
    exhaustive_config = create_exhaustive_preset_config(preset_name, **config_overrides)
    
    # Create browser config
    browser_config = create_exhaustive_browser_config(exhaustive_config)
    
    # Create adaptive config if enabled
    adaptive_config = None
    if exhaustive_config.enable_adaptive_intelligence:
        adaptive_config = configure_adaptive_for_exhaustive_mode(
            confidence_threshold=exhaustive_config.adaptive_confidence_threshold
        )
    
    # Create seeding config if enabled and domain provided
    seeding_config = None
    if exhaustive_config.enable_url_seeder and domain:
        seeding_config = integrate_url_seeder_config(exhaustive_config, domain)
    
    # Create BFS strategy config
    bfs_strategy = create_exhaustive_bfs_strategy(
        max_depth=exhaustive_config.max_depth,
        max_pages=exhaustive_config.max_pages,
        max_concurrent_requests=exhaustive_config.max_concurrent_requests,
        delay_between_requests=exhaustive_config.delay_between_requests,
        file_extensions=exhaustive_config.file_extensions_whitelist,
    )
    
    return {
        'exhaustive_config': exhaustive_config,
        'browser_config': browser_config,
        'adaptive_config': adaptive_config,
        'seeding_config': seeding_config,
        'bfs_strategy': bfs_strategy,
        'validation_errors': validate_exhaustive_config(exhaustive_config),
    }