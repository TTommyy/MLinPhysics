import arcade

from physics_sim.core import LayoutRegion


class BaseSection(arcade.Section):
    """Base section providing common rendering utilities for UI panels."""

    def __init__(
        self,
        region: LayoutRegion,
        background_color: tuple[int, int, int] = (245, 245, 245),
        border_color: tuple[int, int, int] | None = arcade.color.GRAY,
        border_width: int = 2,
    ):
        super().__init__(
            left=region.left,
            bottom=region.bottom,
            width=region.width,
            height=region.height,
        )
        self.region = region
        self.background_color = background_color
        self.border_color = border_color
        self.border_width = border_width

    def draw_background(self):
        """Draw section background."""
        arcade.draw_lrbt_rectangle_filled(
            self.region.left,
            self.region.right,
            self.region.bottom,
            self.region.top,
            self.background_color,
        )

    def draw_border(self, sides: str = "all"):
        """Draw section border.

        Args:
            sides: Which sides to draw ('all', 'left', 'right', 'top', 'bottom')
        """
        if not self.border_color:
            return

        if sides in ("all", "left"):
            arcade.draw_line(
                self.region.left,
                self.region.bottom,
                self.region.left,
                self.region.top,
                self.border_color,
                self.border_width,
            )

        if sides in ("all", "right"):
            arcade.draw_line(
                self.region.right,
                self.region.bottom,
                self.region.right,
                self.region.top,
                self.border_color,
                self.border_width,
            )

        if sides in ("all", "top"):
            arcade.draw_line(
                self.region.left,
                self.region.top,
                self.region.right,
                self.region.top,
                self.border_color,
                self.border_width,
            )

        if sides in ("all", "bottom"):
            arcade.draw_line(
                self.region.left,
                self.region.bottom,
                self.region.right,
                self.region.bottom,
                self.border_color,
                self.border_width,
            )


__all__: list[str] = ["BaseSection"]
