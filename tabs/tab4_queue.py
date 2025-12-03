# tabs/tab4_queue.py

import streamlit as st
import matplotlib.pyplot as plt

from cdpem_core.queues import simulate_mm1_queue


def render() -> None:
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

        fig, ax = plt.subplots()
        ax.plot(times, qs)
        ax.set_xlabel("Time")
        ax.set_ylabel("Queue length")
        ax.set_title("Queue Dynamics (M/M/1)")
        st.pyplot(fig)

        st.write(
            "When λ ≥ μ, the system tends to become unstable and queue length explodes. "
            "Policy can intervene by shifting λ (demand) or μ (capacity) and this framework "
            "lets you quantify stability margins."
        )
