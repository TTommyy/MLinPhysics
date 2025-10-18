import arcade

from physics_sim.core import LayoutRegion
from physics_sim.rendering import ArcadeRenderer
from physics_sim.ui.sections.base_section import BaseSection


class ViewportSection(BaseSection):
    """Central viewport section for rendering the physics simulation."""

    def __init__(self, region: LayoutRegion, sim_width: float, sim_height: float):
        super().__init__(
            region,
            background_color=arcade.color.PLATINUM,
            border_color=None,
        )

        self.renderer = ArcadeRenderer(
            region=region,
            sim_width=sim_width,
            sim_height=sim_height,
        )

    def on_draw(self):
        """Draw the viewport section."""
        self.draw_background()
        # Renderer handles grid and entities

    def render_with_data(self, render_data: list[dict]):
        """Render simulation entities from data dicts.

        This is called from Simulator during on_draw.

        Args:
            render_data: List of entity data dicts from engine
        """
        self.renderer.render_grid()
        self.renderer.render_entities(render_data)

    def on_update(self, delta_time: float):
        """Update section."""
        pass


__all__: list[str] = ["ViewportSection"]
