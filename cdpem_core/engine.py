# cdpem_core/engine.py

import numpy as np


class CDEPMPolicyEngine:
    """
    Communication-Driven Econometric Policy Engine (CDEPM v0.1)

    - State-space economy with Kalman filter
    - PID-like controller for policy
    - Noisy channel between designed policy and effective policy
    """

    def __init__(
        self,
        A: np.ndarray,
        B: np.ndarray,
        C: np.ndarray,
        Q: np.ndarray,
        R: np.ndarray,
        Kp: float = 0.5,
        Ki: float = 0.05,
        Kd: float = 0.1,
        pi_target: float = 0.02,
        channel_sigma: float = 0.1,
    ) -> None:
        # System matrices
        self.A = A
        self.B = B
        self.C = C
        self.Q = Q
        self.R = R

        # Kalman filter state
        self.x_hat = np.zeros((A.shape[0], 1))    # initial state estimate
        self.P = np.eye(A.shape[0]) * 0.1         # initial covariance

        # PID controller params
        self.Kp = Kp
        self.Ki = Ki
        self.Kd = Kd

        # Target inflation
        self.pi_target = pi_target

        # Channel noise (policy implementation uncertainty)
        self.channel_sigma = channel_sigma

        # Internal tracking variables
        self.u_prev = 0.0
        self.e_prev = 0.0
        self.e_int = 0.0   # integral of error

    def kalman_update(self, z, u_eff_prev: float):
        """
        Perform one Kalman filter update given observation z
        and previous effective policy u_eff_prev.
        """
        z = np.array(z).reshape(-1, 1)

        # Prediction
        x_pred = self.A @ self.x_hat + self.B * u_eff_prev
        P_pred = self.A @ self.P @ self.A.T + self.Q

        # Kalman gain
        S = self.C @ P_pred @ self.C.T + self.R
        K = P_pred @ self.C.T @ np.linalg.inv(S)

        # Update
        y = z - self.C @ x_pred
        self.x_hat = x_pred + K @ y
        self.P = (np.eye(self.P.shape[0]) - K @ self.C) @ P_pred

        return self.x_hat

    def policy_update(self) -> float:
        """
        Compute new policy instrument u_t (designed) based on estimated state.
        """
        pi_hat = float(self.x_hat[0, 0])  # assume pi is first state component

        # Error: target - estimated
        e_t = self.pi_target - pi_hat

        # Integrate error
        self.e_int += e_t

        # Derivative of error
        e_der = e_t - self.e_prev

        # PID-like policy update
        u_t = self.u_prev + self.Kp * e_t + self.Ki * self.e_int + self.Kd * e_der

        # Store for next step
        self.u_prev = u_t
        self.e_prev = e_t

        return u_t

    def transmit_policy(self, u_t: float) -> float:
        """
        Apply channel noise to the designed policy: u_eff = u + ε.
        """
        noise = np.random.normal(0, self.channel_sigma)
        u_eff = u_t + noise
        return u_eff


def simulate_cdpm(
    T: int = 100,
    A: np.ndarray | None = None,
    B: np.ndarray | None = None,
    C: np.ndarray | None = None,
    Q: np.ndarray | None = None,
    R: np.ndarray | None = None,
    Kp: float = 0.6,
    Ki: float = 0.02,
    Kd: float = 0.1,
    pi_target: float = 0.02,
    channel_sigma: float = 0.05,
    seed: int | None = None,
):
    """
    Run a CDEPM simulation over T periods and return a history dict.
    """

    if seed is not None:
        np.random.seed(seed)

    # Default simple parameterisation if none passed
    if A is None:
        A = np.array([[0.8, 0.1], [0.1, 0.7]])
    if B is None:
        B = np.array([[0.2], [0.1]])
    if C is None:
        C = np.eye(2)
    if Q is None:
        Q = np.eye(2) * 0.01
    if R is None:
        R = np.eye(2) * 0.05

    engine = CDEPMPolicyEngine(
        A,
        B,
        C,
        Q,
        R,
        Kp=Kp,
        Ki=Ki,
        Kd=Kd,
        pi_target=pi_target,
        channel_sigma=channel_sigma,
    )

    x_true = np.zeros((2, 1))
    u_eff_prev = 0.0

    history = {
        "pi_true": [],
        "y_true": [],
        "pi_hat": [],
        "y_hat": [],
        "u": [],
        "u_eff": [],
    }

    for _ in range(T):
        # Economy evolution (plant)
        w_t = np.random.multivariate_normal([0, 0], Q).reshape(-1, 1)
        x_true = A @ x_true + B * u_eff_prev + w_t

        # Observation
        v_t = np.random.multivariate_normal([0, 0], R).reshape(-1, 1)
        z_t = C @ x_true + v_t

        # Kalman update
        x_hat = engine.kalman_update(z_t, u_eff_prev)

        # Controller
        u_t = engine.policy_update()

        # Channel noise
        u_eff = engine.transmit_policy(u_t)

        # Save history
        history["pi_true"].append(float(x_true[0, 0]))
        history["y_true"].append(float(x_true[1, 0]))
        history["pi_hat"].append(float(x_hat[0, 0]))
        history["y_hat"].append(float(x_hat[1, 0]))
        history["u"].append(float(u_t))
        history["u_eff"].append(float(u_eff))

        u_eff_prev = u_eff

    return history
