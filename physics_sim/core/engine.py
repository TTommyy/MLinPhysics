from abc import ABC, abstractmethod

from .entity import Entity
from .force import Force


class PhysicsEngine(ABC):
    """Abstract base class for physics engine implementations.

    Uses Strategy pattern to allow swapping between different physics
    implementations (numpy-based custom, etc.) while maintaining
    the same interface.
    """

    def __init__(self, bounds: tuple[float, float]):
        """
        Args:
            gravity: Gravity acceleration as np.ndarray([x, y])
            bounds: (width, height) of simulation space
        """
        self.bounds = bounds
        self.forces: list[Force] = []  # List of Force instances

    @abstractmethod
    def add_entity(self, entity: Entity) -> None:
        """Add an entity to the physics simulation."""
        pass

    @abstractmethod
    def remove_entity(self, entity_id: str) -> None:
        """Remove an entity from the physics simulation."""
        pass

    @abstractmethod
    def step(self, dt: float) -> None:
        """Advance the physics simulation by dt seconds."""
        pass

    @abstractmethod
    def clear(self) -> None:
        """Remove all entities from the simulation."""
        pass

    def add_force(self, force) -> None:
        """Add a force to the simulation.

        Args:
            force: Force instance to add
        """
        self.forces.append(force)

    def remove_force(self, force) -> None:
        """Remove a force from the simulation.

        Args:
            force: Force instance to remove
        """
        if force in self.forces:
            self.forces.remove(force)

    def clear_forces(self) -> None:
        """Remove all forces from the simulation."""
        self.forces.clear()

    @abstractmethod
    def pause(self) -> None:
        """Pause the physics simulation."""
        pass

    @abstractmethod
    def is_paused(self) -> bool:
        """Check if physics simulation is paused."""
        pass

    @abstractmethod
    def get_supported_entity_types(self) -> list[type]:
        """Get list of entity classes supported by this engine.

        Returns:
            List of entity classes (e.g., [Ball, Obstacle])
        """
        pass

    @abstractmethod
    def get_render_data(self) -> list[dict]:
        """Get rendering data for all entities.

        Returns:
            List of dicts with:
                - id: entity ID
                - type: EntityType enum or string
                - position: (x, y) tuple
                - render_type: 'circle', 'rectangle', etc.
                - type-specific: radius, width, height, color, etc.
        """
        pass

    @abstractmethod
    def get_inventory_data(self) -> list[dict]:
        """Get detailed physics data for UI display.

        Returns:
            List of dicts with full physics info:
                - id, type, mass, position, velocity, speed
                - acceleration, forces, etc.
        """
        pass

    @abstractmethod
    def get_entity_for_editing(self, entity_id: str) -> Entity | None:
        """Create temporary entity object for editing.

        Returns entity object populated from array data.
        User can modify it, then call update_entity_from_object().

        Args:
            entity_id: ID of entity to edit

        Returns:
            Temporary entity object or None if not found
        """
        pass

    @abstractmethod
    def update_entity_from_object(self, entity: Entity) -> bool:
        """Update array data from modified entity object.

        Args:
            entity: Modified entity object

        Returns:
            True if successful, False otherwise
        """
        pass

    @abstractmethod
    def get_energies(self) -> dict[str, float]:
        """Calculate total kinetic and potential energy in the system.

        Returns:
            Dictionary with keys:
                - 'kinetic': Total kinetic energy (Joules)
                - 'potential': Total potential energy (Joules)
                - 'total': Total energy (Joules)
        """
        pass
