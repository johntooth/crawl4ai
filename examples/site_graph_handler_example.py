#!/usr/bin/env python3
"""
Site Graph Handler Example

This example demonstrates how to use the NetworkX-based site graph handler
for analyzing website structures, detecting patterns, and creating visualizations.
"""

import asyncio
import sys
from pathlib import Path

# Add the parent directory to the path to import crawl4ai
sys.path.insert(0, str(Path(__file__).parent.parent))

from crawl4ai.site_graph_handler import (
    SiteGraphHandler, 
    GraphExportOptions, 
    analyze_site_structure,
    create_site_graph_handler
)
from crawl4ai.site_graph_db import SiteGraphDatabaseManager


async def basic_graph_analysis_example():
    """Basic example of site graph analysis."""
    print("🕸️ Basic Site Graph Analysis Example")
    print("=" * 50)
    
    # Create graph handler
    handler = await create_site_graph_handler()
    
    # Example base URL (replace with actual crawled site)
    base_url = "https://example.com"
    
    try:
        # Build the graph from database
        print(f"📊 Building graph for {base_url}...")
        graph = await handler.build_site_graph(base_url)
        
        print(f"   Nodes: {graph.number_of_nodes()}")
        print(f"   Edges: {graph.number_of_edges()}")
        
        # Analyze metrics
        print("\n📈 Analyzing graph metrics...")
        metrics = await handler.analyze_graph_metrics(base_url)
        
        print(f"   Connected Components: {metrics.connected_components}")
        print(f"   Average Degree: {metrics.average_degree:.2f}")
        print(f"   Density: {metrics.density:.4f}")
        print(f"   Clustering Coefficient: {metrics.clustering_coefficient:.4f}")
        
        if metrics.diameter:
            print(f"   Diameter: {metrics.diameter}")
        if metrics.average_path_length:
            print(f"   Average Path Length: {metrics.average_path_length:.2f}")
        
        # PageRank statistics
        if metrics.page_rank_stats:
            print(f"   PageRank - Max: {metrics.page_rank_stats['max']:.4f}")
            print(f"   PageRank - Mean: {metrics.page_rank_stats['mean']:.4f}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in basic analysis: {e}")
        return False


async def pattern_detection_example():
    """Example of detecting patterns in site graphs."""
    print("\n🔍 Pattern Detection Example")
    print("=" * 50)
    
    handler = await create_site_graph_handler()
    base_url = "https://example.com"
    
    try:
        # Detect patterns
        print(f"🔎 Detecting patterns in {base_url}...")
        patterns = await handler.detect_graph_patterns(base_url)
        
        # Hub nodes (high out-degree)
        if patterns['hub_nodes']:
            print(f"   🌟 Hub Nodes ({len(patterns['hub_nodes'])}):")
            for node in patterns['hub_nodes'][:5]:  # Show first 5
                print(f"      - {node}")
        
        # Authority nodes (high in-degree)
        if patterns['authority_nodes']:
            print(f"   🎯 Authority Nodes ({len(patterns['authority_nodes'])}):")
            for node in patterns['authority_nodes'][:5]:
                print(f"      - {node}")
        
        # Isolated nodes
        if patterns['isolated_nodes']:
            print(f"   🏝️ Isolated Nodes: {len(patterns['isolated_nodes'])}")
        
        # Cycles
        if patterns['cycles']:
            print(f"   🔄 Cycles Found: {len(patterns['cycles'])}")
            for i, cycle in enumerate(patterns['cycles'][:3]):
                print(f"      Cycle {i+1}: {len(cycle)} nodes")
        
        # Bridges and articulation points
        if patterns['bridges']:
            print(f"   🌉 Bridges: {len(patterns['bridges'])}")
        
        if patterns['articulation_points']:
            print(f"   🔗 Articulation Points: {len(patterns['articulation_points'])}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in pattern detection: {e}")
        return False


async def critical_paths_example():
    """Example of finding critical paths in site graphs."""
    print("\n🛤️ Critical Paths Example")
    print("=" * 50)
    
    handler = await create_site_graph_handler()
    base_url = "https://example.com"
    
    try:
        # Find critical paths
        print(f"🗺️ Finding critical paths in {base_url}...")
        critical_paths = await handler.find_critical_paths(base_url)
        
        if critical_paths:
            print(f"   Found {len(critical_paths)} critical paths:")
            
            for path_name, path in list(critical_paths.items())[:5]:  # Show first 5
                print(f"   📍 {path_name}:")
                print(f"      Length: {len(path)} steps")
                if len(path) <= 5:  # Show full path for short paths
                    for i, node in enumerate(path):
                        print(f"         {i+1}. {node}")
                else:  # Show abbreviated path for long paths
                    print(f"         1. {path[0]}")
                    print(f"         ... ({len(path)-2} intermediate steps)")
                    print(f"         {len(path)}. {path[-1]}")
        else:
            print("   No critical paths found")
        
        return True
        
    except Exception as e:
        print(f"❌ Error finding critical paths: {e}")
        return False


