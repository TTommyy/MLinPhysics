import arcade
import arcade.gui

from physics_sim.core import LayoutRegion
from physics_sim.ui.sections.base_section import BaseSection


class InventoryPanelSection(BaseSection):
    """Right panel section displaying entity inventory with pagination."""

    def __init__(self, region: LayoutRegion):
        super().__init__(region, background_color=arcade.uicolor.GREEN_GREEN_SEA)

        self.panel_width = region.width
        self.panel_x = region.x

        # Pagination state
        self.current_page = 0
        self.items_per_page = 5
        self.total_pages = 0

        # UI Manager for buttons
        self.ui_manager = arcade.gui.UIManager()

        # Text cache for performance
        self.entity_text_cache = {}

        # Cache for inventory data and rendered entities
        self._cached_inventory_data: list[dict] = []
        self._cached_page_entities: list[dict] = []

        self._create_text_objects()
        self._create_pagination_ui()

    def _create_text_objects(self):
        """Create reusable text objects."""
        self.page_indicator_text = arcade.Text(
            "Page 1/1",
            self.region.center_x,
            self.region.bottom + 50,
            arcade.color.BLACK,
            10,
            anchor_x="center",
        )

    def _create_pagination_ui(self):
        """Create pagination buttons."""
        button_width = 80
        button_height = 30
        button_margin = 20

        # Previous button
        self.prev_button = arcade.gui.UIFlatButton(
            text="Previous",
            width=button_width,
            height=button_height,
            x=self.region.left + button_margin,
            y=self.region.bottom + 10,
        )
        self.prev_button.on_click = self._on_prev_page

        # Next button
        self.next_button = arcade.gui.UIFlatButton(
            text="Next",
            width=button_width,
            height=button_height,
            x=self.region.right - button_width - button_margin,
            y=self.region.bottom + 10,
        )
        self.next_button.on_click = self._on_next_page

        # Add buttons directly to UI manager
        self.ui_manager.add(self.prev_button)
        self.ui_manager.add(self.next_button)

    def enable(self):
        """Enable UI interaction."""
        self.ui_manager.enable()

    def disable(self):
        """Disable UI interaction."""
        self.ui_manager.disable()

    def _on_prev_page(self, event):
        """Handle previous page button click."""
        if self.current_page > 0:
            self.current_page -= 1
            self._update_page_from_cache()

    def _on_next_page(self, event):
        """Handle next page button click."""
        if self.current_page < self.total_pages - 1:
            self.current_page += 1
            self._update_page_from_cache()

    def _update_page_from_cache(self):
        """Update the displayed page entities from cached data."""
        if not self._cached_inventory_data:
            return

        # Recalculate which entities to show for current page
        start_idx = self.current_page * self.items_per_page
        end_idx = min(start_idx + self.items_per_page, len(self._cached_inventory_data))
        self._cached_page_entities = self._cached_inventory_data[start_idx:end_idx]

    def on_draw(self):
        """Draw the inventory panel section."""
        self.draw_background()
        self.draw_border(sides="left")

        # Draw cached inventory data
        self._draw_cached_inventory()

        # Draw UI elements
        self.ui_manager.draw()

    def render_with_data(self, inventory_data: list[dict]):
        """Update cached inventory data.

        Args:
            inventory_data: List of entity data dicts from engine
        """
        # Cache the new inventory data
        self._cached_inventory_data = inventory_data

        # Update pagination
        entity_count = len(inventory_data)
        self.total_pages = max(
            1, (entity_count + self.items_per_page - 1) // self.items_per_page
        )
        self.current_page = min(self.current_page, self.total_pages - 1)

        # Calculate which entities to show
        start_idx = self.current_page * self.items_per_page
        end_idx = min(start_idx + self.items_per_page, entity_count)
        self._cached_page_entities = inventory_data[start_idx:end_idx]

        # Clean up text cache for entities not on current page
        current_page_ids = {data["id"] for data in self._cached_page_entities}
        stale_ids = set(self.entity_text_cache.keys()) - current_page_ids
        for stale_id in list(stale_ids)[:10]:  # Clean up 10 per frame to avoid lag
            del self.entity_text_cache[stale_id]

    def _draw_cached_inventory(self):
        """Draw the cached inventory data."""
        if not self._cached_inventory_data:
            return

        # Update page indicator
        self.page_indicator_text.text = (
            f"Page {self.current_page + 1}/{self.total_pages}"
        )
        self.page_indicator_text.draw()

        # Draw entities for current page
        entity_start_y = self.region.top - 80
        y_offset = entity_start_y
        card_spacing = 15

        for data in self._cached_page_entities:
            y_offset = self._render_entity_card(data, y_offset)
            y_offset -= card_spacing

        # Update button states
        self.prev_button.disabled = self.current_page == 0
        self.next_button.disabled = self.current_page >= self.total_pages - 1

    def _render_entity_card(self, data: dict, y_offset: float) -> float:
        """Render a single entity as a card.

        Args:
            data: Entity data dict from engine
            y_offset: Current Y position

        Returns:
            Updated Y offset
        """
        x = self.panel_x + 15
        card_width = self.panel_width - 30
        line_height = 14
        padding = 12

        entity_id = data["id"]
        texts = self._get_entity_text_objects(entity_id)

        # Calculate card height
        base_lines = 5  # Type, ID, Mass, Position, Velocity
        force_lines = len(data.get("applied_forces", []))
        card_lines = base_lines + (1 if force_lines > 0 else 0) + force_lines
        card_height = (card_lines * line_height) + (2 * padding)

        # Draw card background with border
        card_top = y_offset
        card_bottom = y_offset - card_height

        arcade.draw_lrbt_rectangle_filled(
            x,
            x + card_width,
            card_bottom,
            card_top,
            arcade.uicolor.WHITE_SILVER,
        )
        arcade.draw_lrbt_rectangle_outline(
            x,
            x + card_width,
            card_bottom,
            card_top,
            arcade.uicolor.GRAY_ASBESTOS,
            2,
        )

        # Start rendering content
        content_y = card_top - padding - 2

        # Entity type header
        texts["header"].text = f"{data.get('type', 'Entity')}"
        texts["header"].x = x + padding
        texts["header"].y = content_y
        texts["header"].draw()
        content_y -= line_height

        # ID
        texts["id_label"].x = x + padding
        texts["id_label"].y = content_y
        texts["id_label"].draw()
        texts["id_value"].text = f"{data['id'][:10]}"
        texts["id_value"].x = x + 60
        texts["id_value"].y = content_y
        texts["id_value"].draw()
        content_y -= line_height

        # Mass
        texts["mass_label"].x = x + padding
        texts["mass_label"].y = content_y
        texts["mass_label"].draw()
        texts["mass_value"].text = f"{data['mass']:.2f} kg"
        texts["mass_value"].x = x + 60
        texts["mass_value"].y = content_y
        texts["mass_value"].draw()
        content_y -= line_height

        # Position
        texts["pos_label"].x = x + padding
        texts["pos_label"].y = content_y
        texts["pos_label"].draw()
        texts[
            "pos_value"
        ].text = f"({data['position'][0]:.1f}, {data['position'][1]:.1f})"
        texts["pos_value"].x = x + 60
        texts["pos_value"].y = content_y
        texts["pos_value"].draw()
        content_y -= line_height

        texts["acc_label"].x = x + padding
        texts["acc_label"].y = content_y
        texts["acc_label"].draw()
        texts[
            "acc_value"
        ].text = f"({data['acceleration'][0]:.1f}, {data['acceleration'][1]:.1f})"
        texts["acc_value"].x = x + 60
        texts["acc_value"].y = content_y
        texts["acc_value"].draw()
        content_y -= line_height

        # Velocity & Speed
        texts["vel_label"].x = x + padding
        texts["vel_label"].y = content_y
        texts["vel_label"].draw()
        vel_text = f"({data['velocity'][0]:.1f}, {data['velocity'][1]:.1f}) [{data['speed']:.1f} m/s]"
        texts["vel_value"].text = vel_text
        texts["vel_value"].x = x + 60
        texts["vel_value"].y = content_y
        texts["vel_value"].draw()
        content_y -= line_height

        # Forces
        forces = data.get("applied_forces", [])
        if forces:
            texts["forces_header"].x = x + padding
            texts["forces_header"].y = content_y
            texts["forces_header"].draw()
            content_y -= line_height

            # Ensure we have enough force text objects
            while len(texts["force_texts"]) < len(forces):
                texts["force_texts"].append(
                    arcade.Text("", 0, 0, arcade.color.DARK_CYAN, 8)
                )

            for i, force_data in enumerate(forces):
                force_text = f"• {force_data['name']}: {force_data['magnitude']:.1f} N"
                texts["force_texts"][i].text = force_text
                texts["force_texts"][i].x = x + padding + 10
                texts["force_texts"][i].y = content_y
                texts["force_texts"][i].draw()
                content_y -= line_height

        return card_bottom

    def _get_entity_text_objects(self, entity_id: str):
        """Get or create text objects for an entity."""
        if entity_id not in self.entity_text_cache:
            self.entity_text_cache[entity_id] = {
                "header": arcade.Text(
                    "", 0, 0, arcade.uicolor.BLUE_PETER_RIVER, 11, bold=True
                ),
                "id_label": arcade.Text("ID:", 5, 0, arcade.color.DARK_CYAN, 9),
                "id_value": arcade.Text("", 0, 0, arcade.color.BLACK, 9),
                "mass_label": arcade.Text("Mass:", 5, 0, arcade.color.DARK_CYAN, 9),
                "mass_value": arcade.Text("", 0, 0, arcade.color.BLACK, 9),
                "pos_label": arcade.Text("Pos:", 5, 0, arcade.color.DARK_CYAN, 9),
                "pos_value": arcade.Text("", 0, 0, arcade.color.BLACK, 9),
                "acc_label": arcade.Text("Acc:", 5, 0, arcade.color.DARK_CYAN, 9),
                "acc_value": arcade.Text("", 0, 0, arcade.color.BLACK, 9),
                "vel_label": arcade.Text("Vel:", 5, 0, arcade.color.DARK_CYAN, 9),
                "vel_value": arcade.Text("", 0, 0, arcade.color.BLACK, 9),
                "forces_header": arcade.Text(
                    "Forces:", 0, 0, arcade.uicolor.RED_ALIZARIN, 9, bold=True
                ),
                "force_texts": [],
            }
        return self.entity_text_cache[entity_id]

    def on_mouse_scroll(self, x: int, y: int, scroll_x: int, scroll_y: int):
        """Handle mouse scroll - no-op now that we use pagination."""
        pass

    def on_update(self, delta_time: float):
        """Update section."""
        pass


__all__: list[str] = ["InventoryPanelSection"]
