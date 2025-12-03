# cdpem_core/networks.py

import networkx as nx


def build_example_supply_chain() -> nx.DiGraph:
    """
    Build a small example supply chain network.
    Nodes: Farm -> Processor -> Distributor -> Retail -> Consumer
    """
    G = nx.DiGraph()
    G.add_edge("Farm", "Processor", weight=0.9)
    G.add_edge("Processor", "Distributor", weight=0.8)
    G.add_edge("Distributor", "Retail", weight=0.85)
    G.add_edge("Retail", "Consumer", weight=0.95)
    return G


def compute_basic_centrality(G: nx.DiGraph):
    """
    Compute basic centrality measures for a given network.
    Returns degree and betweenness centrality dicts.
    """
    degree_c = nx.degree_centrality(G)
    betweenness_c = nx.betweenness_centrality(G)
    return degree_c, betweenness_c
