#!/usr/bin/env python3
"""
Exhaustive Crawling Analytics and Reporting Example

This example demonstrates the comprehensive analytics and reporting system for
exhaustive crawling, including site mapping completeness analysis, dead-end
detection metrics, file discovery statistics, and comprehensive report generation.
"""

import asyncio
import sys
import json
from pathlib import Path
from datetime import datetime, timedelta

# Add the parent directory to the path to import crawl4ai
sys.path.append(str(Path(__file__).parent.parent))

from crawl4ai import AsyncWebCrawler
from crawl4ai.async_configs import CrawlerRunConfig
from crawl4ai.exhaustive_webcrawler import ExhaustiveAsyncWebCrawler
from crawl4ai.exhaustive_configs import ExhaustiveCrawlConfig
from crawl4ai.exhaustive_analytics_reporting import (
    ExhaustiveAnalyticsReporter,
    create_analytics_reporter,
    generate_site_mapping_report
)
from crawl4ai.exhaustive_monitoring import configure_exhaustive_monitoring
from crawl4ai.site_graph_db import create_site_graph_manager


async def basic_analytics_reporting_example():
    """
    Basic example of analytics and reporting for exhaustive crawling.
    """
    print("📊 Basic Analytics and Reporting Example")
    print("=" * 50)
    
    async with ExhaustiveAsyncWebCrawler(verbose=True) as crawler:
        # Create analytics reporter
        reporter = create_analytics_reporter(logger=crawler.logger)
        
        # Start reporting session
        session_id = reporter.start_reporting_session("https://crawl4ai.com/mkdocs/")
        print(f"🚀 Started analytics session: {session_id}")
        
        # Configure monitoring to work with analytics
        monitor = configure_exhaustive_monitoring(
            crawler=crawler,
            logger=crawler.logger,
            dead_end_threshold=5,  # Low threshold for demo
            revisit_threshold=0.7,
            log_discovery_stats=True
        )
        
        # Add callback to track performance in reporter
        def track_performance(analysis, results=None):
            if results:
                for result in results:
                    if result.success:
                        # Estimate load time and data size
                        load_time = 1.0  # Placeholder
                        data_size = len(result.html) if result.html else 0
                        reporter.track_page_performance(result.url, load_time, data_size)
                    else:
                        reporter.track_error(result.url, result.error_message or "Unknown error")
        
        monitor.add_progress_callback(track_performance)
        
        # Configure exhaustive crawling
        config = ExhaustiveCrawlConfig(
            dead_end_threshold=5,
            revisit_ratio_threshold=0.7,
            max_pages=15,  # Limit for demo
            discover_files_during_crawl=True,
            download_discovered_files=True
        )
        
        print(f"\n🕷️ Starting exhaustive crawl with analytics...")
        
        # Run exhaustive crawling
        result = await crawler.arun_exhaustive(
            start_url="https://crawl4ai.com/mkdocs/",
            config=config
        )
        
        print(f"\n📈 Crawl Results Summary:")
        print(f"   Total pages crawled: {result['total_pages_crawled']}")
        print(f"   Successful pages: {result['successful_pages']}")
        print(f"   URLs discovered: {result['total_urls_discovered']}")
        print(f"   Files discovered: {result.get('total_files_discovered', 0)}")
        print(f"   Stop reason: {result['stop_reason']}")
        
        # Generate comprehensive analytics report
        print(f"\n📊 Generating comprehensive analytics report...")
        
        # Get the analytics from the crawler
        crawler_analytics = getattr(crawler, '_analytics', None)
        if not crawler_analytics:
            print("⚠️ No analytics data available from crawler")
            return
        
        comprehensive_report = await reporter.generate_comprehensive_report(
            "https://crawl4ai.com/mkdocs/",
            crawler_analytics,
            session_id
        )
        
        # Display report summary
        print(f"\n📋 Comprehensive Report Summary:")
        print(f"   Report ID: {comprehensive_report.crawl_session_id}")
        print(f"   Base URL: {comprehensive_report.base_url}")
        print(f"   Generated at: {comprehensive_report.report_generated_at}")
        
        if comprehensive_report.site_mapping_completeness:
            smc = comprehensive_report.site_mapping_completeness
            print(f"\n🗺️ Site Mapping Completeness:")
            print(f"   Pages discovered: {smc.total_pages_discovered}")
            print(f"   Pages crawled: {smc.total_pages_crawled}")
            print(f"   Coverage: {smc.coverage_percentage:.1f}%")
            print(f"   Crawl efficiency: {smc.crawl_efficiency:.1f}%")
            print(f"   Discovery rate: {smc.discovery_rate:.2f}")
        
        if comprehensive_report.file_discovery_stats:
            fds = comprehensive_report.file_discovery_stats
            print(f"\n📁 File Discovery Statistics:")
            print(f"   Files discovered: {fds.total_files_discovered}")
            print(f"   Files downloaded: {fds.total_files_downloaded}")
            print(f"   Download success rate: {fds.download_success_rate:.1f}%")
            print(f"   Total download size: {fds.total_download_size:,} bytes")
            if fds.file_type_distribution:
                print(f"   File types: {dict(fds.file_type_distribution)}")
        
        if comprehensive_report.dead_end_analysis:
            dea = comprehensive_report.dead_end_analysis
            print(f"\n🛑 Dead-End Analysis:")
            print(f"   Consecutive dead pages: {dea.consecutive_dead_pages}")
            print(f"   Revisit ratio: {dea.revisit_ratio:.2%}")
            print(f"   Termination reason: {dea.crawl_termination_reason}")
            print(f"   Efficiency decline detected: {dea.efficiency_decline_detected}")
        
        # Performance metrics
        print(f"\n⚡ Performance Metrics:")
        print(f"   Pages per minute: {comprehensive_report.pages_per_minute:.2f}")
        print(f"   Average page load time: {comprehensive_report.average_page_load_time:.2f}s")
        print(f"   Total data processed: {comprehensive_report.total_data_processed:,} bytes")
        
        # Quality scores
        print(f"\n🎯 Quality Scores:")
        print(f"   Content quality: {comprehensive_report.content_quality_score:.1f}/100")
        print(f"   Link integrity: {comprehensive_report.link_integrity_score:.1f}/100")
        print(f"   Site structure: {comprehensive_report.site_structure_score:.1f}/100")
        
        # Recommendations
        if comprehensive_report.optimization_recommendations:
            print(f"\n💡 Optimization Recommendations:")
            for i, rec in enumerate(comprehensive_report.optimization_recommendations, 1):
                print(f"   {i}. {rec}")
        
        if comprehensive_report.crawl_strategy_suggestions:
            print(f"\n🎯 Crawl Strategy Suggestions:")
            for i, suggestion in enumerate(comprehensive_report.crawl_strategy_suggestions, 1):
                print(f"   {i}. {suggestion}")
        
        # Export report to JSON
        output_path = f"exhaustive_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        exported_path = await reporter.export_report_to_json(comprehensive_report, output_path)
        print(f"\n💾 Report exported to: {exported_path}")
        
        return comprehensive_report


