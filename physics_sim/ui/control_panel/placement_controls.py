import arcade.gui


class PlacementControls:
    """Widget group for entity placement controls."""

    def __init__(self):
        self.add_mode = False
        self.available_entity_types: list[type] = []
        self.selected_entity_type_index = 0

        self.on_add_mode_toggle = None
        self.on_object_type_change = None

        self.layout = arcade.gui.UIBoxLayout(space_between=8, vertical=True)
        self._build()

    def _build(self):
        """Build widget layout."""
        # Section label
        label = arcade.gui.UILabel(
            text="Object Placement",
            font_size=10,
            text_color=arcade.color.DARK_GRAY,
        )
        self.layout.add(label)

        # Add mode toggle
        self.add_mode_button = arcade.gui.UIFlatButton(
            text="Add Mode: OFF",
            width=220,
            height=35,
        )
        self.add_mode_button.on_click = self._toggle_add_mode
        self.layout.add(self.add_mode_button)

        # Object type selector
        self.object_type_button = arcade.gui.UIFlatButton(
            text="Type: (no engine)",
            width=220,
            height=35,
        )
        self.object_type_button.on_click = self._cycle_object_type
        self.layout.add(self.object_type_button)

    def _toggle_add_mode(self, event):
        """Toggle add mode on/off."""
        self.add_mode = not self.add_mode
        self.add_mode_button.text = f"Add Mode: {'ON' if self.add_mode else 'OFF'}"
        if self.on_add_mode_toggle:
            self.on_add_mode_toggle(self.add_mode)

    def _cycle_object_type(self, event):
        """Cycle through available entity types."""
        if not self.available_entity_types:
            return

        self.selected_entity_type_index = (self.selected_entity_type_index + 1) % len(
            self.available_entity_types
        )
        entity_class = self.available_entity_types[self.selected_entity_type_index]
        self.object_type_button.text = f"Type: {entity_class.__name__}"
        if self.on_object_type_change:
            self.on_object_type_change(entity_class)

    def set_add_mode(self, enabled: bool):
        """Set add mode programmatically."""
        if self.add_mode != enabled:
            self.add_mode = enabled
            self.add_mode_button.text = f"Add Mode: {'ON' if self.add_mode else 'OFF'}"

    def set_available_entity_types(self, entity_types: list[type]):
        """Set available entity types."""
        self.available_entity_types = entity_types
        self.selected_entity_type_index = 0
        if entity_types:
            self.object_type_button.text = f"Type: {entity_types[0].__name__}"
        else:
            self.object_type_button.text = "Type: (no types)"

    def get_selected_entity_type(self) -> type | None:
        """Get currently selected entity type."""
        if self.available_entity_types:
            return self.available_entity_types[self.selected_entity_type_index]
        return None

    def cycle_type(self):
        """Cycle to next entity type (for keyboard shortcut)."""
        self._cycle_object_type(None)

    def get_layout(self) -> arcade.gui.UIBoxLayout:
        """Get the widget layout."""
        return self.layout


__all__: list[str] = ["PlacementControls"]
