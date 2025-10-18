import arcade


class GridRendererMixin:
    """Mixin for rendering coordinate grid and axis labels."""

    def render_grid(self, grid_spacing: float = 1.0) -> None:
        """Render coordinate grid with labels at fixed spacing."""
        if not self.show_grid:
            return

        grid_color = (200, 200, 200)
        label_color = arcade.color.DARK_GRAY
        axis_color = (150, 150, 150)

        screen_x_axis = self.physics_to_screen_x(0)
        screen_y_axis = self.physics_to_screen_y(0)

        vertical_lines = self._collect_grid_lines(True, grid_spacing, label_color)
        horizontal_lines = self._collect_grid_lines(False, grid_spacing, label_color)

        if vertical_lines:
            arcade.draw_lines(vertical_lines, grid_color, 2)
        if horizontal_lines:
            arcade.draw_lines(horizontal_lines, grid_color, 2)

        axis_lines = [
            (screen_x_axis, self.region.bottom),
            (screen_x_axis, self.region.top),
            (self.region.left, screen_y_axis),
            (self.region.right, screen_y_axis),
        ]
        arcade.draw_lines(axis_lines, axis_color, 4)

        arcade.Text(
            "0,0",
            screen_x_axis + 5,
            screen_y_axis - 15,
            label_color,
            10,
            bold=True,
        ).draw()

        arcade.Text(
            f"{self.sim_width:.1f}",
            self.physics_to_screen_x(self.sim_width) - 20,
            screen_y_axis - 15,
            label_color,
            10,
            bold=True,
        ).draw()

        arcade.Text(
            f"{self.sim_height:.1f}",
            screen_x_axis + 5,
            self.physics_to_screen_y(self.sim_height) + 5,
            label_color,
            10,
            bold=True,
        ).draw()

    def _collect_grid_lines(
        self, is_vertical: bool, grid_spacing: int, label_color
    ) -> list[tuple[float, float]]:
        """Collect grid line points for either vertical or horizontal lines.

        Args:
            is_vertical: If True, collect vertical lines; else horizontal
            grid_spacing: Spacing between grid lines
            label_color: Color for grid labels

        Returns:
            List of (x, y) points for draw_lines()
        """
        lines: list[tuple[float, float]] = []

        if is_vertical:
            x = 0
            while x <= self.sim_width:
                screen_x = self.physics_to_screen_x(x)
                if self.region.left <= screen_x <= self.region.right:
                    lines.append((screen_x, self.region.bottom))
                    lines.append((screen_x, self.region.top))

                    if x > 0:
                        arcade.Text(
                            f"{x:.1f}",
                            screen_x - 10,
                            self.region.bottom + 5,
                            label_color,
                            10,
                        ).draw()
                x += grid_spacing
        else:
            y = 0
            while y <= self.sim_height:
                screen_y = self.physics_to_screen_y(y)
                if self.region.bottom <= screen_y <= self.region.top:
                    lines.append((self.region.left, screen_y))
                    lines.append((self.region.right, screen_y))

                    if y > 0:
                        arcade.Text(
                            f"{y}",
                            self.region.left + 5,
                            screen_y - 10,
                            label_color,
                            10,
                        ).draw()
                y += grid_spacing

        return lines
