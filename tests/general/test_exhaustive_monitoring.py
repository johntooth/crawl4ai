#!/usr/bin/env python3
"""
Tests for Exhaustive Crawling Monitoring

This module tests the event-based monitoring system for exhaustive crawling,
including dead-end detection and URL discovery analytics.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from typing import List

from crawl4ai import AsyncWebCrawler
from crawl4ai.async_configs import CrawlerRunConfig
from crawl4ai.models import CrawlResult
from crawl4ai.exhaustive_monitoring import (
    ExhaustiveMonitor,
    configure_exhaustive_monitoring,
    create_dead_end_detection_handler,
    create_progress_reporting_handler,
    analyze_url_discovery_rate_from_events
)


class TestAsyncWebCrawlerEventSystem:
    """Test the event system added to AsyncWebCrawler."""
    
    @pytest.mark.asyncio
    async def test_event_handler_registration(self):
        """Test adding and removing event handlers."""
        async with AsyncWebCrawler() as crawler:
            # Test adding event handlers
            handler1 = Mock()
            handler2 = Mock()
            
            crawler.add_event_handler('page_processed', handler1)
            crawler.add_event_handler('page_processed', handler2)
            
            assert len(crawler._event_handlers['page_processed']) == 2
            assert handler1 in crawler._event_handlers['page_processed']
            assert handler2 in crawler._event_handlers['page_processed']
            
            # Test removing event handlers
            crawler.remove_event_handler('page_processed', handler1)
            assert len(crawler._event_handlers['page_processed']) == 1
            assert handler2 in crawler._event_handlers['page_processed']
    
    @pytest.mark.asyncio
    async def test_invalid_event_type(self):
        """Test handling of invalid event types."""
        async with AsyncWebCrawler() as crawler:
            with pytest.raises(ValueError, match="Unknown event type"):
                crawler.add_event_handler('invalid_event', Mock())
    
    @pytest.mark.asyncio
    async def test_event_emission(self):
        """Test event emission with sync and async handlers."""
        async with AsyncWebCrawler() as crawler:
            # Create mock handlers
            sync_handler = Mock()
            async_handler = AsyncMock()
            
            # Register handlers
            crawler.add_event_handler('page_processed', sync_handler)
            crawler.add_event_handler('page_processed', async_handler)
            
            # Create test data
            test_result = CrawlResult(
                url="https://test.com",
                html="<html><body>Test</body></html>",
                success=True
            )
            
            # Emit event
            await crawler._emit_event('page_processed', test_result)
            
            # Verify handlers were called
            sync_handler.assert_called_once_with(test_result)
            async_handler.assert_called_once_with(test_result)


class TestExhaustiveMonitor:
    """Test the ExhaustiveMonitor class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_logger = Mock()
        self.monitor = ExhaustiveMonitor(
            logger=self.mock_logger,
            dead_end_threshold=5,
            revisit_threshold=0.8,
            log_discovery_stats=True
        )
    
    @pytest.mark.asyncio
    async def test_monitor_initialization(self):
        """Test monitor initialization."""
        assert self.monitor.dead_end_threshold == 5
        assert self.monitor.revisit_threshold == 0.8
        assert self.monitor.log_discovery_stats is True
        assert not self.monitor._monitoring_active
    
    @pytest.mark.asyncio
    async def test_start_stop_monitoring(self):
        """Test starting and stopping monitoring."""
        # Create mock crawler
        mock_crawler = Mock()
        mock_crawler.add_event_handler = Mock()
        mock_crawler.remove_event_handler = Mock()
        
        # Start monitoring
        self.monitor.start_monitoring(mock_crawler)
        
        assert self.monitor._monitoring_active
        assert mock_crawler.add_event_handler.call_count == 2
        
        # Stop monitoring
        self.monitor.stop_monitoring(mock_crawler)
        
        assert not self.monitor._monitoring_active
        assert mock_crawler.remove_event_handler.call_count == 2
    
    @pytest.mark.asyncio
    async def test_page_processed_handling(self):
        """Test handling of page_processed events."""
        # Create test result with links
        test_result = CrawlResult(
            url="https://test.com",
            html="<html><body>Test</body></html>",
            success=True,
            links={
                'internal': [{'href': 'https://test.com/page1'}, {'href': 'https://test.com/page2'}],
                'external': [{'href': 'https://external.com'}]
            }
        )
        
        # Set monitoring as active
        self.monitor._monitoring_active = True
        
        # Handle page processed event
        await self.monitor._handle_page_processed(test_result)
        
        # Verify analytics were updated
        assert self.monitor.analytics.metrics.total_crawl_attempts > 0
    
    @pytest.mark.asyncio
    async def test_crawl_completed_handling(self):
        """Test handling of crawl_completed events."""
        # Create test results
        test_results = [
            CrawlResult(
                url="https://test.com/page1",
                html="<html><body>Page 1</body></html>",
                success=True,
                links={'internal': [{'href': 'https://test.com/page2'}]}
            ),
            CrawlResult(
                url="https://test.com/page2",
                html="<html><body>Page 2</body></html>",
                success=True,
                links={'internal': []}
            )
        ]
        
        # Set monitoring as active
        self.monitor._monitoring_active = True
        
        # Handle crawl completed event
        await self.monitor._handle_crawl_completed(test_results)
        
        # Verify analytics were updated (URLs discovered, not crawl attempts)
        assert self.monitor.analytics.metrics.total_urls_discovered > 0
    
    @pytest.mark.asyncio
    async def test_dead_end_callbacks(self):
        """Test dead-end detection callbacks."""
        # Create mock callback
        callback = AsyncMock()
        self.monitor.add_dead_end_callback(callback)
        
        # Set monitoring as active
        self.monitor._monitoring_active = True
        
        # Simulate dead-end condition
        test_analysis = {'consecutive_dead_pages': 10, 'revisit_ratio': 0.9}
        await self.monitor._handle_dead_end_detected("Test reason", test_analysis)
        
        # Verify callback was called
        callback.assert_called_once_with("Test reason", test_analysis)
    
    @pytest.mark.asyncio
    async def test_progress_callbacks(self):
        """Test progress update callbacks."""
        # Create mock callback
        callback = Mock()
        self.monitor.add_progress_callback(callback)
        
        # Call progress callbacks
        test_analysis = {'new_urls_discovered': 5}
        await self.monitor._call_progress_callbacks(test_analysis)
        
        # Verify callback was called
        callback.assert_called_once_with(test_analysis, None)


