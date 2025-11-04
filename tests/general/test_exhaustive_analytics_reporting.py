#!/usr/bin/env python3
"""
Tests for Exhaustive Crawling Analytics and Reporting

This module tests the comprehensive analytics and reporting system for exhaustive crawling,
including site mapping completeness, dead-end detection metrics, and file discovery statistics.
"""

import pytest
import asyncio
import json
import tempfile
import os
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch
from typing import List, Dict

from crawl4ai.exhaustive_analytics_reporting import (
    ExhaustiveAnalyticsReporter,
    SiteMappingCompleteness,
    FileDiscoveryStats,
    DeadEndAnalysisReport,
    ComprehensiveSiteReport,
    create_analytics_reporter,
    generate_site_mapping_report
)
from crawl4ai.exhaustive_analytics import ExhaustiveAnalytics, DeadEndMetrics, URLTrackingState
from crawl4ai.site_graph_db import SiteGraphDatabaseManager, URLNode, SiteGraphStats
from crawl4ai.async_database import AsyncDatabaseManager


class TestSiteMappingCompleteness:
    """Test SiteMappingCompleteness metrics calculation."""
    
    def test_completeness_initialization(self):
        """Test initialization of SiteMappingCompleteness."""
        completeness = SiteMappingCompleteness(base_url="https://test.com")
        
        assert completeness.base_url == "https://test.com"
        assert completeness.total_pages_discovered == 0
        assert completeness.coverage_percentage == 0.0
        assert completeness.crawl_efficiency == 0.0
    
    def test_calculate_metrics(self):
        """Test calculation of derived metrics."""
        completeness = SiteMappingCompleteness(
            base_url="https://test.com",
            total_pages_discovered=100,
            total_pages_crawled=80,
            total_pages_successful=70,
            total_pages_failed=10
        )
        
        completeness.calculate_metrics()
        
        assert completeness.coverage_percentage == 80.0  # 80/100 * 100
        assert completeness.crawl_efficiency == 87.5  # 70/80 * 100
        assert completeness.discovery_rate == 1.25  # 100/80
    
    def test_calculate_metrics_zero_division(self):
        """Test metric calculation with zero values."""
        completeness = SiteMappingCompleteness(base_url="https://test.com")
        
        # Should not raise exception
        completeness.calculate_metrics()
        
        assert completeness.coverage_percentage == 0.0
        assert completeness.crawl_efficiency == 0.0
        assert completeness.discovery_rate == 0.0


class TestFileDiscoveryStats:
    """Test FileDiscoveryStats metrics calculation."""
    
    def test_stats_initialization(self):
        """Test initialization of FileDiscoveryStats."""
        stats = FileDiscoveryStats(base_url="https://test.com")
        
        assert stats.base_url == "https://test.com"
        assert stats.total_files_discovered == 0
        assert stats.download_success_rate == 0.0
        assert stats.average_file_size == 0.0
    
    def test_calculate_metrics(self):
        """Test calculation of file discovery metrics."""
        stats = FileDiscoveryStats(
            base_url="https://test.com",
            total_files_discovered=50,
            total_files_downloaded=40,
            total_files_failed=5,
            total_download_size=1000000  # 1MB
        )
        
        stats.calculate_metrics()
        
        assert stats.average_file_size == 25000.0  # 1000000/40
        assert abs(stats.download_success_rate - 88.89) < 0.01  # 40/(40+5) * 100 (approximately)
    
    def test_calculate_metrics_no_downloads(self):
        """Test metric calculation with no downloads."""
        stats = FileDiscoveryStats(base_url="https://test.com")
        
        stats.calculate_metrics()
        
        assert stats.average_file_size == 0.0
        assert stats.download_success_rate == 0.0