async def site_mapping_completeness_analysis_example():
    """
    Example focusing on site mapping completeness analysis.
    """
    print("\n🗺️ Site Mapping Completeness Analysis Example")
    print("=" * 50)
    
    async with AsyncWebCrawler(verbose=True) as crawler:
        # Create analytics reporter
        reporter = create_analytics_reporter(logger=crawler.logger)
        
        # Start reporting session
        session_id = reporter.start_reporting_session("https://crawl4ai.com/mkdocs/")
        
        # Crawl multiple pages to build site graph
        test_urls = [
            "https://crawl4ai.com/mkdocs/",
            "https://crawl4ai.com/mkdocs/first-steps/",
            "https://crawl4ai.com/mkdocs/basic-usage/",
            "https://crawl4ai.com/mkdocs/advanced-features/",
            "https://crawl4ai.com/mkdocs/api-reference/"
        ]
        
        config = CrawlerRunConfig(
            word_count_threshold=10
        )
        
        print(f"🕷️ Crawling {len(test_urls)} pages for site mapping analysis...")
        
        # Crawl pages and track performance
        for i, url in enumerate(test_urls, 1):
            print(f"   {i}/{len(test_urls)}: {url}")
            
            start_time = datetime.now()
            result = await crawler.arun(url, config=config)
            end_time = datetime.now()
            
            load_time = (end_time - start_time).total_seconds()
            data_size = len(result.html) if result.html else 0
            
            if result.success:
                reporter.track_page_performance(url, load_time, data_size)
                print(f"      ✅ Success: {load_time:.2f}s, {data_size:,} bytes")
            else:
                reporter.track_error(url, result.error_message or "Unknown error")
                print(f"      ❌ Failed: {result.error_message}")
        
        # Analyze site mapping completeness
        print(f"\n📊 Analyzing site mapping completeness...")
        
        completeness = await reporter.analyze_site_mapping_completeness("https://crawl4ai.com/mkdocs/")
        
        print(f"\n📋 Site Mapping Completeness Results:")
        print(f"   Base URL: {completeness.base_url}")
        print(f"   Total pages discovered: {completeness.total_pages_discovered}")
        print(f"   Total pages crawled: {completeness.total_pages_crawled}")
        print(f"   Successful pages: {completeness.total_pages_successful}")
        print(f"   Failed pages: {completeness.total_pages_failed}")
        print(f"   Coverage percentage: {completeness.coverage_percentage:.1f}%")
        print(f"   Crawl efficiency: {completeness.crawl_efficiency:.1f}%")
        print(f"   Discovery rate: {completeness.discovery_rate:.2f}")
        
        if completeness.depth_distribution:
            print(f"\n📏 Depth Distribution:")
            for depth, count in sorted(completeness.depth_distribution.items()):
                print(f"      Depth {depth}: {count} pages")
        
        if completeness.content_type_distribution:
            print(f"\n📄 Content Type Distribution:")
            for content_type, count in completeness.content_type_distribution.items():
                print(f"      {content_type}: {count} pages")
        
        if completeness.status_code_distribution:
            print(f"\n🔢 Status Code Distribution:")
            for status_code, count in sorted(completeness.status_code_distribution.items()):
                print(f"      {status_code}: {count} pages")


