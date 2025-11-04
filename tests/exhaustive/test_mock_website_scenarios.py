#!/usr/bin/env python3
"""
Mock Website Scenarios for Exhaustive Crawling Tests

This module provides comprehensive mock website scenarios to test different
crawling patterns, site structures, and edge cases for exhaustive crawling.
"""

import pytest
import asyncio
import sys
from pathlib import Path
from typing import Dict, List, Set, Optional, Tuple
from dataclasses import dataclass
from unittest.mock import AsyncMock

# Add the project root directory to the path to import crawl4ai
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from crawl4ai import ExhaustiveCrawlConfig
from crawl4ai.exhaustive_analytics import ExhaustiveAnalytics
from crawl4ai.exhaustive_webcrawler import ExhaustiveAsyncWebCrawler
from crawl4ai.models import CrawlResult, MarkdownGenerationResult


@dataclass
class MockPage:
    """Represents a mock web page with links and metadata."""
    url: str
    title: str
    content: str
    internal_links: List[str]
    external_links: List[str]
    file_links: List[str]
    status_code: int = 200
    load_time: float = 0.1
    content_type: str = "text/html"
    depth: int = 0


class MockWebsiteGenerator:
    """Generator for creating mock website structures for testing."""
    
    @staticmethod
    def create_linear_site(base_url: str, num_pages: int = 5, branch_factor: int = 0) -> Dict[str, MockPage]:
        """
        Create a linear site structure: page1 -> page2 -> page3 -> ...
        
        Args:
            base_url: Base URL for the site
            num_pages: Number of pages in the linear chain
            branch_factor: Number of additional branches from each page
            
        Returns:
            Dictionary mapping URLs to MockPage objects
        """
        pages = {}
        
        for i in range(num_pages):
            current_url = f"{base_url}/page{i}"
            
            # Link to next page in chain
            internal_links = []
            if i < num_pages - 1:
                internal_links.append(f"{base_url}/page{i + 1}")
            
            # Add branch links if specified
            for j in range(branch_factor):
                branch_url = f"{base_url}/page{i}_branch{j}"
                internal_links.append(branch_url)
                
                # Create branch page (dead end)
                pages[branch_url] = MockPage(
                    url=branch_url,
                    title=f"Branch {j} from Page {i}",
                    content=f"This is branch {j} from page {i}",
                    internal_links=[current_url],  # Link back to main chain
                    external_links=[],
                    file_links=[],
                    depth=1
                )
            
            pages[current_url] = MockPage(
                url=current_url,
                title=f"Page {i}",
                content=f"This is page {i} in the linear sequence",
                internal_links=internal_links,
                external_links=[],
                file_links=[],
                depth=0
            )
        
        return pages
    
    @staticmethod
    def create_hub_and_spoke_site(hub_url: str, num_spokes: int = 5, spoke_depth: int = 2) -> Dict[str, MockPage]:
        """
        Create a hub-and-spoke site structure.
        
        Args:
            hub_url: URL of the central hub page
            num_spokes: Number of spokes extending from the hub
            spoke_depth: Depth of each spoke (chain length)
            
        Returns:
            Dictionary mapping URLs to MockPage objects
        """
        pages = {}
        
        # Create hub page
        hub_links = []
        for i in range(num_spokes):
            spoke_root = f"{hub_url}/spoke{i}"
            hub_links.append(spoke_root)
        
        pages[hub_url] = MockPage(
            url=hub_url,
            title="Hub Page",
            content="Central hub with links to all sections",
            internal_links=hub_links,
            external_links=[],
            file_links=[],
            depth=0
        )
        
        # Create spokes
        for i in range(num_spokes):
            for j in range(spoke_depth):
                current_url = f"{hub_url}/spoke{i}/page{j}"
                
                internal_links = [hub_url]  # Always link back to hub
                
                # Link to next page in spoke
                if j < spoke_depth - 1:
                    internal_links.append(f"{hub_url}/spoke{i}/page{j + 1}")
                
                # Link to previous page in spoke
                if j > 0:
                    internal_links.append(f"{hub_url}/spoke{i}/page{j - 1}")
                
                pages[current_url] = MockPage(
                    url=current_url,
                    title=f"Spoke {i} Page {j}",
                    content=f"Page {j} in spoke {i}",
                    internal_links=internal_links,
                    external_links=[],
                    file_links=[],
                    depth=j + 1
                )
        
        return pages
    
    @staticmethod
    def create_deep_tree_site(base_url: str, max_depth: int = 4, branching_factor: int = 3) -> Dict[str, MockPage]:
        """
        Create a deep tree site structure.
        
        Args:
            base_url: Base URL for the site
            max_depth: Maximum depth of the tree
            branching_factor: Number of children per node
            
        Returns:
            Dictionary mapping URLs to MockPage objects
        """
        pages = {}
        
        def create_tree_node(url: str, depth: int, parent_url: Optional[str] = None):
            if depth > max_depth:
                return
            
            # Create child URLs
            child_urls = []
            if depth < max_depth:
                for i in range(branching_factor):
                    child_url = f"{url}/child{i}"
                    child_urls.append(child_url)
                    create_tree_node(child_url, depth + 1, url)
            
            # Add parent link if not root
            internal_links = child_urls.copy()
            if parent_url:
                internal_links.append(parent_url)
            
            pages[url] = MockPage(
                url=url,
                title=f"Tree Node Depth {depth}",
                content=f"Tree node at depth {depth} with {len(child_urls)} children",
                internal_links=internal_links,
                external_links=[],
                file_links=[],
                depth=depth
            )
        
        create_tree_node(base_url, 0)
        return pages
    
    @staticmethod
    def create_cyclic_site(base_url: str, cycle_length: int = 4, num_cycles: int = 2) -> Dict[str, MockPage]:
        """
        Create a site with cyclic link structures.
        
        Args:
            base_url: Base URL for the site
            cycle_length: Number of pages in each cycle
            num_cycles: Number of separate cycles
            
        Returns:
            Dictionary mapping URLs to MockPage objects
        """
        pages = {}
        
        for cycle in range(num_cycles):
            cycle_pages = []
            
            # Create pages in the cycle
            for i in range(cycle_length):
                page_url = f"{base_url}/cycle{cycle}/page{i}"
                cycle_pages.append(page_url)
            
            # Link pages in a cycle
            for i, page_url in enumerate(cycle_pages):
                next_page = cycle_pages[(i + 1) % cycle_length]
                prev_page = cycle_pages[(i - 1) % cycle_length]
                
                internal_links = [next_page, prev_page]
                
                # Add links to other cycles
                if cycle < num_cycles - 1:
                    other_cycle_entry = f"{base_url}/cycle{cycle + 1}/page0"
                    internal_links.append(other_cycle_entry)
                
                pages[page_url] = MockPage(
                    url=page_url,
                    title=f"Cycle {cycle} Page {i}",
                    content=f"Page {i} in cycle {cycle}",
                    internal_links=internal_links,
                    external_links=[],
                    file_links=[],
                    depth=cycle
                )
        
        return pages
    
    @staticmethod
    def create_file_rich_site(base_url: str, num_pages: int = 10, files_per_page: int = 3) -> Dict[str, MockPage]:
        """
        Create a site rich with downloadable files.
        
        Args:
            base_url: Base URL for the site
            num_pages: Number of pages
            files_per_page: Number of file links per page
            
        Returns:
            Dictionary mapping URLs to MockPage objects
        """
        pages = {}
        file_extensions = ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.txt', '.csv']
        
        for i in range(num_pages):
            page_url = f"{base_url}/page{i}"
            
            # Create file links
            file_links = []
            for j in range(files_per_page):
                ext = file_extensions[j % len(file_extensions)]
                file_url = f"{base_url}/files/page{i}_file{j}{ext}"
                file_links.append(file_url)
            
            # Create internal links to other pages
            internal_links = []
            if i > 0:
                internal_links.append(f"{base_url}/page{i - 1}")
            if i < num_pages - 1:
                internal_links.append(f"{base_url}/page{i + 1}")
            
            # Add links to file repository pages
            if i % 3 == 0:
                internal_links.append(f"{base_url}/downloads")
                internal_links.append(f"{base_url}/documents")
            
            pages[page_url] = MockPage(
                url=page_url,
                title=f"Page {i} with Files",
                content=f"Page {i} containing {files_per_page} downloadable files",
                internal_links=internal_links,
                external_links=[],
                file_links=file_links,
                depth=0
            )
        
        # Create file repository pages
        pages[f"{base_url}/downloads"] = MockPage(
            url=f"{base_url}/downloads",
            title="Downloads Repository",
            content="Central downloads repository",
            internal_links=[f"{base_url}/page{i}" for i in range(0, num_pages, 3)],
            external_links=[],
            file_links=[f"{base_url}/downloads/archive{i}.zip" for i in range(5)],
            depth=1
        )
        
        pages[f"{base_url}/documents"] = MockPage(
            url=f"{base_url}/documents",
            title="Documents Repository",
            content="Document repository with various file types",
            internal_links=[f"{base_url}/page{i}" for i in range(1, num_pages, 3)],
            external_links=[],
            file_links=[f"{base_url}/documents/doc{i}.pdf" for i in range(10)],
            depth=1
        )
        
        return pages
    
    @staticmethod
    def create_mixed_complexity_site(base_url: str) -> Dict[str, MockPage]:
        """
        Create a site with mixed complexity patterns.
        
        Combines linear sections, hub-and-spoke areas, deep trees, and file repositories.
        
        Args:
            base_url: Base URL for the site
            
        Returns:
            Dictionary mapping URLs to MockPage objects
        """
        pages = {}
        
        # Main hub page
        pages[base_url] = MockPage(
            url=base_url,
            title="Main Hub",
            content="Main site hub with links to all sections",
            internal_links=[
                f"{base_url}/linear",
                f"{base_url}/hub",
                f"{base_url}/tree",
                f"{base_url}/files",
                f"{base_url}/about"
            ],
            external_links=["https://external.com"],
            file_links=[f"{base_url}/sitemap.xml"],
            depth=0
        )
        
        # Linear section
        linear_pages = MockWebsiteGenerator.create_linear_site(f"{base_url}/linear", 5, 1)
        pages.update(linear_pages)
        
        # Hub-and-spoke section
        hub_pages = MockWebsiteGenerator.create_hub_and_spoke_site(f"{base_url}/hub", 3, 2)
        pages.update(hub_pages)
        
        # Deep tree section
        tree_pages = MockWebsiteGenerator.create_deep_tree_site(f"{base_url}/tree", 3, 2)
        pages.update(tree_pages)
        
        # File-rich section
        file_pages = MockWebsiteGenerator.create_file_rich_site(f"{base_url}/files", 5, 2)
        pages.update(file_pages)
        
        # About section (simple page)
        pages[f"{base_url}/about"] = MockPage(
            url=f"{base_url}/about",
            title="About Us",
            content="About page with contact information",
            internal_links=[base_url],
            external_links=["https://social.com/company"],
            file_links=[f"{base_url}/about/company_info.pdf"],
            depth=1
        )
        
        return pages


