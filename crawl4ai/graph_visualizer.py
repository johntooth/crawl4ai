#!/usr/bin/env python3
"""
Graph Visualization Utilities

Advanced visualization tools for site graphs using multiple rendering engines
and interactive features for the Domain Intelligence Crawler.
"""

import networkx as nx
from typing import Dict, List, Optional, Tuple, Any, Union
from pathlib import Path
import json
import logging
from datetime import datetime
from urllib.parse import urlparse

# Optional visualization imports
try:
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    from matplotlib.colors import LinearSegmentedColormap
    import numpy as np
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

try:
    import plotly.graph_objects as go
    import plotly.express as px
    from plotly.subplots import make_subplots
    import plotly.offline as pyo
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

try:
    import pygraphviz as pgv
    GRAPHVIZ_AVAILABLE = True
except ImportError:
    GRAPHVIZ_AVAILABLE = False

logger = logging.getLogger(__name__)


class GraphVisualizer:
    """Advanced graph visualization with multiple rendering engines."""
    
    def __init__(self, graph_handler):
        """Initialize with a SiteGraphHandler instance."""
        self.graph_handler = graph_handler
        self.graph = graph_handler.graph
        self.nodes = graph_handler.nodes
        
    def create_hierarchical_layout(self, root_url: Optional[str] = None) -> Dict[str, Tuple[float, float]]:
        """Create a hierarchical layout based on crawl depth."""
        if not root_url:
            # Find the node with minimum depth as root
            root_candidates = [url for url, node in self.nodes.items() if node.depth == 0]
            if root_candidates:
                root_url = root_candidates[0]
            else:
                # Fallback to any node
                root_url = list(self.graph.nodes())[0] if self.graph.nodes() else None
        
        if not root_url or root_url not in self.graph:
            return nx.spring_layout(self.graph)
        
        # Group nodes by depth
        depth_groups = {}
        for url, node in self.nodes.items():
            depth = node.depth
            if depth not in depth_groups:
                depth_groups[depth] = []
            depth_groups[depth].append(url)
        
        # Create positions
        pos = {}
        max_depth = max(depth_groups.keys()) if depth_groups else 0
        
        for depth, urls in depth_groups.items():
            y = max_depth - depth  # Higher depth = lower y position
            num_nodes = len(urls)
            
            if num_nodes == 1:
                pos[urls[0]] = (0, y)
            else:
                x_positions = np.linspace(-num_nodes/2, num_nodes/2, num_nodes) if MATPLOTLIB_AVAILABLE else [i - num_nodes/2 for i in range(num_nodes)]
                for i, url in enumerate(urls):
                    pos[url] = (x_positions[i], y)
        
        return pos
    
    def create_domain_clustered_layout(self) -> Dict[str, Tuple[float, float]]:
        """Create layout with nodes clustered by domain."""
        # Group nodes by domain
        domain_groups = {}
        for url in self.graph.nodes():
            parsed = urlparse(url)
            domain = parsed.netloc
            if domain not in domain_groups:
                domain_groups[domain] = []
            domain_groups[domain].append(url)
        
        # Create subgraphs for each domain
        pos = {}
        domain_centers = {}
        
        # Calculate domain centers in a circle
        num_domains = len(domain_groups)
        if num_domains == 1:
            domain_centers[list(domain_groups.keys())[0]] = (0, 0)
        else:
            if MATPLOTLIB_AVAILABLE:
                angles = np.linspace(0, 2*np.pi, num_domains, endpoint=False)
                radius = max(3, num_domains)
                
                for i, domain in enumerate(domain_groups.keys()):
                    x = radius * np.cos(angles[i])
                    y = radius * np.sin(angles[i])
                    domain_centers[domain] = (x, y)
            else:
                # Fallback without numpy
                import math
                for i, domain in enumerate(domain_groups.keys()):
                    angle = 2 * math.pi * i / num_domains
                    radius = max(3, num_domains)
                    x = radius * math.cos(angle)
                    y = radius * math.sin(angle)
                    domain_centers[domain] = (x, y)
        
        # Position nodes within each domain cluster
        for domain, urls in domain_groups.items():
            center_x, center_y = domain_centers[domain]
            
            if len(urls) == 1:
                pos[urls[0]] = (center_x, center_y)
            else:
                # Create subgraph layout
                subgraph = self.graph.subgraph(urls)
                sub_pos = nx.spring_layout(subgraph, k=0.5, iterations=50)
                
                # Offset by domain center
                for url, (x, y) in sub_pos.items():
                    pos[url] = (center_x + x, center_y + y)
        
        return pos
    
    def create_force_directed_layout(self, iterations: int = 100, k: Optional[float] = None) -> Dict[str, Tuple[float, float]]:
        """Create an optimized force-directed layout."""
        return nx.spring_layout(self.graph, k=k, iterations=iterations, seed=42)
    
    def visualize_with_matplotlib(self, 
                                 output_path: Optional[str] = None,
                                 layout_type: str = "spring",
                                 color_scheme: str = "depth",
                                 size_scheme: str = "pagerank",
                                 show_labels: bool = True,
                                 highlight_files: bool = True,
                                 figsize: Tuple[int, int] = (15, 10),
                                 dpi: int = 300) -> Optional[str]:
        """Create advanced matplotlib visualization."""
        if not MATPLOTLIB_AVAILABLE:
            logger.error("Matplotlib not available")
            return None
        
        if self.graph.number_of_nodes() == 0:
            logger.warning("Cannot visualize empty graph")
            return None
        
        # Choose layout
        if layout_type == "hierarchical":
            pos = self.create_hierarchical_layout()
        elif layout_type == "domain_clustered":
            pos = self.create_domain_clustered_layout()
        elif layout_type == "force_directed":
            pos = self.create_force_directed_layout()
        else:  # spring (default)
            pos = nx.spring_layout(self.graph, k=1, iterations=50)
        
        # Create figure with subplots
        fig, (ax_main, ax_legend) = plt.subplots(1, 2, figsize=figsize, 
                                                gridspec_kw={'width_ratios': [4, 1]})
        
        # Calculate node attributes
        centrality = self.graph_handler.calculate_centrality_measures()
        
        # Node sizes
        if size_scheme == "pagerank":
            pagerank = centrality.get('pagerank', {})
            node_sizes = [max(100, pagerank.get(node, 0.001) * 3000) for node in self.graph.nodes()]
        elif size_scheme == "degree":
            degrees = dict(self.graph.degree())
            max_degree = max(degrees.values()) if degrees else 1
            node_sizes = [max(100, (degrees.get(node, 1) / max_degree) * 1000) for node in self.graph.nodes()]
        elif size_scheme == "betweenness":
            betweenness = centrality.get('betweenness', {})
            node_sizes = [max(100, betweenness.get(node, 0.001) * 2000) for node in self.graph.nodes()]
        else:
            node_sizes = [300] * self.graph.number_of_nodes()
        
        # Node colors
        if color_scheme == "depth":
            node_colors = [self.nodes.get(node, type('obj', (object,), {'depth': 0})()).depth 
                          for node in self.graph.nodes()]
            colormap = plt.cm.viridis
            color_label = "Crawl Depth"
        elif color_scheme == "pagerank":
            pagerank = centrality.get('pagerank', {})
            node_colors = [pagerank.get(node, 0) for node in self.graph.nodes()]
            colormap = plt.cm.plasma
            color_label = "PageRank Score"
        elif color_scheme == "file_type":
            node_colors = []
            color_map = {'page': 0, 'pdf': 1, 'doc': 2, 'xls': 3, 'other': 4}
            for node in self.graph.nodes():
                node_data = self.nodes.get(node)
                if not node_data or not node_data.is_file:
                    node_colors.append(color_map['page'])
                elif node_data.file_extension in ['.pdf']:
                    node_colors.append(color_map['pdf'])
                elif node_data.file_extension in ['.doc', '.docx']:
                    node_colors.append(color_map['doc'])
                elif node_data.file_extension in ['.xls', '.xlsx']:
                    node_colors.append(color_map['xls'])
                else:
                    node_colors.append(color_map['other'])
            colormap = plt.cm.Set1
            color_label = "Node Type"
        else:
            node_colors = 'lightblue'
            colormap = None
            color_label = None
        
        # Draw nodes
        nodes = nx.draw_networkx_nodes(self.graph, pos, 
                                      node_size=node_sizes,
                                      node_color=node_colors,
                                      cmap=colormap,
                                      alpha=0.8,
                                      ax=ax_main)
        
        # Draw edges with different styles
        regular_edges = []
        file_edges = []
        
        for edge in self.graph.edges():
            target_node = self.nodes.get(edge[1])
            if target_node and target_node.is_file:
                file_edges.append(edge)
            else:
                regular_edges.append(edge)
        
        # Draw regular edges
        if regular_edges:
            nx.draw_networkx_edges(self.graph, pos,
                                  edgelist=regular_edges,
                                  edge_color='gray',
                                  alpha=0.6,
                                  arrows=True,
                                  arrowsize=15,
                                  ax=ax_main)
        
        # Draw file edges with different style
        if file_edges and highlight_files:
            nx.draw_networkx_edges(self.graph, pos,
                                  edgelist=file_edges,
                                  edge_color='red',
                                  alpha=0.8,
                                  arrows=True,
                                  arrowsize=15,
                                  style='dashed',
                                  ax=ax_main)
        
        # Add labels for small graphs
        if show_labels and self.graph.number_of_nodes() <= 30:
            labels = {}
            for node in self.graph.nodes():
                parsed = urlparse(node)
                if parsed.path:
                    label = parsed.path.split('/')[-1][:10]
                else:
                    label = parsed.netloc[:10]
                labels[node] = label
            
            nx.draw_networkx_labels(self.graph, pos, labels, 
                                   font_size=8, font_weight='bold', ax=ax_main)
        
        # Main plot formatting
        ax_main.set_title(f"Site Graph Analysis\n{self.graph.number_of_nodes()} nodes, {self.graph.number_of_edges()} edges", 
                         fontsize=16, fontweight='bold')
        ax_main.axis('off')
        
        # Add colorbar if applicable
        if colormap and color_label:
            sm = plt.cm.ScalarMappable(cmap=colormap, 
                                     norm=plt.Normalize(vmin=min(node_colors), vmax=max(node_colors)))
            sm.set_array([])
            cbar = plt.colorbar(sm, ax=ax_main, shrink=0.8)
            cbar.set_label(color_label, fontsize=12)
        
        # Create legend
        ax_legend.axis('off')
        legend_elements = []
        
        if highlight_files:
            legend_elements.extend([
                mpatches.Patch(color='lightblue', label='Web Pages'),
                mpatches.Patch(color='red', label='Files'),
                plt.Line2D([0], [0], color='gray', label='Page Links'),
                plt.Line2D([0], [0], color='red', linestyle='--', label='File Links')
            ])
        
        if size_scheme != "constant":
            legend_elements.append(mpatches.Patch(color='white', label=f'Size: {size_scheme.title()}'))
        
        if legend_elements:
            ax_legend.legend(handles=legend_elements, loc='center', fontsize=10)
        
        # Add statistics text
        analysis = self.graph_handler.analyze_graph()
        stats_text = f"""Graph Statistics:
        
Nodes: {analysis.total_nodes}
Edges: {analysis.total_edges}
Density: {analysis.density:.3f}
Components: {analysis.connected_components}
Dead Ends: {len(analysis.dead_ends)}
Entry Points: {len(analysis.entry_points)}
File Nodes: {len(analysis.file_nodes)}
        
Top PageRank:
        """
        
        for i, (url, score) in enumerate(analysis.page_rank_top_10[:3]):
            parsed = urlparse(url)
            short_url = parsed.path.split('/')[-1] if parsed.path else parsed.netloc
            stats_text += f"{i+1}. {short_url[:20]}... ({score:.3f})\n"
        
        ax_legend.text(0.05, 0.3, stats_text, fontsize=9, verticalalignment='top',
                      bbox=dict(boxstyle='round', facecolor='lightgray', alpha=0.8))
        
        plt.tight_layout()
        
        if output_path:
            plt.savefig(output_path, dpi=dpi, bbox_inches='tight', facecolor='white')
            plt.close()
            return output_path
        else:
            plt.show()
            return None
    
    def create_interactive_dashboard(self, output_path: Optional[str] = None) -> Optional[str]:
        """Create comprehensive interactive dashboard with multiple views."""
        if not PLOTLY_AVAILABLE:
            logger.error("Plotly not available")
            return None
        
        if self.graph.number_of_nodes() == 0:
            logger.warning("Cannot create dashboard for empty graph")
            return None
        
        # Calculate layouts and metrics
        pos = self.create_force_directed_layout()
        analysis = self.graph_handler.analyze_graph()
        centrality = self.graph_handler.calculate_centrality_measures()
        
        # Create subplots
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Site Graph Network', 'PageRank Distribution', 
                          'Degree Distribution', 'Node Type Analysis'),
            specs=[[{"type": "scatter"}, {"type": "bar"}],
                   [{"type": "histogram"}, {"type": "pie"}]]
        )
        
        # 1. Main network graph
        edge_x, edge_y = [], []
        for edge in self.graph.edges():
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])
        
        fig.add_trace(
            go.Scatter(x=edge_x, y=edge_y, mode='lines', 
                      line=dict(width=0.5, color='#888'),
                      hoverinfo='none', showlegend=False),
            row=1, col=1
        )
        
        # Node data
        node_x = [pos[node][0] for node in self.graph.nodes()]
        node_y = [pos[node][1] for node in self.graph.nodes()]
        node_colors = []
        node_sizes = []
        node_text = []
        
        pagerank = centrality.get('pagerank', {})
        
        for node in self.graph.nodes():
            node_data = self.nodes.get(node)
            
            # Color by type
            if node_data and node_data.is_file:
                node_colors.append('red')
            else:
                node_colors.append('blue')
            
            # Size by PageRank
            size = max(5, pagerank.get(node, 0.001) * 500)
            node_sizes.append(size)
            
            # Hover text
            parsed = urlparse(node)
            display_name = parsed.path.split('/')[-1] if parsed.path else parsed.netloc
            node_text.append(f"{display_name}<br>PageRank: {pagerank.get(node, 0):.4f}")
        
        fig.add_trace(
            go.Scatter(x=node_x, y=node_y, mode='markers',
                      marker=dict(size=node_sizes, color=node_colors, 
                                 line=dict(width=1, color='white')),
                      text=node_text, hoverinfo='text',
                      showlegend=False),
            row=1, col=1
        )
        
        # 2. PageRank distribution
        top_pagerank = analysis.page_rank_top_10[:10]
        pr_urls = [urlparse(url).path.split('/')[-1] if urlparse(url).path else urlparse(url).netloc 
                  for url, _ in top_pagerank]
        pr_scores = [score for _, score in top_pagerank]
        
        fig.add_trace(
            go.Bar(x=pr_urls, y=pr_scores, name='PageRank',
                  marker_color='lightblue'),
            row=1, col=2
        )
        
        # 3. Degree distribution
        degrees = [d for n, d in self.graph.degree()]
        fig.add_trace(
            go.Histogram(x=degrees, nbinsx=20, name='Degree Distribution',
                        marker_color='lightgreen'),
            row=2, col=1
        )
        
        # 4. Node type pie chart
        file_count = len(analysis.file_nodes)
        page_count = analysis.total_nodes - file_count
        
        fig.add_trace(
            go.Pie(labels=['Pages', 'Files'], values=[page_count, file_count],
                  marker_colors=['blue', 'red']),
            row=2, col=2
        )
        
        # Update layout
        fig.update_layout(
            title_text=f"Site Graph Dashboard - {analysis.total_nodes} Nodes, {analysis.total_edges} Edges",
            title_x=0.5,
            height=800,
            showlegend=False
        )
        
        # Update subplot axes
        fig.update_xaxes(showgrid=False, zeroline=False, showticklabels=False, row=1, col=1)
        fig.update_yaxes(showgrid=False, zeroline=False, showticklabels=False, row=1, col=1)
        
        if output_path:
            fig.write_html(output_path)
            return output_path
        else:
            fig.show()
            return None
    
    def export_for_cytoscape(self, output_path: str) -> str:
        """Export graph in Cytoscape.js format."""
        elements = []
        
        # Add nodes
        centrality = self.graph_handler.calculate_centrality_measures()
        pagerank = centrality.get('pagerank', {})
        
        for node in self.graph.nodes():
            node_data = self.nodes.get(node)
            
            element = {
                'data': {
                    'id': node,
                    'label': urlparse(node).path.split('/')[-1] if urlparse(node).path else urlparse(node).netloc,
                    'pagerank': pagerank.get(node, 0),
                    'degree': self.graph.degree(node),
                    'is_file': node_data.is_file if node_data else False,
                    'depth': node_data.depth if node_data else 0
                }
            }
            elements.append(element)
        
        # Add edges
        for edge in self.graph.edges():
            element = {
                'data': {
                    'id': f"{edge[0]}-{edge[1]}",
                    'source': edge[0],
                    'target': edge[1]
                }
            }
            elements.append(element)
        
        # Create Cytoscape format
        cytoscape_data = {
            'elements': elements,
            'style': [
                {
                    'selector': 'node',
                    'style': {
                        'background-color': 'data(is_file) ? "red" : "blue"',
                        'label': 'data(label)',
                        'width': 'mapData(pagerank, 0, 1, 20, 80)',
                        'height': 'mapData(pagerank, 0, 1, 20, 80)'
                    }
                },
                {
                    'selector': 'edge',
                    'style': {
                        'width': 2,
                        'line-color': '#ccc',
                        'target-arrow-color': '#ccc',
                        'target-arrow-shape': 'triangle'
                    }
                }
            ],
            'layout': {
                'name': 'cose',
                'idealEdgeLength': 100,
                'nodeOverlap': 20
            }
        }
        
        with open(output_path, 'w') as f:
            json.dump(cytoscape_data, f, indent=2)
        
        return output_path


