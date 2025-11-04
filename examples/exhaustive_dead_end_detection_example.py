#!/usr/bin/env python3
"""
Example: Exhaustive Crawling with Dead-End Detection

This example demonstrates how to use the new dead-end detection functionality
implemented in task 3. It shows how to:

1. Use ExhaustiveAnalytics for URL discovery rate analysis
2. Implement dead-end detection with configurable thresholds
3. Track revisit ratios and URL discovery patterns
4. Integrate with existing AsyncWebCrawler analytics

Requirements covered:
- 2.4: Strategic discovery with dead-end detection
- 6.4: Real-time processing with URL tracking
- 7.1: Analytics for crawling performance
"""

import asyncio
import sys
import os

# Add crawl4ai to path for this example
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig
from crawl4ai.exhaustive_analytics import ExhaustiveAnalytics
from crawl4ai.exhaustive_integration import configure_exhaustive_crawler
from crawl4ai.async_logger import AsyncLogger


async def example_basic_dead_end_detection():
    """
    Basic example of dead-end detection using ExhaustiveAnalytics.
    """
    print("=== Basic Dead-End Detection Example ===\n")
    
    # Create analytics engine
    logger = AsyncLogger(verbose=True)
    analytics = ExhaustiveAnalytics(logger=logger)
    
    # Start a crawl session
    analytics.start_crawl_session()
    
    # Simulate crawling results with decreasing URL discovery
    print("Simulating crawl results with decreasing URL discovery...\n")
    
    # Mock crawl results (in real usage, these come from AsyncWebCrawler.arun())
    mock_results = [
        # First batch: many new URLs discovered
        {
            'url': 'https://example.com',
            'links': {'internal': [{'href': f'https://example.com/page{i}'} for i in range(10)]}
        },
        # Second batch: fewer URLs
        {
            'url': 'https://example.com/page1', 
            'links': {'internal': [{'href': f'https://example.com/sub{i}'} for i in range(5)]}
        },
        # Third batch: very few URLs
        {
            'url': 'https://example.com/page2',
            'links': {'internal': [{'href': 'https://example.com/final'}]}
        },
        # Fourth batch: no new URLs (dead end)
        {
            'url': 'https://example.com/page3',
            'links': {'internal': []}
        }
    ]
    
    # Process each batch and analyze
    for i, mock_result in enumerate(mock_results, 1):
        print(f"Processing batch {i}...")
        
        # In real usage, you'd get CrawlResult objects from crawler.arun()
        # Here we simulate the analysis
        from crawl4ai.models import CrawlResult, MarkdownGenerationResult
        
        # Create mock CrawlResult
        result = CrawlResult(
            url=mock_result['url'],
            html="<html>Mock content</html>",
            success=True,
            markdown=MarkdownGenerationResult(
                raw_markdown="Mock content",
                markdown_with_citations="Mock content",
                references_markdown=""
            ),
            links=mock_result['links'],
            metadata={'depth': i-1}
        )
        
        # Analyze the results
        analysis = analytics.analyze_crawl_results([result], mock_result['url'])
        
        print(f"  New URLs discovered: {analysis['new_urls_discovered']}")
        print(f"  Consecutive dead pages: {analysis['consecutive_dead_pages']}")
        print(f"  Revisit ratio: {analysis['revisit_ratio']:.2%}")
        print(f"  Should continue: {analysis['should_continue']}")
        
        # Check if we should stop
        should_stop, reason = analytics.should_stop_crawling(
            dead_end_threshold=3,  # Stop after 3 consecutive dead pages
            revisit_threshold=0.8   # Stop if 80% of URLs are revisits
        )
        
        if should_stop:
            print(f"  🛑 Stopping crawl: {reason}")
            break
        
        print()
    
    # Get final statistics
    stats = analytics.get_comprehensive_stats()
    print("Final Statistics:")
    print(f"  Total URLs discovered: {stats['session_stats']['total_urls_discovered']}")
    print(f"  Total crawl attempts: {stats['session_stats']['total_crawl_attempts']}")
    print(f"  Discovery rate history: {stats['discovery_history']}")
    print()


