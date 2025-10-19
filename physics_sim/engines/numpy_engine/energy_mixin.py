import numpy as np


class EnergyMixin:
    def get_energies(self) -> dict[str, float]:
        if self._n_entities == 0:
            return {"kinetic": 0.0, "potential": 0.0, "total": 0.0}
        n = self._n_entities
        dyn = self._dynamic_mask[:n]
        velocities_sq = np.sum(self._velocities[:n][dyn] ** 2, axis=1)
        kinetic = float(0.5 * np.sum(self._masses[:n][dyn] * velocities_sq))
        potential = 0.0
        for force in self.forces:
            potential += force.get_potential_energy_contribution(
                positions=self._positions[:n][dyn],
                masses=self._masses[:n][dyn],
            )
        total = kinetic + potential
        return {"kinetic": kinetic, "potential": potential, "total": total}
