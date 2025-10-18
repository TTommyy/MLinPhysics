import arcade


class ShapeRendererMixin:
    """Mixin for rendering different entity shapes (circles, rectangles, etc.)."""

    def _render_entity(self, render_data: dict) -> None:
        """Render a single entity based on its render data."""
        entity_type = render_data.get("type")

        if entity_type == "circle":
            self._render_circle(render_data)
        elif entity_type == "circle_static":
            self._render_circle_static(render_data)
        elif entity_type == "rectangle":
            self._render_rectangle(render_data)

    def _render_circle(self, data: dict) -> None:
        """Render a circle entity."""
        pos_x, pos_y = data["position"]
        radius = data["radius"]
        color = data["color"]

        screen_x = self.physics_to_screen_x(pos_x)
        screen_y = self.physics_to_screen_y(pos_y)
        screen_radius = radius * self.scale

        arcade.draw_circle_filled(screen_x, screen_y, screen_radius, color)
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

        left = screen_x - screen_width / 2
        right = screen_x + screen_width / 2
        bottom = screen_y - screen_height / 2
        top = screen_y + screen_height / 2

        arcade.draw_lrbt_rectangle_filled(left, right, bottom, top, color)
        arcade.draw_lrbt_rectangle_outline(
            left, right, bottom, top, arcade.color.BLACK, 2
        )
