# tabs/tab3_network.py

import streamlit as st
import plotly.graph_objects as go
import networkx as nx

from cdpem_core.networks import (
    build_example_supply_chain,
    compute_basic_centrality,
)


def render(accent: str, get_figure, data_ctx: dict):
    st.subheader("Network View of Policy Transmission")
    st.write(
        "Build a network from your dataset (e.g., origin–destination, firm–firm) "
        "or use the toy agri-food chain example."
    )

    df = data_ctx.get("df")
    cols = list(df.columns) if df is not None else []

    mode = "Toy example"
    if df is not None and len(cols) >= 2:
        mode = st.radio(
            "Network source",
            ["Toy example", "Build from dataset"],
            help="For dataset mode, select two columns representing source and target.",
        )

    if mode == "Toy example":
        G = build_example_supply_chain()
    else:
        src_col = st.selectbox("Source column", cols)
        tgt_col = st.selectbox("Target column", cols, index=min(1, len(cols) - 1))

        # Build graph from pairs
        G = nx.DiGraph()
        for _, row in df[[src_col, tgt_col]].dropna().iterrows():
            u = str(row[src_col])
            v = str(row[tgt_col])
            if u and v:
                if G.has_edge(u, v):
                    G[u][v]["weight"] += 1
                else:
                    G.add_edge(u, v, weight=1)

        if G.number_of_nodes() == 0:
            st.error("No valid edges found in dataset for selected columns.")
            return

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
        title="Network View",
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
        "In dataset mode, this is a real structural representation of your system: "
        "nodes with high betweenness are critical intermediaries for policy and information."
    )
