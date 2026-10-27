from physics_sim.ui.widgets import (
    BUTTON_ACTIVE_COLOR,
    BUTTON_COLOR,
    FlatButton,
    TextLabel,
    vbox,
)


class PlacementControls:
    """Widget group for entity placement controls."""

    def __init__(self, button_width: int | None = None):
        self.add_mode = False
        self.available_entity_types: list[type] = []
        self.selected_entity_type_index = 0
        self.button_width = button_width

        self.on_add_mode_toggle = None
        self.on_object_type_change = None

        self.layout = vbox(spacing=6)
        self._build()

    def _build(self):
        """Build widget layout."""
        self.layout.add_widget(TextLabel("Object Placement", font_size=13, bold=True))

        self.add_mode_button = FlatButton("Add Mode: OFF")
        self.add_mode_button.bind(on_release=self._toggle_add_mode)
        self.layout.add_widget(self.add_mode_button)

        self.object_type_button = FlatButton("Type: (no engine)")
        self.object_type_button.bind(on_release=self._cycle_object_type)
        self.layout.add_widget(self.object_type_button)

    def _refresh_add_mode_button(self):
        self.add_mode_button.text = f"Add Mode: {'ON' if self.add_mode else 'OFF'}"
        self.add_mode_button.set_color(
            BUTTON_ACTIVE_COLOR if self.add_mode else BUTTON_COLOR
        )

    def _toggle_add_mode(self, *_):
        """Toggle add mode on/off."""
        self.add_mode = not self.add_mode
        self._refresh_add_mode_button()
        if self.on_add_mode_toggle:
            self.on_add_mode_toggle(self.add_mode)

    def _cycle_object_type(self, *_):
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
        """Set add mode programmatically (does not fire callbacks)."""
        self.add_mode = enabled
        self._refresh_add_mode_button()

    def set_available_entity_types(self, entity_types: list[type]):
        """Set available entity types."""
        self.available_entity_types = list(entity_types)
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

    def get_layout(self):
        """Get the widget layout."""
        return self.layout


__all__: list[str] = ["PlacementControls"]
