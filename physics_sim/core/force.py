from abc import ABC, abstractmethod
from typing import Any

import numpy as np


class Force(ABC):
    """Abstract base class for forces in the simulation.

    Forces can be global (apply to all entities) or entity-specific
    (apply only to entities with certain properties).
    """

    def __init__(self, name: str):
        """
        Args:
            name: Human-readable name for this force (e.g., "Gravity", "Drag")
        """
        self.name = name

    def apply_force(
        self,
        positions: np.ndarray,
        velocities: np.ndarray,
        masses: np.ndarray,
        entity_types: np.ndarray,
        dt: float,
        **kwargs,
    ) -> np.ndarray:
        """Vectorized force calculation for batch of entities.

        Args:
            positions: Position vectors, shape (n, 2)
            velocities: Velocity vectors, shape (n, 2)
            masses: Mass values, shape (n,)
            entity_types: Entity type IDs, shape (n,)
            dt: Time step
            **kwargs: Additional entity-specific properties (drag_coeffs, cross_sections, etc.)

        Returns:
            Force vectors for all entities, shape (n, 2)
        """
        # Default implementation: fallback to per-entity (slow but correct)
        n = len(positions)
        forces = np.zeros((n, 2), dtype=np.float64)
        # Note: This is a fallback. Subclasses should override for performance.
        return forces

    def get_potential_energy_contribution(
        self,
        positions: np.ndarray,
        masses: np.ndarray,
        **kwargs,
    ) -> float:
        """Calculate potential energy contribution from this force.

        Args:
            positions: Position vectors, shape (n, 2)
            masses: Mass values, shape (n,)
            **kwargs: Additional force-specific parameters

        Returns:
            Total potential energy contribution in Joules
        """
        return 0.0

    def apply_constraints(
        self,
        positions: np.ndarray,
        velocities: np.ndarray,
        masses: np.ndarray,
        entity_types: np.ndarray,
        dt: float,
        **kwargs,
    ) -> np.ndarray:
        """Default: no-op. PBD constraints project positions.

        Args:
            positions: Position vectors, shape (n, 2)
            prev_positions: Previous position vectors, shape (n, 2)
            velocities: Velocity vectors, shape (n, 2)
            masses: Mass values, shape (n,)
            entity_types: Entity type IDs, shape (n,)
            dt: Time step
            **kwargs: Additional entity-specific properties

        Returns:
            positions after constraint
        """
        return None

    @classmethod
    @abstractmethod
    def get_name(cls) -> str:
        """Get force name"""
        pass

    @classmethod
    def is_unique(cls) -> bool:
        """Determine if only one instance of this force can exist.

        Returns:
            True if only one instance allowed, False if multiple instances allowed
        """
        return True

    @classmethod
    def get_default_parameters(cls) -> dict[str, dict[str, Any]]:
        """Get default settable parameters for force creation.

        Returns metadata for editable parameters.
        Subclasses should override this to provide their specific parameters.

        Returns:
            Dictionary mapping parameter names to their metadata:
            {
                "param_name": {
                    "type": "float" | "int" | "bool" | "vector",
                    "default": default_value,
                    "min": min_value (optional),
                    "max": max_value (optional),
                    "label": "Display Label"
                }
            }
        """
        return {}

    def get_settable_parameters(self) -> dict[str, dict[str, Any]]:
        """Get metadata for all editable parameters with current values.

        Returns:
            Dictionary mapping parameter names to their metadata with current values
        """
        return {}

    def update_parameters(self, config: dict[str, Any]) -> bool:
        """Update force parameters from config dict.

        Args:
            config: Dictionary of parameter values to update

        Returns:
            True if update successful, False otherwise
        """
        return True

    def get_render_data(self, sample_points: np.ndarray) -> dict[str, Any]:
        """Optional render data for visualization overlays and vector fields.

        Args:
            sample_points: Physics-space points (N,2) where acceleration field may be sampled.

        Returns:
            Dict with optional keys:
              - "vector_field": np.ndarray shape (N,2) acceleration contributions at sample_points
              - "overlays": list of overlay dicts
        """
        # Default: no visualization for this force
        return {}

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name})"