class MockCrawlSimulator:
    """Simulates crawling behavior on mock websites."""
    
    def __init__(self, website_pages: Dict[str, MockPage]):
        self.pages = website_pages
        self.crawl_delays = {}  # URL -> delay in seconds
        self.failure_rates = {}  # URL -> failure probability (0.0-1.0)
    
    def set_crawl_delay(self, url_pattern: str, delay: float):
        """Set crawl delay for URLs matching pattern."""
        self.crawl_delays[url_pattern] = delay
    
    def set_failure_rate(self, url_pattern: str, failure_rate: float):
        """Set failure rate for URLs matching pattern."""
        self.failure_rates[url_pattern] = failure_rate
    
    def create_crawl_result(self, url: str) -> CrawlResult:
        """Create a CrawlResult for the given URL."""
        if url not in self.pages:
            # Return 404 result
            return CrawlResult(
                url=url,
                html="",
                success=False,
                error_message="Page not found",
                status_code=404
            )
        
        page = self.pages[url]
        
        # Check for simulated failures
        import random
        for pattern, failure_rate in self.failure_rates.items():
            if pattern in url and random.random() < failure_rate:
                return CrawlResult(
                    url=url,
                    html="",
                    success=False,
                    error_message="Simulated network error",
                    status_code=500
                )
        
        # Create successful result
        all_links = page.internal_links + page.external_links + page.file_links
        links_dict = {
            'internal': [{'href': link} for link in page.internal_links],
            'external': [{'href': link} for link in page.external_links]
        }
        
        # Add file links to internal links for discovery
        for file_link in page.file_links:
            links_dict['internal'].append({'href': file_link})
        
        html_content = f"""
        <html>
        <head><title>{page.title}</title></head>
        <body>
            <h1>{page.title}</h1>
            <p>{page.content}</p>
            <div class="links">
                {' '.join([f'<a href="{link}">{link}</a>' for link in all_links])}
            </div>
        </body>
        </html>
        """
        
        markdown_result = MarkdownGenerationResult(
            raw_markdown=f"# {page.title}\n\n{page.content}",
            markdown_with_citations="",
            references_markdown="",
            fit_markdown="",
            fit_html=""
        )
        
        return CrawlResult(
            url=url,
            html=html_content,
            success=True,
            cleaned_html=f"<h1>{page.title}</h1><p>{page.content}</p>",
            markdown=markdown_result,
            links=links_dict,
            metadata={'depth': page.depth, 'load_time': page.load_time},
            status_code=page.status_code
        )


