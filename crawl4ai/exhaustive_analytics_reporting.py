"""
Exhaustive Crawling Analytics and Reporting Module

This module provides comprehensive analytics and reporting for exhaustive crawling,
extending existing analytics infrastructure to track site mapping completeness,
dead-end detection metrics, and file discovery statistics.

Follows existing Crawl4AI patterns:
- Uses existing analytics patterns from exhaustive_analytics.py
- Integrates with existing monitoring from exhaustive_monitoring.py
- Uses existing database patterns from site_graph_db.py
- Follows existing logging and error handling
"""

import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field, asdict
from collections import defaultdict, Counter
from pathlib import Path

from .models import CrawlResult
from .exhaustive_analytics import ExhaustiveAnalytics, DeadEndMetrics, URLTrackingState
from .site_graph_db import SiteGraphDatabaseManager, URLNode, SiteGraphStats
from .async_logger import AsyncLoggerBase


@dataclass
class SiteMappingCompleteness:
    """Metrics for site mapping completeness analysis"""
    base_url: str
    total_pages_discovered: int = 0
    total_pages_crawled: int = 0
    total_pages_successful: int = 0
    total_pages_failed: int = 0
    coverage_percentage: float = 0.0
    depth_distribution: Dict[int, int] = field(default_factory=dict)
    content_type_distribution: Dict[str, int] = field(default_factory=dict)
    status_code_distribution: Dict[int, int] = field(default_factory=dict)
    crawl_efficiency: float = 0.0  # successful_pages / total_attempts
    discovery_rate: float = 0.0  # pages_discovered / pages_crawled
    
    def calculate_metrics(self):
        """Calculate derived metrics from base data"""
        if self.total_pages_discovered > 0:
            self.coverage_percentage = (self.total_pages_crawled / self.total_pages_discovered) * 100
        
        if self.total_pages_crawled > 0:
            self.crawl_efficiency = (self.total_pages_successful / self.total_pages_crawled) * 100
            
        if self.total_pages_crawled > 0:
            self.discovery_rate = self.total_pages_discovered / self.total_pages_crawled


@dataclass
class FileDiscoveryStats:
    """Statistics for file discovery and download operations"""
    base_url: str
    total_files_discovered: int = 0
    total_files_downloaded: int = 0
    total_files_failed: int = 0
    total_download_size: int = 0  # bytes
    file_type_distribution: Dict[str, int] = field(default_factory=dict)
    download_status_distribution: Dict[str, int] = field(default_factory=dict)
    average_file_size: float = 0.0
    download_success_rate: float = 0.0
    largest_file_size: int = 0
    smallest_file_size: int = 0
    download_duration: Optional[timedelta] = None
    
    def calculate_metrics(self):
        """Calculate derived metrics from base data"""
        if self.total_files_downloaded > 0:
            self.average_file_size = self.total_download_size / self.total_files_downloaded
            
        total_attempts = self.total_files_downloaded + self.total_files_failed
        if total_attempts > 0:
            self.download_success_rate = (self.total_files_downloaded / total_attempts) * 100


@dataclass
class DeadEndAnalysisReport:
    """Comprehensive dead-end detection analysis"""
    base_url: str
    dead_end_threshold_reached: bool = False
    consecutive_dead_pages: int = 0
    revisit_ratio: float = 0.0
    discovery_rate_trend: List[float] = field(default_factory=list)
    time_since_last_discovery: Optional[timedelta] = None
    dead_end_patterns: Dict[str, int] = field(default_factory=dict)  # URL patterns that led to dead ends
    crawl_termination_reason: str = ""
    efficiency_decline_detected: bool = False
    
    def analyze_termination_reason(self, metrics: DeadEndMetrics):
        """Analyze and set the crawl termination reason"""
        if self.consecutive_dead_pages >= 50:  # Default threshold
            self.crawl_termination_reason = f"Consecutive dead pages threshold reached ({self.consecutive_dead_pages})"
        elif self.revisit_ratio >= 0.95:
            self.crawl_termination_reason = f"High revisit ratio detected ({self.revisit_ratio:.2%})"
        elif len(self.discovery_rate_trend) >= 5 and all(rate < 0.5 for rate in self.discovery_rate_trend[-5:]):
            self.crawl_termination_reason = "Sustained low discovery rate"
        else:
            self.crawl_termination_reason = "Manual termination or other condition"


