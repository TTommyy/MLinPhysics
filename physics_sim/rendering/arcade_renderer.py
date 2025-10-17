import arcade

from physics_sim.core import Entity, LayoutRegion, Renderer


class ArcadeRenderer(Renderer):
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

    def render_entities(self, entities: list[Entity]) -> None:
        """Render all entities in the simulation."""
        for entity in entities:
            render_data = entity.get_render_data()
            self._render_entity(render_data)

    def _render_entity(self, render_data: dict) -> None:
        """Render a single entity based on its render data."""
        entity_type = render_data.get("type")

        if entity_type == "circle":
            self._render_circle(render_data)
        elif entity_type == "circle_static":
            self._render_circle_static(render_data)
        elif entity_type == "rectangle":
            self._render_rectangle(render_data)
        # TODO: Add support for other shapes
        # elif entity_type == "polygon":
        #     self._render_polygon(render_data)

    def _render_circle(self, data: dict) -> None:
        """Render a circle entity."""
        pos_x, pos_y = data["position"]
        radius = data["radius"]
        color = data["color"]

        screen_x = self.physics_to_screen_x(pos_x)
        screen_y = self.physics_to_screen_y(pos_y)
        screen_radius = radius * self.scale

        arcade.draw_circle_filled(screen_x, screen_y, screen_radius, color)

        # Optional: Draw outline for better visibility
        arcade.draw_circle_outline(
            screen_x, screen_y, screen_radius, arcade.color.BLACK, 2
        )

    def _render_circle_static(self, data: dict) -> None:
        """Render a static circle obstacle."""
        pos_x, pos_y = data["position"]
        radius = data["radius"]
        color = data["color"]

        screen_x = self.physics_to_screen_x(pos_x)
        screen_y = self.physics_to_screen_y(pos_y)
        screen_radius = radius * self.scale

        arcade.draw_circle_filled(screen_x, screen_y, screen_radius, color)
        arcade.draw_circle_outline(
            screen_x, screen_y, screen_radius, arcade.color.BLACK, 3
        )

    def _render_rectangle(self, data: dict) -> None:
        """Render a rectangle obstacle."""
        pos_x, pos_y = data["position"]
        width = data["width"]
        height = data["height"]
        color = data["color"]

        screen_x = self.physics_to_screen_x(pos_x)
        screen_y = self.physics_to_screen_y(pos_y)
        screen_width = width * self.scale
        screen_height = height * self.scale

        # Calculate edge coordinates from center position
        left = screen_x - screen_width / 2
        right = screen_x + screen_width / 2
        bottom = screen_y - screen_height / 2
        top = screen_y + screen_height / 2

        # Draw filled rectangle
        arcade.draw_lrbt_rectangle_filled(left, right, bottom, top, color)

        # Draw outline
        arcade.draw_lrbt_rectangle_outline(
            left, right, bottom, top, arcade.color.BLACK, 2
        )

    def render_grid(self, grid_spacing: float = 1.0) -> None:
        """Render coordinate grid with labels at fixed spacing."""
        if not self.show_grid:
            return

        grid_color = (200, 200, 200)
        label_color = arcade.color.DARK_GRAY
        axis_color = (150, 150, 150)

        screen_x_axis = self.physics_to_screen_x(0)
        screen_y_axis = self.physics_to_screen_y(0)

        # Collect grid line points
        vertical_lines = self._collect_grid_lines(True, grid_spacing, label_color)
        horizontal_lines = self._collect_grid_lines(False, grid_spacing, label_color)

        # Draw all grid lines
        if vertical_lines:
            arcade.draw_lines(vertical_lines, grid_color, 2)
        if horizontal_lines:
            arcade.draw_lines(horizontal_lines, grid_color, 2)

        # Draw axes
        axis_lines = [
            (screen_x_axis, self.region.bottom),
            (screen_x_axis, self.region.top),
            (self.region.left, screen_y_axis),
            (self.region.right, screen_y_axis),
        ]
        arcade.draw_lines(axis_lines, axis_color, 4)

        # Draw axis labels
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

    def render_ui(self, ui_elements: list) -> None:
        """Render UI elements (panels, buttons, etc.)."""
        # UI elements handle their own rendering in arcade
        pass

    def pause(self) -> None:
        """Pauses the simulation."""
        self._paused = True

    def is_paused(self) -> bool:
        """Returns True if the simulation is paused."""
        return self._paused

    def toggle_pause(self) -> None:
        """Toggles the pause state of the simulation."""
        self._paused = not self._paused
