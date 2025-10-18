import math

import arcade


class GridRendererMixin:
    """Mixin for rendering coordinate grid and axis labels."""

    def render_grid(self, base_spacing: int = 1) -> None:
        """Render coordinate grid with major/minor lines and labels.

        Args:
            base_spacing: Base spacing in physics units (will be adapted)
        """
        if not self.show_grid:
            return

        # Calculate adaptive spacing based on scale
        spacing = self._calculate_grid_spacing(base_spacing)
        major_interval = 2  # Major grid every 5 units

        # Color scheme
        minor_grid_color = (240, 240, 240)
        major_grid_color = (200, 200, 200)
        axis_color = (100, 100, 100)
        origin_color = (80, 80, 255)
        label_color = (60, 60, 60)

        # Get axis positions
        screen_x_axis = self.physics_to_screen_x(0)
        screen_y_axis = self.physics_to_screen_y(0)

        # Collect grid lines
        minor_v, major_v, labels_v = self._collect_vertical_lines(
            spacing, major_interval
        )
        minor_h, major_h, labels_h = self._collect_horizontal_lines(
            spacing, major_interval
        )

        # Draw minor grid first (background)
        if minor_v:
            arcade.draw_lines(minor_v, minor_grid_color, 1)
        if minor_h:
            arcade.draw_lines(minor_h, minor_grid_color, 1)

        # Draw major grid
        if major_v:
            arcade.draw_lines(major_v, major_grid_color, 2)
        if major_h:
            arcade.draw_lines(major_h, major_grid_color, 2)

        # Draw axes (thicker, more prominent)
        if self.region.left <= screen_x_axis <= self.region.right:
            arcade.draw_line(
                screen_x_axis,
                self.region.bottom,
                screen_x_axis,
                self.region.top,
                axis_color,
                3,
            )
        if self.region.bottom <= screen_y_axis <= self.region.top:
            arcade.draw_line(
                self.region.left,
                screen_y_axis,
                self.region.right,
                screen_y_axis,
                axis_color,
                3,
            )

        # Draw origin marker
        origin_x = self.physics_to_screen_x(0)
        origin_y = self.physics_to_screen_y(0)
        if (
            self.region.left <= origin_x <= self.region.right
            and self.region.bottom <= origin_y <= self.region.top
        ):
            arcade.draw_circle_filled(origin_x, origin_y, 4, origin_color)

        # Draw labels (only for major grid lines)
        for label_text, x, y in labels_v + labels_h:
            arcade.Text(
                label_text,
                x,
                y,
                label_color,
                9,  # Larger font
                bold=True,
            ).draw()

    def _calculate_grid_spacing(self, base_spacing: float) -> float:
        """Calculate adaptive grid spacing based on zoom level.

        Returns spacing that keeps grid density reasonable.
        Ensures spacing is in "nice" numbers (1, 2, 5, 10, 20, 50, etc.)
        """
        # Calculate how many pixels per physics unit
        pixels_per_unit = self.scale

        # Target: grid lines every 30-80 pixels
        target_pixels = 50

        # Calculate ideal spacing
        ideal_spacing = target_pixels / pixels_per_unit

        # Round to nice number (1, 2, 5) * 10^n
        magnitude = 10 ** math.floor(math.log10(ideal_spacing))
        normalized = ideal_spacing / magnitude

        if normalized < 1.5:
            nice_spacing = 1 * magnitude
        elif normalized < 3.5:
            nice_spacing = 2 * magnitude
        elif normalized < 7.5:
            nice_spacing = 5 * magnitude
        else:
            nice_spacing = 10 * magnitude

        return max(nice_spacing, base_spacing)

    def _collect_vertical_lines(
        self, spacing: float, major_interval: int
    ) -> tuple[
        list[tuple[float, float]],
        list[tuple[float, float]],
        list[tuple[str, float, float]],
    ]:
        """Collect vertical grid lines (minor, major, labels).

        Returns:
            (minor_lines, major_lines, labels)
            labels are (text, x, y) tuples
        """
        minor_lines = []
        major_lines = []
        labels = []

        # Find range of x values to draw
        x_min = (
            math.floor(self.screen_to_physics_x(self.region.left) / spacing) * spacing
        )
        x_max = (
            math.ceil(self.screen_to_physics_x(self.region.right) / spacing) * spacing
        )

        x = x_min
        while x <= x_max:
            screen_x = self.physics_to_screen_x(x)
            if self.region.left <= screen_x <= self.region.right:
                is_major = abs(x % (spacing * major_interval)) < 0.01

                if is_major and x != 0:
                    major_lines.append((screen_x, self.region.bottom))
                    major_lines.append((screen_x, self.region.top))

                    # Label position: below axis or at bottom
                    screen_y_axis = self.physics_to_screen_y(0)
                    label_y = (
                        screen_y_axis - 15
                        if self.region.bottom <= screen_y_axis <= self.region.top
                        else self.region.bottom + 5
                    )

                    labels.append((
                        f"{int(x) if x == int(x) else x}",
                        screen_x - 10,
                        label_y,
                    ))
                elif not is_major and x != 0:
                    minor_lines.append((screen_x, self.region.bottom))
                    minor_lines.append((screen_x, self.region.top))

            x += spacing

        return minor_lines, major_lines, labels

    def _collect_horizontal_lines(
        self, spacing: float, major_interval: int
    ) -> tuple[
        list[tuple[float, float]],
        list[tuple[float, float]],
        list[tuple[str, float, float]],
    ]:
        """Collect horizontal grid lines (minor, major, labels).

        Returns:
            (minor_lines, major_lines, labels)
            labels are (text, x, y) tuples
        """
        minor_lines = []
        major_lines = []
        labels = []

        # Find range of y values to draw
        y_min = (
            math.floor(self.screen_to_physics_y(self.region.bottom) / spacing) * spacing
        )
        y_max = math.ceil(self.screen_to_physics_y(self.region.top) / spacing) * spacing

        y = y_min
        while y <= y_max:
            screen_y = self.physics_to_screen_y(y)
            if self.region.bottom <= screen_y <= self.region.top:
                is_major = abs(y % (spacing * major_interval)) < 0.01

                if is_major and y != 0:
                    major_lines.append((self.region.left, screen_y))
                    major_lines.append((self.region.right, screen_y))

                    # Label position: left of axis or at left edge
                    screen_x_axis = self.physics_to_screen_x(0)
                    label_x = (
                        screen_x_axis - 25
                        if self.region.left <= screen_x_axis <= self.region.right
                        else self.region.left + 5
                    )

                    labels.append((
                        f"{int(y) if y == int(y) else y}",
                        label_x,
                        screen_y - 5,
                    ))
                elif not is_major and y != 0:
                    minor_lines.append((self.region.left, screen_y))
                    minor_lines.append((self.region.right, screen_y))

            y += spacing

        return minor_lines, major_lines, labels
