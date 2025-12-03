# tabs/tab3_network.py

import streamlit as st
import plotly.graph_objects as go
import networkx as nx

from cdpem_core.networks import (
    build_example_supply_chain,
    compute_basic_centrality,
)


def render(accent: str, get_figure):
    st.subheader("Network View of Policy Transmission")
    st.write(
        "Illustrative supply-chain network to think about structural bottlenecks "
        "and critical nodes for policy signals."
    )

    G = build_example_supply_chain()
    degree_c, betweenness_c = compute_basic_centrality(G)

    pos = nx.spring_layout(G, seed=42)

    xs = [pos[n][0] for n in G.nodes()]
    ys = [pos[n][1] for n in G.nodes()]

    edge_x = []
    edge_y = []
    for u, v in G.edges():
        x0, y0 = pos[u]
        x1, y1 = pos[v]
        edge_x += [x0, x1, None]
        edge_y += [y0, y1, None]

    fig = get_figure(accent)

    # edges
    fig.add_trace(
        go.Scatter(
            x=edge_x,
            y=edge_y,
            mode="lines",
            line=dict(width=1.5, color=accent),
            hoverinfo="none",
            name="Edges",
        )
    )

    # nodes
    fig.add_trace(
        go.Scatter(
            x=xs,
            y=ys,
            mode="markers+text",
            text=list(G.nodes()),
            textposition="top center",
            marker=dict(
                size=18,
                color="rgba(10,10,20,0.9)",
                line=dict(color=accent, width=2),
            ),
            hovertemplate="<b>%{text}</b><br>x=%{x:.3f}<br>y=%{y:.3f}<br>",
            name="Nodes",
        )
    )

    fig.update_layout(
        title="Supply Chain Network (Illustrative)",
        showlegend=False,
        xaxis=dict(showticklabels=False),
        yaxis=dict(showticklabels=False),
    )

    st.plotly_chart(fig, use_container_width=True)

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
