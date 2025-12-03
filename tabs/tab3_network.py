# tabs/tab3_network.py

import streamlit as st
import matplotlib.pyplot as plt
import networkx as nx

from cdpem_core.networks import (
    build_example_supply_chain,
    compute_basic_centrality,
)


def render() -> None:
    st.subheader("Network View of Policy Transmission")
    st.write(
        "Illustrative supply-chain network to think about structural bottlenecks "
        "and critical nodes for policy signals."
    )

    G = build_example_supply_chain()
    degree_c, betweenness_c = compute_basic_centrality(G)

    st.markdown("### Supply Chain Graph")

    fig, ax = plt.subplots()
    pos = nx.spring_layout(G, seed=42)
    nx.draw(G, pos, with_labels=True, ax=ax, arrows=True)
    st.pyplot(fig)

    st.markdown("### Centrality Measures")
    st.write("**Degree centrality** (connectivity importance):")
    st.json(degree_c)
    st.write("**Betweenness centrality** (flow bottleneck importance):")
    st.json(betweenness_c)

    st.write(
        "Nodes with high betweenness centrality are structurally critical for policy "
        "transmission. In a real system you would replace this toy graph with an Irish "
        "agri-food, banking, or labour network."
    )
