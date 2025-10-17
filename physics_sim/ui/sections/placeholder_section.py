import arcade

from physics_sim.core import LayoutRegion
from physics_sim.ui.sections.base_section import BaseSection


class PlaceholderSection(BaseSection):
    """Placeholder section for future UI components."""

    def __init__(
        self,
        region: LayoutRegion,
        label: str,
        background_color: tuple[int, int, int] = (220, 220, 240),
    ):
        super().__init__(
            region,
            background_color=background_color,
            border_color=arcade.color.GRAY,
        )
        self.text = arcade.Text(
            label,
            region.center_x,
            region.center_y,
            arcade.color.DARK_GRAY,
            16,
            anchor_x="center",
            anchor_y="center",
            bold=True,
        )

    def on_draw(self):
        """Draw the placeholder section."""
        self.draw_background()
        self.draw_border()
        self.text.draw()

    def on_update(self, delta_time: float):
        """Update section."""
        pass


__all__: list[str] = ["PlaceholderSection"]
