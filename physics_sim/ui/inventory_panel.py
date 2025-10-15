import arcade
import arcade.gui

from physics_sim.core import PhysicalEntity


class InventoryPanel:
    """Fixed right panel displaying physics data for all entities in the simulation.

    Shows detailed information including:
    - Entity ID and type
    - Mass, position, velocity, speed
    - Active forces and their magnitudes
    """

    def __init__(self, screen_width: int, screen_height: int, panel_width: int = 350):
        """
        Args:
            screen_width: Window width in pixels
            screen_height: Window height in pixels
            panel_width: Width of the inventory panel
        """
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.panel_width = panel_width
        self.panel_x = screen_width - panel_width

        # Scroll offset
        self.scroll_offset = 0
        self.max_scroll = 0

        # UI Manager
        self.ui_manager = arcade.gui.UIManager()

    def render(self, entities: list):
        """Render the inventory panel with entity data.

        Args:
            entities: List of entities to display
        """
        # Draw panel background
        arcade.draw_lrbt_rectangle_filled(
            self.panel_x, self.screen_width, 0, self.screen_height, (245, 245, 245)
        )

        # Draw left border
        arcade.draw_line(
            self.panel_x, 0, self.panel_x, self.screen_height, arcade.color.GRAY, 2
        )

        # Draw title
        arcade.draw_text(
            "ENTITY INVENTORY",
            self.panel_x + 15,
            self.screen_height - 30,
            arcade.color.BLACK,
            16,
            bold=True,
        )

        # Draw count
        arcade.draw_text(
            f"{len([e for e in entities if isinstance(e, PhysicalEntity)])} entities",
            self.panel_x + 15,
            self.screen_height - 55,
            arcade.color.DARK_GRAY,
            10,
        )

        # Draw entity data
        y_offset = self.screen_height - 75 + self.scroll_offset
        line_height = 16

        for entity in entities:
            if not isinstance(entity, PhysicalEntity):
                continue

            # Skip if scrolled out of view
            if y_offset < -100 or y_offset > self.screen_height:
                y_offset -= self._get_entity_display_height(entity, line_height)
                continue

            y_offset = self._render_entity_data(entity, y_offset, line_height)

        # Calculate max scroll
        total_height = abs(y_offset - (self.screen_height - 75))
        self.max_scroll = max(0, total_height - self.screen_height + 100)

    def _get_entity_display_height(
        self, entity: PhysicalEntity, line_height: int
    ) -> int:
        """Calculate display height for an entity."""
        data = entity.get_physics_data()
        base_lines = (
            7  # ID, type, mass, position, velocity, acceleration, forces header
        )
        force_lines = len(data.get("applied_forces", []))
        return (base_lines + force_lines + 1) * line_height

    def _render_entity_data(
        self, entity: PhysicalEntity, y_offset: float, line_height: int
    ) -> float:
        """Render data for a single entity.

        Args:
            entity: Entity to render
            y_offset: Current Y position
            line_height: Height per line

        Returns:
            Updated Y offset
        """
        data = entity.get_physics_data()
        x = self.panel_x + 15

        # Entity header with background
        header_y = y_offset
        arcade.draw_lrbt_rectangle_filled(
            self.panel_x + 15,
            self.panel_x + self.panel_width - 15,
            header_y - line_height,
            header_y + 4,
            (230, 230, 230),
        )

        arcade.draw_text(
            f"{data.get('type', 'Entity')}",
            x + 5,
            y_offset,
            arcade.color.DARK_BLUE,
            11,
            bold=True,
        )
        y_offset -= line_height + 5

        # Basic properties
        props = [
            ("ID", f"{data['id'][:12]}..."),
            ("Mass", f"{data['mass']:.2f} kg"),
            ("Position", f"({data['position'][0]:.1f}, {data['position'][1]:.1f})"),
            ("Velocity", f"({data['velocity'][0]:.1f}, {data['velocity'][1]:.1f})"),
            ("Speed", f"{data['speed']:.2f} m/s"),
        ]

        for label, value in props:
            arcade.draw_text(
                f"{label}:",
                x + 5,
                y_offset,
                arcade.color.DARK_GRAY,
                9,
            )
            arcade.draw_text(
                value,
                x + 80,
                y_offset,
                arcade.color.BLACK,
                9,
            )
            y_offset -= line_height

        # Forces
        forces = data.get("applied_forces", [])
        if forces:
            y_offset -= 3
            arcade.draw_text(
                "Forces:",
                x + 5,
                y_offset,
                arcade.color.DARK_RED,
                9,
                bold=True,
            )
            y_offset -= line_height

            for force_data in forces:
                force_text = f"• {force_data['name']}: {force_data['magnitude']:.1f} N"
                arcade.draw_text(
                    force_text,
                    x + 10,
                    y_offset,
                    arcade.color.DARK_GRAY,
                    8,
                )
                y_offset -= line_height

        # Separator line
        y_offset -= 8
        arcade.draw_line(
            x,
            y_offset,
            self.panel_x + self.panel_width - 15,
            y_offset,
            (220, 220, 220),
            1,
        )
        y_offset -= 8

        return y_offset

    def on_mouse_scroll(self, x: int, y: int, scroll_x: int, scroll_y: int):
        """Handle mouse scroll for panel scrolling.

        Args:
            x: Mouse X position
            y: Mouse Y position
            scroll_x: Scroll amount X
            scroll_y: Scroll amount Y
        """
        # Check if mouse is over the panel
        if x >= self.panel_x:
            self.scroll_offset += scroll_y * 20
            # Clamp scroll
            self.scroll_offset = max(-self.max_scroll, min(0, self.scroll_offset))
