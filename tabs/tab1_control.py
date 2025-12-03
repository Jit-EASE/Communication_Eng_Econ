# tabs/tab1_control.py

import streamlit as st
import matplotlib.pyplot as plt

from cdpem_core.engine import simulate_cdpm


def render() -> None:
    st.subheader("Kalman-Controlled Policy Dynamics")
    st.write(
        "Real-time state estimation, PID-like control, and a noisy policy channel "
        "for inflation stabilisation."
    )

    col1, col2 = st.columns(2)
    with col1:
        T = st.slider("Simulation horizon (T)", 50, 500, 200, step=10)
        pi_target = st.slider("Target inflation (π*)", 0.0, 0.10, 0.02, step=0.005)
        channel_sigma = st.slider(
            "Channel noise σ (policy implementation uncertainty)",
            0.0,
            0.2,
            0.05,
            step=0.01,
        )
    with col2:
        Kp = st.slider("Kp (proportional gain)", 0.0, 2.0, 0.6, step=0.05)
        Ki = st.slider("Ki (integral gain)", 0.0, 0.2, 0.02, step=0.005)
        Kd = st.slider("Kd (derivative gain)", 0.0, 0.5, 0.1, step=0.01)

    if st.button("Run simulation"):
        hist = simulate_cdpm(
            T=T,
            Kp=Kp,
            Ki=Ki,
            Kd=Kd,
            pi_target=pi_target,
            channel_sigma=channel_sigma,
            seed=42,
        )

        # Inflation plot
        fig1, ax1 = plt.subplots()
        ax1.plot(hist["pi_true"], label="True inflation")
        ax1.plot(hist["pi_hat"], label="Estimated inflation", linestyle="--")
        ax1.axhline(pi_target, label="Target", linestyle=":")
        ax1.set_xlabel("Time")
        ax1.set_ylabel("Inflation")
        ax1.legend()
        ax1.set_title("Inflation dynamics")
        st.pyplot(fig1)

        # Policy vs effective policy
        fig2, ax2 = plt.subplots()
        ax2.plot(hist["u"], label="Policy (designed)")
        ax2.plot(hist["u_eff"], label="Policy (effective)", linestyle="--")
        ax2.set_xlabel("Time")
        ax2.set_ylabel("Policy instrument")
        ax2.legend()
        ax2.set_title("Policy signal vs noisy channel")
        st.pyplot(fig2)
