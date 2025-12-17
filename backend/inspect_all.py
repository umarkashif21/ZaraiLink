import networkx as nx

GRAPHS = {
    "Company–Product": "company_product_graph.graphml",
    "Product–Product Co-Trade": "product_co_trade_graph.graphml",
    "Company–Company": "company_company_graph.graphml",
    "Company–Country": "company_country_graph.graphml",
    "Product–Country": "product_country_graph.graphml",
}

def inspect_graph(name, path):
    print(f"\n{'='*60}")
    print(f"🔍 INSPECTING: {name}")
    print(f"{'='*60}")
    
    try:
        G = nx.read_graphml(path)
        print(f"✅ Nodes: {G.number_of_nodes()}")
        print(f"✅ Edges: {G.number_of_edges()}")
        
        
        print("\n📌 Sample Nodes (first 5):")
        for i, node in enumerate(list(G.nodes())[:5]):
            print(f"  {i+1}. {node}")
        
        
        print("\n🔗 Sample Edges (first 5):")
        for i, (u, v, data) in enumerate(list(G.edges(data=True))[:5]):
            weight = data.get('weight', 'N/A')
            print(f"  {i+1}. {u} ↔ {v} | weight = {weight}")
            
    except FileNotFoundError:
        print(f"❌ File not found: {path}")
    except Exception as e:
        print(f"❌ Error loading graph: {e}")

if __name__ == "__main__":
    for name, path in GRAPHS.items():
        inspect_graph(name, path)