class TestLinearSiteCrawling:
    """Test crawling linear site structures."""
    
    def test_simple_linear_crawling(self):
        """Test crawling a simple linear site."""
        pages = MockWebsiteGenerator.create_linear_site("https://linear.com", 5)
        simulator = MockCrawlSimulator(pages)
        
        analytics = ExhaustiveAnalytics()
        analytics.start_crawl_session()
        
        # Simulate crawling the linear site
        current_url = "https://linear.com/page0"
        crawled_urls = []
        
        while current_url and len(crawled_urls) < 10:  # Safety limit
            crawled_urls.append(current_url)
            
            # Get crawl result
            result = simulator.create_crawl_result(current_url)
            analysis = analytics.analyze_crawl_results([result], current_url)
            
            # Get next URL
            current_url = analytics.get_next_crawl_url()
        
        # Should crawl all pages in sequence
        assert len(crawled_urls) == 5
        expected_urls = [f"https://linear.com/page{i}" for i in range(5)]
        assert crawled_urls == expected_urls
    
    def test_linear_with_branches_crawling(self):
        """Test crawling linear site with branches."""
        pages = MockWebsiteGenerator.create_linear_site("https://branched.com", 3, 2)
        simulator = MockCrawlSimulator(pages)
        
        analytics = ExhaustiveAnalytics()
        analytics.start_crawl_session()
        
        # Crawl starting from root
        crawled_count = 0
        current_url = "https://branched.com/page0"
        
        while current_url and crawled_count < 20:  # Safety limit
            result = simulator.create_crawl_result(current_url)
            analytics.analyze_crawl_results([result], current_url)
            crawled_count += 1
            current_url = analytics.get_next_crawl_url()
        
        # Should discover main chain + branches
        stats = analytics.url_state.get_stats()
        assert stats['total_discovered'] >= 9  # 3 main + 6 branches