class TestDeadEndAnalysisReport:
    """Test DeadEndAnalysisReport analysis functionality."""
    
    def test_analyze_termination_reason(self):
        """Test analysis of crawl termination reasons."""
        # Create mock metrics
        metrics = Mock()
        
        # Test consecutive dead pages threshold
        report = DeadEndAnalysisReport(
            base_url="https://test.com",
            consecutive_dead_pages=60
        )
        report.analyze_termination_reason(metrics)
        assert "Consecutive dead pages threshold reached" in report.crawl_termination_reason
        
        # Test high revisit ratio
        report = DeadEndAnalysisReport(
            base_url="https://test.com",
            consecutive_dead_pages=10,
            revisit_ratio=0.96
        )
        report.analyze_termination_reason(metrics)
        assert "High revisit ratio detected" in report.crawl_termination_reason
        
        # Test low discovery rate
        report = DeadEndAnalysisReport(
            base_url="https://test.com",
            consecutive_dead_pages=10,
            revisit_ratio=0.5,
            discovery_rate_trend=[0.1, 0.2, 0.1, 0.3, 0.2]
        )
        report.analyze_termination_reason(metrics)
        assert "Sustained low discovery rate" in report.crawl_termination_reason


class TestComprehensiveSiteReport:
    """Test ComprehensiveSiteReport functionality."""
    
    def test_report_initialization(self):
        """Test initialization of ComprehensiveSiteReport."""
        report = ComprehensiveSiteReport(
            base_url="https://test.com",
            crawl_session_id="test_session",
            report_generated_at=datetime.now()
        )
        
        assert report.base_url == "https://test.com"
        assert report.crawl_session_id == "test_session"
        assert report.pages_per_minute == 0.0
        assert len(report.optimization_recommendations) == 0
    
    def test_calculate_performance_metrics(self):
        """Test calculation of performance metrics."""
        start_time = datetime.now()
        end_time = start_time + timedelta(minutes=10)
        
        report = ComprehensiveSiteReport(
            base_url="https://test.com",
            crawl_session_id="test_session",
            report_generated_at=datetime.now(),
            crawl_start_time=start_time,
            crawl_end_time=end_time,
            total_crawl_duration=end_time - start_time
        )
        
        # Add site mapping data
        report.site_mapping_completeness = SiteMappingCompleteness(
            base_url="https://test.com",
            total_pages_crawled=50
        )
        
        report.calculate_performance_metrics()
        
        assert report.pages_per_minute == 5.0  # 50 pages / 10 minutes
    
    def test_generate_recommendations(self):
        """Test generation of optimization recommendations."""
        report = ComprehensiveSiteReport(
            base_url="https://test.com",
            crawl_session_id="test_session",
            report_generated_at=datetime.now(),
            pages_per_minute=0.5  # Slow crawling
        )
        
        # Add low efficiency site mapping
        report.site_mapping_completeness = SiteMappingCompleteness(
            base_url="https://test.com",
            crawl_efficiency=70.0,  # Below 80%
            coverage_percentage=60.0  # Below 70%
        )
        
        # Add low success rate file discovery
        report.file_discovery_stats = FileDiscoveryStats(
            base_url="https://test.com",
            download_success_rate=85.0  # Below 90%
        )
        
        # Add efficiency decline detection
        report.dead_end_analysis = DeadEndAnalysisReport(
            base_url="https://test.com",
            efficiency_decline_detected=True
        )
        
        report.generate_recommendations()
        
        # Should generate multiple recommendations
        assert len(report.optimization_recommendations) >= 4
        assert any("crawl efficiency" in rec.lower() for rec in report.optimization_recommendations)
        assert any("coverage" in rec.lower() for rec in report.optimization_recommendations)
        assert any("download success rate" in rec.lower() for rec in report.optimization_recommendations)
        assert any("crawl speed" in rec.lower() for rec in report.optimization_recommendations)


