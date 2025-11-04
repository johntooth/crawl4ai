#!/usr/bin/env python3
"""
Example: Exhaustive Crawling Orchestration (Task 6 Implementation)

This example demonstrates the improved exhaustive crawling orchestration that:
1. Uses existing arun() as foundation for all crawling operations
2. Implements loop logic to continue crawling until dead-end threshold is reached
3. Manages URL queue for continuing from discovered URLs
4. Provides progress tracking using existing crawl analytics

Key improvements in this implementation:
- Better integration with existing AsyncWebCrawler infrastructure
- Robust URL queue management for discovered URLs
- Enhanced progress tracking and analytics
- Proper error handling and resource management

Requirements covered:
- 2.1: Strategic discovery with comprehensive site mapping
- 2.2: URL discovery and queue management
- 6.4: Real-time processing with URL tracking
- 7.1: Analytics for crawling performance
"""

import asyncio
import sys
import os
from pathlib import Path

# Add crawl4ai to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from crawl4ai import AsyncWebCrawler, BrowserConfig
from crawl4ai.exhaustive_webcrawler import ExhaustiveAsyncWebCrawler
from crawl4ai.exhaustive_configs import ExhaustiveCrawlConfig, create_exhaustive_config_preset


async def example_basic_orchestration():
    """
    Basic example of exhaustive crawling orchestration.
    """
    print("=== Basic Exhaustive Crawling Orchestration ===\n")
    
    # Create configuration for exhaustive crawling
    config = ExhaustiveCrawlConfig(
        dead_end_threshold=5,  # Stop after 5 consecutive pages with no new URLs
        revisit_ratio=0.85,    # Stop when 85% of URLs are revisits
        exhaustive_max_pages=20,  # Limit for demonstration
        verbose=True
    )
    
    # Add custom orchestration parameters
    config.batch_size = 3  # Process 3 URLs at a time
    config.continue_on_dead_ends = True  # Keep going until threshold
    config.log_discovery_stats = True  # Log progress
    
    print(f"Configuration:")
    print(f"  Dead end threshold: {config.dead_end_threshold}")
    print(f"  Revisit ratio: {config.revisit_ratio}")
    print(f"  Max pages: {config.exhaustive_max_pages}")
    print(f"  Batch size: {config.batch_size}")
    print(f"  Continue on dead ends: {config.continue_on_dead_ends}")
    print()
    
    # Create exhaustive crawler
    browser_config = BrowserConfig(headless=True)
    crawler = ExhaustiveAsyncWebCrawler(config=browser_config)
    
    try:
        # Test HTML with multiple levels of links
        test_html = """
        <html>
        <head><title>Hub Page</title></head>
        <body>
            <h1>Main Hub</h1>
            <nav>
                <a href="https://example.com/category1">Category 1</a>
                <a href="https://example.com/category2">Category 2</a>
                <a href="https://example.com/about">About</a>
                <a href="https://example.com/contact">Contact</a>
            </nav>
            <p>This is the main hub page with links to various sections.</p>
        </body>
        </html>
        """
        
        print("Starting exhaustive crawl orchestration...")
        
        # Run exhaustive crawling with orchestration
        result = await crawler.arun_exhaustive(f"raw:{test_html}", config=config)
        
        print(f"\n🎉 Exhaustive crawl orchestration completed!")
        print(f"\nResults Summary:")
        print(f"  Total pages crawled: {result['total_pages_crawled']}")
        print(f"  Successful pages: {result['successful_pages']}")
        print(f"  URLs discovered: {result['total_urls_discovered']}")
        print(f"  URLs remaining in queue: {result.get('urls_in_queue', 0)}")
        print(f"  Stop reason: {result['stop_reason']}")
        
        # Show analytics from existing crawl infrastructure
        analytics = result['analytics']
        session_stats = analytics['session_stats']
        
        print(f"\nAnalytics (using existing crawl analytics):")
        print(f"  Crawl duration: {session_stats['crawl_duration']}")
        print(f"  Average discovery rate: {session_stats['average_discovery_rate']:.2f} URLs/page")
        print(f"  Final revisit ratio: {session_stats['revisit_ratio']:.2%}")
        print(f"  Consecutive dead pages: {session_stats['consecutive_dead_pages']}")
        
        # Show URL tracking state
        url_tracking = analytics['url_tracking']
        print(f"\nURL Queue Management:")
        print(f"  Total discovered: {url_tracking['total_discovered']}")
        print(f"  Total crawled: {url_tracking['total_crawled']}")
        print(f"  Success rate: {url_tracking['success_rate']:.2%}")
        print(f"  Pending count: {url_tracking['pending_count']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Example failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        if hasattr(crawler, 'close'):
            await crawler.close()


async def example_progress_tracking():
    """
    Example demonstrating real-time progress tracking during orchestration.
    """
    print("\n=== Progress Tracking During Orchestration ===\n")
    
    # Create configuration with progress tracking enabled
    config = create_exhaustive_config_preset(
        "fast",  # Use fast preset for quicker demonstration
        exhaustive_max_pages=15,
        verbose=True
    )
    
    # Add orchestration parameters
    config.batch_size = 2
    config.log_discovery_stats = True
    
    browser_config = BrowserConfig(headless=True)
    crawler = ExhaustiveAsyncWebCrawler(config=browser_config)
    
    try:
        # Create a more complex HTML structure for testing
        complex_html = """
        <html>
        <head><title>Complex Site</title></head>
        <body>
            <h1>Complex Site Structure</h1>
            <div class="navigation">
                <a href="https://example.com/products">Products</a>
                <a href="https://example.com/services">Services</a>
                <a href="https://example.com/blog">Blog</a>
                <a href="https://example.com/support">Support</a>
                <a href="https://example.com/docs">Documentation</a>
            </div>
            <div class="content">
                <p>Main content with more links:</p>
                <a href="https://example.com/news">Latest News</a>
                <a href="https://example.com/events">Events</a>
            </div>
        </body>
        </html>
        """
        
        print("Starting orchestration with progress tracking...")
        
        # Start the exhaustive crawl
        result = await crawler.arun_exhaustive(f"raw:{complex_html}", config=config)
        
        # Get final progress tracking information
        progress = crawler.get_progress_tracking()
        
        print(f"\n📊 Final Progress Tracking Report:")
        print(f"  Session active: {progress['session_active']}")
        print(f"  Crawl duration: {progress['crawl_duration']}")
        print(f"  Pages crawled: {progress['pages_crawled']}")
        print(f"  URLs discovered: {progress['urls_discovered']}")
        print(f"  URLs pending: {progress['urls_pending']}")
        print(f"  Success rate: {progress['success_rate']:.2%}")
        
        print(f"\n🎯 Dead-End Detection Status:")
        dead_end = progress['dead_end_status']
        print(f"  Consecutive dead pages: {dead_end['consecutive_dead_pages']}")
        print(f"  Revisit ratio: {dead_end['revisit_ratio']:.2%}")
        print(f"  Average discovery rate: {dead_end['average_discovery_rate']:.2f}")
        print(f"  Time since last discovery: {dead_end['time_since_last_discovery']}")
        
        print(f"\n📈 Discovery Trend (last 5 batches): {progress['discovery_trend']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Progress tracking example failed: {e}")
        return False
    
    finally:
        if hasattr(crawler, 'close'):
            await crawler.close()


async def example_url_queue_management():
    """
    Example demonstrating URL queue management for continuing from discovered URLs.
    """
    print("\n=== URL Queue Management Example ===\n")
    
    # Configuration focused on URL discovery and queue management
    config = ExhaustiveCrawlConfig(
        dead_end_threshold=8,  # Higher threshold to see more queue activity
        revisit_ratio=0.90,
        exhaustive_max_pages=25,
        verbose=True
    )
    
    # Configure for detailed queue management
    config.batch_size = 4  # Larger batches to show queue management
    config.continue_on_dead_ends = True
    config.include_external_links = False  # Focus on internal structure
    config.log_discovery_stats = True  # Enable logging
    
    browser_config = BrowserConfig(headless=True)
    crawler = ExhaustiveAsyncWebCrawler(config=browser_config)
    
    try:
        # HTML with hierarchical link structure
        hierarchical_html = """
        <html>
        <head><title>Hierarchical Site</title></head>
        <body>
            <h1>Site Root</h1>
            <div class="level1">
                <h2>Level 1 Links</h2>
                <a href="https://example.com/level1/page1">Level 1 - Page 1</a>
                <a href="https://example.com/level1/page2">Level 1 - Page 2</a>
                <a href="https://example.com/level1/page3">Level 1 - Page 3</a>
            </div>
            <div class="level2">
                <h2>Level 2 Links</h2>
                <a href="https://example.com/level2/section1">Level 2 - Section 1</a>
                <a href="https://example.com/level2/section2">Level 2 - Section 2</a>
            </div>
            <div class="external">
                <h2>External Links (should be ignored)</h2>
                <a href="https://external.com/page1">External Page 1</a>
                <a href="https://external.com/page2">External Page 2</a>
            </div>
        </body>
        </html>
        """
        
        print("Starting URL queue management demonstration...")
        print("This will show how URLs are discovered and queued for crawling.\n")
        
        # Run exhaustive crawling with focus on queue management
        result = await crawler.arun_exhaustive(f"raw:{hierarchical_html}", config=config)
        
        print(f"\n🔄 URL Queue Management Results:")
        print(f"  Total pages processed: {result['total_pages_crawled']}")
        print(f"  URLs discovered and queued: {result['total_urls_discovered']}")
        print(f"  URLs remaining in queue: {result.get('urls_in_queue', 0)}")
        print(f"  Queue processing efficiency: {(result['total_pages_crawled'] / max(1, result['total_urls_discovered'])) * 100:.1f}%")
        
        # Show detailed analytics about URL management
        analytics = result['analytics']
        url_tracking = analytics['url_tracking']
        
        print(f"\n📋 Detailed URL Tracking:")
        print(f"  Discovered: {url_tracking['total_discovered']}")
        print(f"  Successfully crawled: {url_tracking['total_crawled']}")
        print(f"  Failed attempts: {url_tracking['total_failed']}")
        print(f"  Still pending: {url_tracking['pending_count']}")
        print(f"  Overall success rate: {url_tracking['success_rate']:.2%}")
        
        # Show discovery pattern
        discovery_history = analytics.get('discovery_history', [])
        if discovery_history:
            print(f"\n📊 URL Discovery Pattern: {discovery_history}")
            print(f"  Peak discovery: {max(discovery_history)} URLs in one batch")
            print(f"  Average discovery: {sum(discovery_history) / len(discovery_history):.1f} URLs per batch")
        
        return True
        
    except Exception as e:
        print(f"❌ URL queue management example failed: {e}")
        return False
    
    finally:
        if hasattr(crawler, 'close'):
            await crawler.close()


async def main():
    """Run all orchestration examples."""
    print("Exhaustive Crawling Orchestration Examples")
    print("=" * 60)
    print("Demonstrating Task 6: Implement exhaustive crawling orchestration")
    print("- Uses existing arun() as foundation")
    print("- Loop logic to continue until dead-end threshold")
    print("- URL queue management for discovered URLs")
    print("- Progress tracking using existing crawl analytics")
    print()
    
    try:
        # Run all examples
        basic_success = await example_basic_orchestration()
        progress_success = await example_progress_tracking()
        queue_success = await example_url_queue_management()
        
        print("\n" + "=" * 60)
        print("📋 Example Results Summary:")
        print(f"  Basic orchestration: {'✓ PASSED' if basic_success else '❌ FAILED'}")
        print(f"  Progress tracking: {'✓ PASSED' if progress_success else '❌ FAILED'}")
        print(f"  URL queue management: {'✓ PASSED' if queue_success else '❌ FAILED'}")
        
        if all([basic_success, progress_success, queue_success]):
            print("\n🎉 All orchestration examples completed successfully!")
            print("\n🔧 Key Implementation Features:")
            print("✓ arun_exhaustive method using existing arun() as foundation")
            print("✓ Loop logic to continue crawling until dead-end threshold reached")
            print("✓ URL queue management for continuing from discovered URLs")
            print("✓ Progress tracking using existing crawl analytics")
            print("✓ Integration with ExhaustiveAnalytics for dead-end detection")
            print("✓ Robust error handling and resource management")
            print("✓ Batch processing for efficient concurrent crawling")
            print("✓ Real-time monitoring and logging")
        else:
            print("\n❌ Some examples failed - check the output above for details")
            
    except Exception as e:
        print(f"❌ Example suite failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())