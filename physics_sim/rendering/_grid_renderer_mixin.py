import math

from kivy.graphics import Color, Ellipse, InstructionGroup, Line, Rectangle

from physics_sim.ui.utils import format_number


def _rgb(c: tuple[int, int, int], a: float = 1.0) -> tuple[float, float, float, float]:
    return (c[0] / 255.0, c[1] / 255.0, c[2] / 255.0, a)


class GridRendererMixin:
    """Mixin for rendering coordinate grid and axis labels on a Kivy canvas."""

    # Grid styling constants
    _GRID_MAJOR_INTERVAL: int = 2
    _GRID_TARGET_PIXELS: int = 50
    _MINOR_GRID_COLOR: tuple[int, int, int] = (225, 225, 225)
    _MAJOR_GRID_COLOR: tuple[int, int, int] = (190, 190, 190)
    _AXIS_COLOR: tuple[int, int, int] = (100, 100, 100)
    _ORIGIN_COLOR: tuple[int, int, int] = (80, 80, 255)
    _LABEL_COLOR: tuple[int, int, int] = (60, 60, 60)
    _MINOR_GRID_WIDTH: float = 1.0
    _MAJOR_GRID_WIDTH: float = 1.2
    _AXIS_WIDTH: float = 1.6
    _ORIGIN_RADIUS_PX: float = 4.0
    _LABEL_FONT_SIZE: float = 10

    grid_group: InstructionGroup

    def _init_grid_renderer(self) -> None:
        self._grid_cache_key: tuple | None = None

    def invalidate_grid(self) -> None:
        """Force the grid (and grid sample points) to be rebuilt."""
        self._grid_cache_key = None
        self._grid_sample_points = None

    def render_grid(self, base_spacing: int = 1) -> None:
        """Render coordinate grid with major/minor lines and labels.

        Args:
            base_spacing: Base spacing in physics units (will be adapted)
        """
        if not self.show_grid:
            if self._grid_cache_key != "hidden":
                self.grid_group.clear()
                self._grid_cache_key = "hidden"
            return

        if self.region.width <= 0 or self.region.height <= 0:
            return

        spacing = self._calculate_grid_spacing(base_spacing)
        key = (
            float(self.scale),
            float(self.region.left),
            float(self.region.right),
            float(self.region.bottom),
            float(self.region.top),
            float(spacing),
        )
        if key == self._grid_cache_key:
            return
        self._grid_cache_key = key
        self._build_grid(spacing)

    def _build_grid(self, spacing: float) -> None:
        group = self.grid_group
        group.clear()

        minor_v, major_v, labels_v = self._collect_vertical_lines(
            spacing, self._GRID_MAJOR_INTERVAL
        )
        minor_h, major_h, labels_h = self._collect_horizontal_lines(
            spacing, self._GRID_MAJOR_INTERVAL
        )

        def add_segments(points: list[tuple[float, float]], color, width) -> None:
            if not points:
                return
            group.add(Color(*_rgb(color)))
            for i in range(0, len(points) - 1, 2):
                (x0, y0), (x1, y1) = points[i], points[i + 1]
                group.add(Line(points=[x0, y0, x1, y1], width=width))

        add_segments(minor_v + minor_h, self._MINOR_GRID_COLOR, self._MINOR_GRID_WIDTH)
        add_segments(major_v + major_h, self._MAJOR_GRID_COLOR, self._MAJOR_GRID_WIDTH)

        # Axes
        screen_x_axis = self.physics_to_screen_x(0)
        screen_y_axis = self.physics_to_screen_y(0)
        axes: list[tuple[float, float]] = []
        if self.region.left <= screen_x_axis <= self.region.right:
            axes += [(screen_x_axis, self.region.bottom), (screen_x_axis, self.region.top)]
        if self.region.bottom <= screen_y_axis <= self.region.top:
            axes += [(self.region.left, screen_y_axis), (self.region.right, screen_y_axis)]
        add_segments(axes, self._AXIS_COLOR, self._AXIS_WIDTH)

        # Origin marker
        if (
            self.region.left <= screen_x_axis <= self.region.right
            and self.region.bottom <= screen_y_axis <= self.region.top
        ):
            r = self._ORIGIN_RADIUS_PX
            group.add(Color(*_rgb(self._ORIGIN_COLOR)))
            group.add(Ellipse(pos=(screen_x_axis - r, screen_y_axis - r), size=(2 * r, 2 * r)))

        # Labels
        label_color = _rgb(self._LABEL_COLOR)
        group.add(Color(1, 1, 1, 1))
        for text, x, y in labels_v + labels_h:
            texture = self._text_cache.get(text, self._LABEL_FONT_SIZE, label_color, True)
            group.add(Rectangle(texture=texture, size=texture.size, pos=(x, y)))

    def _calculate_grid_spacing(self, base_spacing: float) -> float:
        """Calculate adaptive grid spacing based on zoom level.

        Returns spacing in "nice" numbers (1, 2, 5, 10, 20, 50, etc.)
        """
        pixels_per_unit = max(self.scale, 1e-9)
        ideal_spacing = self._GRID_TARGET_PIXELS / pixels_per_unit
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

    @staticmethod
    def _is_major(value: float, spacing: float, major_interval: int) -> bool:
        step = spacing * major_interval
        ratio = value / step
        return abs(ratio - round(ratio)) < 1e-6

    def _collect_vertical_lines(self, spacing: float, major_interval: int):
        """Collect vertical grid lines.

        Returns:
            (minor_lines, major_lines, labels); labels are (text, x, y) tuples
        """
        minor_lines: list[tuple[float, float]] = []
        major_lines: list[tuple[float, float]] = []
        labels: list[tuple[str, float, float]] = []

        i_min = math.floor(self.screen_to_physics_x(self.region.left) / spacing)
        i_max = math.ceil(self.screen_to_physics_x(self.region.right) / spacing)
        screen_y_axis = self.physics_to_screen_y(0)
        axis_visible = self.region.bottom <= screen_y_axis <= self.region.top

        for i in range(i_min, i_max + 1):
            x = i * spacing
            screen_x = self.physics_to_screen_x(x)
            if not (self.region.left <= screen_x <= self.region.right) or i == 0:
                continue
            if self._is_major(x, spacing, major_interval):
                major_lines += [(screen_x, self.region.bottom), (screen_x, self.region.top)]
                label_y = screen_y_axis - 16 if axis_visible else self.region.bottom + 4
                label_y = max(label_y, self.region.bottom + 2)
                labels.append((format_number(x), screen_x + 2, label_y))
            else:
                minor_lines += [(screen_x, self.region.bottom), (screen_x, self.region.top)]
        return minor_lines, major_lines, labels

    def _collect_horizontal_lines(self, spacing: float, major_interval: int):
        """Collect horizontal grid lines.

        Returns:
            (minor_lines, major_lines, labels); labels are (text, x, y) tuples
        """
        minor_lines: list[tuple[float, float]] = []
        major_lines: list[tuple[float, float]] = []
        labels: list[tuple[str, float, float]] = []

        j_min = math.floor(self.screen_to_physics_y(self.region.bottom) / spacing)
        j_max = math.ceil(self.screen_to_physics_y(self.region.top) / spacing)
        screen_x_axis = self.physics_to_screen_x(0)
        axis_visible = self.region.left <= screen_x_axis <= self.region.right

        for j in range(j_min, j_max + 1):
            y = j * spacing
            screen_y = self.physics_to_screen_y(y)
            if not (self.region.bottom <= screen_y <= self.region.top) or j == 0:
                continue
            if self._is_major(y, spacing, major_interval):
                major_lines += [(self.region.left, screen_y), (self.region.right, screen_y)]
                label_x = screen_x_axis + 4 if axis_visible else self.region.left + 4
                labels.append((format_number(y), label_x, screen_y + 2))
            else:
                minor_lines += [(self.region.left, screen_y), (self.region.right, screen_y)]
        return minor_lines, major_lines, labels

    # Helper to sample physics-space grid intersections for force field rendering
    def get_grid_sample_points(
        self, include_minor: bool = True, custom_spacing: float | None = None
    ) -> list[tuple[float, float]]:
        if self._grid_sample_points:
            return self._grid_sample_points
        if self.region.width <= 0 or self.region.height <= 0:
            return []

        spacing = (
            max(self._calculate_grid_spacing(1), custom_spacing)
            if custom_spacing is not None
            else self._calculate_grid_spacing(1)
        )
        major_interval = self._GRID_MAJOR_INTERVAL

        i_min = math.ceil(self.screen_to_physics_x(self.region.left) / spacing)
        i_max = math.floor(self.screen_to_physics_x(self.region.right) / spacing)
        j_min = math.ceil(self.screen_to_physics_y(self.region.bottom) / spacing)
        j_max = math.floor(self.screen_to_physics_y(self.region.top) / spacing)

        xs = [
            i * spacing
            for i in range(i_min, i_max + 1)
            if include_minor or i == 0 or self._is_major(i * spacing, spacing, major_interval)
        ]
        ys = [
            j * spacing
            for j in range(j_min, j_max + 1)
            if include_minor or j == 0 or self._is_major(j * spacing, spacing, major_interval)
        ]
        points = [(float(xv), float(yv)) for xv in xs for yv in ys]
        self._grid_sample_points = points
        return points