class TestExhaustiveAnalyticsReporter:
    """Test ExhaustiveAnalyticsReporter functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_site_graph_manager = Mock(spec=SiteGraphDatabaseManager)
        self.mock_logger = Mock()
        self.reporter = ExhaustiveAnalyticsReporter(
            site_graph_manager=self.mock_site_graph_manager,
            logger=self.mock_logger
        )
    
    def test_start_reporting_session(self):
        """Test starting a reporting session."""
        session_id = self.reporter.start_reporting_session("https://test.com", "custom_session")
        
        assert session_id == "custom_session"
        assert self.reporter._session_start_time is not None
        assert self.reporter._session_metrics['base_url'] == "https://test.com"
        assert self.reporter._session_metrics['session_id'] == "custom_session"
    
    def test_start_reporting_session_auto_id(self):
        """Test starting a reporting session with auto-generated ID."""
        session_id = self.reporter.start_reporting_session("https://test.com")
        
        assert session_id.startswith("session_")
        assert self.reporter._session_start_time is not None
    
    @pytest.mark.asyncio
    async def test_analyze_site_mapping_completeness(self):
        """Test analysis of site mapping completeness."""
        # Mock site graph data
        mock_urls = [
            URLNode(
                url="https://test.com/page1",
                last_checked=datetime.now(),
                status_code=200,
                content_type="text/html",
                metadata={'depth': 1}
            ),
            URLNode(
                url="https://test.com/page2",
                last_checked=datetime.now(),
                status_code=404,
                content_type="text/html",
                metadata={'depth': 2}
            ),
            URLNode(
                url="https://test.com/page3",
                last_checked=None,  # Not crawled yet
                metadata={'depth': 1}
            )
        ]
        
        self.mock_site_graph_manager.get_site_graph.return_value = {
            'urls': mock_urls,
            'files': [],
            'total_urls': len(mock_urls),
            'total_files': 0
        }
        
        completeness = await self.reporter.analyze_site_mapping_completeness("https://test.com")
        
        assert completeness.base_url == "https://test.com"
        assert completeness.total_pages_discovered == 3
        assert completeness.total_pages_crawled == 2  # Only 2 have last_checked
        assert completeness.total_pages_successful == 1  # Only 1 has 200 status
        assert completeness.total_pages_failed == 1  # Only 1 has 404 status
        assert 1 in completeness.depth_distribution
        assert 2 in completeness.depth_distribution
        assert "text/html" in completeness.content_type_distribution
    
    @pytest.mark.asyncio
    async def test_analyze_file_discovery_stats(self):
        """Test analysis of file discovery statistics."""
        # Mock file data
        mock_files = [
            URLNode(
                url="https://test.com/file1.pdf",
                is_file=True,
                file_extension=".pdf",
                download_status="completed",
                file_size=1000000,
                content_type="application/pdf"
            ),
            URLNode(
                url="https://test.com/file2.doc",
                is_file=True,
                file_extension=".doc",
                download_status="completed",
                file_size=500000,
                content_type="application/msword"
            ),
            URLNode(
                url="https://test.com/file3.pdf",
                is_file=True,
                file_extension=".pdf",
                download_status="failed",
                content_type="application/pdf"
            )
        ]
        
        self.mock_site_graph_manager.get_site_graph.return_value = {
            'urls': [],
            'files': mock_files,
            'total_urls': 0,
            'total_files': len(mock_files)
        }
        
        stats = await self.reporter.analyze_file_discovery_stats("https://test.com")
        
        assert stats.base_url == "https://test.com"
        assert stats.total_files_discovered == 3
        assert stats.total_files_downloaded == 2
        assert stats.total_files_failed == 1
        assert stats.total_download_size == 1500000  # 1MB + 0.5MB
        assert stats.largest_file_size == 1000000
        assert stats.smallest_file_size == 500000
        assert ".pdf" in stats.file_type_distribution
        assert ".doc" in stats.file_type_distribution
        assert stats.file_type_distribution[".pdf"] == 2
        assert stats.file_type_distribution[".doc"] == 1
    
    def test_analyze_dead_end_detection(self):
        """Test analysis of dead-end detection metrics."""
        # Create mock analytics
        mock_analytics = Mock(spec=ExhaustiveAnalytics)
        mock_metrics = Mock(spec=DeadEndMetrics)
        mock_url_state = Mock(spec=URLTrackingState)
        
        # Configure mock data
        mock_metrics.consecutive_dead_pages = 25
        mock_metrics.revisit_ratio = 0.75
        mock_metrics.discovery_rate_history = [5, 4, 3, 2, 1, 0, 0, 0]
        mock_metrics.time_since_last_discovery = timedelta(minutes=30)
        
        mock_url_state.failed_urls = {
            "https://test.com/admin/page1",
            "https://test.com/admin/page2",
            "https://test.com/private/page1"
        }
        
        mock_analytics.metrics = mock_metrics
        mock_analytics.url_state = mock_url_state
        
        analysis = self.reporter.analyze_dead_end_detection(mock_analytics)
        
        assert analysis.consecutive_dead_pages == 25
        assert analysis.revisit_ratio == 0.75
        assert len(analysis.discovery_rate_trend) == 8
        assert analysis.time_since_last_discovery == timedelta(minutes=30)
        assert not analysis.dead_end_threshold_reached  # 25 < 50
        assert analysis.efficiency_decline_detected  # Recent trend much lower than early
        assert "test.com/admin" in analysis.dead_end_patterns
        assert "test.com/private" in analysis.dead_end_patterns
    
    @pytest.mark.asyncio
    async def test_generate_comprehensive_report(self):
        """Test generation of comprehensive report."""
        # Mock analytics
        mock_analytics = Mock(spec=ExhaustiveAnalytics)
        mock_metrics = Mock(spec=DeadEndMetrics)
        mock_metrics.crawl_start_time = datetime.now() - timedelta(hours=1)
        mock_metrics.consecutive_dead_pages = 10
        mock_metrics.revisit_ratio = 0.5
        mock_metrics.discovery_rate_history = [5, 4, 3, 2, 1]
        mock_metrics.time_since_last_discovery = timedelta(minutes=10)
        
        mock_url_state = Mock(spec=URLTrackingState)
        mock_url_state.failed_urls = set()
        
        mock_analytics.metrics = mock_metrics
        mock_analytics.url_state = mock_url_state
        
        # Mock site graph data
        self.mock_site_graph_manager.get_site_graph.return_value = {
            'urls': [URLNode(url="https://test.com/page1", last_checked=datetime.now(), status_code=200)],
            'files': [URLNode(url="https://test.com/file1.pdf", is_file=True, download_status="completed")],
            'total_urls': 1,
            'total_files': 1
        }
        
        # Set up session metrics
        self.reporter._session_metrics = {
            'page_load_times': [1.0, 2.0, 1.5],
            'data_processed': 1000000
        }
        
        report = await self.reporter.generate_comprehensive_report(
            "https://test.com",
            mock_analytics,
            "test_session"
        )
        
        assert report.base_url == "https://test.com"
        assert report.crawl_session_id == "test_session"
        assert report.site_mapping_completeness is not None
        assert report.file_discovery_stats is not None
        assert report.dead_end_analysis is not None
        assert report.average_page_load_time == 1.5  # Average of [1.0, 2.0, 1.5]
        assert report.total_data_processed == 1000000
        assert report.total_crawl_duration is not None
        assert len(report.optimization_recommendations) >= 0
    
    @pytest.mark.asyncio
    async def test_export_report_to_json(self):
        """Test exporting report to JSON format."""
        # Create a simple report
        report = ComprehensiveSiteReport(
            base_url="https://test.com",
            crawl_session_id="test_session",
            report_generated_at=datetime.now(),
            pages_per_minute=5.0,
            optimization_recommendations=["Test recommendation"]
        )
        
        # Add component data
        report.site_mapping_completeness = SiteMappingCompleteness(
            base_url="https://test.com",
            total_pages_discovered=10,
            total_pages_crawled=8
        )
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = os.path.join(temp_dir, "test_report.json")
            
            exported_path = await self.reporter.export_report_to_json(report, output_path)
            
            assert exported_path == output_path
            assert os.path.exists(output_path)
            
            # Verify JSON content
            with open(output_path, 'r') as f:
                data = json.load(f)
            
            assert data['base_url'] == "https://test.com"
            assert data['crawl_session_id'] == "test_session"
            assert data['pages_per_minute'] == 5.0
            assert "Test recommendation" in data['optimization_recommendations']
            assert 'site_mapping_completeness' in data
            assert data['site_mapping_completeness']['total_pages_discovered'] == 10
    
    def test_track_page_performance(self):
        """Test tracking page performance metrics."""
        # Start session first
        self.reporter.start_reporting_session("https://test.com")
        
        # Track some performance data
        self.reporter.track_page_performance("https://test.com/page1", 1.5, 50000)
        self.reporter.track_page_performance("https://test.com/page2", 2.0, 75000)
        
        assert len(self.reporter._session_metrics['page_load_times']) == 2
        assert 1.5 in self.reporter._session_metrics['page_load_times']
        assert 2.0 in self.reporter._session_metrics['page_load_times']
        assert self.reporter._session_metrics['data_processed'] == 125000
    
    def test_track_error(self):
        """Test tracking errors for reporting."""
        # Start session first
        self.reporter.start_reporting_session("https://test.com")
        
        # Track some errors
        self.reporter.track_error("https://test.com/error1", "404 Not Found")
        self.reporter.track_error("https://test.com/error2", "500 Server Error")
        
        assert self.reporter._session_metrics['error_count'] == 2


class TestFactoryFunctions:
    """Test factory functions and convenience methods."""
    
    def test_create_analytics_reporter(self):
        """Test creating analytics reporter with factory function."""
        reporter = create_analytics_reporter()
        
        assert isinstance(reporter, ExhaustiveAnalyticsReporter)
        assert reporter.site_graph_manager is not None
    
    @pytest.mark.asyncio
    async def test_generate_site_mapping_report(self):
        """Test convenience function for generating reports."""
        # Create mock analytics
        mock_analytics = Mock(spec=ExhaustiveAnalytics)
        mock_metrics = Mock(spec=DeadEndMetrics)
        mock_metrics.crawl_start_time = datetime.now()
        mock_metrics.consecutive_dead_pages = 5
        mock_metrics.revisit_ratio = 0.3
        mock_metrics.discovery_rate_history = [5, 4, 3]
        mock_metrics.time_since_last_discovery = None
        
        mock_url_state = Mock(spec=URLTrackingState)
        mock_url_state.failed_urls = set()
        
        mock_analytics.metrics = mock_metrics
        mock_analytics.url_state = mock_url_state
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = os.path.join(temp_dir, "convenience_report.json")
            
            # Mock the site graph manager to avoid database operations
            with patch('crawl4ai.exhaustive_analytics_reporting.create_analytics_reporter') as mock_create:
                mock_reporter = Mock(spec=ExhaustiveAnalyticsReporter)
                mock_reporter.start_reporting_session.return_value = "test_session"
                
                # Create a minimal report
                mock_report = ComprehensiveSiteReport(
                    base_url="https://test.com",
                    crawl_session_id="test_session",
                    report_generated_at=datetime.now()
                )
                mock_reporter.generate_comprehensive_report.return_value = mock_report
                mock_reporter.export_report_to_json.return_value = output_path
                
                mock_create.return_value = mock_reporter
                
                result_path = await generate_site_mapping_report(
                    "https://test.com",
                    mock_analytics,
                    output_path
                )
                
                assert result_path == output_path
                mock_reporter.start_reporting_session.assert_called_once_with("https://test.com")
                mock_reporter.generate_comprehensive_report.assert_called_once()
                mock_reporter.export_report_to_json.assert_called_once()


class TestIntegrationScenarios:
    """Test integration scenarios with realistic data."""
    
    @pytest.mark.asyncio
    async def test_complete_analytics_workflow(self):
        """Test complete analytics workflow from start to finish."""
        # Create reporter with mocked dependencies
        mock_site_graph_manager = Mock(spec=SiteGraphDatabaseManager)
        mock_logger = Mock()
        reporter = ExhaustiveAnalyticsReporter(mock_site_graph_manager, mock_logger)
        
        # Start session
        session_id = reporter.start_reporting_session("https://example.com")
        
        # Track some performance data
        reporter.track_page_performance("https://example.com/page1", 1.2, 45000)
        reporter.track_page_performance("https://example.com/page2", 0.8, 32000)
        reporter.track_error("https://example.com/error", "404 Not Found")
        
        # Mock comprehensive site data
        mock_urls = [
            URLNode(url="https://example.com/", last_checked=datetime.now(), status_code=200, content_type="text/html"),
            URLNode(url="https://example.com/about", last_checked=datetime.now(), status_code=200, content_type="text/html"),
            URLNode(url="https://example.com/contact", last_checked=datetime.now(), status_code=404, content_type="text/html"),
            URLNode(url="https://example.com/hidden", last_checked=None)  # Not crawled
        ]
        
        mock_files = [
            URLNode(url="https://example.com/doc.pdf", is_file=True, file_extension=".pdf", 
                   download_status="completed", file_size=1000000),
            URLNode(url="https://example.com/image.jpg", is_file=True, file_extension=".jpg", 
                   download_status="failed")
        ]
        
        mock_site_graph_manager.get_site_graph.return_value = {
            'urls': mock_urls,
            'files': mock_files,
            'total_urls': len(mock_urls),
            'total_files': len(mock_files)
        }
        
        # Create mock analytics
        mock_analytics = Mock(spec=ExhaustiveAnalytics)
        mock_metrics = Mock(spec=DeadEndMetrics)
        mock_metrics.crawl_start_time = datetime.now() - timedelta(minutes=30)
        mock_metrics.consecutive_dead_pages = 15
        mock_metrics.revisit_ratio = 0.6
        mock_metrics.discovery_rate_history = [8, 6, 4, 2, 1, 0]
        mock_metrics.time_since_last_discovery = timedelta(minutes=5)
        
        mock_url_state = Mock(spec=URLTrackingState)
        mock_url_state.failed_urls = {"https://example.com/contact"}
        
        mock_analytics.metrics = mock_metrics
        mock_analytics.url_state = mock_url_state
        
        # Generate comprehensive report
        report = await reporter.generate_comprehensive_report("https://example.com", mock_analytics, session_id)
        
        # Verify report completeness
        assert report.base_url == "https://example.com"
        assert report.crawl_session_id == session_id
        assert report.site_mapping_completeness is not None
        assert report.file_discovery_stats is not None
        assert report.dead_end_analysis is not None
        
        # Verify site mapping metrics
        site_metrics = report.site_mapping_completeness
        assert site_metrics.total_pages_discovered == 4
        assert site_metrics.total_pages_crawled == 3  # 3 have last_checked
        assert site_metrics.total_pages_successful == 2  # 2 have 200 status
        assert site_metrics.total_pages_failed == 1  # 1 has 404 status
        
        # Verify file discovery metrics
        file_metrics = report.file_discovery_stats
        assert file_metrics.total_files_discovered == 2
        assert file_metrics.total_files_downloaded == 1
        assert file_metrics.total_files_failed == 1
        
        # Verify dead-end analysis
        dead_end_analysis = report.dead_end_analysis
        assert dead_end_analysis.consecutive_dead_pages == 15
        assert dead_end_analysis.revisit_ratio == 0.6
        assert not dead_end_analysis.dead_end_threshold_reached  # 15 < 50
        
        # Verify performance metrics were calculated
        assert report.average_page_load_time == 1.0  # (1.2 + 0.8) / 2
        assert report.total_data_processed == 77000  # 45000 + 32000
        
        # Export report and verify
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = os.path.join(temp_dir, "integration_report.json")
            exported_path = await reporter.export_report_to_json(report, output_path)
            
            assert os.path.exists(exported_path)
            
            # Verify exported JSON structure
            with open(exported_path, 'r') as f:
                data = json.load(f)
            
            assert data['base_url'] == "https://example.com"
            assert 'site_mapping_completeness' in data
            assert 'file_discovery_stats' in data
            assert 'dead_end_analysis' in data
            assert data['average_page_load_time'] == 1.0


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])