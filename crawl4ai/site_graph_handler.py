"""
Site Graph Handler using NetworkX

This module provides graph-based analysis and visualization of website structures
using NetworkX for the Domain Intelligence Crawler. It handles site relationship
mapping, graph analysis, and export capabilities.

Integrates with existing Crawl4AI patterns:
- Uses existing async_database.py for persistence
- Follows existing logging patterns
- Integrates with site_graph_db.py for data storage
"""

import asyncio
import json
import networkx as nx
from typing import Dict, List, Optional, Tuple, Set, Any, Union
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path

# Optional imports for visualization
try:
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    plt = None
    mpatches = None

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    np = None

try:
    import plotly.graph_objects as go
    import plotly.express as px
    from plotly.subplots import make_subplots
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False
    go = None
    px = None

from .site_graph_db import SiteGraphDatabaseManager, URLNode, SiteGraphStats
from .async_logger import AsyncLogger


@dataclass
class GraphMetrics:
    """Metrics for site graph analysis"""
    total_nodes: int = 0
    total_edges: int = 0
    connected_components: int = 0
    average_degree: float = 0.0
    density: float = 0.0
    diameter: Optional[int] = None
    average_path_length: Optional[float] = None
    clustering_coefficient: float = 0.0
    page_rank_stats: Optional[Dict[str, float]] = None
    centrality_stats: Optional[Dict[str, Dict[str, float]]] = None


@dataclass
class GraphExportOptions:
    """Options for graph export"""
    format: str = "graphml"  # graphml, gexf, json, dot, pajek
    include_metadata: bool = True
    include_file_nodes: bool = True
    include_failed_nodes: bool = False
    max_nodes: Optional[int] = None
    filter_by_depth: Optional[int] = None


