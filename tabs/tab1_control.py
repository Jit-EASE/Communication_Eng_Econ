# tabs/tab1_control.py

import streamlit as st
import plotly.graph_objects as go

from cdpem_core.engine import simulate_cdpm


def render(accent: str, get_figure):
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

        hover_style = "<b>%{fullData.name}</b><br>t=%{x}<br>value=%{y:.4f}<br>"

        # Inflation dynamics
        fig1 = get_figure(accent)
        fig1.add_trace(
            go.Scatter(
                y=hist["pi_true"],
                mode="lines",
                name="True inflation",
                hovertemplate=hover_style,
            )
        )
        fig1.add_trace(
            go.Scatter(
                y=hist["pi_hat"],
                mode="lines",
                name="Estimated inflation",
                line=dict(dash="dash"),
                hovertemplate=hover_style,
            )
        )
        fig1.add_hline(
            y=pi_target,
            line=dict(color=accent, dash="dot"),
            annotation_text="Target",
        )
        fig1.update_layout(
            title="Inflation Dynamics", xaxis_title="Time", yaxis_title="Inflation"
        )
        st.plotly_chart(fig1, use_container_width=True)

        # Policy vs effective policy
        fig2 = get_figure(accent)
        fig2.add_trace(
            go.Scatter(
                y=hist["u"],
                mode="lines",
                name="Policy (designed)",
                hovertemplate=hover_style,
            )
        )
        fig2.add_trace(
            go.Scatter(
                y=hist["u_eff"],
                mode="lines",
                name="Policy (effective)",
                line=dict(dash="dash"),
                hovertemplate=hover_style,
            )
        )
        fig2.update_layout(
            title="Policy Signal vs Noisy Channel",
            xaxis_title="Time",
            yaxis_title="Policy Instrument",
        )
        st.plotly_chart(fig2, use_container_width=True)