@dataclass
class ComprehensiveSiteReport:
    """Complete site mapping and analytics report"""
    base_url: str
    crawl_session_id: str
    report_generated_at: datetime
    crawl_start_time: Optional[datetime] = None
    crawl_end_time: Optional[datetime] = None
    total_crawl_duration: Optional[timedelta] = None
    
    # Core metrics
    site_mapping_completeness: Optional[SiteMappingCompleteness] = None
    file_discovery_stats: Optional[FileDiscoveryStats] = None
    dead_end_analysis: Optional[DeadEndAnalysisReport] = None
    
    # Performance metrics
    pages_per_minute: float = 0.0
    average_page_load_time: float = 0.0
    total_data_processed: int = 0  # bytes
    
    # Quality metrics
    content_quality_score: float = 0.0
    link_integrity_score: float = 0.0
    site_structure_score: float = 0.0
    
    # Recommendations
    optimization_recommendations: List[str] = field(default_factory=list)
    crawl_strategy_suggestions: List[str] = field(default_factory=list)
    
    def calculate_performance_metrics(self):
        """Calculate performance-related metrics"""
        if self.total_crawl_duration and self.site_mapping_completeness:
            duration_minutes = self.total_crawl_duration.total_seconds() / 60
            if duration_minutes > 0:
                self.pages_per_minute = self.site_mapping_completeness.total_pages_crawled / duration_minutes
    
    def generate_recommendations(self):
        """Generate optimization recommendations based on metrics"""
        recommendations = []
        
        if self.site_mapping_completeness:
            if self.site_mapping_completeness.crawl_efficiency < 80:
                recommendations.append("Consider improving error handling - crawl efficiency is below 80%")
            
            if self.site_mapping_completeness.coverage_percentage < 70:
                recommendations.append("Site coverage is low - consider adjusting crawl depth or filters")
        
        if self.file_discovery_stats:
            if self.file_discovery_stats.download_success_rate < 90:
                recommendations.append("File download success rate is low - check network stability and retry logic")
        
        if self.dead_end_analysis:
            if self.dead_end_analysis.efficiency_decline_detected:
                recommendations.append("Crawl efficiency declined - consider adaptive crawling strategies")
        
        if self.pages_per_minute < 1.0:
            recommendations.append("Crawl speed is slow - consider increasing concurrency or reducing delays")
        
        self.optimization_recommendations = recommendations