# Utility functions for common visualization tasks
def quick_visualize(graph_handler, output_dir: str = "visualizations") -> Dict[str, str]:
    """Create a quick set of standard visualizations."""
    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True)
    
    visualizer = GraphVisualizer(graph_handler)
    results = {}
    
    # Static matplotlib visualization
    if MATPLOTLIB_AVAILABLE:
        static_path = output_dir / "site_graph_static.png"
        result = visualizer.visualize_with_matplotlib(
            output_path=str(static_path),
            layout_type="spring",
            color_scheme="depth",
            size_scheme="pagerank"
        )
        if result:
            results['static'] = result
    
    # Interactive dashboard
    if PLOTLY_AVAILABLE:
        dashboard_path = output_dir / "site_graph_dashboard.html"
        result = visualizer.create_interactive_dashboard(str(dashboard_path))
        if result:
            results['dashboard'] = result
    
    # Cytoscape export
    cytoscape_path = output_dir / "site_graph_cytoscape.json"
    result = visualizer.export_for_cytoscape(str(cytoscape_path))
    if result:
        results['cytoscape'] = result
    
    return results


def analyze_graph_patterns(graph_handler) -> Dict[str, Any]:
    """Analyze common graph patterns and structures."""
    analysis = graph_handler.analyze_graph()
    centrality = graph_handler.calculate_centrality_measures()
    
    patterns = {
        'hub_and_spoke': {
            'detected': False,
            'hub_nodes': [],
            'confidence': 0.0
        },
        'hierarchical': {
            'detected': False,
            'levels': 0,
            'confidence': 0.0
        },
        'small_world': {
            'detected': False,
            'clustering_coefficient': analysis.clustering_coefficient,
            'average_path_length': 0.0,
            'confidence': 0.0
        },
        'scale_free': {
            'detected': False,
            'power_law_exponent': 0.0,
            'confidence': 0.0
        }
    }
    
    # Hub and spoke detection
    if centrality.get('degree'):
        degrees = list(centrality['degree'].values())
        max_degree = max(degrees) if degrees else 0
        avg_degree = sum(degrees) / len(degrees) if degrees else 0
        
        if max_degree > 3 * avg_degree and max_degree > 10:
            patterns['hub_and_spoke']['detected'] = True
            patterns['hub_and_spoke']['confidence'] = min(1.0, max_degree / (5 * avg_degree))
            
            # Find hub nodes (top 10% by degree)
            degree_threshold = sorted(degrees, reverse=True)[max(0, len(degrees) // 10)]
            patterns['hub_and_spoke']['hub_nodes'] = [
                node for node, degree in centrality['degree'].items() 
                if degree >= degree_threshold
            ][:5]  # Top 5 hubs
    
    # Hierarchical structure detection
    depth_groups = {}
    for node_data in graph_handler.nodes.values():
        depth = node_data.depth
        if depth not in depth_groups:
            depth_groups[depth] = 0
        depth_groups[depth] += 1
    
    if len(depth_groups) > 2:
        patterns['hierarchical']['detected'] = True
        patterns['hierarchical']['levels'] = len(depth_groups)
        
        # Confidence based on depth distribution uniformity
        counts = list(depth_groups.values())
        if len(counts) > 1:
            variance = sum((x - sum(counts)/len(counts))**2 for x in counts) / len(counts)
            patterns['hierarchical']['confidence'] = max(0.0, 1.0 - variance / (sum(counts)/len(counts))**2)
    
    return patterns