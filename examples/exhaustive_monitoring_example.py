#!/usr/bin/env python3
"""
Exhaustive Crawling Monitoring Example

This example demonstrates how to use the AsyncWebCrawler event system for
real-time monitoring of exhaustive crawling with dead-end detection and
URL discovery analytics.
"""

import asyncio
import sys
from pathlib import Path

# Add the parent directory to the path to import crawl4ai
sys.path.append(str(Path(__file__).parent.parent))

from crawl4ai import AsyncWebCrawler
from crawl4ai.async_configs import CrawlerRunConfig
from crawl4ai.exhaustive_monitoring import (
    configure_exhaustive_monitoring,
    create_dead_end_detection_handler,
    create_progress_reporting_handler
)


async def basic_monitoring_example():
    """
    Basic example of exhaustive crawling monitoring using the event system.
    """
    print("🔍 Basic Exhaustive Crawling Monitoring Example")
    print("=" * 50)
    
    async with AsyncWebCrawler(verbose=True) as crawler:
        # Configure exhaustive monitoring with the crawler
        monitor = configure_exhaustive_monitoring(
            crawler=crawler,
            logger=crawler.logger,
            dead_end_threshold=10,  # Lower threshold for demo
            revisit_threshold=0.8,  # Lower threshold for demo
            log_discovery_stats=True
        )
        
        # Add custom callbacks for dead-end detection
        def on_dead_end_detected(reason: str, analysis: dict):
            print(f"\n🛑 DEAD END DETECTED: {reason}")
            print(f"   Analysis: {analysis}")
        
        def on_progress_update(analysis: dict, results=None):
            if results:
                print(f"📊 Progress: {len(results)} pages processed, "
                      f"{analysis['new_urls_discovered']} new URLs discovered")
        
        monitor.add_dead_end_callback(on_dead_end_detected)
        monitor.add_progress_callback(on_progress_update)
        
        # Start crawling with monitoring
        print(f"\n🚀 Starting monitored crawl...")
        
        # Crawl a few pages to demonstrate monitoring
        test_urls = [
            "https://crawl4ai.com/mkdocs/",
            "https://crawl4ai.com/mkdocs/first-steps/",
            "https://crawl4ai.com/mkdocs/basic-usage/"
        ]
        
        config = CrawlerRunConfig(
            word_count_threshold=10,
            verbose=True
        )
        
        for url in test_urls:
            print(f"\n📄 Crawling: {url}")
            result = await crawler.arun(url, config=config)
            
            if result.success:
                print(f"   ✅ Success: {len(result.markdown)} chars")
            else:
                print(f"   ❌ Failed: {result.error_message}")
            
            # Get current monitoring metrics
            metrics = monitor.get_current_metrics()
            print(f"   📈 Metrics: {metrics.consecutive_dead_pages} dead pages, "
                  f"{metrics.revisit_ratio:.2%} revisit ratio")
        
        # Get final comprehensive stats
        final_stats = monitor.get_comprehensive_stats()
        print(f"\n📊 Final Statistics:")
        print(f"   Total URLs discovered: {final_stats['session_stats']['total_urls_discovered']}")
        print(f"   Total crawl attempts: {final_stats['session_stats']['total_crawl_attempts']}")
        print(f"   Session duration: {final_stats['session_stats']['crawl_duration']}")
        
        # Stop monitoring
        monitor.stop_monitoring(crawler)


