#!/usr/bin/env python3
"""
Comprehensive Tests for Site Graph Handler

Tests for NetworkX-based site graph analysis, visualization, and export capabilities.
"""

import pytest
import asyncio
import tempfile
import json
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch

# Import the modules to test
from crawl4ai.site_graph_handler import (
    SiteGraphHandler,
    GraphNode,
    GraphEdge,
    GraphAnalysisResult,
    create_graph_from_crawl_results,
    analyze_site_graph_async
)
from crawl4ai.graph_visualizer import (
    GraphVisualizer,
    quick_visualize,
    analyze_graph_patterns
)


class TestGraphNode:
    """Test GraphNode data class."""
    
    def test_basic_node_creation(self):
        """Test basic node creation."""
        node = GraphNode(
            url="https://example.com",
            title="Test Page",
            content_type="text/html",
            status_code=200,
            depth=0
        )
        
        assert node.url == "https://example.com"
        assert node.title == "Test Page"
        assert node.content_type == "text/html"
        assert node.status_code == 200
        assert node.depth == 0
        assert not node.is_file
        assert node.metadata == {}
    
    def test_file_node_auto_detection(self):
        """Test automatic file detection."""
        # PDF file
        pdf_node = GraphNode(url="https://example.com/document.pdf")
        assert pdf_node.is_file
        assert pdf_node.file_extension == ".pdf"
        
        # Regular page
        page_node = GraphNode(url="https://example.com/page")
        assert not page_node.is_file
        assert page_node.file_extension is None
        
        # ZIP file
        zip_node = GraphNode(url="https://example.com/archive.zip")
        assert zip_node.is_file
        assert zip_node.file_extension == ".zip"
    
    def test_node_with_metadata(self):
        """Test node with custom metadata."""
        metadata = {"custom_field": "value", "score": 0.85}
        node = GraphNode(
            url="https://example.com",
            metadata=metadata
        )
        
        assert node.metadata == metadata


class TestGraphEdge:
    """Test GraphEdge data class."""
    
    def test_basic_edge_creation(self):
        """Test basic edge creation."""
        edge = GraphEdge(
            source="https://example.com",
            target="https://example.com/page",
            edge_type="link",
            anchor_text="Click here"
        )
        
        assert edge.source == "https://example.com"
        assert edge.target == "https://example.com/page"
        assert edge.edge_type == "link"
        assert edge.anchor_text == "Click here"
        assert edge.metadata == {}
    
    def test_edge_with_metadata(self):
        """Test edge with custom metadata."""
        metadata = {"weight": 0.5, "category": "navigation"}
        edge = GraphEdge(
            source="https://example.com",
            target="https://example.com/page",
            metadata=metadata
        )
        
        assert edge.metadata == metadata