async def file_discovery_analytics_example():
    """
    Example focusing on file discovery and download analytics.
    """
    print("\n📁 File Discovery Analytics Example")
    print("=" * 50)
    
    async with ExhaustiveAsyncWebCrawler(verbose=True) as crawler:
        # Create analytics reporter
        reporter = create_analytics_reporter(logger=crawler.logger)
        
        # Start reporting session
        session_id = reporter.start_reporting_session("https://crawl4ai.com/")
        
        # Configure for file discovery
        config = ExhaustiveCrawlConfig(
            discover_files_during_crawl=True,
            download_discovered_files=True,
            file_extensions_whitelist=['.pdf', '.doc', '.docx', '.txt', '.json'],
            max_pages=10,  # Limit for demo
        )
        
        print(f"🔍 Starting crawl with file discovery enabled...")
        
        # Run crawl with file discovery
        result = await crawler.arun_exhaustive(
            start_url="https://crawl4ai.com/",
            config=config
        )
        
        print(f"\n📈 File Discovery Results:")
        print(f"   Total files discovered: {result.get('total_files_discovered', 0)}")
        print(f"   Files downloaded: {result.get('files_downloaded', 0)}")
        print(f"   Download failures: {result.get('download_failures', 0)}")
        
        # Analyze file discovery statistics
        print(f"\n📊 Analyzing file discovery statistics...")
        
        file_stats = await reporter.analyze_file_discovery_stats("https://crawl4ai.com/")
        
        print(f"\n📋 File Discovery Statistics:")
        print(f"   Base URL: {file_stats.base_url}")
        print(f"   Total files discovered: {file_stats.total_files_discovered}")
        print(f"   Total files downloaded: {file_stats.total_files_downloaded}")
        print(f"   Total files failed: {file_stats.total_files_failed}")
        print(f"   Download success rate: {file_stats.download_success_rate:.1f}%")
        print(f"   Total download size: {file_stats.total_download_size:,} bytes")
        print(f"   Average file size: {file_stats.average_file_size:,.0f} bytes")
        
        if file_stats.largest_file_size > 0:
            print(f"   Largest file: {file_stats.largest_file_size:,} bytes")
            print(f"   Smallest file: {file_stats.smallest_file_size:,} bytes")
        
        if file_stats.file_type_distribution:
            print(f"\n📄 File Type Distribution:")
            for file_type, count in sorted(file_stats.file_type_distribution.items()):
                print(f"      {file_type}: {count} files")
        
        if file_stats.download_status_distribution:
            print(f"\n📊 Download Status Distribution:")
            for status, count in file_stats.download_status_distribution.items():
                print(f"      {status}: {count} files")