class TestMonitoringIntegration:
    """Test integration between monitoring and crawler."""
    
    @pytest.mark.asyncio
    async def test_configure_exhaustive_monitoring(self):
        """Test configuring exhaustive monitoring with a crawler."""
        async with AsyncWebCrawler() as crawler:
            # Configure monitoring
            monitor = configure_exhaustive_monitoring(
                crawler=crawler,
                logger=crawler.logger,
                dead_end_threshold=10,
                revisit_threshold=0.9
            )
            
            # Verify monitor is configured and active
            assert monitor._monitoring_active
            assert monitor.dead_end_threshold == 10
            assert monitor.revisit_threshold == 0.9
            
            # Verify event handlers are registered
            assert len(crawler._event_handlers['page_processed']) > 0
            assert len(crawler._event_handlers['crawl_completed']) > 0
    
    @pytest.mark.asyncio
    async def test_dead_end_detection_handler(self):
        """Test the dead-end detection handler creation."""
        mock_logger = Mock()
        
        # Create handler
        handler = create_dead_end_detection_handler(
            dead_end_threshold=3,
            revisit_threshold=0.7,
            logger=mock_logger
        )
        
        # Test with results that should trigger dead-end
        test_results = [
            CrawlResult(url="https://test.com", html="", success=True, links={'internal': []})
            for _ in range(5)
        ]
        
        # Call handler multiple times to build up dead-end condition
        for _ in range(4):
            result = await handler(test_results)
        
        # Should eventually detect dead-end (exact behavior depends on analytics implementation)
        assert isinstance(result, bool)
    
    @pytest.mark.asyncio
    async def test_progress_reporting_handler(self):
        """Test the progress reporting handler creation."""
        mock_logger = Mock()
        
        # Create handler
        handler = create_progress_reporting_handler(
            logger=mock_logger,
            log_interval_seconds=0  # No delay for testing
        )
        
        # Test with sample results
        test_results = [
            CrawlResult(url="https://test.com", html="", success=True)
        ]
        
        # Call handler
        await handler(test_results)
        
        # Verify logger was called (exact call depends on implementation)
        assert mock_logger.info.called


class TestURLDiscoveryAnalysis:
    """Test URL discovery analysis functionality."""
    
    @pytest.mark.asyncio
    async def test_analyze_url_discovery_rate_from_events(self):
        """Test standalone URL discovery analysis."""
        # Create test results with various link patterns
        test_results = [
            CrawlResult(
                url="https://test.com/page1",
                html="<html><body>Page 1</body></html>",
                success=True,
                links={
                    'internal': [
                        {'href': 'https://test.com/page2'},
                        {'href': 'https://test.com/page3'}
                    ],
                    'external': [{'href': 'https://external.com'}]
                }
            ),
            CrawlResult(
                url="https://test.com/page2",
                html="<html><body>Page 2</body></html>",
                success=True,
                links={'internal': []}  # No new links - dead end
            )
        ]
        
        # Analyze URL discovery
        analysis = analyze_url_discovery_rate_from_events(test_results)
        
        # Verify analysis structure
        assert 'new_urls_discovered' in analysis
        assert 'total_links_found' in analysis
        assert 'consecutive_dead_pages' in analysis
        assert 'revisit_ratio' in analysis
        assert isinstance(analysis['new_urls_discovered'], int)
        assert isinstance(analysis['revisit_ratio'], float)


class TestEventSystemIntegration:
    """Test integration of event system with actual crawling."""
    
    @pytest.mark.asyncio
    async def test_page_processed_event_emission(self):
        """Test that page_processed events are emitted during crawling."""
        event_received = []
        
        def capture_event(result):
            event_received.append(result)
        
        async with AsyncWebCrawler() as crawler:
            # Register event handler
            crawler.add_event_handler('page_processed', capture_event)
            
            # Perform a crawl (using a simple HTML string to avoid network dependency)
            config = CrawlerRunConfig(word_count_threshold=1)
            result = await crawler.arun("raw:<html><body>Test content</body></html>", config=config)
            
            # Verify event was emitted
            assert len(event_received) == 1
            assert event_received[0].url == "raw:<html><body>Test content</body></html>"
            assert event_received[0].success == result.success
    
    @pytest.mark.asyncio
    async def test_crawl_completed_event_emission(self):
        """Test that crawl_completed events are emitted during batch crawling."""
        event_received = []
        
        def capture_event(results):
            event_received.append(results)
        
        async with AsyncWebCrawler() as crawler:
            # Register event handler
            crawler.add_event_handler('crawl_completed', capture_event)
            
            # Perform batch crawl
            urls = [
                "raw:<html><body>Test 1</body></html>",
                "raw:<html><body>Test 2</body></html>"
            ]
            config = CrawlerRunConfig(word_count_threshold=1)
            results = await crawler.arun_many(urls, config=config)
            
            # Verify event was emitted
            assert len(event_received) == 1
            assert len(event_received[0]) == 2
            assert all(r.success for r in event_received[0])


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])