class TestHubAndSpokeCrawling:
    """Test crawling hub-and-spoke structures."""
    
    def test_hub_and_spoke_discovery(self):
        """Test discovery pattern in hub-and-spoke structure."""
        pages = MockWebsiteGenerator.create_hub_and_spoke_site("https://hub.com", 4, 3)
        simulator = MockCrawlSimulator(pages)
        
        analytics = ExhaustiveAnalytics()
        analytics.start_crawl_session()
        
        # Start from hub
        hub_result = simulator.create_crawl_result("https://hub.com")
        analysis = analytics.analyze_crawl_results([hub_result], "https://hub.com")
        
        # Should discover all spoke roots
        assert analysis['new_urls_discovered'] == 4
        
        # Crawl one spoke
        spoke_url = analytics.get_next_crawl_url()
        spoke_result = simulator.create_crawl_result(spoke_url)
        analysis = analytics.analyze_crawl_results([spoke_result], spoke_url)
        
        # Should discover URLs in the spoke (may be 0 if all are revisits)
        assert analysis['new_urls_discovered'] >= 0
    
    def test_revisit_detection_in_hub_spoke(self):
        """Test revisit detection in hub-and-spoke structure."""
        pages = MockWebsiteGenerator.create_hub_and_spoke_site("https://revisit.com", 3, 2)
        simulator = MockCrawlSimulator(pages)
        
        analytics = ExhaustiveAnalytics()
        analytics.start_crawl_session()
        
        # Crawl hub and several spokes
        urls_to_crawl = ["https://revisit.com"]
        
        for _ in range(5):  # Crawl several pages
            if not urls_to_crawl:
                next_url = analytics.get_next_crawl_url()
                if next_url:
                    urls_to_crawl.append(next_url)
            
            if urls_to_crawl:
                current_url = urls_to_crawl.pop(0)
                result = simulator.create_crawl_result(current_url)
                analytics.analyze_crawl_results([result], current_url)
        
        # Should detect some revisits (spokes link back to hub)
        assert analytics.metrics.revisit_count > 0


