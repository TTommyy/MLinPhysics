from abc import ABC, abstractmethod

from .entity import Entity
from .force import Force
from .vector import Vector2D


class PhysicsEngine(ABC):
    """Abstract base class for physics engine implementations.

    Uses Strategy pattern to allow swapping between different physics
    implementations (numpy-based custom, pymunk, etc.) while maintaining
    the same interface.
    """

    def __init__(self, gravity: Vector2D, bounds: tuple[float, float]):
        """
        Args:
            gravity: Gravity acceleration vector (e.g., Vector2D(0, -10))
            bounds: (width, height) of simulation space
        """
        self.gravity = gravity
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
    def get_entities(self) -> list[Entity]:
        """Get all entities currently in the simulation."""
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
