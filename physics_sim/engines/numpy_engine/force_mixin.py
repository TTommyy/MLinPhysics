import numpy as np


class ForceMixin:
    def _clear_applied_forces(self, n: int) -> None:
        for i in range(n):
            self._applied_forces[i].clear()

    def _apply_forces(self, dt: float, dyn: np.ndarray, n: int) -> None:
        for force in self.forces:
            force_vectors = force.apply_force(
                positions=self._positions[:n][dyn],
                velocities=self._velocities[:n][dyn],
                masses=self._masses[:n][dyn],
                drag_coeffs=self._drag_coeffs[:n][dyn],
                cross_sections=self._cross_sections[:n][dyn],
                entity_types=self._entity_types[:n][dyn],
                dt=dt,
            )
            masses_reshaped = self._masses[:n][dyn][:, np.newaxis]
            self._accelerations[:n][dyn] += force_vectors / masses_reshaped

            dyn_indices = np.where(dyn)[0]
            for i, entity_idx in enumerate(dyn_indices):
                self._applied_forces[entity_idx].append((force.name, force_vectors[i]))
