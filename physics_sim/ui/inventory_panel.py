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

        # Text objects for performance (instead of draw_text)
        # Cache for entity text objects to avoid recreation
        self.entity_text_cache = {}
        self.debug_title_text = arcade.Text(
            "DEBUG INFO",
            self.panel_x + 15,
            self.screen_height - 25,
            arcade.color.DARK_RED,
            10,
            bold=True,
        )
        self.debug_fps_text = arcade.Text(
            "FPS: 0.0",
            self.panel_x + 20,
            self.screen_height - 43,
            arcade.color.BLACK,
            9,
        )
        self.debug_engine_text = arcade.Text(
            "Engine: Unknown",
            self.panel_x + 20,
            self.screen_height - 57,
            arcade.color.BLACK,
            9,
        )
        self.debug_entities_text = arcade.Text(
            "Entities: 0",
            self.panel_x + 20,
            self.screen_height - 71,
            arcade.color.BLACK,
            9,
        )
        self.title_text = arcade.Text(
            "ENTITY INVENTORY",
            self.panel_x + 15,
            self.screen_height - 30,
            arcade.color.BLACK,
            16,
            bold=True,
        )
        self.count_text = arcade.Text(
            "0 entities",
            self.panel_x + 15,
            self.screen_height - 55,
            arcade.color.DARK_GRAY,
            10,
        )

    def render(self, entities: list, fps: float = 0.0, engine_name: str = ""):
        """Render the inventory panel with entity data and debug info.

        Args:
            entities: List of entities to display
            fps: Current frames per second
            engine_name: Name of the physics engine
        """
        # Draw panel background
        arcade.draw_lrbt_rectangle_filled(
            self.panel_x, self.screen_width, 0, self.screen_height, (245, 245, 245)
        )

        # Draw left border
        arcade.draw_line(
            self.panel_x, 0, self.panel_x, self.screen_height, arcade.color.GRAY, 2
        )

        # Update and draw debug info section
        if fps > 0:
            debug_y = self.screen_height - 25

            # Update debug text content
            self.debug_fps_text.text = f"FPS: {fps:.1f}"
            self.debug_engine_text.text = f"Engine: {engine_name}"
            entity_count = len([e for e in entities if isinstance(e, PhysicalEntity)])
            self.debug_entities_text.text = f"Entities: {entity_count}"

            # Update positions
            self.debug_title_text.y = debug_y
            self.debug_fps_text.y = debug_y - 18
            self.debug_engine_text.y = debug_y - 32
            self.debug_entities_text.y = debug_y - 46

            # Draw debug texts
            self.debug_title_text.draw()
            self.debug_fps_text.draw()
            self.debug_engine_text.draw()
            self.debug_entities_text.draw()

            # Separator line
            debug_y -= 51
            arcade.draw_line(
                self.panel_x + 10,
                debug_y,
                self.panel_x + self.panel_width - 15,
                debug_y,
                (200, 200, 200),
                1,
            )

        # Calculate title position based on whether debug info is shown
        title_y = self.screen_height - 30
        if fps > 0:
            # Adjust title position if debug info is shown
            title_y = debug_y - 15

        # Update and draw title
        self.title_text.y = title_y
        self.title_text.draw()

        # Update and draw count
        entity_count = len([e for e in entities if isinstance(e, PhysicalEntity)])
        self.count_text.text = f"{entity_count} entities"
        self.count_text.y = title_y - 25
        self.count_text.draw()

        # Draw entity data
        entity_start_y = title_y - 45  # Start entities below the count
        y_offset = entity_start_y + self.scroll_offset
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
        total_height = abs(y_offset - entity_start_y)
        self.max_scroll = max(
            0, total_height - (self.screen_height - entity_start_y) + 50
        )

        # Clean up Text objects for entities that no longer exist
        current_entity_ids = {
            entity.id for entity in entities if isinstance(entity, PhysicalEntity)
        }
        stale_ids = set(self.entity_text_cache.keys()) - current_entity_ids
        for stale_id in stale_ids:
            del self.entity_text_cache[stale_id]

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

    def _get_entity_text_objects(self, entity_id: str):
        """Get or create Text objects for an entity."""
        if entity_id not in self.entity_text_cache:
            self.entity_text_cache[entity_id] = {
                "header": arcade.Text("", 0, 0, arcade.color.DARK_BLUE, 11, bold=True),
                "id_label": arcade.Text("ID:", 0, 0, arcade.color.DARK_GRAY, 9),
                "id_value": arcade.Text("", 0, 0, arcade.color.BLACK, 9),
                "mass_label": arcade.Text("Mass:", 0, 0, arcade.color.DARK_GRAY, 9),
                "mass_value": arcade.Text("", 0, 0, arcade.color.BLACK, 9),
                "pos_label": arcade.Text("Position:", 0, 0, arcade.color.DARK_GRAY, 9),
                "pos_value": arcade.Text("", 0, 0, arcade.color.BLACK, 9),
                "vel_label": arcade.Text("Velocity:", 0, 0, arcade.color.DARK_GRAY, 9),
                "vel_value": arcade.Text("", 0, 0, arcade.color.BLACK, 9),
                "speed_label": arcade.Text("Speed:", 0, 0, arcade.color.DARK_GRAY, 9),
                "speed_value": arcade.Text("", 0, 0, arcade.color.BLACK, 9),
                "forces_header": arcade.Text(
                    "Forces:", 0, 0, arcade.color.DARK_RED, 9, bold=True
                ),
                "force_texts": [],  # Will be created dynamically
            }
        return self.entity_text_cache[entity_id]

    def _render_entity_data(
        self, entity: PhysicalEntity, y_offset: float, line_height: int
    ) -> float:
        """Render data for a single entity using Text objects.

        Args:
            entity: Entity to render
            y_offset: Current Y position
            line_height: Height per line

        Returns:
            Updated Y offset
        """
        data = entity.get_physics_data()
        x = self.panel_x + 15
        entity_id = data["id"]

        # Get Text objects for this entity
        texts = self._get_entity_text_objects(entity_id)

        # Entity header with background
        header_y = y_offset
        arcade.draw_lrbt_rectangle_filled(
            self.panel_x + 15,
            self.panel_x + self.panel_width - 15,
            header_y - line_height,
            header_y + 4,
            (230, 230, 230),
        )

        # Update and draw header
        texts["header"].text = f"{data.get('type', 'Entity')}"
        texts["header"].x = x + 5
        texts["header"].y = y_offset
        texts["header"].draw()
        y_offset -= line_height + 5

        # Update and draw basic properties
        texts["id_label"].x = x + 5
        texts["id_label"].y = y_offset
        texts["id_label"].draw()

        texts["id_value"].text = f"{data['id'][:12]}..."
        texts["id_value"].x = x + 80
        texts["id_value"].y = y_offset
        texts["id_value"].draw()
        y_offset -= line_height

        texts["mass_label"].x = x + 5
        texts["mass_label"].y = y_offset
        texts["mass_label"].draw()

        texts["mass_value"].text = f"{data['mass']:.2f} kg"
        texts["mass_value"].x = x + 80
        texts["mass_value"].y = y_offset
        texts["mass_value"].draw()
        y_offset -= line_height

        texts["pos_label"].x = x + 5
        texts["pos_label"].y = y_offset
        texts["pos_label"].draw()

        texts[
            "pos_value"
        ].text = f"({data['position'][0]:.1f}, {data['position'][1]:.1f})"
        texts["pos_value"].x = x + 80
        texts["pos_value"].y = y_offset
        texts["pos_value"].draw()
        y_offset -= line_height

        texts["vel_label"].x = x + 5
        texts["vel_label"].y = y_offset
        texts["vel_label"].draw()

        texts[
            "vel_value"
        ].text = f"({data['velocity'][0]:.1f}, {data['velocity'][1]:.1f})"
        texts["vel_value"].x = x + 80
        texts["vel_value"].y = y_offset
        texts["vel_value"].draw()
        y_offset -= line_height

        texts["speed_label"].x = x + 5
        texts["speed_label"].y = y_offset
        texts["speed_label"].draw()

        texts["speed_value"].text = f"{data['speed']:.2f} m/s"
        texts["speed_value"].x = x + 80
        texts["speed_value"].y = y_offset
        texts["speed_value"].draw()
        y_offset -= line_height

        # Forces
        forces = data.get("applied_forces", [])
        if forces:
            y_offset -= 3
            texts["forces_header"].x = x + 5
            texts["forces_header"].y = y_offset
            texts["forces_header"].draw()
            y_offset -= line_height

            # Ensure we have enough force text objects
            while len(texts["force_texts"]) < len(forces):
                texts["force_texts"].append(
                    arcade.Text("", 0, 0, arcade.color.DARK_GRAY, 8)
                )

            for i, force_data in enumerate(forces):
                force_text = f"• {force_data['name']}: {force_data['magnitude']:.1f} N"
                texts["force_texts"][i].text = force_text
                texts["force_texts"][i].x = x + 10
                texts["force_texts"][i].y = y_offset
                texts["force_texts"][i].draw()
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
