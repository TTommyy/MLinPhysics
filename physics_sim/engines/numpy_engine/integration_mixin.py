from typing import Protocol

import numpy as np
from numba import jit


@jit
def _reset_accelerations_kernel(
    accelerations: np.ndarray, dyn: np.ndarray, n: int
) -> None:
    accelerations[:n][dyn] = 0.0


@jit
def _integrate_euler_kernel(
    positions: np.ndarray,
    velocities: np.ndarray,
    accelerations: np.ndarray,
    dt: float,
    dyn: np.ndarray,
    n: int,
) -> None:
    velocities[:n][dyn] += accelerations[:n][dyn] * dt
    positions[:n][dyn] += velocities[:n][dyn] * dt


class IntegrationMixinAttr(Protocol):
    _accelerations: np.ndarray
    _velocities: np.ndarray
    _positions: np.ndarray


class IntegrationMixin(IntegrationMixinAttr):
    def _reset_accelerations(self, dyn: np.ndarray, n: int) -> None:
        _reset_accelerations_kernel(self._accelerations, dyn, n)

    def _integrate_euler(self, dt: float, dyn: np.ndarray, n: int) -> None:
        _integrate_euler_kernel(
            self._positions, self._velocities, self._accelerations, dt, dyn, n
        )

    def pause(self) -> None:
        self._paused = True

    def is_paused(self) -> bool:
        return self._paused

    def toggle_pause(self) -> None:
        self._paused = not self._paused