async def custom_event_handlers_example():
    """
    Example showing how to create and register custom event handlers.
    """
    print("\n🎯 Custom Event Handlers Example")
    print("=" * 50)
    
    async with AsyncWebCrawler(verbose=True) as crawler:
        # Create custom dead-end detection handler
        dead_end_handler = create_dead_end_detection_handler(
            dead_end_threshold=5,
            revisit_threshold=0.7,
            logger=crawler.logger
        )
        
        # Create custom progress reporting handler
        progress_handler = create_progress_reporting_handler(
            logger=crawler.logger,
            log_interval_seconds=10
        )
        
        # Register custom event handlers directly with crawler
        crawler.add_event_handler('page_processed', 
                                lambda result: print(f"📄 Page processed: {result.url}"))
        
        crawler.add_event_handler('crawl_completed', dead_end_handler)
        crawler.add_event_handler('crawl_completed', progress_handler)
        
        # Custom URL discovery handler
        async def url_discovery_handler(result):
            if result.success and hasattr(result, 'links') and result.links:
                internal_count = len(result.links.get('internal', []))
                external_count = len(result.links.get('external', []))
                print(f"🔗 URLs discovered: {internal_count} internal, {external_count} external")
        
        crawler.add_event_handler('page_processed', url_discovery_handler)
        
        # Test crawling with custom handlers
        print(f"\n🚀 Starting crawl with custom handlers...")
        
        test_urls = [
            "https://crawl4ai.com/mkdocs/",
            "https://crawl4ai.com/mkdocs/basic-usage/"
        ]
        
        config = CrawlerRunConfig(
            word_count_threshold=10,
            verbose=True
        )
        
        # Use arun_many to trigger crawl_completed events
        results = await crawler.arun_many(test_urls, config=config)
        
        print(f"\n✅ Completed crawling {len(results)} URLs")
        for i, result in enumerate(results):
            if result.success:
                print(f"   {i+1}. {result.url}: {len(result.markdown)} chars")
            else:
                print(f"   {i+1}. {result.url}: FAILED - {result.error_message}")


async def monitoring_with_exhaustive_crawler_example():
    """
    Example showing monitoring integration with ExhaustiveAsyncWebCrawler.
    """
    print("\n🔄 Monitoring with Exhaustive Crawler Example")
    print("=" * 50)
    
    # Import ExhaustiveAsyncWebCrawler
    from crawl4ai.exhaustive_webcrawler import ExhaustiveAsyncWebCrawler
    from crawl4ai.exhaustive_configs import ExhaustiveCrawlConfig
    
    async with ExhaustiveAsyncWebCrawler(verbose=True) as crawler:
        # Configure monitoring for exhaustive crawler
        monitor = configure_exhaustive_monitoring(
            crawler=crawler,
            logger=crawler.logger,
            dead_end_threshold=3,  # Very low for demo
            revisit_threshold=0.6,
            log_discovery_stats=True
        )
        
        # Add callback to stop exhaustive crawling on dead-end
        async def stop_on_dead_end(reason: str, analysis: dict):
            print(f"\n🛑 Stopping exhaustive crawl: {reason}")
            await crawler.stop_exhaustive_crawling()
        
        monitor.add_dead_end_callback(stop_on_dead_end)
        
        # Configure exhaustive crawling
        config = ExhaustiveCrawlConfig(
            word_count_threshold=10,
            dead_end_threshold=3,
            revisit_ratio=0.6,
            exhaustive_max_pages=10,  # Limit for demo
            batch_size=2,
            log_discovery_stats=True,
            verbose=True
        )
        
        print(f"\n🚀 Starting exhaustive crawl with monitoring...")
        
        # Run exhaustive crawling
        result = await crawler.arun_exhaustive(
            start_url="https://crawl4ai.com/mkdocs/",
            config=config
        )
        
        print(f"\n📊 Exhaustive Crawl Results:")
        print(f"   Total pages crawled: {result['total_pages_crawled']}")
        print(f"   Successful pages: {result['successful_pages']}")
        print(f"   URLs discovered: {result['total_urls_discovered']}")
        print(f"   Stop reason: {result['stop_reason']}")
        
        # Get monitoring statistics
        monitor_stats = monitor.get_comprehensive_stats()
        print(f"\n📈 Monitoring Statistics:")
        print(f"   Session duration: {monitor_stats['session_stats']['crawl_duration']}")
        print(f"   Dead pages detected: {monitor_stats['session_stats']['consecutive_dead_pages']}")
        print(f"   Final revisit ratio: {monitor_stats['session_stats']['revisit_ratio']:.2%}")


async def main():
    """Run all monitoring examples."""
    print("🕷️ Exhaustive Crawling Monitoring Examples")
    print("=" * 60)
    
    try:
        # Run basic monitoring example
        await basic_monitoring_example()
        
        # Run custom event handlers example
        await custom_event_handlers_example()
        
        # Run monitoring with exhaustive crawler example
        await monitoring_with_exhaustive_crawler_example()
        
        print("\n✅ All monitoring examples completed successfully!")
        
    except KeyboardInterrupt:
        print("\n⏹️ Examples interrupted by user")
    except Exception as e:
        print(f"\n❌ Error running examples: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Run the examples
    asyncio.run(main())