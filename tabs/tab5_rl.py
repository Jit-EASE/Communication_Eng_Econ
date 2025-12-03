import streamlit as st
import numpy as np
import plotly.graph_objects as go

# --------------------------------------------------------------------
# BASIC PID SIMILATION CORE (unchanged)
# --------------------------------------------------------------------

def simulate_pid(real_series, kp, ki, kd, target=0.0):
    """
    PID on real data.
    real_series: np.array of the real dataset column
    target: desired equilibrium level
    """
    n = len(real_series)
    out = np.zeros(n)
    ierr = 0.0
    prev_err = 0.0

    for t in range(n):
        x = real_series[t]
        err = x - target
        ierr += err
        derr = err - prev_err

        out[t] = kp*err + ki*ierr + kd*derr
        prev_err = err

    return out


def loss_fn(real_series, pid_output):
    """Minimise volatility + distance from target."""
    return np.mean((real_series - pid_output)**2) + np.var(pid_output)


def coarse_grid_search(real_series, target):
    """Find best PID params for real dataset."""
    best_loss = float("inf")
    best_params = (0,0,0)
    best_out = None

    for kp in [0.05, 0.1, 0.2, 0.3]:
        for ki in [0.00, 0.01, 0.02]:
            for kd in [0.00, 0.01]:
                out = simulate_pid(real_series, kp, ki, kd, target)
                L = loss_fn(real_series, out)
                if L < best_loss:
                    best_loss = L
                    best_params = (kp, ki, kd)
                    best_out = out

    return best_params, best_loss, best_out


# --------------------------------------------------------------------
# STREAMLIT TAB UI
# --------------------------------------------------------------------

def render(accent, get_figure, data_ctx):
    st.markdown("### Policy Tuner (Real Dataset Enabled)")

    df = data_ctx["df"]
    numerics = data_ctx["numeric_cols"]

    # ------------------------------------------------------------
    # 1) If no dataset → fallback to simulated synthetic data
    # ------------------------------------------------------------
    if df is None or len(numerics) == 0:
        st.warning("No numeric dataset found — running synthetic simulation.")

        # create synthetic inflation for fallback
        n = 120
        t = np.arange(n)
        real_series = 2.0 + 0.3*np.sin(0.1*t) + 0.1*np.random.randn(n)
        target = 2.0

    else:
        # ------------------------------------------------------------
        # 2) Choose a column from the uploaded dataset
        # ------------------------------------------------------------
        st.markdown("#### Select numeric column to tune against")
        col = st.selectbox("Dataset Column:", numerics)

        real_series = df[col].dropna().values.astype(float)
        n = len(real_series)

        # Auto-target suggestion as median or user selection
        target = st.number_input(
            "Target Level:",
            value=float(np.median(real_series)),
            step=0.1,
            format="%.3f"
        )

    # ------------------------------------------------------------
    # 3) RUN TUNER
    # ------------------------------------------------------------
    if st.button("Run PID Tuner"):
        best_params, best_loss, best_out = coarse_grid_search(real_series, target)
        kp, ki, kd = best_params

        st.success(
            f"**Best Params:** kp={kp}, ki={ki}, kd={kd} | "
            f"Loss={best_loss:.4f}"
        )

        # ------------------------------------------------------------
        # 4) Plot real vs PID output
        # ------------------------------------------------------------
        fig = get_figure(accent)
        fig.add_trace(go.Scatter(
            y=real_series,
            mode="lines",
            name="Real Series",
            hovertemplate="<b>Real</b><br>%{y:.4f}<br>"
        ))

        fig.add_trace(go.Scatter(
            y=best_out,
            mode="lines",
            name="PID Output",
            line=dict(dash="dash"),
            hovertemplate="<b>PID</b><br>%{y:.4f}<br>"
        ))

        fig.add_hline(
            y=target,
            line=dict(color=accent, dash="dot"),
            annotation_text="Target"
        )

        fig.update_layout(
            title=f"PID Tuning Result (Target={target})",
            xaxis_title="Time Index",
            yaxis_title="Value"
        )

        st.plotly_chart(fig, use_container_width=True)
