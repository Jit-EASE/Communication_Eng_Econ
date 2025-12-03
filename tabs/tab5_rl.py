# tabs/tab5_rl.py

import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

from cdpem_core.rl_tuner import coarse_grid_search


def render() -> None:
    st.subheader("Policy Parameter Tuner (Coarse Search)")
    st.write(
        "Primitive RL-lite tuner for PID parameters, minimising a loss that combines "
        "inflation volatility and policy effort."
    )

    pi_target = st.slider("Target inflation (π*)", 0.0, 0.10, 0.02, step=0.005)
    channel_sigma = st.slider("Channel noise σ", 0.0, 0.2, 0.05, step=0.01)
    T = st.slider("Simulation horizon (T)", 50, 500, 200, step=10)

    st.markdown("### Parameter search grids")
    st.write("Keep the grid small initially to avoid heavy compute inside Streamlit.")

    Kp_min, Kp_max = st.slider("Kp range", 0.0, 2.0, (0.2, 1.0), step=0.1)
    Ki_min, Ki_max = st.slider("Ki range", 0.0, 0.2, (0.0, 0.1), step=0.01)
    Kd_min, Kd_max = st.slider("Kd range", 0.0, 0.5, (0.0, 0.3), step=0.05)

    step_count = st.slider("Number of steps per dimension", 2, 6, 3)

    if st.button("Run tuner"):
        Kp_grid = np.linspace(Kp_min, Kp_max, step_count)
        Ki_grid = np.linspace(Ki_min, Ki_max, step_count)
        Kd_grid = np.linspace(Kd_min, Kd_max, step_count)

        best_params, best_loss, best_hist = coarse_grid_search(
            Kp_grid,
            Ki_grid,
            Kd_grid,
            pi_target=pi_target,
            channel_sigma=channel_sigma,
            T=T,
            seed=123,
        )

        if best_params is None or best_hist is None:
            st.error("No parameters evaluated – check your grid.")
            return

        Kp_best, Ki_best, Kd_best = best_params

        st.markdown("### Best parameters found")
        st.write(
            {
                "Kp": Kp_best,
                "Ki": Ki_best,
                "Kd": Kd_best,
                "Loss": best_loss,
            }
        )

        fig, ax = plt.subplots()
        ax.plot(best_hist["pi_true"], label="True inflation")
        ax.axhline(pi_target, label="Target", linestyle=":")
        ax.set_xlabel("Time")
        ax.set_ylabel("Inflation")
        ax.legend()
        ax.set_title("Inflation path under tuned PID parameters")
        st.pyplot(fig)

        st.write(
            "This is a coarse search, not a full RL agent yet. But it already encodes "
            "the logic of a self-tuning controller that learns stabilising policy mixes."
        )
