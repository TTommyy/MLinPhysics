from __future__ import annotations

from typing import Protocol

import numpy as np

from physics_sim.core import Force


class EnergyAttrs(Protocol):
    forces: list[Force]
    _n_entities: int
    _positions: np.ndarray
    _velocities: np.ndarray
    _masses: np.ndarray
    _dynamic_mask: np.ndarray


class EnergyMixin(EnergyAttrs):
    def get_energies(self) -> dict[str, float]:
        if self._n_entities == 0:
            return {"kinetic": 0.0, "potential": 0.0, "total": 0.0}
        n = self._n_entities
        dyn = self._dynamic_mask[:n]
        velocities_sq = np.sum(self._velocities[:n][dyn] ** 2, axis=1)
        kinetic = float(0.5 * np.sum(self._masses[:n][dyn] * velocities_sq))
        potential = float(
            sum(
                force.get_potential_energy_contribution(
                    positions=self._positions[:n][dyn],
                    masses=self._masses[:n][dyn],
                )
                for force in self.forces
            )
        )
        total = kinetic + potential
        return {"kinetic": kinetic, "potential": potential, "total": total}
