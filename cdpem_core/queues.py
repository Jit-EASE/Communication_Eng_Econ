# cdpem_core/queues.py

import numpy as np


def simulate_mm1_queue(
    lmbda: float = 0.8,
    mu: float = 1.0,
    T: float = 1000.0,
    seed: int | None = None,
):
    """
    Simulate an M/M/1 queue with arrival rate λ and service rate μ.

    Returns
    -------
    times : list[float]
    qs : list[int]
        Queue length time series.
    """
    if seed is not None:
        np.random.seed(seed)

    t = 0.0
    queue_length = 0
    times = [0.0]
    qs = [0]

    while t < T:
        # Time to next arrival and next service completion
        t_arrival = np.random.exponential(1.0 / lmbda) if lmbda > 0 else np.inf
        t_service = np.random.exponential(1.0 / mu) if (mu > 0 and queue_length > 0) else np.inf

        if t_arrival < t_service:
            # Arrival occurs
            t += t_arrival
            queue_length += 1
        else:
            # Service completion
            t += t_service
            if queue_length > 0:
                queue_length -= 1

        times.append(t)
        qs.append(queue_length)

    return times, qs