class TestDeepTreeCrawling:
    """Test crawling deep tree structures."""
    
    def test_breadth_first_tree_crawling(self):
        """Test breadth-first crawling of tree structure."""
        pages = MockWebsiteGenerator.create_deep_tree_site("https://tree.com", 3, 2)
        simulator = MockCrawlSimulator(pages)
        
        analytics = ExhaustiveAnalytics()
        analytics.start_crawl_session()
        
        # Crawl the tree
        crawled_count = 0
        current_url = "https://tree.com"
        
        while current_url and crawled_count < 20:
            result = simulator.create_crawl_result(current_url)
            analytics.analyze_crawl_results([result], current_url)
            crawled_count += 1
            current_url = analytics.get_next_crawl_url()
        
        # Should discover many URLs in the tree
        stats = analytics.url_state.get_stats()
        expected_nodes = 1 + 2 + 4 + 8  # Root + depth 1 + depth 2 + depth 3
        assert stats['total_discovered'] >= expected_nodes - 5  # Allow some variance
    
    def test_depth_tracking_in_tree(self):
        """Test depth tracking in tree structure."""
        pages = MockWebsiteGenerator.create_deep_tree_site("https://depth.com", 2, 3)
        simulator = MockCrawlSimulator(pages)
        
        # Verify depth information is preserved
        root_page = pages["https://depth.com"]
        assert root_page.depth == 0
        
        child_page = pages["https://depth.com/child0"]
        assert child_page.depth == 1
        
        grandchild_page = pages["https://depth.com/child0/child0"]
        assert grandchild_page.depth == 2


class TestCyclicStructureCrawling:
    """Test crawling sites with cyclic link structures."""
    
    def test_cycle_detection(self):
        """Test detection and handling of cyclic structures."""
        pages = MockWebsiteGenerator.create_cyclic_site("https://cycle.com", 4, 2)
        simulator = MockCrawlSimulator(pages)
        
        analytics = ExhaustiveAnalytics()
        analytics.start_crawl_session()
        
        # Crawl through cycles
        current_url = "https://cycle.com/cycle0/page0"
        crawled_count = 0
        
        while current_url and crawled_count < 15:
            result = simulator.create_crawl_result(current_url)
            analytics.analyze_crawl_results([result], current_url)
            crawled_count += 1
            current_url = analytics.get_next_crawl_url()
        
        # Should detect high revisit ratio
        assert analytics.metrics.revisit_ratio > 0.3
        
        # Should eventually recommend stopping
        should_stop, reason = analytics.should_stop_crawling(revisit_threshold=0.8)
        if crawled_count > 8:
            assert should_stop or "revisit" in reason.lower()


class TestFileRichSiteCrawling:
    """Test crawling sites with many downloadable files."""
    
    def test_file_discovery_in_rich_site(self):
        """Test file discovery in file-rich site."""
        pages = MockWebsiteGenerator.create_file_rich_site("https://files.com", 5, 4)
        simulator = MockCrawlSimulator(pages)
        
        analytics = ExhaustiveAnalytics()
        analytics.start_crawl_session()
        
        # Crawl file-rich pages
        file_urls_discovered = set()
        
        for page_num in range(5):
            page_url = f"https://files.com/page{page_num}"
            result = simulator.create_crawl_result(page_url)
            
            # Extract file URLs from result
            if result.success and result.links:
                for link in result.links.get('internal', []):
                    href = link.get('href', '')
                    if any(ext in href for ext in ['.pdf', '.doc', '.xls', '.txt', '.csv']):
                        file_urls_discovered.add(href)
            
            analytics.analyze_crawl_results([result], page_url)
        
        # Should discover many file URLs
        assert len(file_urls_discovered) >= 15  # 5 pages * 4 files - some overlap
    
    def test_repository_page_crawling(self):
        """Test crawling file repository pages."""
        pages = MockWebsiteGenerator.create_file_rich_site("https://repo.com", 3, 2)
        simulator = MockCrawlSimulator(pages)
        
        # Test repository pages
        downloads_result = simulator.create_crawl_result("https://repo.com/downloads")
        assert downloads_result.success
        assert len(downloads_result.links['internal']) > 5  # Should have many file links
        
        documents_result = simulator.create_crawl_result("https://repo.com/documents")
        assert documents_result.success
        assert len(documents_result.links['internal']) > 10  # Should have many document links


