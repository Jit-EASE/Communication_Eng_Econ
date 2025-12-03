# tabs/tab1_control.py

import streamlit as st
import plotly.graph_objects as go

from cdpem_core.engine import simulate_cdpm


def render(accent: str, get_figure, data_ctx: dict):
    st.subheader("Kalman-Controlled Policy Dynamics")
    st.write(
        "Real-time state estimation, PID-like control, and a noisy policy channel "
        "for inflation stabilisation. You can optionally overlay a real data series "
        "from the uploaded dataset."
    )

    df = data_ctx.get("df")
    numeric_cols = data_ctx.get("numeric_cols", [])

    mode = "Synthetic only"
    col_mode = st.columns(1)[0]
    if df is not None and numeric_cols:
        mode = col_mode.radio(
            "Data mode",
            ["Synthetic only", "Synthetic + overlay real series"],
            help="If you choose overlay, select a numeric column from the dataset to compare with the simulated inflation.",
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

    overlay_col = None
    if mode == "Synthetic + overlay real series" and df is not None and numeric_cols:
        overlay_col = st.selectbox(
            "Column to overlay as 'observed' inflation",
            numeric_cols,
        )

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
                name="True inflation (model)",
                hovertemplate=hover_style,
            )
        )
        fig1.add_trace(
            go.Scatter(
                y=hist["pi_hat"],
                mode="lines",
                name="Estimated inflation (Kalman)",
                line=dict(dash="dash"),
                hovertemplate=hover_style,
            )
        )
        fig1.add_hline(
            y=pi_target,
            line=dict(color=accent, dash="dot"),
            annotation_text="Target",
        )

        if overlay_col is not None:
            ser = df[overlay_col].dropna()
            fig1.add_trace(
                go.Scatter(
                    x=list(range(len(ser))),
                    y=ser.values,
                    mode="lines",
                    name=f"Observed ({overlay_col})",
                    line=dict(color="rgba(255,255,255,0.7)", width=2),
                    hovertemplate="<b>Observed</b><br>t=%{x}<br>value=%{y:.4f}<br>",
                )
            )

        fig1.update_layout(
            title="Inflation Dynamics",
            xaxis_title="Time",
            yaxis_title="Inflation / Index",
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