class ExhaustiveAnalyticsReporter:
    """
    Comprehensive analytics and reporting system for exhaustive crawling.
    
    Provides detailed analysis of site mapping completeness, dead-end detection,
    file discovery statistics, and generates comprehensive reports.
    """
    
    def __init__(
        self,
        site_graph_manager: SiteGraphDatabaseManager,
        logger: Optional[AsyncLoggerBase] = None
    ):
        self.site_graph_manager = site_graph_manager
        self.logger = logger
        self._session_start_time: Optional[datetime] = None
        self._session_metrics: Dict[str, Any] = {}
        
    def start_reporting_session(self, base_url: str, session_id: str = None) -> str:
        """
        Start a new reporting session for analytics tracking.
        
        Args:
            base_url: Base URL being crawled
            session_id: Optional session identifier
            
        Returns:
            Session ID for tracking
        """
        if session_id is None:
            session_id = f"session_{int(time.time())}"
            
        self._session_start_time = datetime.now()
        self._session_metrics = {
            'session_id': session_id,
            'base_url': base_url,
            'start_time': self._session_start_time,
            'page_load_times': [],
            'data_processed': 0,
            'error_count': 0
        }
        
        if self.logger:
            self.logger.info(
                f"Started analytics reporting session: {session_id}",
                tag="ANALYTICS"
            )
        
        return session_id
    
    async def analyze_site_mapping_completeness(self, base_url: str) -> SiteMappingCompleteness:
        """
        Analyze site mapping completeness using site graph data.
        
        Args:
            base_url: Base URL to analyze
            
        Returns:
            SiteMappingCompleteness metrics
        """
        try:
            # Get site graph data
            site_graph = await self.site_graph_manager.get_site_graph(base_url, include_files=False)
            urls = site_graph.get('urls', [])
            
            # Initialize completeness metrics
            completeness = SiteMappingCompleteness(base_url=base_url)
            
            # Calculate basic counts
            completeness.total_pages_discovered = len(urls)
            
            crawled_urls = [url for url in urls if url.last_checked is not None]
            completeness.total_pages_crawled = len(crawled_urls)
            
            successful_urls = [url for url in crawled_urls if url.status_code and 200 <= url.status_code < 400]
            completeness.total_pages_successful = len(successful_urls)
            
            failed_urls = [url for url in crawled_urls if url.status_code and url.status_code >= 400]
            completeness.total_pages_failed = len(failed_urls)
            
            # Calculate depth distribution
            depth_counter = Counter()
            for url in urls:
                depth = url.metadata.get('depth', 0) if url.metadata else 0
                depth_counter[depth] += 1
            completeness.depth_distribution = dict(depth_counter)
            
            # Calculate content type distribution
            content_type_counter = Counter()
            for url in crawled_urls:
                content_type = url.content_type or 'unknown'
                # Simplify content type (remove charset, etc.)
                main_type = content_type.split(';')[0].strip()
                content_type_counter[main_type] += 1
            completeness.content_type_distribution = dict(content_type_counter)
            
            # Calculate status code distribution
            status_code_counter = Counter()
            for url in crawled_urls:
                if url.status_code:
                    status_code_counter[url.status_code] += 1
            completeness.status_code_distribution = dict(status_code_counter)
            
            # Calculate derived metrics
            completeness.calculate_metrics()
            
            if self.logger:
                self.logger.info(
                    f"Site mapping completeness: {completeness.coverage_percentage:.1f}% "
                    f"({completeness.total_pages_crawled}/{completeness.total_pages_discovered} pages)",
                    tag="ANALYTICS"
                )
            
            return completeness
            
        except Exception as e:
            if self.logger:
                self.logger.error(
                    f"Failed to analyze site mapping completeness: {str(e)}",
                    tag="ERROR"
                )
            return SiteMappingCompleteness(base_url=base_url)
    
    async def analyze_file_discovery_stats(self, base_url: str) -> FileDiscoveryStats:
        """
        Analyze file discovery and download statistics.
        
        Args:
            base_url: Base URL to analyze
            
        Returns:
            FileDiscoveryStats metrics
        """
        try:
            # Get file data from site graph
            site_graph = await self.site_graph_manager.get_site_graph(base_url, include_files=True)
            files = site_graph.get('files', [])
            
            # Initialize file stats
            stats = FileDiscoveryStats(base_url=base_url)
            
            # Calculate basic counts
            stats.total_files_discovered = len(files)
            
            downloaded_files = [f for f in files if f.download_status == 'completed']
            stats.total_files_downloaded = len(downloaded_files)
            
            failed_files = [f for f in files if f.download_status == 'failed']
            stats.total_files_failed = len(failed_files)
            
            # Calculate download size statistics
            file_sizes = [f.file_size for f in downloaded_files if f.file_size]
            if file_sizes:
                stats.total_download_size = sum(file_sizes)
                stats.largest_file_size = max(file_sizes)
                stats.smallest_file_size = min(file_sizes)
            
            # Calculate file type distribution
            file_type_counter = Counter()
            for file in files:
                if file.file_extension:
                    file_type_counter[file.file_extension.lower()] += 1
                else:
                    # Try to determine from content type
                    content_type = file.content_type or 'unknown'
                    if 'pdf' in content_type:
                        file_type_counter['.pdf'] += 1
                    elif 'image' in content_type:
                        file_type_counter['.image'] += 1
                    else:
                        file_type_counter['unknown'] += 1
            stats.file_type_distribution = dict(file_type_counter)
            
            # Calculate download status distribution
            status_counter = Counter()
            for file in files:
                status_counter[file.download_status] += 1
            stats.download_status_distribution = dict(status_counter)
            
            # Calculate derived metrics
            stats.calculate_metrics()
            
            if self.logger:
                self.logger.info(
                    f"File discovery stats: {stats.total_files_downloaded}/{stats.total_files_discovered} "
                    f"files downloaded ({stats.download_success_rate:.1f}% success rate)",
                    tag="ANALYTICS"
                )
            
            return stats
            
        except Exception as e:
            if self.logger:
                self.logger.error(
                    f"Failed to analyze file discovery stats: {str(e)}",
                    tag="ERROR"
                )
            return FileDiscoveryStats(base_url=base_url)
    
    def analyze_dead_end_detection(self, analytics: ExhaustiveAnalytics) -> DeadEndAnalysisReport:
        """
        Analyze dead-end detection metrics and patterns.
        
        Args:
            analytics: ExhaustiveAnalytics instance with current metrics
            
        Returns:
            DeadEndAnalysisReport with analysis results
        """
        try:
            metrics = analytics.metrics
            url_state = analytics.url_state
            
            # Initialize dead-end analysis
            analysis = DeadEndAnalysisReport(base_url="")  # Will be set by caller
            
            # Basic dead-end metrics
            analysis.consecutive_dead_pages = metrics.consecutive_dead_pages
            analysis.revisit_ratio = metrics.revisit_ratio
            analysis.discovery_rate_trend = metrics.discovery_rate_history.copy()
            analysis.time_since_last_discovery = metrics.time_since_last_discovery
            
            # Determine if dead-end threshold was reached
            analysis.dead_end_threshold_reached = metrics.consecutive_dead_pages >= 50  # Default threshold
            
            # Analyze URL patterns that led to dead ends
            dead_end_patterns = defaultdict(int)
            for url in url_state.failed_urls:
                # Extract pattern from URL (domain, path structure, etc.)
                try:
                    from urllib.parse import urlparse
                    parsed = urlparse(url)
                    path_parts = parsed.path.split('/')
                    if len(path_parts) > 1:
                        pattern = f"{parsed.netloc}/{path_parts[1]}"  # Domain + first path segment
                        dead_end_patterns[pattern] += 1
                except:
                    dead_end_patterns['unknown'] += 1
            
            analysis.dead_end_patterns = dict(dead_end_patterns)
            
            # Detect efficiency decline
            if len(analysis.discovery_rate_trend) >= 5:
                recent_trend = analysis.discovery_rate_trend[-5:]
                early_trend = analysis.discovery_rate_trend[:5] if len(analysis.discovery_rate_trend) >= 10 else recent_trend
                
                recent_avg = sum(recent_trend) / len(recent_trend)
                early_avg = sum(early_trend) / len(early_trend)
                
                # Efficiency decline if recent average is significantly lower
                analysis.efficiency_decline_detected = recent_avg < early_avg * 0.5
            
            # Analyze termination reason
            analysis.analyze_termination_reason(metrics)
            
            if self.logger:
                self.logger.info(
                    f"Dead-end analysis: {analysis.consecutive_dead_pages} consecutive dead pages, "
                    f"{analysis.revisit_ratio:.2%} revisit ratio",
                    tag="ANALYTICS"
                )
            
            return analysis
            
        except Exception as e:
            if self.logger:
                self.logger.error(
                    f"Failed to analyze dead-end detection: {str(e)}",
                    tag="ERROR"
                )
            return DeadEndAnalysisReport(base_url="")
    
    async def generate_comprehensive_report(
        self,
        base_url: str,
        analytics: ExhaustiveAnalytics,
        session_id: str = None
    ) -> ComprehensiveSiteReport:
        """
        Generate a comprehensive site mapping and analytics report.
        
        Args:
            base_url: Base URL that was crawled
            analytics: ExhaustiveAnalytics instance with session data
            session_id: Optional session identifier
            
        Returns:
            ComprehensiveSiteReport with complete analysis
        """
        try:
            # Initialize report
            report = ComprehensiveSiteReport(
                base_url=base_url,
                crawl_session_id=session_id or f"report_{int(time.time())}",
                report_generated_at=datetime.now()
            )
            
            # Set crawl timing information
            if analytics.metrics.crawl_start_time:
                report.crawl_start_time = analytics.metrics.crawl_start_time
                report.crawl_end_time = datetime.now()
                report.total_crawl_duration = report.crawl_end_time - report.crawl_start_time
            
            # Generate component analyses
            report.site_mapping_completeness = await self.analyze_site_mapping_completeness(base_url)
            report.file_discovery_stats = await self.analyze_file_discovery_stats(base_url)
            report.dead_end_analysis = self.analyze_dead_end_detection(analytics)
            report.dead_end_analysis.base_url = base_url
            
            # Calculate performance metrics
            if self._session_metrics:
                page_load_times = self._session_metrics.get('page_load_times', [])
                if page_load_times:
                    report.average_page_load_time = sum(page_load_times) / len(page_load_times)
                
                report.total_data_processed = self._session_metrics.get('data_processed', 0)
            
            report.calculate_performance_metrics()
            
            # Calculate quality scores (simplified scoring system)
            if report.site_mapping_completeness:
                # Content quality based on success rate and coverage
                success_rate = report.site_mapping_completeness.crawl_efficiency / 100
                coverage_rate = report.site_mapping_completeness.coverage_percentage / 100
                report.content_quality_score = (success_rate * 0.6 + coverage_rate * 0.4) * 100
                
                # Link integrity based on successful vs failed pages
                total_attempts = (report.site_mapping_completeness.total_pages_successful + 
                                report.site_mapping_completeness.total_pages_failed)
                if total_attempts > 0:
                    report.link_integrity_score = (report.site_mapping_completeness.total_pages_successful / total_attempts) * 100
                
                # Site structure score based on depth distribution and organization
                depth_dist = report.site_mapping_completeness.depth_distribution
                if depth_dist:
                    max_depth = max(depth_dist.keys())
                    avg_depth = sum(d * count for d, count in depth_dist.items()) / sum(depth_dist.values())
                    # Good structure has reasonable depth (not too shallow, not too deep)
                    optimal_depth = 4
                    depth_score = max(0, 100 - abs(avg_depth - optimal_depth) * 10)
                    report.site_structure_score = min(100, depth_score)
            
            # Generate recommendations
            report.generate_recommendations()
            
            # Add crawl strategy suggestions
            strategy_suggestions = []
            if report.dead_end_analysis and report.dead_end_analysis.efficiency_decline_detected:
                strategy_suggestions.append("Consider using adaptive crawling with learning algorithms")
            
            if report.site_mapping_completeness and report.site_mapping_completeness.coverage_percentage < 50:
                strategy_suggestions.append("Increase crawl depth or adjust URL filtering rules")
            
            if report.pages_per_minute < 0.5:
                strategy_suggestions.append("Increase concurrency or reduce request delays for better performance")
            
            report.crawl_strategy_suggestions = strategy_suggestions
            
            if self.logger:
                self.logger.success(
                    f"Generated comprehensive report for {base_url}: "
                    f"{report.site_mapping_completeness.total_pages_crawled if report.site_mapping_completeness else 0} pages, "
                    f"{report.file_discovery_stats.total_files_discovered if report.file_discovery_stats else 0} files",
                    tag="REPORT"
                )
            
            return report
            
        except Exception as e:
            if self.logger:
                self.logger.error(
                    f"Failed to generate comprehensive report: {str(e)}",
                    tag="ERROR"
                )
            # Return minimal report on error
            return ComprehensiveSiteReport(
                base_url=base_url,
                crawl_session_id=session_id or "error_report",
                report_generated_at=datetime.now()
            )
    
    async def export_report_to_json(self, report: ComprehensiveSiteReport, output_path: str = None) -> str:
        """
        Export comprehensive report to JSON format.
        
        Args:
            report: ComprehensiveSiteReport to export
            output_path: Optional output file path
            
        Returns:
            Path to exported JSON file
        """
        try:
            if output_path is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                safe_url = report.base_url.replace('://', '_').replace('/', '_')
                output_path = f"site_report_{safe_url}_{timestamp}.json"
            
            # Convert report to dictionary for JSON serialization
            report_dict = {
                'base_url': report.base_url,
                'crawl_session_id': report.crawl_session_id,
                'report_generated_at': report.report_generated_at.isoformat(),
                'crawl_start_time': report.crawl_start_time.isoformat() if report.crawl_start_time else None,
                'crawl_end_time': report.crawl_end_time.isoformat() if report.crawl_end_time else None,
                'total_crawl_duration': str(report.total_crawl_duration) if report.total_crawl_duration else None,
                'pages_per_minute': report.pages_per_minute,
                'average_page_load_time': report.average_page_load_time,
                'total_data_processed': report.total_data_processed,
                'content_quality_score': report.content_quality_score,
                'link_integrity_score': report.link_integrity_score,
                'site_structure_score': report.site_structure_score,
                'optimization_recommendations': report.optimization_recommendations,
                'crawl_strategy_suggestions': report.crawl_strategy_suggestions
            }
            
            # Add component analyses
            if report.site_mapping_completeness:
                report_dict['site_mapping_completeness'] = asdict(report.site_mapping_completeness)
            
            if report.file_discovery_stats:
                report_dict['file_discovery_stats'] = asdict(report.file_discovery_stats)
            
            if report.dead_end_analysis:
                analysis_dict = asdict(report.dead_end_analysis)
                # Convert timedelta to string for JSON serialization
                if analysis_dict.get('time_since_last_discovery'):
                    analysis_dict['time_since_last_discovery'] = str(analysis_dict['time_since_last_discovery'])
                report_dict['dead_end_analysis'] = analysis_dict
            
            # Write JSON file
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(report_dict, f, indent=2, ensure_ascii=False, default=str)
            
            if self.logger:
                self.logger.success(
                    f"Exported comprehensive report to: {output_path}",
                    tag="EXPORT"
                )
            
            return output_path
            
        except Exception as e:
            if self.logger:
                self.logger.error(
                    f"Failed to export report to JSON: {str(e)}",
                    tag="ERROR"
                )
            raise
    
    def track_page_performance(self, url: str, load_time: float, data_size: int = 0):
        """
        Track page performance metrics for reporting.
        
        Args:
            url: URL that was processed
            load_time: Time taken to load/process the page
            data_size: Size of data processed (bytes)
        """
        if self._session_metrics:
            self._session_metrics['page_load_times'].append(load_time)
            self._session_metrics['data_processed'] += data_size
    
    def track_error(self, url: str, error_message: str):
        """
        Track errors for reporting.
        
        Args:
            url: URL where error occurred
            error_message: Error description
        """
        if self._session_metrics:
            self._session_metrics['error_count'] += 1
        
        if self.logger:
            self.logger.warning(
                f"Tracked error for {url}: {error_message}",
                tag="TRACK_ERROR"
            )


