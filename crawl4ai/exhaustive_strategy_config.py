"""
Configuration utilities for exhaustive site mapping using existing BFSDeepCrawlStrategy.

This module provides configuration functions that set up the existing BFSDeepCrawlStrategy
with exhaustive parameters for comprehensive site mapping that continues "until dead ends".
"""

import logging
from typing import Optional, List
from math import inf as infinity

from .deep_crawling import BFSDeepCrawlStrategy, FilterChain, URLPatternFilter, ContentTypeFilter
from .deep_crawling.scorers import URLScorer


def create_exhaustive_bfs_strategy(
    max_depth: int = 100,
    max_pages: int = 10000,
    max_concurrent_requests: int = 20,
    delay_between_requests: float = 0.1,
    include_external: bool = False,
    respect_robots_txt: bool = False,
    enable_minimal_filtering: bool = True,
    file_extensions: Optional[List[str]] = None,
    logger: Optional[logging.Logger] = None
) -> BFSDeepCrawlStrategy:
    """
    Create a BFSDeepCrawlStrategy configured for exhaustive site mapping.
    
    This function configures the existing BFSDeepCrawlStrategy with parameters optimized
    for "crawl until dead ends" behavior, including:
    - High limits that effectively mean "until dead ends"
    - Minimal filtering to allow maximum URL discovery
    - High concurrency and minimal delays for aggressive crawling
    - No scoring restrictions that might cause premature stopping
    
    Args:
        max_depth: Maximum crawl depth (default: 100 for "effectively infinite")
        max_pages: Maximum pages to crawl (default: 10000 for comprehensive coverage)
        max_concurrent_requests: High concurrency for aggressive crawling (default: 20)
        delay_between_requests: Minimal politeness delay (default: 0.1 seconds)
        include_external: Whether to include external links (default: False)
        respect_robots_txt: Whether to respect robots.txt (default: False for completeness)
        enable_minimal_filtering: Whether to apply minimal filtering (default: True)
        file_extensions: List of file extensions to discover (default: comprehensive list)
        logger: Optional logger instance
        
    Returns:
        BFSDeepCrawlStrategy: Configured strategy for exhaustive crawling
        
    Requirements addressed:
        - 2.1: Strategic discovery with comprehensive link following
        - 2.2: Discover file download links through minimal filtering
        - 2.3: Build complete site graph with high limits
    """
    # Create minimal FilterChain for maximum URL discovery
    filter_chain = create_minimal_filter_chain(
        enable_filtering=enable_minimal_filtering,
        file_extensions=file_extensions
    )
    
    # Configure BFSDeepCrawlStrategy with exhaustive parameters
    strategy = BFSDeepCrawlStrategy(
        max_depth=max_depth,  # High limit - effectively "until dead ends"
        filter_chain=filter_chain,  # Minimal filtering for maximum discovery
        url_scorer=None,  # No scoring to avoid premature stopping
        include_external=include_external,  # Configurable external link handling
        score_threshold=-infinity,  # Accept all URLs (no scoring restrictions)
        max_pages=max_pages,  # High page limit for comprehensive coverage
        logger=logger or logging.getLogger(__name__)
    )
    
    # Configure aggressive crawling settings
    # Note: These would be set on the crawler instance, not the strategy
    # The strategy doesn't directly control these, but we document the recommended settings
    strategy._recommended_crawler_settings = {
        'max_concurrent_requests': max_concurrent_requests,
        'delay_between_requests': delay_between_requests,
        'respect_robots_txt': respect_robots_txt
    }
    
    return strategy


