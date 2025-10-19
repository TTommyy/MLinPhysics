from typing import Any

import numpy as np

from physics_sim.core import PhysicsEngine

from .boundary_mixin import BoundaryMixin
from .collision_mixin import CollisionMixin
from .data_export_mixin import DataExportMixin
from .energy_mixin import EnergyMixin
from .entity_api_mixin import EntityApiMixin
from .force_mixin import ForceMixin
from .integration_mixin import IntegrationMixin
from .pbd_mixin import PBDMixIn
from .storage_mixin import StorageMixin


class NumpyPhysicsEngine(
    StorageMixin,
    ForceMixin,
    IntegrationMixin,
    PBDMixIn,
    BoundaryMixin,
    CollisionMixin,
    EntityApiMixin,
    DataExportMixin,
    EnergyMixin,
    PhysicsEngine,
):
    def __init__(self, bounds: tuple[float, float]):
        PhysicsEngine.__init__(self, bounds)
        StorageMixin.__init__(self)
        self._paused: bool = False

    def step(self, dt: float) -> None:
        """Advance simulation using vectorized Euler integration with PBD constraints."""
        if self._paused or self._n_entities == 0:
            return

        n = self._n_entities
        dyn = self._dynamic_mask[:n]
        if dyn.sum() == 0:
            return

        self._prev_positions = self._positions[:n][dyn].copy()

        self._reset_accelerations(dyn, n)
        self._clear_applied_forces(n)
        self._apply_forces(dt, dyn, n)
        self._integrate_euler(dt, dyn, n)
        self._apply_constraints(dt, dyn, n)

        self._handle_boundary_collisions_vectorized()
        self._handle_ball_ball_collisions_vectorized()
        self._handle_ball_obstacle_collisions_vectorized()

    def get_forces_render_data(self, sample_points: np.ndarray) -> dict[str, Any]:
        if sample_points is None or len(sample_points) == 0:
            return {"vector_field": np.zeros((0, 2)), "overlays": []}

        # Mocked batch for visualization sampling
        positions = np.asarray(sample_points, dtype=np.float64)
        velocities = np.zeros_like(positions)
        masses = np.ones((len(positions),), dtype=np.float64)
        entity_types = np.zeros((len(positions),), dtype=np.int32)
        dt = 0.0

        # Provide engine state for forces that need current entities
        n = self._n_entities
        engine_state = {
            "all_positions": self._positions[:n].copy(),
            "all_velocities": self._velocities[:n].copy(),
            "all_masses": self._masses[:n].copy(),
            "entity_types": self._entity_types[:n].copy(),
            "type_properties": self._type_properties,
            "dynamic_mask": self._dynamic_mask[:n].copy(),
        }

        accumulated = np.zeros_like(positions, dtype=np.float64)
        overlays: list[dict[str, Any]] = []

        for force in self.forces:
            try:
                vecs = force.apply_force(
                    positions=positions,
                    velocities=velocities,
                    masses=masses,
                    entity_types=entity_types,
                    dt=dt,
                    engine_state=engine_state,
                )
            except Exception:
                vecs = None
            if isinstance(vecs, np.ndarray) and vecs.shape == accumulated.shape:
                accumulated += vecs

            try:
                rd = force.get_render_data(None)
            except Exception:
                rd = {}
            if isinstance(rd, dict):
                ov = rd.get("overlays")
                if isinstance(ov, list):
                    overlays.extend(ov)

        return {"vector_field": accumulated, "overlays": overlays}
