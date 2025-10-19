import numpy as np


class PBDMixIn:
    def _apply_constraints(self, dt: float, dyn: np.ndarray, n: int) -> None:
        for force in self.forces:
            positions_new = force.apply_constraints(
                positions=self._positions[:n][dyn],
                velocities=self._velocities[:n][dyn],
                masses=self._masses[:n][dyn],
                entity_types=self._entity_types[:n][dyn],
                dt=dt,
            )

            if positions_new is not None:
                self._positions[:n][dyn] = positions_new

        self._velocities[:n][dyn] = (
            self._positions[:n][dyn] - self._prev_positions
        ) / dt
