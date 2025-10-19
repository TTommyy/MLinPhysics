import math

import arcade


class GridRendererMixin:
    """Mixin for rendering coordinate grid and axis labels."""

    # Grid styling constants
    _GRID_MAJOR_INTERVAL: int = 2
    _GRID_TARGET_PIXELS: int = 50
    _MINOR_GRID_COLOR: tuple[int, int, int] = (240, 240, 240)
    _MAJOR_GRID_COLOR: tuple[int, int, int] = (200, 200, 200)
    _AXIS_COLOR: tuple[int, int, int] = (100, 100, 100)
    _ORIGIN_COLOR: tuple[int, int, int] = (80, 80, 255)
    _LABEL_COLOR: tuple[int, int, int] = (60, 60, 60)
    _MINOR_GRID_WIDTH: float = 1.0
    _MAJOR_GRID_WIDTH: float = 2.0
    _AXIS_WIDTH: float = 3.0
    _ORIGIN_RADIUS_PX: float = 4.0

    def render_grid(self, base_spacing: int = 1) -> None:
        """Render coordinate grid with major/minor lines and labels.

        Args:
            base_spacing: Base spacing in physics units (will be adapted)
        """
        if not self.show_grid:
            return

        # Calculate adaptive spacing based on scale
        spacing = self._calculate_grid_spacing(base_spacing)

        # Prepare cache containers
        if not hasattr(self, "_grid_cache_key"):
            self._grid_cache_key = None
            self._grid_shape_minor_v = None
            self._grid_shape_minor_h = None
            self._grid_shape_major_v = None
            self._grid_shape_major_h = None
            self._grid_shape_axes = None
            self._grid_shape_origin = None
            self._grid_text_labels: list[arcade.Text] = []

        key = (
            float(self.scale),
            float(self.region.left),
            float(self.region.right),
            float(self.region.bottom),
            float(self.region.top),
            float(spacing),
        )

        if key != self._grid_cache_key:
            # Rebuild shapes and labels
            self._grid_cache_key = key

            # Get axis positions
            screen_x_axis = self.physics_to_screen_x(0)
            screen_y_axis = self.physics_to_screen_y(0)

            # Collect grid lines
            minor_v, major_v, labels_v = self._collect_vertical_lines(
                spacing, self._GRID_MAJOR_INTERVAL
            )
            minor_h, major_h, labels_h = self._collect_horizontal_lines(
                spacing, self._GRID_MAJOR_INTERVAL
            )

            # Build line shapes
            def _mk_colors(
                num: int, rgb: tuple[int, int, int]
            ) -> list[tuple[int, int, int, int]]:
                r, g, b = rgb
                return [(r, g, b, 255)] * num

            self._grid_shape_minor_v = (
                arcade.shape_list.create_lines_with_colors(
                    minor_v,
                    _mk_colors(len(minor_v), self._MINOR_GRID_COLOR),
                    self._MINOR_GRID_WIDTH,
                )
                if minor_v
                else None
            )
            self._grid_shape_minor_h = (
                arcade.shape_list.create_lines_with_colors(
                    minor_h,
                    _mk_colors(len(minor_h), self._MINOR_GRID_COLOR),
                    self._MINOR_GRID_WIDTH,
                )
                if minor_h
                else None
            )
            self._grid_shape_major_v = (
                arcade.shape_list.create_lines_with_colors(
                    major_v,
                    _mk_colors(len(major_v), self._MAJOR_GRID_COLOR),
                    self._MAJOR_GRID_WIDTH,
                )
                if major_v
                else None
            )
            self._grid_shape_major_h = (
                arcade.shape_list.create_lines_with_colors(
                    major_h,
                    _mk_colors(len(major_h), self._MAJOR_GRID_COLOR),
                    self._MAJOR_GRID_WIDTH,
                )
                if major_h
                else None
            )

            # Axes
            axes_shapes = arcade.shape_list.ShapeElementList()
            has_axis = False
            if self.region.left <= screen_x_axis <= self.region.right:
                axes_shapes.append(
                    arcade.shape_list.create_line(
                        screen_x_axis,
                        self.region.bottom,
                        screen_x_axis,
                        self.region.top,
                        self._AXIS_COLOR,
                        self._AXIS_WIDTH,
                    )
                )
                has_axis = True
            if self.region.bottom <= screen_y_axis <= self.region.top:
                axes_shapes.append(
                    arcade.shape_list.create_line(
                        self.region.left,
                        screen_y_axis,
                        self.region.right,
                        screen_y_axis,
                        self._AXIS_COLOR,
                        self._AXIS_WIDTH,
                    )
                )
                has_axis = True
            self._grid_shape_axes = axes_shapes if has_axis else None

            # Origin marker
            origin_x = self.physics_to_screen_x(0)
            origin_y = self.physics_to_screen_y(0)
            if (
                self.region.left <= origin_x <= self.region.right
                and self.region.bottom <= origin_y <= self.region.top
            ):
                self._grid_shape_origin = arcade.shape_list.create_ellipse_filled(
                    origin_x,
                    origin_y,
                    self._ORIGIN_RADIUS_PX * 2,
                    self._ORIGIN_RADIUS_PX * 2,
                    self._ORIGIN_COLOR,
                )
            else:
                self._grid_shape_origin = None

            # Labels (Text objects are faster than draw_text)
            self._grid_text_labels = []
            for label_text, x, y in labels_v + labels_h:
                self._grid_text_labels.append(
                    arcade.Text(
                        label_text,
                        x,
                        y,
                        self._LABEL_COLOR,
                        9,
                        bold=True,
                    )
                )

        # Draw cached shapes
        if self._grid_shape_minor_v:
            self._grid_shape_minor_v.draw()
        if self._grid_shape_minor_h:
            self._grid_shape_minor_h.draw()
        if self._grid_shape_major_v:
            self._grid_shape_major_v.draw()
        if self._grid_shape_major_h:
            self._grid_shape_major_h.draw()
        if self._grid_shape_axes:
            self._grid_shape_axes.draw()
        if self._grid_shape_origin:
            self._grid_shape_origin.draw()
        for t in self._grid_text_labels:
            t.draw()

    def _calculate_grid_spacing(self, base_spacing: float) -> float:
        """Calculate adaptive grid spacing based on zoom level.

        Returns spacing that keeps grid density reasonable.
        Ensures spacing is in "nice" numbers (1, 2, 5, 10, 20, 50, etc.)
        """
        # Calculate how many pixels per physics unit
        pixels_per_unit = self.scale

        # Target: grid lines every ~_GRID_TARGET_PIXELS pixels
        target_pixels = self._GRID_TARGET_PIXELS

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

    # Helper to sample physics-space grid intersections for force field rendering
    def get_grid_sample_points(
        self, include_minor: bool = True, custom_spacing: float | None = None
    ) -> list[tuple[float, float]]:
        if self._grid_sample_points:
            return self._grid_sample_points

        spacing = (
            max(self._calculate_grid_spacing(1), custom_spacing)
            if custom_spacing is not None
            else self._calculate_grid_spacing(1)
        )
        major_interval = 2

        # Collect x and y coordinates for intersections
        x_min = (
            math.ceil(self.screen_to_physics_x(self.region.left) / spacing) * spacing
        )
        x_max = (
            math.floor(self.screen_to_physics_x(self.region.right) / spacing) * spacing
        )
        y_min = (
            math.ceil(self.screen_to_physics_y(self.region.bottom) / spacing) * spacing
        )
        y_max = (
            math.floor(self.screen_to_physics_y(self.region.top) / spacing) * spacing
        )

        xs = []
        x = x_min
        while x <= x_max:
            is_major = abs(x % (spacing * major_interval)) < 0.01
            if include_minor or is_major or abs(x) < 1e-9:
                xs.append(x)
            x += spacing

        ys = []
        y = y_min
        while y <= y_max:
            is_major = abs(y % (spacing * major_interval)) < 0.01
            if include_minor or is_major or abs(y) < 1e-9:
                ys.append(y)
            y += spacing

        points: list[tuple[float, float]] = []
        for xv in xs:
            for yv in ys:
                points.append((float(xv), float(yv)))
        self._grid_sample_points = points
        return points