async def dead_end_detection_analytics_example():
    """
    Example focusing on dead-end detection analytics.
    """
    print("\n🛑 Dead-End Detection Analytics Example")
    print("=" * 50)
    
    async with ExhaustiveAsyncWebCrawler(verbose=True) as crawler:
        # Create analytics reporter
        reporter = create_analytics_reporter(logger=crawler.logger)
        
        # Configure monitoring with low thresholds for demo
        monitor = configure_exhaustive_monitoring(
            crawler=crawler,
            logger=crawler.logger,
            dead_end_threshold=3,  # Very low for demo
            revisit_threshold=0.5,
            log_discovery_stats=True
        )
        
        # Add callback to analyze dead-end patterns
        def analyze_dead_end(reason: str, analysis: dict):
            print(f"\n🛑 Dead-end detected: {reason}")
            print(f"   Analysis data: {analysis}")
            
            # Get current analytics from crawler
            if hasattr(crawler, '_analytics'):
                dead_end_analysis = reporter.analyze_dead_end_detection(crawler._analytics)
                
                print(f"\n📊 Dead-End Analysis Results:")
                print(f"   Consecutive dead pages: {dead_end_analysis.consecutive_dead_pages}")
                print(f"   Revisit ratio: {dead_end_analysis.revisit_ratio:.2%}")
                print(f"   Threshold reached: {dead_end_analysis.dead_end_threshold_reached}")
                print(f"   Efficiency decline: {dead_end_analysis.efficiency_decline_detected}")
                print(f"   Termination reason: {dead_end_analysis.crawl_termination_reason}")
                
                if dead_end_analysis.dead_end_patterns:
                    print(f"   Dead-end patterns: {dict(dead_end_analysis.dead_end_patterns)}")
        
        monitor.add_dead_end_callback(analyze_dead_end)
        
        # Configure exhaustive crawling with aggressive settings
        config = ExhaustiveCrawlConfig(
            dead_end_threshold=3,
            revisit_ratio_threshold=0.5,
            max_pages=8,  # Small limit to trigger dead-end
        )
        
        print(f"🕷️ Starting crawl with aggressive dead-end detection...")
        
        # Run exhaustive crawling
        result = await crawler.arun_exhaustive(
            start_url="https://crawl4ai.com/mkdocs/",
            config=config
        )
        
        print(f"\n📈 Final Results:")
        print(f"   Total pages crawled: {result['total_pages_crawled']}")
        print(f"   Stop reason: {result['stop_reason']}")
        
        # Final dead-end analysis
        if hasattr(crawler, '_analytics'):
            final_analysis = reporter.analyze_dead_end_detection(crawler._analytics)
            
            print(f"\n🔍 Final Dead-End Analysis:")
            print(f"   Discovery rate trend: {final_analysis.discovery_rate_trend}")
            print(f"   Time since last discovery: {final_analysis.time_since_last_discovery}")
            print(f"   Final termination reason: {final_analysis.crawl_termination_reason}")


async def comprehensive_report_generation_example():
    """
    Example showing comprehensive report generation and export.
    """
    print("\n📊 Comprehensive Report Generation Example")
    print("=" * 50)
    
    # Use the convenience function for complete workflow
    print(f"🚀 Using convenience function for complete analytics workflow...")
    
    async with ExhaustiveAsyncWebCrawler(verbose=True) as crawler:
        # Configure exhaustive crawling
        config = ExhaustiveCrawlConfig(
            dead_end_threshold=8,
            revisit_ratio_threshold=0.8,
            max_pages=12,
            discover_files_during_crawl=True,
            download_discovered_files=True
        )
        
        # Run exhaustive crawling
        result = await crawler.arun_exhaustive(
            start_url="https://crawl4ai.com/mkdocs/",
            config=config
        )
        
        print(f"\n📈 Crawl completed:")
        print(f"   Pages crawled: {result['total_pages_crawled']}")
        print(f"   Stop reason: {result['stop_reason']}")
        
        # Generate comprehensive report using convenience function
        if hasattr(crawler, '_analytics'):
            print(f"\n📊 Generating comprehensive report...")
            
            report_path = await generate_site_mapping_report(
                base_url="https://crawl4ai.com/mkdocs/",
                analytics=crawler._analytics,
                output_path=f"comprehensive_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            )
            
            print(f"✅ Comprehensive report generated: {report_path}")
            
            # Display report summary
            with open(report_path, 'r') as f:
                report_data = json.load(f)
            
            print(f"\n📋 Report Summary:")
            print(f"   Base URL: {report_data['base_url']}")
            print(f"   Session ID: {report_data['crawl_session_id']}")
            print(f"   Generated at: {report_data['report_generated_at']}")
            
            if 'site_mapping_completeness' in report_data:
                smc = report_data['site_mapping_completeness']
                print(f"   Site coverage: {smc['coverage_percentage']:.1f}%")
                print(f"   Crawl efficiency: {smc['crawl_efficiency']:.1f}%")
            
            if 'optimization_recommendations' in report_data:
                print(f"   Recommendations: {len(report_data['optimization_recommendations'])}")
                for rec in report_data['optimization_recommendations'][:3]:  # Show first 3
                    print(f"      • {rec}")
        else:
            print("⚠️ No analytics data available from crawler")


async def main():
    """Run all analytics and reporting examples."""
    print("📊 Exhaustive Crawling Analytics and Reporting Examples")
    print("=" * 60)
    
    try:
        # Run basic analytics and reporting example
        await basic_analytics_reporting_example()
        
        # Run site mapping completeness analysis
        await site_mapping_completeness_analysis_example()
        
        # Run file discovery analytics example
        await file_discovery_analytics_example()
        
        # Run dead-end detection analytics example
        await dead_end_detection_analytics_example()
        
        # Run comprehensive report generation example
        await comprehensive_report_generation_example()
        
        print("\n✅ All analytics and reporting examples completed successfully!")
        
    except KeyboardInterrupt:
        print("\n⏹️ Examples interrupted by user")
    except Exception as e:
        print(f"\n❌ Error running examples: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Run the examples
    asyncio.run(main())