"""
Example demonstrating ExhaustiveCrawlConfig for comprehensive site mapping.

This example shows how to use the ExhaustiveCrawlConfig to perform "crawl until dead ends"
behavior for comprehensive site mapping and file discovery.
"""

import asyncio
import sys
from pathlib import Path

# Add the parent directory to the path to import crawl4ai
sys.path.insert(0, str(Path(__file__).parent.parent))

from crawl4ai import (
    AsyncWebCrawler, 
    ExhaustiveCrawlConfig, 
    create_exhaustive_config_preset,
    create_exhaustive_bfs_strategy,
    create_minimal_filter_chain,
    configure_exhaustive_crawler_settings,
    create_exhaustive_strategy_preset
)


async def basic_exhaustive_crawling():
    """Basic example of exhaustive crawling configuration."""
    print("=== Basic Exhaustive Crawling ===")
    
    # Create an exhaustive crawling configuration
    config = ExhaustiveCrawlConfig(
        dead_end_threshold=20,  # Stop after 20 consecutive pages with no new URLs
        revisit_ratio=0.90,     # Stop when 90% of URLs are revisits
        exhaustive_max_depth=50,    # Maximum depth to crawl
        exhaustive_max_pages=1000,  # Maximum pages to crawl
        discover_files_during_crawl=True,   # Enable file discovery
        download_discovered_files=False,    # Don't download files in this example
        verbose=True
    )
    
    print(f"Configuration created:")
    print(f"  - Dead end threshold: {config.dead_end_threshold}")
    print(f"  - Revisit ratio: {config.revisit_ratio}")
    print(f"  - Max depth: {config.exhaustive_max_depth}")
    print(f"  - Max pages: {config.exhaustive_max_pages}")
    print(f"  - File discovery: {config.discover_files_during_crawl}")
    print(f"  - Is exhaustive mode: {config.is_exhaustive_mode()}")
    
    # Check dead-end status simulation
    status = config.get_dead_end_status(
        consecutive_empty_pages=15,
        current_revisit_ratio=0.85
    )
    print(f"  - Dead-end status: {status}")


async def preset_configurations():
    """Example using preset configurations."""
    print("\n=== Preset Configurations ===")
    
    presets = ["comprehensive", "balanced", "fast", "files_focused"]
    
    for preset_name in presets:
        config = create_exhaustive_config_preset(preset_name)
        print(f"\n{preset_name.upper()} preset:")
        print(f"  - Max depth: {config.exhaustive_max_depth}")
        print(f"  - Max pages: {config.exhaustive_max_pages}")
        print(f"  - Dead end threshold: {config.dead_end_threshold}")
        print(f"  - Revisit ratio: {config.revisit_ratio}")
        print(f"  - Semaphore count: {config.semaphore_count}")
        print(f"  - Mean delay: {config.mean_delay}")


async def custom_preset_with_overrides():
    """Example of customizing presets with overrides."""
    print("\n=== Custom Preset with Overrides ===")
    
    # Start with balanced preset but customize for specific needs
    config = create_exhaustive_config_preset(
        "balanced",
        base_url="https://example.com",
        dead_end_threshold=15,      # More aggressive stopping
        semaphore_count=30,         # Higher concurrency
        discover_files_during_crawl=True,
        download_discovered_files=True
    )
    
    print(f"Customized balanced preset:")
    print(f"  - Base URL: {config.url}")
    print(f"  - Dead end threshold: {config.dead_end_threshold} (overridden)")
    print(f"  - Semaphore count: {config.semaphore_count} (overridden)")
    print(f"  - Max depth: {config.exhaustive_max_depth} (from preset)")
    print(f"  - File discovery: {config.discover_files_during_crawl} (overridden)")


async def configuration_cloning():
    """Example of cloning and modifying configurations."""
    print("\n=== Configuration Cloning ===")
    
    # Create base configuration
    base_config = ExhaustiveCrawlConfig(
        dead_end_threshold=30,
        exhaustive_max_depth=40
    )
    
    # Clone with modifications for different scenarios
    aggressive_config = base_config.clone(
        dead_end_threshold=10,      # More aggressive
        semaphore_count=50,         # Higher concurrency
        mean_delay=0.05             # Faster crawling
    )
    
    conservative_config = base_config.clone(
        dead_end_threshold=50,      # More patient
        semaphore_count=5,          # Lower concurrency
        mean_delay=0.5              # Slower, more polite
    )
    
    print(f"Base config - Dead end threshold: {base_config.dead_end_threshold}")
    print(f"Aggressive config - Dead end threshold: {aggressive_config.dead_end_threshold}")
    print(f"Conservative config - Dead end threshold: {conservative_config.dead_end_threshold}")


async def deep_crawl_strategy_integration():
    """Example showing how ExhaustiveCrawlConfig integrates with deep crawling."""
    print("\n=== Deep Crawl Strategy Integration ===")
    
    config = ExhaustiveCrawlConfig()
    
    # The config automatically creates a BFSDeepCrawlStrategy
    if config.deep_crawl_strategy:
        strategy = config.deep_crawl_strategy
        print(f"Deep crawl strategy: {type(strategy).__name__}")
        print(f"  - Max depth: {strategy.max_depth}")
        print(f"  - Max pages: {strategy.max_pages}")
        print(f"  - Include external: {strategy.include_external}")
        print(f"  - Score threshold: {strategy.score_threshold}")
        print(f"  - Filter chain: {len(strategy.filter_chain.filters)} filters")


