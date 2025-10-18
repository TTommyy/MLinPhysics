import arcade

from physics_sim.core import LayoutRegion
from physics_sim.ui.sections.base_section import BaseSection


class DebugInfoSection(BaseSection):
    """Top panel section displaying debug information."""

    def __init__(self, region: LayoutRegion):
        super().__init__(
            region,
            background_color=(220, 220, 240),
            border_color=arcade.color.GRAY,
        )

        self._create_text_objects()

    def _create_text_objects(self):
        """Create reusable text objects."""
        x = self.region.x + 15
        y = self.region.center_y

        self.title_text = arcade.Text(
            "DEBUG INFO",
            x,
            y + 20,
            arcade.color.DARK_RED,
            12,
            bold=True,
        )
        self.fps_text = arcade.Text(
            "FPS: 0.0",
            x,
            y,
            arcade.color.BLACK,
            10,
        )
        self.engine_text = arcade.Text(
            "Engine: Unknown",
            x + 120,
            y,
            arcade.color.BLACK,
            10,
        )
        self.entity_counts_text = arcade.Text(
            "",
            x + 280,
            y,
            arcade.color.BLACK,
            10,
        )

    def on_draw(self):
        """Draw the debug info section."""
        self.draw_background()
        self.draw_border()

    def render_with_data(
        self, fps: float, engine_name: str, entity_counts: dict[str, int]
    ):
        """Render debug information.

        Args:
            fps: Current frames per second
            engine_name: Name of the physics engine
            entity_counts: Dictionary mapping entity type names to counts
        """
        self.fps_text.text = f"FPS: {fps:.1f}"
        self.engine_text.text = f"Engine: {engine_name}"

        # Format entity counts
        if entity_counts:
            counts_str = " | ".join([
                f"{type_name}: {count}" for type_name, count in entity_counts.items()
            ])
            self.entity_counts_text.text = counts_str
        else:
            self.entity_counts_text.text = "No entities"

        # Draw all text
        self.title_text.draw()
        self.fps_text.draw()
        self.engine_text.draw()
        self.entity_counts_text.draw()

    def on_update(self, delta_time: float):
        """Update section."""
        pass


__all__: list[str] = ["DebugInfoSection"]