def create_analytics_reporter(
    site_graph_manager: SiteGraphDatabaseManager = None,
    logger: AsyncLoggerBase = None
) -> ExhaustiveAnalyticsReporter:
    """
    Factory function to create ExhaustiveAnalyticsReporter.
    
    Args:
        site_graph_manager: Optional site graph database manager
        logger: Optional logger instance
        
    Returns:
        ExhaustiveAnalyticsReporter instance
    """
    if site_graph_manager is None:
        from .site_graph_db import create_site_graph_manager
        site_graph_manager = create_site_graph_manager()
    
    return ExhaustiveAnalyticsReporter(site_graph_manager, logger)


async def generate_site_mapping_report(
    base_url: str,
    analytics: ExhaustiveAnalytics,
    output_path: str = None,
    logger: AsyncLoggerBase = None
) -> str:
    """
    Convenience function to generate and export a comprehensive site mapping report.
    
    Args:
        base_url: Base URL that was crawled
        analytics: ExhaustiveAnalytics instance with session data
        output_path: Optional output file path for JSON export
        logger: Optional logger instance
        
    Returns:
        Path to exported report file
    """
    reporter = create_analytics_reporter(logger=logger)
    
    # Start reporting session
    session_id = reporter.start_reporting_session(base_url)
    
    # Generate comprehensive report
    report = await reporter.generate_comprehensive_report(base_url, analytics, session_id)
    
    # Export to JSON
    return await reporter.export_report_to_json(report, output_path)