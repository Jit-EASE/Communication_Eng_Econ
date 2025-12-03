# tabs/tab2_cycle.py

import streamlit as st
import plotly.graph_objects as go

from cdpem_core.engine import simulate_cdpm
from cdpem_core.fft_cycle import compute_fft_spectrum


def render(accent: str, get_figure, data_ctx: dict):
    st.subheader("Cycle Detection via FFT")
    st.write(
        "Spectral analysis of inflation under communication-driven policy dynamics. "
        "You can either analyse the simulated series or any numeric column from the dataset."
    )

    df = data_ctx.get("df")
    numeric_cols = data_ctx.get("numeric_cols", [])

    mode = "Use simulated series"
    if df is not None and numeric_cols:
        mode = st.radio(
            "Source for FFT:",
            ["Use simulated series", "Use dataset column"],
        )

    T = st.slider("Simulation horizon (T)", 50, 500, 200, step=10)
    pi_target = st.slider("Target inflation (π*)", 0.0, 0.10, 0.02, step=0.005)
    Kp = st.slider("Kp", 0.0, 2.0, 0.6, step=0.05)
    Ki = st.slider("Ki", 0.0, 0.2, 0.02, step=0.005)
    Kd = st.slider("Kd", 0.0, 0.5, 0.1, step=0.01)
    channel_sigma = st.slider("Channel noise σ", 0.0, 0.2, 0.05, step=0.01)

    col_from_data = None
    if mode == "Use dataset column" and df is not None and numeric_cols:
        col_from_data = st.selectbox("Column for FFT", numeric_cols)

    if st.button("Run cycle analysis"):
        if mode == "Use simulated series":
            hist = simulate_cdpm(
                T=T,
                Kp=Kp,
                Ki=Ki,
                Kd=Kd,
                pi_target=pi_target,
                channel_sigma=channel_sigma,
                seed=123,
            )
            series = hist["pi_true"]
        else:
            if col_from_data is None:
                st.error("Select a column from the dataset.")
                return
            series = df[col_from_data].dropna().values.tolist()

        freqs, amps = compute_fft_spectrum(series, dt=1.0)

        if len(freqs) == 0:
            st.warning("Not enough data points to compute spectrum.")
            return

        fig = get_figure(accent)
        fig.add_trace(
            go.Scatter(
                x=freqs,
                y=amps,
                mode="lines",
                name="FFT Spectrum",
                hovertemplate=(
                    "<b>Frequency:</b> %{x:.4f}<br>"
                    "<b>Amplitude:</b> %{y:.4f}<br>"
                ),
            )
        )
        fig.update_layout(
            title="Spectrum (FFT)",
            xaxis_title="Frequency (cycles per period)",
            yaxis_title="Amplitude",
        )
        st.plotly_chart(fig, use_container_width=True)

        st.write(
            "Peaks in the spectrum correspond to dominant cycles. "
            "For real data, this helps identify empirical periodicities; "
            "for simulated data, it reveals the frequency footprint of your policy design."
        )