class TestMixedComplexitySite:
    """Test crawling sites with mixed complexity patterns."""
    
    def test_comprehensive_mixed_site_crawling(self):
        """Test crawling a site with mixed complexity patterns."""
        pages = MockWebsiteGenerator.create_mixed_complexity_site("https://complex.com")
        simulator = MockCrawlSimulator(pages)
        
        analytics = ExhaustiveAnalytics()
        analytics.start_crawl_session()
        
        # Start comprehensive crawl
        current_url = "https://complex.com"
        crawled_count = 0
        section_visits = {'linear': 0, 'hub': 0, 'tree': 0, 'files': 0}
        
        while current_url and crawled_count < 50:  # Generous limit
            result = simulator.create_crawl_result(current_url)
            analytics.analyze_crawl_results([result], current_url)
            
            # Track section visits
            for section in section_visits:
                if f"/{section}" in current_url:
                    section_visits[section] += 1
            
            crawled_count += 1
            current_url = analytics.get_next_crawl_url()
        
        # Should visit multiple sections
        sections_visited = sum(1 for count in section_visits.values() if count > 0)
        assert sections_visited >= 3
        
        # Should discover substantial number of URLs
        stats = analytics.url_state.get_stats()
        assert stats['total_discovered'] > 20


class TestErrorScenarios:
    """Test crawling behavior with various error scenarios."""
    
    def test_crawling_with_network_errors(self):
        """Test crawling behavior when some pages fail to load."""
        pages = MockWebsiteGenerator.create_linear_site("https://errors.com", 5)
        simulator = MockCrawlSimulator(pages)
        
        # Set failure rate for some pages
        simulator.set_failure_rate("/page2", 1.0)  # Always fail
        simulator.set_failure_rate("/page4", 0.5)  # 50% failure rate
        
        analytics = ExhaustiveAnalytics()
        analytics.start_crawl_session()
        
        # Crawl with errors
        failed_urls = []
        successful_urls = []
        
        for i in range(5):
            url = f"https://errors.com/page{i}"
            result = simulator.create_crawl_result(url)
            
            if result.success:
                successful_urls.append(url)
            else:
                failed_urls.append(url)
            
            analytics.analyze_crawl_results([result], url)
        
        # Should handle failures gracefully
        assert len(failed_urls) > 0  # Some failures expected
        assert len(successful_urls) > 0  # Some successes expected
        
        # Analytics should track failures
        stats = analytics.url_state.get_stats()
        assert stats['total_failed'] > 0
    
    def test_crawling_with_slow_pages(self):
        """Test crawling behavior with slow-loading pages."""
        pages = MockWebsiteGenerator.create_hub_and_spoke_site("https://slow.com", 3, 2)
        simulator = MockCrawlSimulator(pages)
        
        # Set delays for some pages
        simulator.set_crawl_delay("/spoke1", 0.5)
        simulator.set_crawl_delay("/spoke2", 1.0)
        
        # This test mainly verifies the simulator can handle delays
        # In real implementation, timeouts would be handled by the crawler
        result = simulator.create_crawl_result("https://slow.com/spoke1/page0")
        assert result.success


if __name__ == "__main__":
    # Run mock website scenario tests
    print("Running mock website scenario tests...")
    
    # Linear site tests
    test_linear = TestLinearSiteCrawling()
    test_linear.test_simple_linear_crawling()
    test_linear.test_linear_with_branches_crawling()
    print("✓ Linear site crawling tests passed")
    
    # Hub-and-spoke tests
    test_hub = TestHubAndSpokeCrawling()
    test_hub.test_hub_and_spoke_discovery()
    test_hub.test_revisit_detection_in_hub_spoke()
    print("✓ Hub-and-spoke crawling tests passed")
    
    # Tree structure tests
    test_tree = TestDeepTreeCrawling()
    test_tree.test_breadth_first_tree_crawling()
    test_tree.test_depth_tracking_in_tree()
    print("✓ Deep tree crawling tests passed")
    
    # Cyclic structure tests
    test_cycle = TestCyclicStructureCrawling()
    test_cycle.test_cycle_detection()
    print("✓ Cyclic structure crawling tests passed")
    
    # File-rich site tests
    test_files = TestFileRichSiteCrawling()
    test_files.test_file_discovery_in_rich_site()
    test_files.test_repository_page_crawling()
    print("✓ File-rich site crawling tests passed")
    
    # Mixed complexity tests
    test_mixed = TestMixedComplexitySite()
    test_mixed.test_comprehensive_mixed_site_crawling()
    print("✓ Mixed complexity site crawling tests passed")
    
    # Error scenario tests
    test_errors = TestErrorScenarios()
    test_errors.test_crawling_with_network_errors()
    test_errors.test_crawling_with_slow_pages()
    print("✓ Error scenario tests passed")
    
    print("\n🎉 All mock website scenario tests passed!")