def create_minimal_filter_chain(
    enable_filtering: bool = True,
    file_extensions: Optional[List[str]] = None,
    exclude_patterns: Optional[List[str]] = None
) -> FilterChain:
    """
    Create a minimal FilterChain that allows maximum URL discovery.
    
    This function creates a FilterChain with minimal restrictions to ensure
    comprehensive site mapping while still providing basic filtering capabilities
    for file discovery and obvious exclusions.
    
    Args:
        enable_filtering: Whether to enable any filtering (default: True)
        file_extensions: File extensions to include for discovery (default: comprehensive list)
        exclude_patterns: Patterns to exclude (default: minimal exclusions)
        
    Returns:
        FilterChain: Minimal filter chain for maximum discovery
        
    Requirements addressed:
        - 2.2: Configure minimal FilterChain to allow maximum URL discovery
        - 4.1: File extension detection for comprehensive file discovery
    """
    filters = []
    
    if not enable_filtering:
        # Return empty filter chain for absolute maximum discovery
        return FilterChain(filters)
    
    # Default comprehensive file extensions for discovery
    if file_extensions is None:
        file_extensions = [
            # Documents
            'pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx',
            'odt', 'ods', 'odp', 'rtf', 'txt', 'csv',
            # Archives
            'zip', 'tar', 'gz', 'rar', '7z', 'bz2',
            # Media
            'jpg', 'jpeg', 'png', 'gif', 'svg', 'bmp', 'tiff',
            'mp3', 'wav', 'mp4', 'avi', 'mov', 'wmv',
            # Web formats
            'html', 'htm', 'xml', 'json', 'css', 'js',
            # Other
            'epub', 'mobi', 'apk', 'exe', 'dmg', 'iso'
        ]
    
    # Default minimal exclusions (only obvious non-content)
    if exclude_patterns is None:
        exclude_patterns = [
            # Exclude obvious non-content patterns
            '*/wp-admin/*',  # WordPress admin
            '*/admin/*',     # Generic admin
            '*/login/*',     # Login pages
            '*/logout/*',    # Logout pages
            '*/api/v*',      # API endpoints (versioned)
            '*/.git/*',      # Git repositories
            '*/.svn/*',      # SVN repositories
            '*/node_modules/*',  # Node.js modules
            '*/vendor/*',    # Vendor directories
            '*/_*',          # Hidden/private directories
            '*/cgi-bin/*',   # CGI scripts
        ]
    
    # Add comprehensive URL pattern filter that accepts almost everything
    # Use reverse=True with exclusion patterns to allow everything except specific patterns
    if exclude_patterns:
        filters.append(URLPatternFilter(
            patterns=exclude_patterns,
            use_glob=True,
            reverse=True  # Reverse logic: reject if matches exclusion patterns
        ))
    
    # Add content type filter for comprehensive file discovery
    # Include all common content types for maximum discovery
    comprehensive_content_types = [
        'text/html', 'text/plain', 'text/xml', 'text/css',
        'application/pdf', 'application/json', 'application/xml',
        'application/zip', 'application/gzip', 'application/x-tar',
        'application/msword', 'application/vnd.ms-excel', 'application/vnd.ms-powerpoint',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'application/vnd.openxmlformats-officedocument.presentationml.presentation',
        'image/jpeg', 'image/png', 'image/gif', 'image/svg+xml',
        'audio/mpeg', 'audio/wav', 'video/mp4', 'video/avi',
        'application/octet-stream'  # Catch-all for binary files
    ]
    
    filters.append(ContentTypeFilter(
        allowed_types=comprehensive_content_types,
        check_extension=True
    ))
    
    return FilterChain(filters)


def configure_exhaustive_crawler_settings(crawler_config: dict) -> dict:
    """
    Configure crawler settings for exhaustive crawling behavior.
    
    This function provides recommended settings for the AsyncWebCrawler when used
    with an exhaustive BFS strategy to ensure aggressive crawling with high concurrency
    and minimal delays.
    
    Args:
        crawler_config: Base crawler configuration dictionary
        
    Returns:
        dict: Updated configuration with exhaustive crawling settings
        
    Requirements addressed:
        - 2.3: Set high concurrency and minimal delays for aggressive crawling
    """
    exhaustive_settings = {
        # High concurrency for aggressive crawling
        'semaphore_count': 20,
        'max_concurrent_requests': 20,
        
        # Minimal delays for faster crawling
        'mean_delay': 0.1,
        'max_range': 0.1,
        'delay_between_requests': 0.1,
        
        # Override politeness settings for completeness
        'respect_robots_txt': False,
        'check_robots_txt': False,
        
        # Optimize for discovery
        'include_external': False,  # Stay within domain by default
        'follow_redirects': True,
        'max_redirects': 10,
        
        # Enable caching to avoid re-crawling
        'cache_mode': 'enabled',
        
        # Verbose logging for monitoring
        'verbose': True,
        
        # High timeout values for comprehensive coverage
        'page_timeout': 30000,  # 30 seconds
        'request_timeout': 20000,  # 20 seconds
    }
    
    # Merge with existing config (exhaustive settings take precedence)
    updated_config = {**crawler_config, **exhaustive_settings}
    
    return updated_config


def create_exhaustive_strategy_preset(
    preset_name: str = "comprehensive",
    **overrides
) -> BFSDeepCrawlStrategy:
    """
    Create predefined exhaustive BFS strategy presets for common scenarios.
    
    Args:
        preset_name: Name of the preset configuration
                    - "comprehensive": Maximum coverage with high limits
                    - "balanced": Moderate limits with good performance  
                    - "fast": Lower limits for quicker completion
                    - "files_focused": Optimized for file discovery
        **overrides: Additional parameters to override preset defaults
        
    Returns:
        BFSDeepCrawlStrategy: Configured strategy for the specified preset
    """
    presets = {
        "comprehensive": {
            "max_depth": 100,
            "max_pages": 10000,
            "max_concurrent_requests": 20,
            "delay_between_requests": 0.1,
            "enable_minimal_filtering": True,
        },
        "balanced": {
            "max_depth": 50,
            "max_pages": 5000,
            "max_concurrent_requests": 15,
            "delay_between_requests": 0.2,
            "enable_minimal_filtering": True,
        },
        "fast": {
            "max_depth": 25,
            "max_pages": 2000,
            "max_concurrent_requests": 25,
            "delay_between_requests": 0.05,
            "enable_minimal_filtering": True,
        },
        "files_focused": {
            "max_depth": 75,
            "max_pages": 7500,
            "max_concurrent_requests": 15,
            "delay_between_requests": 0.15,
            "enable_minimal_filtering": True,
            "file_extensions": [
                'pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx',
                'zip', 'tar', 'gz', 'rar', '7z', 'txt', 'csv',
                'epub', 'mobi', 'json', 'xml'
            ]
        }
    }
    
    if preset_name not in presets:
        raise ValueError(f"Unknown preset '{preset_name}'. Available: {list(presets.keys())}")
    
    preset_config = presets[preset_name].copy()
    preset_config.update(overrides)
    
    return create_exhaustive_bfs_strategy(**preset_config)