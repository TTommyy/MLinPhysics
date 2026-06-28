from __future__ import annotations

from typing import Any

import numpy as np
from numba import njit

from physics_sim.core import Force


class ExplosionImpulseForce(Force):
    def __init__(
        self,
        center: np.ndarray | list[float] = [10.0, 5.0],
        peak_impulse: float = 50.0,
        duration: float = 0.3,
        falloff: float = 1.0,
    ) -> None:
        super().__init__("Explosion")
        self.center = np.asarray(center, dtype=np.float64)
        self.peak_impulse = float(peak_impulse)
        self.duration = max(1e-6, float(duration))
        self.falloff = max(0.0, float(falloff))
        self._time = 0.0

    @classmethod
    def get_name(cls) -> str:
        return "Explosion"

    @classmethod
    def is_unique(cls) -> bool:
        return False

    def apply_force(
        self,
        positions: np.ndarray,
        velocities: np.ndarray,
        masses: np.ndarray,
        entity_types: np.ndarray,
        dt: float,
        **kwargs,
    ) -> np.ndarray:
        # Simple time-boxed impulse distributed as force over this frame
        if dt > 0:
            self._time += dt
        if self._time > self.duration:
            return np.zeros_like(positions)

        return _compute_explosion_impulse_force(
            positions=positions,
            center=self.center,
            peak_impulse=self.peak_impulse,
            duration=self.duration,
            falloff=self.falloff,
            time=self._time,
            dt=dt,
        )

    def get_render_data(self, sample_points: np.ndarray) -> dict[str, Any]:
        t_norm = max(0.0, 1.0 - self._time / self.duration)
        overlays = [
            {
                "kind": "circle",
                "position": self.center.tolist(),
                "radius": max(0.2, (self.peak_impulse * t_norm) / 25.0),
                "color": (160, 60, 60),
            }
        ]
        return {"overlays": overlays}

    @classmethod
    def get_default_parameters(cls) -> dict[str, dict[str, Any]]:
        return {
            "center": {"type": "vector", "default": [10.0, 5.0], "label": "Center"},
            "peak_impulse": {
                "type": "float",
                "default": 50.0,
                "min": 0.0,
                "max": 500.0,
                "label": "Peak impulse",
            },
            "duration": {
                "type": "float",
                "default": 0.3,
                "min": 0.05,
                "max": 5.0,
                "label": "Duration (s)",
            },
            "falloff": {
                "type": "float",
                "default": 1.0,
                "min": 0.0,
                "max": 3.0,
                "label": "Radial falloff",
            },
        }

    def get_settable_parameters(self) -> dict[str, dict[str, Any]]:
        return {
            "center": {
                "type": "vector",
                "default": self.center.tolist(),
                "label": "Center",
            },
            "peak_impulse": {
                "type": "float",
                "default": float(self.peak_impulse),
                "min": 0.0,
                "max": 500.0,
                "label": "Peak impulse",
            },
            "duration": {
                "type": "float",
                "default": float(self.duration),
                "min": 0.05,
                "max": 5.0,
                "label": "Duration (s)",
            },
            "falloff": {
                "type": "float",
                "default": float(self.falloff),
                "min": 0.0,
                "max": 3.0,
                "label": "Radial falloff",
            },
        }

    def update_parameters(self, config: dict[str, Any]) -> bool:
        try:
            if "center" in config:
                self.center = np.asarray(config["center"], dtype=np.float64)
            if "peak_impulse" in config:
                self.peak_impulse = float(config["peak_impulse"])
            if "duration" in config:
                self.duration = max(1e-6, float(config["duration"]))
            if "falloff" in config:
                self.falloff = max(0.0, float(config["falloff"]))
            return True
        except (ValueError, TypeError):
            return False


@njit
def _compute_explosion_impulse_force(
    positions: np.ndarray,
    center: np.ndarray,
    peak_impulse: float,
    duration: float,
    falloff: float,
    time: float,
    dt: float,
) -> np.ndarray:
    n = positions.shape[0]
    result = np.zeros_like(positions)

    if time > duration or n == 0:
        return result

    t_norm = 1.0 - time / duration
    if t_norm < 0.0:
        t_norm = 0.0

    impulse_mag = peak_impulse * t_norm
    safe_dt = dt if dt > 1e-6 else 1e-6

    for i in range(n):
        dx = positions[i, 0] - center[0]
        dy = positions[i, 1] - center[1]
        r2 = dx * dx + dy * dy
        safe_r2 = r2 if r2 >= 1e-10 else 1e-10
        safe_r = np.sqrt(safe_r2)
        dirs_x = dx / safe_r
        dirs_y = dy / safe_r
        falloff_term = safe_r**falloff if falloff != 0.0 else 1.0
        if falloff_term <= 1e-12:
            falloff_term = 1e-12
        magnitude = (impulse_mag / safe_dt) / falloff_term
        result[i, 0] = dirs_x * magnitude
        result[i, 1] = dirs_y * magnitude

    return result