async def graph_export_example():
    """Example of exporting graphs in different formats."""
    print("\n💾 Graph Export Example")
    print("=" * 50)
    
    handler = await create_site_graph_handler()
    base_url = "https://example.com"
    
    try:
        # Export in different formats
        export_formats = [
            ("graphml", "graph_export.graphml"),
            ("json", "graph_export.json"),
            ("gexf", "graph_export.gexf")
        ]
        
        for format_name, filename in export_formats:
            print(f"📤 Exporting to {format_name.upper()}...")
            
            options = GraphExportOptions(
                format=format_name,
                include_metadata=True,
                include_file_nodes=True,
                include_failed_nodes=False,
                max_nodes=500  # Limit for performance
            )
            
            output_path = f"./exports/{filename}"
            exported_path = await handler.export_graph(base_url, output_path, options)
            print(f"   ✅ Exported to: {exported_path}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in graph export: {e}")
        return False


async def graph_visualization_example():
    """Example of creating graph visualizations."""
    print("\n🎨 Graph Visualization Example")
    print("=" * 50)
    
    handler = await create_site_graph_handler()
    base_url = "https://example.com"
    
    try:
        # Create visualizations with different layouts
        layouts = [
            ("spring", "Spring Layout"),
            ("circular", "Circular Layout"),
            ("random", "Random Layout")
        ]
        
        for layout, description in layouts:
            print(f"🖼️ Creating {description}...")
            
            output_path = f"./visualizations/graph_{layout}.png"
            viz_path = await handler.visualize_graph(
                base_url=base_url,
                output_path=output_path,
                layout=layout,
                figsize=(12, 8),
                node_size_attr='degree'
            )
            print(f"   ✅ Visualization saved: {viz_path}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in visualization: {e}")
        # This might fail if matplotlib is not available
        print("   Note: Visualization requires matplotlib to be installed")
        return False


async def comprehensive_analysis_example():
    """Example using the convenience function for comprehensive analysis."""
    print("\n🔬 Comprehensive Analysis Example")
    print("=" * 50)
    
    base_url = "https://example.com"
    
    try:
        print(f"🧪 Running comprehensive analysis for {base_url}...")
        
        # Use convenience function
        results = await analyze_site_structure(
            base_url=base_url,
            export_path="./exports/comprehensive_analysis.graphml"
        )
        
        # Display results
        print("\n📊 Analysis Results:")
        
        # Graph summary
        summary = results['graph_summary']
        print(f"   Nodes: {summary['nodes']}")
        print(f"   Edges: {summary['edges']}")
        print(f"   Connected: {summary['is_connected']}")
        
        # Metrics
        metrics = results['metrics']
        print(f"   Components: {metrics['connected_components']}")
        print(f"   Density: {metrics['density']:.4f}")
        print(f"   Clustering: {metrics['clustering_coefficient']:.4f}")
        
        # Patterns
        patterns = results['patterns']
        print(f"   Hub Nodes: {len(patterns['hub_nodes'])}")
        print(f"   Authority Nodes: {len(patterns['authority_nodes'])}")
        print(f"   Cycles: {len(patterns['cycles'])}")
        
        # Critical paths
        critical_paths = results['critical_paths']
        print(f"   Critical Paths: {len(critical_paths)}")
        
        if 'exported_to' in results:
            print(f"   📤 Exported to: {results['exported_to']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in comprehensive analysis: {e}")
        return False


async def main():
    """Run all graph handler examples."""
    print("🕸️ Site Graph Handler Examples")
    print("=" * 60)
    print("This example demonstrates NetworkX-based site graph analysis")
    print("Note: Examples assume you have crawled data in the database")
    print("=" * 60)
    
    examples = [
        ("Basic Graph Analysis", basic_graph_analysis_example),
        ("Pattern Detection", pattern_detection_example),
        ("Critical Paths", critical_paths_example),
        ("Graph Export", graph_export_example),
        ("Graph Visualization", graph_visualization_example),
        ("Comprehensive Analysis", comprehensive_analysis_example)
    ]
    
    results = []
    
    for name, example_func in examples:
        try:
            success = await example_func()
            results.append((name, success))
        except Exception as e:
            print(f"❌ {name} failed: {e}")
            results.append((name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 Example Results Summary:")
    
    for name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"   {status} - {name}")
    
    successful = sum(1 for _, success in results if success)
    total = len(results)
    
    print(f"\n🎯 Overall: {successful}/{total} examples completed successfully")
    
    if successful < total:
        print("\nNote: Some examples may fail if:")
        print("- No crawled data exists in the database")
        print("- Required dependencies (matplotlib, networkx) are not installed")
        print("- Database connection issues")


if __name__ == "__main__":
    asyncio.run(main())