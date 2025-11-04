#!/usr/bin/env python3
"""
Example demonstrating exhaustive crawling configuration helpers.

This example shows how to use the configuration helpers to set up
exhaustive crawling with different presets and customizations.
"""

import asyncio
import logging
from pathlib import Path

from crawl4ai.exhaustive_configs import (
    ExhaustiveCrawlConfig,
    configure_adaptive_for_exhaustive_mode,
    create_minimal_filter_scorer_config,
    create_exhaustive_preset_config,
    setup_exhaustive_crawling,
    integrate_url_seeder_config,
    validate_exhaustive_config
)


async def example_basic_exhaustive_config():
    """Example of creating a basic exhaustive crawling configuration."""
    print("=== Basic Exhaustive Configuration ===")
    
    # Create a basic exhaustive config
    config = ExhaustiveCrawlConfig(
        max_depth=50,
        max_pages=2000,
        dead_end_threshold=25,
        enable_url_seeder=True,
        discover_files_during_crawl=True
    )
    
    # Validate the configuration
    errors = validate_exhaustive_config(config)
    if errors:
        print(f"Configuration errors: {errors}")
    else:
        print("✓ Configuration is valid")
    
    print(f"Max depth: {config.max_depth}")
    print(f"Max pages: {config.max_pages}")
    print(f"Dead-end threshold: {config.dead_end_threshold}")
    print(f"URL seeder enabled: {config.enable_url_seeder}")
    print()


async def example_preset_configurations():
    """Example of using preset configurations."""
    print("=== Preset Configurations ===")
    
    presets = ["comprehensive", "balanced", "fast", "files_focused", "adaptive"]
    
    for preset_name in presets:
        print(f"\n{preset_name.upper()} Preset:")
        config = create_exhaustive_preset_config(preset_name)
        
        print(f"  Max depth: {config.max_depth}")
        print(f"  Max pages: {config.max_pages}")
        print(f"  Concurrency: {config.max_concurrent_requests}")
        print(f"  Dead-end threshold: {config.dead_end_threshold}")
        print(f"  File discovery: {config.discover_files_during_crawl}")
        print(f"  Adaptive intelligence: {config.enable_adaptive_intelligence}")


async def example_adaptive_configuration():
    """Example of configuring adaptive crawler for exhaustive mode."""
    print("\n=== Adaptive Configuration ===")
    
    # Configure adaptive crawler for exhaustive mode
    adaptive_config = configure_adaptive_for_exhaustive_mode(
        max_depth=75,
        confidence_threshold=0.85,
        strategy="statistical"
    )
    
    print(f"Max depth: {adaptive_config.max_depth}")
    print(f"Max pages: {adaptive_config.max_pages}")
    print(f"Confidence threshold: {adaptive_config.confidence_threshold}")
    print(f"Strategy: {adaptive_config.strategy}")
    print(f"State persistence: {adaptive_config.save_state}")


async def example_filter_scorer_configuration():
    """Example of creating minimal filter and scorer configurations."""
    print("\n=== Filter and Scorer Configuration ===")
    
    # Create minimal filter/scorer config for maximum discovery
    config = create_minimal_filter_scorer_config(
        enable_file_discovery=True,
        file_extensions=['pdf', 'doc', 'docx', 'txt', 'csv'],
        exclude_patterns=['*/admin/*', '*/login/*']
    )
    
    print("Filter configuration:")
    print(f"  File discovery enabled: {config['filter_config']['file_discovery_enabled']}")
    print(f"  File extensions: {config['filter_config']['file_extensions']}")
    print(f"  Exclude patterns: {config['filter_config']['exclude_patterns']}")
    
    print("Scorer configuration:")
    print(f"  Scoring enabled: {config['scorer_config']['enable_scoring']}")
    print(f"  Score threshold: {config['scorer_config']['score_threshold']}")


