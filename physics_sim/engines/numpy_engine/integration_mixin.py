import numpy as np


class IntegrationMixin:
    def _reset_accelerations(self, dyn: np.ndarray, n: int) -> None:
        self._accelerations[:n][dyn] = 0.0

    def _integrate_euler(self, dt: float, dyn: np.ndarray, n: int) -> None:
        self._velocities[:n][dyn] += self._accelerations[:n][dyn] * dt
        self._positions[:n][dyn] += self._velocities[:n][dyn] * dt

    def pause(self) -> None:
        self._paused = True

    def is_paused(self) -> bool:
        return self._paused

    def toggle_pause(self) -> None:
        self._paused = not self._paused