async def exhaustive_strategy_configuration():
    """Example showing direct BFS strategy configuration for exhaustive crawling."""
    print("\n=== Exhaustive BFS Strategy Configuration ===")
    
    # Create exhaustive BFS strategy with default parameters
    default_strategy = create_exhaustive_bfs_strategy()
    print(f"Default strategy:")
    print(f"  - Max depth: {default_strategy.max_depth}")
    print(f"  - Max pages: {default_strategy.max_pages}")
    print(f"  - Include external: {default_strategy.include_external}")
    print(f"  - Score threshold: {default_strategy.score_threshold}")
    print(f"  - Filter chain: {len(default_strategy.filter_chain.filters)} filters")
    
    # Create custom exhaustive strategy
    custom_strategy = create_exhaustive_bfs_strategy(
        max_depth=50,
        max_pages=5000,
        max_concurrent_requests=15,
        delay_between_requests=0.2,
        include_external=True
    )
    print(f"\nCustom strategy:")
    print(f"  - Max depth: {custom_strategy.max_depth}")
    print(f"  - Max pages: {custom_strategy.max_pages}")
    print(f"  - Include external: {custom_strategy.include_external}")
    
    # Create strategy using presets
    comprehensive = create_exhaustive_strategy_preset("comprehensive")
    balanced = create_exhaustive_strategy_preset("balanced")
    fast = create_exhaustive_strategy_preset("fast")
    files_focused = create_exhaustive_strategy_preset("files_focused")
    
    print(f"\nStrategy presets:")
    print(f"  - Comprehensive: depth={comprehensive.max_depth}, pages={comprehensive.max_pages}")
    print(f"  - Balanced: depth={balanced.max_depth}, pages={balanced.max_pages}")
    print(f"  - Fast: depth={fast.max_depth}, pages={fast.max_pages}")
    print(f"  - Files focused: depth={files_focused.max_depth}, pages={files_focused.max_pages}")


async def minimal_filter_configuration():
    """Example showing minimal filter chain configuration."""
    print("\n=== Minimal Filter Configuration ===")
    
    # Create minimal filter chain with default settings
    minimal_filters = create_minimal_filter_chain()
    print(f"Minimal filter chain: {len(minimal_filters.filters)} filters")
    
    # Create filter chain with no filtering (maximum discovery)
    no_filters = create_minimal_filter_chain(enable_filtering=False)
    print(f"No filtering: {len(no_filters.filters)} filters")
    
    # Create filter chain with custom file extensions
    custom_filters = create_minimal_filter_chain(
        file_extensions=['pdf', 'doc', 'docx', 'xls', 'xlsx'],
        exclude_patterns=['*/admin/*', '*/login/*']
    )
    print(f"Custom filters: {len(custom_filters.filters)} filters")


async def crawler_settings_configuration():
    """Example showing crawler settings configuration for exhaustive crawling."""
    print("\n=== Crawler Settings Configuration ===")
    
    # Base crawler configuration
    base_config = {
        'semaphore_count': 5,
        'mean_delay': 0.5,
        'verbose': False
    }
    
    # Configure for exhaustive crawling
    exhaustive_config = configure_exhaustive_crawler_settings(base_config)
    
    print(f"Base config:")
    print(f"  - Semaphore count: {base_config['semaphore_count']}")
    print(f"  - Mean delay: {base_config['mean_delay']}")
    print(f"  - Verbose: {base_config['verbose']}")
    
    print(f"\nExhaustive config:")
    print(f"  - Semaphore count: {exhaustive_config['semaphore_count']}")
    print(f"  - Mean delay: {exhaustive_config['mean_delay']}")
    print(f"  - Verbose: {exhaustive_config['verbose']}")
    print(f"  - Respect robots.txt: {exhaustive_config['respect_robots_txt']}")
    print(f"  - Max concurrent requests: {exhaustive_config['max_concurrent_requests']}")


async def main():
    """Run all examples."""
    print("ExhaustiveCrawlConfig Examples")
    print("=" * 50)
    
    await basic_exhaustive_crawling()
    await preset_configurations()
    await custom_preset_with_overrides()
    await configuration_cloning()
    await deep_crawl_strategy_integration()
    await exhaustive_strategy_configuration()
    await minimal_filter_configuration()
    await crawler_settings_configuration()
    
    print("\n" + "=" * 50)
    print("All examples completed!")
    print("\nTo use ExhaustiveCrawlConfig with AsyncWebCrawler:")
    print("```python")
    print("config = ExhaustiveCrawlConfig()")
    print("async with AsyncWebCrawler() as crawler:")
    print("    result = await crawler.arun('https://example.com', config=config)")
    print("```")


if __name__ == "__main__":
    asyncio.run(main())