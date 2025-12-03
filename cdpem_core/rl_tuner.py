# cdpem_core/rl_tuner.py

import numpy as np

from .engine import simulate_cdpm


def evaluate_policy(
    Kp: float,
    Ki: float,
    Kd: float,
    pi_target: float = 0.02,
    channel_sigma: float = 0.05,
    T: int = 200,
    seed: int | None = None,
):
    """
    Run a simulation and return a simple loss:
    L = Var(pi - target) + lambda * Var(u)
    """
    hist = simulate_cdpm(
        T=T,
        Kp=Kp,
        Ki=Ki,
        Kd=Kd,
        pi_target=pi_target,
        channel_sigma=channel_sigma,
        seed=seed,
    )

    pi_true = np.array(hist["pi_true"])
    u = np.array(hist["u"])

    dev = pi_true - pi_target
    var_pi = float(np.var(dev)) if len(dev) > 0 else 0.0
    var_u = float(np.var(u)) if len(u) > 0 else 0.0

    lam = 0.1
    loss = var_pi + lam * var_u

    return loss, hist


def coarse_grid_search(
    Kp_grid,
    Ki_grid,
    Kd_grid,
    pi_target: float = 0.02,
    channel_sigma: float = 0.05,
    T: int = 200,
    seed: int | None = None,
):
    """
    Coarse search over PID parameters. Returns best params, loss, and history.
    """
    best_loss = np.inf
    best_params = None
    best_hist = None

    for Kp in Kp_grid:
        for Ki in Ki_grid:
            for Kd in Kd_grid:
                loss, hist = evaluate_policy(
                    Kp,
                    Ki,
                    Kd,
                    pi_target=pi_target,
                    channel_sigma=channel_sigma,
                    T=T,
                    seed=seed,
                )
                if loss < best_loss:
                    best_loss = loss
                    best_params = (float(Kp), float(Ki), float(Kd))
                    best_hist = hist

    return best_params, best_loss, best_hist
