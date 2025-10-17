import arcade

from physics_sim.core import LayoutRegion


class PlaceholderPanel:
    """Placeholder panel for future UI components.

    Renders a simple background with a centered title label
    to indicate where future components will be placed.
    """

    def __init__(self, region: LayoutRegion, label: str, color: tuple[int, int, int]):
        """
        Args:
            region: Layout region defining position and size
            label: Text to display in the center
            color: Background color RGB tuple
        """
        self.region = region
        self.color = color
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

    def render(self) -> None:
        """Render the placeholder panel."""
        # Draw background
        arcade.draw_lrbt_rectangle_filled(
            self.region.left,
            self.region.right,
            self.region.bottom,
            self.region.top,
            self.color,
        )

        # Draw border
        arcade.draw_lrbt_rectangle_outline(
            self.region.left,
            self.region.right,
            self.region.bottom,
            self.region.top,
            arcade.color.GRAY,
            2,
        )

        # Draw centered label
        self.text.draw()


__all__: list[str] = ["PlaceholderPanel"]