async def example_complete_setup():
    """Example of complete exhaustive crawling setup."""
    print("\n=== Complete Setup ===")
    
    # Set up complete exhaustive crawling configuration
    setup = setup_exhaustive_crawling(
        preset_name="balanced",
        domain="example.com",
        max_depth=40,
        enable_url_seeder=True,
        discover_files_during_crawl=True
    )
    
    print("Complete setup includes:")
    print(f"  ✓ Exhaustive config: {type(setup['exhaustive_config']).__name__}")
    print(f"  ✓ Browser config: {type(setup['browser_config']).__name__}")
    print(f"  ✓ BFS strategy: {type(setup['bfs_strategy']).__name__}")
    
    if setup['seeding_config']:
        print(f"  ✓ Seeding config: {type(setup['seeding_config']).__name__}")
    
    if setup['adaptive_config']:
        print(f"  ✓ Adaptive config: {type(setup['adaptive_config']).__name__}")
    
    if setup['validation_errors']:
        print(f"  ⚠ Validation errors: {setup['validation_errors']}")
    else:
        print("  ✓ All configurations validated successfully")


async def example_url_seeder_integration():
    """Example of URL seeder integration."""
    print("\n=== URL Seeder Integration ===")
    
    # Create exhaustive config with URL seeder enabled
    exhaustive_config = create_exhaustive_preset_config(
        "comprehensive",
        enable_url_seeder=True,
        seeder_sources="sitemap+cc",
        seeder_max_urls=500
    )
    
    # Create seeding config for integration
    seeding_config = integrate_url_seeder_config(
        exhaustive_config,
        domain="example.com"
    )
    
    print(f"Seeder sources: {seeding_config.source}")
    print(f"Max URLs: {seeding_config.max_urls}")
    print(f"Concurrency: {seeding_config.concurrency}")
    print(f"Extract head: {seeding_config.extract_head}")
    print(f"Filter nonsense: {seeding_config.filter_nonsense_urls}")


async def example_custom_configuration():
    """Example of creating a custom configuration with validation."""
    print("\n=== Custom Configuration with Validation ===")
    
    # Create a custom configuration
    config = ExhaustiveCrawlConfig(
        max_depth=60,
        max_pages=3000,
        max_concurrent_requests=12,
        delay_between_requests=0.15,
        dead_end_threshold=30,
        revisit_ratio_threshold=0.88,
        discover_files_during_crawl=True,
        download_discovered_files=False,
        enable_url_seeder=True,
        seeder_sources="sitemap",
        seeder_max_urls=400,
        enable_adaptive_intelligence=True,
        adaptive_confidence_threshold=0.82,
        file_extensions_whitelist=['pdf', 'doc', 'txt', 'csv', 'json'],
        enable_progress_tracking=True,
        progress_report_interval=50
    )
    
    # Validate the configuration
    errors = validate_exhaustive_config(config)
    
    if errors:
        print("Configuration validation failed:")
        for error in errors:
            print(f"  ✗ {error}")
    else:
        print("✓ Custom configuration validated successfully")
        print(f"  Max depth: {config.max_depth}")
        print(f"  Max pages: {config.max_pages}")
        print(f"  Concurrency: {config.max_concurrent_requests}")
        print(f"  Dead-end threshold: {config.dead_end_threshold}")
        print(f"  Adaptive intelligence: {config.enable_adaptive_intelligence}")
        print(f"  File extensions: {config.file_extensions_whitelist}")


async def main():
    """Run all examples."""
    print("Exhaustive Crawling Configuration Examples")
    print("=" * 50)
    
    await example_basic_exhaustive_config()
    await example_preset_configurations()
    await example_adaptive_configuration()
    await example_filter_scorer_configuration()
    await example_complete_setup()
    await example_url_seeder_integration()
    await example_custom_configuration()
    
    print("\n" + "=" * 50)
    print("All examples completed successfully! ✓")


if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    
    # Run examples
    asyncio.run(main())