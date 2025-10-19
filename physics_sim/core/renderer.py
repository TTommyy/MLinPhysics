from abc import ABC, abstractmethod

from .entity import Entity


class Renderer(ABC):
    """Abstract base class for rendering implementations.

    Allows swapping between different rendering backends (Arcade, Pygame, etc.)
    while maintaining the same interface.
    """

    def __init__(
        self,
        screen_width: int,
        screen_height: int,
        sim_width: float,
        sim_height: float,
    ):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.sim_width = sim_width
        self.sim_height = sim_height
        self.scale = min(screen_width / sim_width, screen_height / sim_height)

        self.show_debug = True
        self.show_grid = True
        self.show_forces = False

    @abstractmethod
    def physics_to_screen_x(self, x: float) -> float:
        """Convert physics X coordinate to screen coordinate."""
        pass

    @abstractmethod
    def physics_to_screen_y(self, y: float) -> float:
        """Convert physics Y coordinate to screen coordinate."""
        pass

    @abstractmethod
    def screen_to_physics_x(self, x: float) -> float:
        """Convert screen X coordinate to physics coordinate."""
        pass

    @abstractmethod
    def screen_to_physics_y(self, y: float) -> float:
        """Convert screen Y coordinate to physics coordinate."""
        pass

    @abstractmethod
    def clear(self) -> None:
        """Clear the screen."""
        pass

    @abstractmethod
    def render_entities(self, entities: list[Entity]) -> None:
        """Render all entities in the simulation."""
        pass

    @abstractmethod
    def render_grid(self, grid_spacing: float = 1.0) -> None:
        """Render coordinate grid with labels."""
        pass

    @abstractmethod
    def render_ui(self, ui_elements: list) -> None:
        """Render UI elements (panels, buttons, etc.)."""
        pass

    def toggle_debug(self) -> None:
        """Toggle debug information display."""
        self.show_debug = not self.show_debug

    def toggle_grid(self) -> None:
        """Toggle grid display."""
        self.show_grid = not self.show_grid

    def toggle_forces(self) -> None:
        """Toggle forces overlay display."""
        self.show_forces = not self.show_forces

    @abstractmethod
    def pause(self) -> None:
        """Pause rendering/input handling."""
        pass

    @abstractmethod
    def is_paused(self) -> bool:
        """Check if renderer is paused."""
        pass
