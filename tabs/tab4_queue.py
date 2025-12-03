# tabs/tab4_queue.py

import streamlit as st
import plotly.graph_objects as go

from cdpem_core.queues import simulate_mm1_queue


def render(accent: str, get_figure):
    st.subheader("Queueing & Congestion Dynamics")
    st.write(
        "M/M/1 queue as a minimal model of congestion in policy-relevant systems "
        "(hospitals, ports, agencies, grant processing, etc.)."
    )

    lmbda = st.slider("Arrival rate λ", 0.1, 2.0, 0.8, step=0.05)
    mu = st.slider("Service rate μ", 0.1, 3.0, 1.0, step=0.05)
    T = st.slider("Simulation horizon (time units)", 100, 5000, 1000, step=100)

    if st.button("Simulate queue"):
        times, qs = simulate_mm1_queue(lmbda=lmbda, mu=mu, T=float(T), seed=42)

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
            "Policy can intervene by shifting λ (demand) or μ (capacity) and this framework "
            "lets you quantify stability margins."
        )