class SiteGraphHandler:
    """
    NetworkX-based site graph handler for analyzing website structures.
    
    Provides graph construction, analysis, visualization, and export capabilities
    for the Domain Intelligence Crawler.
    """
    
    def __init__(self, db_manager: Optional[SiteGraphDatabaseManager] = None, logger: Optional[AsyncLogger] = None):
        self.db_manager = db_manager or SiteGraphDatabaseManager()
        self.logger = logger or AsyncLogger(verbose=False, tag_width=10)
        self.graph: nx.DiGraph = nx.DiGraph()
        self._graph_cache: Dict[str, nx.DiGraph] = {}
        self._metrics_cache: Dict[str, GraphMetrics] = {}
    
    async def build_site_graph(self, base_url: str, refresh_cache: bool = False) -> nx.DiGraph:
        """
        Build a NetworkX directed graph from the site database.
        
        Args:
            base_url: Base URL to build graph for
            refresh_cache: Whether to refresh cached graph
            
        Returns:
            NetworkX DiGraph representing the site structure
        """
        if not refresh_cache and base_url in self._graph_cache:
            return self._graph_cache[base_url]
        
        try:
            self.logger.info(f"Building site graph for {base_url}", tag="GRAPH")
            
            # Get site data from database
            site_data = await self.db_manager.get_site_graph(base_url)
            
            # Create new directed graph
            graph = nx.DiGraph()
            
            # Add nodes and edges
            for url_node in site_data.get('urls', []):
                # Add node with attributes
                node_attrs = {
                    'url': url_node.url,
                    'status_code': url_node.status_code,
                    'content_type': url_node.content_type,
                    'is_file': url_node.is_file,
                    'file_extension': url_node.file_extension,
                    'file_size': url_node.file_size,
                    'discovered_at': url_node.discovered_at.isoformat() if url_node.discovered_at else None,
                    'last_checked': url_node.last_checked.isoformat() if url_node.last_checked else None,
                    'download_status': url_node.download_status,
                    'error_message': url_node.error_message,
                    'retry_count': url_node.retry_count,
                    'metadata': url_node.metadata or {}
                }
                
                graph.add_node(url_node.url, **node_attrs)
                
                # Add edge from source to this URL
                if url_node.source_url and url_node.source_url != url_node.url:
                    edge_attrs = {
                        'discovered_at': url_node.discovered_at.isoformat() if url_node.discovered_at else None,
                        'link_type': 'internal' if self._is_internal_link(url_node.url, base_url) else 'external'
                    }
                    graph.add_edge(url_node.source_url, url_node.url, **edge_attrs)
            
            # Add file nodes if they exist
            for file_node in site_data.get('files', []):
                if file_node.url not in graph:
                    file_attrs = {
                        'url': file_node.url,
                        'is_file': True,
                        'file_extension': file_node.file_extension,
                        'file_size': file_node.file_size,
                        'download_status': file_node.download_status,
                        'local_path': file_node.local_path,
                        'checksum': file_node.checksum,
                        'content_type': file_node.content_type
                    }
                    graph.add_node(file_node.url, **file_attrs)
                    
                    # Add edge from source to file
                    if file_node.source_url:
                        graph.add_edge(file_node.source_url, file_node.url, link_type='file')
            
            # Cache the graph
            self._graph_cache[base_url] = graph
            
            self.logger.success(
                f"Built site graph: {graph.number_of_nodes()} nodes, {graph.number_of_edges()} edges",
                tag="GRAPH"
            )
            
            return graph
            
        except Exception as e:
            self.logger.error(f"Failed to build site graph: {str(e)}", tag="ERROR")
            raise
    
    def _is_internal_link(self, url: str, base_url: str) -> bool:
        """Check if a URL is internal to the base domain."""
        from urllib.parse import urlparse
        
        try:
            base_domain = urlparse(base_url).netloc
            url_domain = urlparse(url).netloc
            return url_domain == base_domain or url_domain == ''
        except:
            return False
    
    async def analyze_graph_metrics(self, base_url: str, refresh_cache: bool = False) -> GraphMetrics:
        """
        Analyze graph metrics for a site.
        
        Args:
            base_url: Base URL to analyze
            refresh_cache: Whether to refresh cached metrics
            
        Returns:
            GraphMetrics object with analysis results
        """
        if not refresh_cache and base_url in self._metrics_cache:
            return self._metrics_cache[base_url]
        
        try:
            graph = await self.build_site_graph(base_url, refresh_cache)
            
            self.logger.info(f"Analyzing graph metrics for {base_url}", tag="ANALYZE")
            
            # Basic metrics
            total_nodes = graph.number_of_nodes()
            total_edges = graph.number_of_edges()
            
            if total_nodes == 0:
                return GraphMetrics()
            
            # Connected components (treat as undirected for this analysis)
            undirected_graph = graph.to_undirected()
            connected_components = nx.number_connected_components(undirected_graph)
            
            # Degree statistics
            degrees = [d for n, d in graph.degree()]
            average_degree = np.mean(degrees) if degrees else 0.0
            
            # Density
            density = nx.density(graph)
            
            # Path-based metrics (only for largest connected component)
            diameter = None
            average_path_length = None
            
            if connected_components > 0:
                largest_cc = max(nx.connected_components(undirected_graph), key=len)
                if len(largest_cc) > 1:
                    cc_subgraph = undirected_graph.subgraph(largest_cc)
                    try:
                        diameter = nx.diameter(cc_subgraph)
                        average_path_length = nx.average_shortest_path_length(cc_subgraph)
                    except nx.NetworkXError:
                        # Graph might not be connected
                        pass
            
            # Clustering coefficient
            clustering_coefficient = nx.average_clustering(undirected_graph)
            
            # PageRank analysis
            page_rank_stats = None
            try:
                pagerank = nx.pagerank(graph, max_iter=100)
                if pagerank:
                    pr_values = list(pagerank.values())
                    page_rank_stats = {
                        'max': max(pr_values),
                        'min': min(pr_values),
                        'mean': np.mean(pr_values),
                        'std': np.std(pr_values)
                    }
            except (nx.PowerIterationFailedConvergence, nx.NetworkXError):
                pass
            
            # Centrality analysis
            centrality_stats = None
            try:
                # Only calculate for reasonably sized graphs
                if total_nodes <= 1000:
                    betweenness = nx.betweenness_centrality(graph, k=min(100, total_nodes))
                    closeness = nx.closeness_centrality(graph)
                    
                    centrality_stats = {
                        'betweenness': {
                            'max': max(betweenness.values()) if betweenness else 0,
                            'mean': np.mean(list(betweenness.values())) if betweenness else 0
                        },
                        'closeness': {
                            'max': max(closeness.values()) if closeness else 0,
                            'mean': np.mean(list(closeness.values())) if closeness else 0
                        }
                    }
            except (nx.NetworkXError, MemoryError):
                pass
            
            metrics = GraphMetrics(
                total_nodes=total_nodes,
                total_edges=total_edges,
                connected_components=connected_components,
                average_degree=average_degree,
                density=density,
                diameter=diameter,
                average_path_length=average_path_length,
                clustering_coefficient=clustering_coefficient,
                page_rank_stats=page_rank_stats,
                centrality_stats=centrality_stats
            )
            
            # Cache the metrics
            self._metrics_cache[base_url] = metrics
            
            self.logger.success(f"Analyzed graph metrics: {total_nodes} nodes, {total_edges} edges", tag="ANALYZE")
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Failed to analyze graph metrics: {str(e)}", tag="ERROR")
            raise
    
    async def find_critical_paths(self, base_url: str, target_nodes: Optional[List[str]] = None) -> Dict[str, List[str]]:
        """
        Find critical paths in the site graph.
        
        Args:
            base_url: Base URL to analyze
            target_nodes: Specific target nodes to find paths to
            
        Returns:
            Dictionary of paths from root to critical nodes
        """
        try:
            graph = await self.build_site_graph(base_url)
            
            # Find root nodes (nodes with no incoming edges)
            root_nodes = [n for n in graph.nodes() if graph.in_degree(n) == 0]
            if not root_nodes:
                root_nodes = [base_url] if base_url in graph else []
            
            # Find leaf nodes (nodes with no outgoing edges) if no targets specified
            if not target_nodes:
                target_nodes = [n for n in graph.nodes() if graph.out_degree(n) == 0]
            
            critical_paths = {}
            
            for root in root_nodes:
                for target in target_nodes:
                    if root != target and nx.has_path(graph, root, target):
                        try:
                            path = nx.shortest_path(graph, root, target)
                            path_key = f"{root} -> {target}"
                            critical_paths[path_key] = path
                        except nx.NetworkXNoPath:
                            continue
            
            return critical_paths
            
        except Exception as e:
            self.logger.error(f"Failed to find critical paths: {str(e)}", tag="ERROR")
            return {}
    
    async def detect_graph_patterns(self, base_url: str) -> Dict[str, Any]:
        """
        Detect common patterns in the site graph.
        
        Args:
            base_url: Base URL to analyze
            
        Returns:
            Dictionary of detected patterns
        """
        try:
            graph = await self.build_site_graph(base_url)
            
            patterns = {
                'hub_nodes': [],
                'authority_nodes': [],
                'isolated_nodes': [],
                'cycles': [],
                'bridges': [],
                'articulation_points': []
            }
            
            # Hub nodes (high out-degree)
            out_degrees = dict(graph.out_degree())
            if out_degrees:
                avg_out_degree = np.mean(list(out_degrees.values()))
                patterns['hub_nodes'] = [
                    node for node, degree in out_degrees.items() 
                    if degree > avg_out_degree * 2
                ]
            
            # Authority nodes (high in-degree)
            in_degrees = dict(graph.in_degree())
            if in_degrees:
                avg_in_degree = np.mean(list(in_degrees.values()))
                patterns['authority_nodes'] = [
                    node for node, degree in in_degrees.items() 
                    if degree > avg_in_degree * 2
                ]
            
            # Isolated nodes
            patterns['isolated_nodes'] = list(nx.isolates(graph))
            
            # Cycles (strongly connected components with more than one node)
            try:
                sccs = list(nx.strongly_connected_components(graph))
                patterns['cycles'] = [list(scc) for scc in sccs if len(scc) > 1]
            except:
                pass
            
            # Bridges and articulation points (treat as undirected)
            undirected_graph = graph.to_undirected()
            try:
                patterns['bridges'] = list(nx.bridges(undirected_graph))
                patterns['articulation_points'] = list(nx.articulation_points(undirected_graph))
            except:
                pass
            
            return patterns
            
        except Exception as e:
            self.logger.error(f"Failed to detect graph patterns: {str(e)}", tag="ERROR")
            return {}
    
    async def export_graph(self, base_url: str, output_path: str, options: Optional[GraphExportOptions] = None) -> str:
        """
        Export site graph to various formats.
        
        Args:
            base_url: Base URL to export
            output_path: Output file path
            options: Export options
            
        Returns:
            Path to exported file
        """
        options = options or GraphExportOptions()
        
        try:
            graph = await self.build_site_graph(base_url)
            
            # Apply filters
            filtered_graph = self._apply_export_filters(graph, options)
            
            # Ensure output directory exists
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            
            # Export based on format
            if options.format.lower() == 'graphml':
                nx.write_graphml(filtered_graph, output_path)
            elif options.format.lower() == 'gexf':
                nx.write_gexf(filtered_graph, output_path)
            elif options.format.lower() == 'json':
                data = nx.node_link_data(filtered_graph)
                with open(output_path, 'w') as f:
                    json.dump(data, f, indent=2, default=str)
            elif options.format.lower() == 'dot':
                nx.drawing.nx_pydot.write_dot(filtered_graph, output_path)
            elif options.format.lower() == 'pajek':
                nx.write_pajek(filtered_graph, output_path)
            else:
                raise ValueError(f"Unsupported export format: {options.format}")
            
            self.logger.success(f"Exported graph to {output_path}", tag="EXPORT")
            return output_path
            
        except Exception as e:
            self.logger.error(f"Failed to export graph: {str(e)}", tag="ERROR")
            raise
    
    def _apply_export_filters(self, graph: nx.DiGraph, options: GraphExportOptions) -> nx.DiGraph:
        """Apply filters to graph before export."""
        filtered_graph = graph.copy()
        
        # Filter by file nodes
        if not options.include_file_nodes:
            file_nodes = [n for n, d in filtered_graph.nodes(data=True) if d.get('is_file', False)]
            filtered_graph.remove_nodes_from(file_nodes)
        
        # Filter by failed nodes
        if not options.include_failed_nodes:
            failed_nodes = [
                n for n, d in filtered_graph.nodes(data=True) 
                if d.get('status_code', 200) >= 400 or d.get('error_message')
            ]
            filtered_graph.remove_nodes_from(failed_nodes)
        
        # Filter by depth
        if options.filter_by_depth is not None:
            # This would require depth calculation from root nodes
            pass
        
        # Limit number of nodes
        if options.max_nodes and filtered_graph.number_of_nodes() > options.max_nodes:
            # Keep nodes with highest PageRank
            try:
                pagerank = nx.pagerank(filtered_graph)
                top_nodes = sorted(pagerank.items(), key=lambda x: x[1], reverse=True)[:options.max_nodes]
                nodes_to_keep = [node for node, _ in top_nodes]
                filtered_graph = filtered_graph.subgraph(nodes_to_keep).copy()
            except:
                # Fallback: keep random subset
                import random
                nodes_to_keep = random.sample(list(filtered_graph.nodes()), options.max_nodes)
                filtered_graph = filtered_graph.subgraph(nodes_to_keep).copy()
        
        return filtered_graph
    
    async def visualize_graph(self, base_url: str, output_path: str, layout: str = 'spring', 
                            figsize: Tuple[int, int] = (12, 8), node_size_attr: str = 'degree') -> str:
        """
        Create a visualization of the site graph.
        
        Args:
            base_url: Base URL to visualize
            output_path: Output image path
            layout: Layout algorithm ('spring', 'circular', 'random', 'shell')
            figsize: Figure size tuple
            node_size_attr: Attribute to use for node sizing
            
        Returns:
            Path to visualization file
        """
        try:
            graph = await self.build_site_graph(base_url)
            
            # Limit graph size for visualization
            if graph.number_of_nodes() > 100:
                # Use PageRank to select most important nodes
                pagerank = nx.pagerank(graph)
                top_nodes = sorted(pagerank.items(), key=lambda x: x[1], reverse=True)[:100]
                nodes_to_keep = [node for node, _ in top_nodes]
                graph = graph.subgraph(nodes_to_keep).copy()
            
            # Set up the plot
            plt.figure(figsize=figsize)
            
            # Choose layout
            if layout == 'spring':
                pos = nx.spring_layout(graph, k=1, iterations=50)
            elif layout == 'circular':
                pos = nx.circular_layout(graph)
            elif layout == 'random':
                pos = nx.random_layout(graph)
            elif layout == 'shell':
                pos = nx.shell_layout(graph)
            else:
                pos = nx.spring_layout(graph)
            
            # Node sizes based on attribute
            if node_size_attr == 'degree':
                node_sizes = [graph.degree(node) * 100 + 50 for node in graph.nodes()]
            elif node_size_attr == 'in_degree':
                node_sizes = [graph.in_degree(node) * 100 + 50 for node in graph.nodes()]
            elif node_size_attr == 'out_degree':
                node_sizes = [graph.out_degree(node) * 100 + 50 for node in graph.nodes()]
            else:
                node_sizes = [100] * graph.number_of_nodes()
            
            # Node colors based on type
            node_colors = []
            for node in graph.nodes():
                node_data = graph.nodes[node]
                if node_data.get('is_file', False):
                    node_colors.append('lightcoral')
                elif node_data.get('status_code', 200) >= 400:
                    node_colors.append('red')
                elif node == base_url:
                    node_colors.append('lightgreen')
                else:
                    node_colors.append('lightblue')
            
            # Draw the graph
            nx.draw(graph, pos, 
                   node_color=node_colors,
                   node_size=node_sizes,
                   with_labels=False,
                   arrows=True,
                   edge_color='gray',
                   alpha=0.7)
            
            # Add title
            plt.title(f"Site Graph: {base_url}\n{graph.number_of_nodes()} nodes, {graph.number_of_edges()} edges")
            
            # Save the plot
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            self.logger.success(f"Created graph visualization: {output_path}", tag="VIZ")
            return output_path
            
        except Exception as e:
            self.logger.error(f"Failed to create visualization: {str(e)}", tag="ERROR")
            raise
    
    def clear_cache(self, base_url: Optional[str] = None):
        """Clear cached graphs and metrics."""
        if base_url:
            self._graph_cache.pop(base_url, None)
            self._metrics_cache.pop(base_url, None)
        else:
            self._graph_cache.clear()
            self._metrics_cache.clear()
        
        self.logger.info("Cleared graph cache", tag="CACHE")


# Convenience functions
async def create_site_graph_handler(db_manager: Optional[SiteGraphDatabaseManager] = None) -> SiteGraphHandler:
    """Create a SiteGraphHandler with default configuration."""
    return SiteGraphHandler(db_manager=db_manager)


async def analyze_site_structure(base_url: str, export_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Convenience function to analyze site structure and optionally export results.
    
    Args:
        base_url: Base URL to analyze
        export_path: Optional path to export graph
        
    Returns:
        Dictionary with analysis results
    """
    handler = await create_site_graph_handler()
    
    # Build graph and analyze
    graph = await handler.build_site_graph(base_url)
    metrics = await handler.analyze_graph_metrics(base_url)
    patterns = await handler.detect_graph_patterns(base_url)
    critical_paths = await handler.find_critical_paths(base_url)
    
    results = {
        'metrics': asdict(metrics),
        'patterns': patterns,
        'critical_paths': critical_paths,
        'graph_summary': {
            'nodes': graph.number_of_nodes(),
            'edges': graph.number_of_edges(),
            'is_connected': nx.is_weakly_connected(graph)
        }
    }
    
    # Export if requested
    if export_path:
        await handler.export_graph(base_url, export_path)
        results['exported_to'] = export_path
    
    return results