class TestSiteGraphHandler:
    """Test SiteGraphHandler main functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.handler = SiteGraphHandler()
        
        # Create sample nodes
        self.nodes = [
            GraphNode(
                url="https://example.com",
                title="Homepage",
                content_type="text/html",
                status_code=200,
                depth=0
            ),
            GraphNode(
                url="https://example.com/about",
                title="About Us",
                content_type="text/html",
                status_code=200,
                depth=1
            ),
            GraphNode(
                url="https://example.com/contact",
                title="Contact",
                content_type="text/html",
                status_code=200,
                depth=1
            ),
            GraphNode(
                url="https://example.com/docs/manual.pdf",
                title="Manual",
                content_type="application/pdf",
                status_code=200,
                depth=2,
                is_file=True,
                file_extension=".pdf"
            )
        ]
        
        # Create sample edges
        self.edges = [
            GraphEdge(
                source="https://example.com",
                target="https://example.com/about",
                edge_type="link",
                anchor_text="About"
            ),
            GraphEdge(
                source="https://example.com",
                target="https://example.com/contact",
                edge_type="link",
                anchor_text="Contact"
            ),
            GraphEdge(
                source="https://example.com/about",
                target="https://example.com/docs/manual.pdf",
                edge_type="link",
                anchor_text="Download Manual"
            )
        ]
    
    def test_add_nodes(self):
        """Test adding nodes to the graph."""
        for node in self.nodes:
            self.handler.add_node(node)
        
        assert len(self.handler.nodes) == 4
        assert len(self.handler.graph.nodes()) == 4
        
        # Check node attributes
        homepage = self.handler.get_node("https://example.com")
        assert homepage.title == "Homepage"
        assert homepage.depth == 0
    
    def test_add_edges(self):
        """Test adding edges to the graph."""
        # Add nodes first
        for node in self.nodes:
            self.handler.add_node(node)
        
        # Add edges
        for edge in self.edges:
            self.handler.add_edge(edge)
        
        assert len(self.handler.edges) == 3
        assert len(self.handler.graph.edges()) == 3
        
        # Check edge attributes
        assert self.handler.graph.has_edge("https://example.com", "https://example.com/about")
    
    def test_get_neighbors(self):
        """Test getting node neighbors."""
        # Set up graph
        for node in self.nodes:
            self.handler.add_node(node)
        for edge in self.edges:
            self.handler.add_edge(edge)
        
        # Test outgoing neighbors
        out_neighbors = self.handler.get_neighbors("https://example.com", "out")
        assert len(out_neighbors) == 2
        assert "https://example.com/about" in out_neighbors
        assert "https://example.com/contact" in out_neighbors
        
        # Test incoming neighbors
        in_neighbors = self.handler.get_neighbors("https://example.com/about", "in")
        assert len(in_neighbors) == 1
        assert "https://example.com" in in_neighbors
        
        # Test both directions
        both_neighbors = self.handler.get_neighbors("https://example.com/about", "both")
        assert len(both_neighbors) == 2
    
    def test_shortest_path(self):
        """Test shortest path calculation."""
        # Set up graph
        for node in self.nodes:
            self.handler.add_node(node)
        for edge in self.edges:
            self.handler.add_edge(edge)
        
        # Test existing path
        path = self.handler.get_shortest_path(
            "https://example.com",
            "https://example.com/docs/manual.pdf"
        )
        assert path is not None
        assert len(path) == 3
        assert path[0] == "https://example.com"
        assert path[-1] == "https://example.com/docs/manual.pdf"
        
        # Test non-existing path
        no_path = self.handler.get_shortest_path(
            "https://example.com/contact",
            "https://example.com/docs/manual.pdf"
        )
        assert no_path is None
    
    def test_remove_node(self):
        """Test node removal."""
        # Set up graph
        for node in self.nodes:
            self.handler.add_node(node)
        for edge in self.edges:
            self.handler.add_edge(edge)
        
        initial_nodes = len(self.handler.nodes)
        initial_edges = len(self.handler.edges)
        
        # Remove a node
        removed = self.handler.remove_node("https://example.com/about")
        assert removed
        
        # Check node is removed
        assert len(self.handler.nodes) == initial_nodes - 1
        assert "https://example.com/about" not in self.handler.nodes
        
        # Check associated edges are removed
        assert len(self.handler.edges) < initial_edges
    
    def test_centrality_measures(self):
        """Test centrality calculations."""
        # Set up graph
        for node in self.nodes:
            self.handler.add_node(node)
        for edge in self.edges:
            self.handler.add_edge(edge)
        
        centrality = self.handler.calculate_centrality_measures()
        
        # Check all measures are present
        expected_measures = ['degree', 'in_degree', 'out_degree', 'betweenness', 
                           'closeness', 'pagerank', 'hubs', 'authorities']
        for measure in expected_measures:
            assert measure in centrality
            assert isinstance(centrality[measure], dict)
        
        # Check homepage has highest PageRank (it's the entry point)
        pagerank = centrality['pagerank']
        homepage_pr = pagerank.get("https://example.com", 0)
        assert homepage_pr > 0
    
    def test_graph_analysis(self):
        """Test comprehensive graph analysis."""
        # Set up graph
        for node in self.nodes:
            self.handler.add_node(node)
        for edge in self.edges:
            self.handler.add_edge(edge)
        
        analysis = self.handler.analyze_graph()
        
        # Check analysis result structure
        assert isinstance(analysis, GraphAnalysisResult)
        assert analysis.total_nodes == 4
        assert analysis.total_edges == 3
        assert analysis.density > 0
        assert len(analysis.file_nodes) == 1
        assert len(analysis.entry_points) >= 1
        
        # Check PageRank results
        assert len(analysis.page_rank_top_10) <= 4
        assert all(isinstance(item, tuple) and len(item) == 2 
                  for item in analysis.page_rank_top_10)
    
    def test_empty_graph_analysis(self):
        """Test analysis of empty graph."""
        analysis = self.handler.analyze_graph()
        
        assert analysis.total_nodes == 0
        assert analysis.total_edges == 0
        assert analysis.density == 0.0
        assert len(analysis.page_rank_top_10) == 0
    
    def test_graph_filtering(self):
        """Test graph filtering operations."""
        # Set up graph
        for node in self.nodes:
            self.handler.add_node(node)
        for edge in self.edges:
            self.handler.add_edge(edge)
        
        # Filter by domain
        domain_subgraph = self.handler.filter_by_domain("example.com")
        assert len(domain_subgraph.nodes) == 4  # All nodes are from example.com
        
        # Filter by file type
        file_subgraph = self.handler.filter_by_file_type([".pdf"])
        assert len(file_subgraph.nodes) == 1
        assert "https://example.com/docs/manual.pdf" in file_subgraph.nodes
        
        # Custom subgraph
        selected_nodes = ["https://example.com", "https://example.com/about"]
        custom_subgraph = self.handler.get_subgraph(selected_nodes)
        assert len(custom_subgraph.nodes) == 2
    
    def test_export_formats(self):
        """Test graph export to various formats."""
        # Set up graph
        for node in self.nodes:
            self.handler.add_node(node)
        for edge in self.edges:
            self.handler.add_edge(edge)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            exported_files = self.handler.export_to_formats(temp_dir)
            
            # Check that files were created
            assert 'graphml' in exported_files
            assert 'json' in exported_files
            
            # Check GraphML file exists
            graphml_path = Path(exported_files['graphml'])
            assert graphml_path.exists()
            
            # Check JSON file exists and is valid
            json_path = Path(exported_files['json'])
            assert json_path.exists()
            
            with open(json_path, 'r') as f:
                json_data = json.load(f)
                assert 'nodes' in json_data
                assert 'edges' in json_data
                assert len(json_data['nodes']) == 4
                assert len(json_data['edges']) == 3
    
    def test_statistics(self):
        """Test comprehensive statistics."""
        # Set up graph
        for node in self.nodes:
            self.handler.add_node(node)
        for edge in self.edges:
            self.handler.add_edge(edge)
        
        stats = self.handler.get_statistics()
        
        # Check structure
        assert 'basic_stats' in stats
        assert 'node_types' in stats
        assert 'top_nodes' in stats
        
        # Check basic stats
        basic = stats['basic_stats']
        assert basic['total_nodes'] == 4
        assert basic['total_edges'] == 3
        
        # Check node types
        node_types = stats['node_types']
        assert node_types['total_files'] == 1
        assert node_types['total_pages'] == 3


class TestGraphVisualizer:
    """Test GraphVisualizer functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.handler = SiteGraphHandler()
        
        # Create a simple graph
        nodes = [
            GraphNode(url="https://example.com", title="Home", depth=0),
            GraphNode(url="https://example.com/page1", title="Page 1", depth=1),
            GraphNode(url="https://example.com/page2", title="Page 2", depth=1),
            GraphNode(url="https://example.com/file.pdf", title="File", depth=2, is_file=True)
        ]
        
        edges = [
            GraphEdge(source="https://example.com", target="https://example.com/page1"),
            GraphEdge(source="https://example.com", target="https://example.com/page2"),
            GraphEdge(source="https://example.com/page1", target="https://example.com/file.pdf")
        ]
        
        for node in nodes:
            self.handler.add_node(node)
        for edge in edges:
            self.handler.add_edge(edge)
        
        self.visualizer = GraphVisualizer(self.handler)
    
    def test_layout_creation(self):
        """Test different layout algorithms."""
        # Test hierarchical layout
        hierarchical_pos = self.visualizer.create_hierarchical_layout()
        assert len(hierarchical_pos) == 4
        assert all(isinstance(pos, tuple) and len(pos) == 2 
                  for pos in hierarchical_pos.values())
        
        # Test domain clustered layout
        domain_pos = self.visualizer.create_domain_clustered_layout()
        assert len(domain_pos) == 4
        
        # Test force directed layout
        force_pos = self.visualizer.create_force_directed_layout()
        assert len(force_pos) == 4
    
    def test_cytoscape_export(self):
        """Test Cytoscape format export."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            output_path = f.name
        
        try:
            result_path = self.visualizer.export_for_cytoscape(output_path)
            assert result_path == output_path
            
            # Check file content
            with open(output_path, 'r') as f:
                data = json.load(f)
                
            assert 'elements' in data
            assert 'style' in data
            assert 'layout' in data
            
            # Check elements
            elements = data['elements']
            nodes = [e for e in elements if 'source' not in e['data']]
            edges = [e for e in elements if 'source' in e['data']]
            
            assert len(nodes) == 4
            assert len(edges) == 3
            
        finally:
            Path(output_path).unlink(missing_ok=True)
    
    @patch('crawl4ai.graph_visualizer.MATPLOTLIB_AVAILABLE', True)
    @patch('matplotlib.pyplot.savefig')
    @patch('matplotlib.pyplot.close')
    def test_matplotlib_visualization(self, mock_close, mock_savefig):
        """Test matplotlib visualization (mocked)."""
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            output_path = f.name
        
        try:
            # Mock the visualization
            with patch.object(self.visualizer, 'visualize_with_matplotlib') as mock_viz:
                mock_viz.return_value = output_path
                
                result = self.visualizer.visualize_with_matplotlib(
                    output_path=output_path,
                    layout_type="spring",
                    color_scheme="depth"
                )
                
                assert result == output_path
                mock_viz.assert_called_once()
                
        finally:
            Path(output_path).unlink(missing_ok=True)
    
    @patch('crawl4ai.graph_visualizer.PLOTLY_AVAILABLE', True)
    def test_interactive_dashboard(self):
        """Test interactive dashboard creation (mocked)."""
        with tempfile.NamedTemporaryFile(suffix='.html', delete=False) as f:
            output_path = f.name
        
        try:
            # Mock the dashboard creation
            with patch.object(self.visualizer, 'create_interactive_dashboard') as mock_dash:
                mock_dash.return_value = output_path
                
                result = self.visualizer.create_interactive_dashboard(output_path)
                
                assert result == output_path
                mock_dash.assert_called_once()
                
        finally:
            Path(output_path).unlink(missing_ok=True)


class TestUtilityFunctions:
    """Test utility functions."""
    
    def test_create_graph_from_crawl_results(self):
        """Test creating graph from crawl results."""
        # Mock crawl results
        class MockCrawlResult:
            def __init__(self, url, success=True, title=None, links=None):
                self.url = url
                self.success = success
                self.title = title
                self.links = links or {'internal': []}
                self.status_code = 200 if success else 404
                self.content_type = "text/html"
        
        crawl_results = [
            MockCrawlResult(
                "https://example.com",
                title="Homepage",
                links={'internal': [
                    {'href': 'https://example.com/about', 'text': 'About'},
                    {'href': 'https://example.com/contact', 'text': 'Contact'}
                ]}
            ),
            MockCrawlResult(
                "https://example.com/about",
                title="About Us"
            ),
            MockCrawlResult(
                "https://example.com/failed",
                success=False
            )
        ]
        
        graph_handler = create_graph_from_crawl_results(crawl_results)
        
        # Check that successful results were added
        assert len(graph_handler.nodes) >= 2  # At least homepage and about
        assert "https://example.com" in graph_handler.nodes
        assert "https://example.com/about" in graph_handler.nodes
        
        # Check that edges were created
        assert len(graph_handler.edges) >= 1
    
    @pytest.mark.asyncio
    async def test_analyze_site_graph_async(self):
        """Test async graph analysis."""
        handler = SiteGraphHandler()
        
        # Add some nodes
        nodes = [
            GraphNode(url="https://example.com", depth=0),
            GraphNode(url="https://example.com/page", depth=1)
        ]
        edges = [
            GraphEdge(source="https://example.com", target="https://example.com/page")
        ]
        
        for node in nodes:
            handler.add_node(node)
        for edge in edges:
            handler.add_edge(edge)
        
        # Test async analysis
        analysis = await analyze_site_graph_async(handler)
        
        assert isinstance(analysis, GraphAnalysisResult)
        assert analysis.total_nodes == 2
        assert analysis.total_edges == 1
    
    def test_analyze_graph_patterns(self):
        """Test graph pattern analysis."""
        handler = SiteGraphHandler()
        
        # Create a hub-and-spoke pattern
        hub_url = "https://example.com"
        spoke_urls = [f"https://example.com/page{i}" for i in range(5)]
        
        # Add hub node
        handler.add_node(GraphNode(url=hub_url, depth=0))
        
        # Add spoke nodes and edges
        for spoke_url in spoke_urls:
            handler.add_node(GraphNode(url=spoke_url, depth=1))
            handler.add_edge(GraphEdge(source=hub_url, target=spoke_url))
        
        patterns = analyze_graph_patterns(handler)
        
        assert 'hub_and_spoke' in patterns
        assert 'hierarchical' in patterns
        
        # Should detect hub and spoke pattern
        hub_pattern = patterns['hub_and_spoke']
        assert hub_pattern['detected']
        assert hub_pattern['confidence'] > 0
        assert hub_url in hub_pattern['hub_nodes']


class TestIntegration:
    """Integration tests."""
    
    @pytest.mark.asyncio
    async def test_full_workflow(self):
        """Test complete workflow from creation to analysis."""
        # Create handler
        handler = SiteGraphHandler()
        
        # Build a realistic site structure
        base_url = "https://docs.example.com"
        urls = [
            f"{base_url}",
            f"{base_url}/getting-started",
            f"{base_url}/api",
            f"{base_url}/tutorials",
            f"{base_url}/tutorials/basic",
            f"{base_url}/downloads/manual.pdf"
        ]
        
        # Add nodes
        for i, url in enumerate(urls):
            is_file = url.endswith('.pdf')
            depth = url.count('/') - 2
            
            node = GraphNode(
                url=url,
                title=f"Page {i}",
                depth=depth,
                is_file=is_file,
                status_code=200,
                last_crawled=datetime.now()
            )
            handler.add_node(node)
        
        # Add edges to create realistic structure
        edges_data = [
            (urls[0], urls[1]),  # home -> getting-started
            (urls[0], urls[2]),  # home -> api
            (urls[0], urls[3]),  # home -> tutorials
            (urls[3], urls[4]),  # tutorials -> basic
            (urls[4], urls[5])   # basic -> manual.pdf
        ]
        
        for source, target in edges_data:
            handler.add_edge(GraphEdge(source=source, target=target))
        
        # Perform analysis
        analysis = await analyze_site_graph_async(handler)
        
        # Verify results
        assert analysis.total_nodes == 6
        assert analysis.total_edges == 5
        assert len(analysis.file_nodes) == 1
        assert analysis.density > 0
        
        # Test export
        with tempfile.TemporaryDirectory() as temp_dir:
            exported = handler.export_to_formats(temp_dir)
            assert len(exported) > 0
            
            # Verify JSON export
            if 'json' in exported:
                with open(exported['json'], 'r') as f:
                    data = json.load(f)
                    assert len(data['nodes']) == 6
                    assert len(data['edges']) == 5
        
        # Test visualization
        visualizer = GraphVisualizer(handler)
        
        # Test Cytoscape export
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            cyto_path = f.name
        
        try:
            result = visualizer.export_for_cytoscape(cyto_path)
            assert Path(result).exists()
        finally:
            Path(cyto_path).unlink(missing_ok=True)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])