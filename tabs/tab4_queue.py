# tabs/tab4_queue.py

import streamlit as st
import plotly.graph_objects as go

from cdpem_core.queues import simulate_mm1_queue


def render(accent: str, get_figure, data_ctx: dict):
    st.subheader("Queueing & Congestion Dynamics")
    st.write(
        "M/M/1 queue as a minimal model of congestion. You can simulate or plot an "
        "empirical queue length / workload series from the dataset."
    )

    df = data_ctx.get("df")
    numeric_cols = data_ctx.get("numeric_cols", [])

    mode = "Simulate M/M/1"
    if df is not None and numeric_cols:
        mode = st.radio(
            "Mode",
            ["Simulate M/M/1", "Use dataset numeric column as queue length"],
        )

    if mode == "Simulate M/M/1":
        lmbda = st.slider("Arrival rate λ", 0.1, 2.0, 0.8, step=0.05)
        mu = st.slider("Service rate μ", 0.1, 3.0, 1.0, step=0.05)
        T = st.slider("Simulation horizon (time units)", 100, 5000, 1000, step=100)

        if st.button("Run (simulate)"):
            times, qs = simulate_mm1_queue(
                lmbda=lmbda, mu=mu, T=float(T), seed=42
            )

            fig = get_figure(accent)
            fig.add_trace(
                go.Scatter(
                    x=times,
                    y=qs,
                    mode="lines",
                    name="Queue length",
                    hovertemplate="<b>t:</b> %{x:.2f}<br><b>q(t):</b> %{y}<br>",
                )
            )
            fig.update_layout(
                title="Queue Dynamics (M/M/1)",
                xaxis_title="Time",
                yaxis_title="Queue Length",
            )

            st.plotly_chart(fig, use_container_width=True)

            st.write(
                "When λ ≥ μ, the system tends to become unstable and queue length explodes. "
                "Policy can intervene by shifting λ (demand) or μ (capacity)."
            )
    else:
        col_q = st.selectbox(
            "Dataset column representing queue length / workload",
            numeric_cols,
        )

        if st.button("Plot dataset queue series"):
            series = df[col_q].dropna()
            fig = get_figure(accent)
            fig.add_trace(
                go.Scatter(
                    x=list(range(len(series))),
                    y=series.values,
                    mode="lines",
                    name=f"{col_q}",
                    hovertemplate="<b>t=%{x}</b><br>value=%{y:.4f}<br>",
                )
            )
            fig.update_layout(
                title=f"Empirical Queue / Workload Series ({col_q})",
                xaxis_title="Index",
                yaxis_title="Value",
            )
            st.plotly_chart(fig, use_container_width=True)

            st.write(
                "This is a direct view of congestion in your dataset. You can "
                "compare it with simulated queue dynamics in the other mode."
            )
