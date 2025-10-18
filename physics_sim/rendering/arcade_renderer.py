import arcade

from physics_sim.core import LayoutRegion, Renderer

from ._grid_renderer_mixin import GridRendererMixin
from ._pause_manager_mixin import PauseManagerMixin
from ._shape_renderer_mixin import ShapeRendererMixin


class ArcadeRenderer(
    ShapeRendererMixin, GridRendererMixin, PauseManagerMixin, Renderer
):
    """Renderer using Arcade library for visualization.

    Handles:
    - Coordinate system transformation (physics space → screen space)
    - Entity rendering (circles, shapes, etc.)
    - Debug information display
    - Grid rendering with coordinate labels
    """

    def __init__(self, region: LayoutRegion, sim_width: float, sim_height: float):
        """
        Args:
            region: Viewport region defining screen bounds
            sim_width: Simulation width in physics units
            sim_height: Simulation height in physics units
        """
        super().__init__(region.width, region.height, sim_width, sim_height)
        self.region = region
        # Recalculate scale based on region dimensions
        self.scale = min(region.width / sim_width, region.height / sim_height)
        self.sim_width = sim_width
        self.sim_height = sim_height
        self._paused = False

    def physics_to_screen_x(self, x: float) -> float:
        """Convert physics X coordinate to screen coordinate."""
        return self.region.left + (x * self.scale)

    def physics_to_screen_y(self, y: float) -> float:
        """Convert physics Y coordinate to screen coordinate.

        Physics origin is at region.bottom (bottom of viewport), Y increases upward.
        """
        return self.region.bottom + (y * self.scale)

    def screen_to_physics_x(self, x: float) -> float:
        """Convert screen X coordinate to physics coordinate."""
        return (x - self.region.left) / self.scale

    def screen_to_physics_y(self, y: float) -> float:
        """Convert screen Y coordinate to physics coordinate."""
        return (y - self.region.bottom) / self.scale

    def clear(self) -> None:
        """Clear the screen."""
        arcade.start_render()
        arcade.set_background_color(arcade.color.WHITE)

    def render_entities(self, render_data: list[dict]) -> None:
        """Render entities from data dicts (not entity objects)."""
        for data in render_data:
            self._render_entity(data)

    def render_ui(self, ui_elements: list) -> None:
        """Render UI elements (panels, buttons, etc.)."""
        # UI elements handle their own rendering in arcade
        pass