async def example_integration_with_crawler():
    """
    Example of integrating dead-end detection with AsyncWebCrawler.
    """
    print("=== Integration with AsyncWebCrawler Example ===\n")
    
    try:
        # Create crawler with headless browser
        browser_config = BrowserConfig(headless=True)
        crawler = AsyncWebCrawler(config=browser_config)
        
        # Configure exhaustive crawling integration
        integration = configure_exhaustive_crawler(crawler)
        
        # Add event handlers for dead-end detection
        async def on_page_processed(result, analysis):
            print(f"Page processed: {result.url}")
            print(f"  New URLs: {analysis['new_urls_discovered']}")
            print(f"  Dead pages: {analysis['consecutive_dead_pages']}")
        
        async def on_crawl_completed(event_data):
            print(f"Crawl batch completed:")
            print(f"  Results: {len(event_data['results'])}")
            print(f"  Should stop: {event_data['should_stop']}")
            if event_data['should_stop']:
                print(f"  Reason: {event_data['stop_reason']}")
        
        # Register event handlers
        integration.add_event_handler('on_page_processed', on_page_processed)
        integration.add_event_handler('on_crawl_completed', on_crawl_completed)
        
        print("Integration configured successfully!")
        print("In a real scenario, you would now call crawler.arun() or crawler.arun_many()")
        print("and the dead-end detection would work automatically.\n")
        
        # Get current metrics
        metrics = integration.get_current_metrics()
        print("Current metrics:", metrics['session_stats'])
        
    except ImportError as e:
        print(f"Skipping crawler integration example due to missing dependencies: {e}")


async def example_url_discovery_analysis():
    """
    Example of standalone URL discovery rate analysis.
    """
    print("=== URL Discovery Rate Analysis Example ===\n")
    
    from crawl4ai.exhaustive_integration import analyze_url_discovery_rate
    from crawl4ai.models import CrawlResult, MarkdownGenerationResult
    
    # Create mock results with different link patterns
    results = []
    
    # Result with many internal links
    result1 = CrawlResult(
        url="https://example.com/hub",
        html="<html>Hub page</html>",
        success=True,
        markdown=MarkdownGenerationResult(
            raw_markdown="Hub page content",
            markdown_with_citations="Hub page content",
            references_markdown=""
        ),
        links={
            'internal': [{'href': f'https://example.com/category{i}'} for i in range(8)],
            'external': [{'href': 'https://external.com/link1'}]
        }
    )
    results.append(result1)
    
    # Result with few links
    result2 = CrawlResult(
        url="https://example.com/category1",
        html="<html>Category page</html>",
        success=True,
        markdown=MarkdownGenerationResult(
            raw_markdown="Category content",
            markdown_with_citations="Category content", 
            references_markdown=""
        ),
        links={
            'internal': [{'href': 'https://example.com/item1'}, {'href': 'https://example.com/item2'}],
            'external': []
        }
    )
    results.append(result2)
    
    # Analyze discovery rate
    analysis = analyze_url_discovery_rate(results)
    
    print("URL Discovery Analysis Results:")
    print(f"  New URLs discovered: {analysis['new_urls_discovered']}")
    print(f"  Total links found: {analysis['total_links_found']}")
    print(f"  Consecutive dead pages: {analysis['consecutive_dead_pages']}")
    print(f"  Should continue crawling: {analysis['should_continue']}")
    print()


async def main():
    """Run all examples."""
    print("Exhaustive Crawling Dead-End Detection Examples\n")
    print("This demonstrates the implementation of task 3:")
    print("- Dead-end detection using existing AsyncWebCrawler analytics")
    print("- URL discovery rate analysis")
    print("- Revisit ratio calculation")
    print("- Integration with existing crawl infrastructure\n")
    
    try:
        await example_basic_dead_end_detection()
        await example_integration_with_crawler()
        await example_url_discovery_analysis()
        
        print("🎉 All examples completed successfully!")
        print("\nKey Features Demonstrated:")
        print("✓ Dead-end detection with configurable thresholds")
        print("✓ URL discovery rate monitoring")
        print("✓ Revisit ratio calculation")
        print("✓ Integration with existing AsyncWebCrawler analytics")
        print("✓ Real-time crawl progress tracking")
        
    except Exception as e:
        print(f"❌ Example failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())