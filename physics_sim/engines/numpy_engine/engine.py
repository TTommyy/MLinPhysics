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
