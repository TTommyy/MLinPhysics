import arcade.gui


class DisplayControls:
    """Widget group for display and simulation controls."""

    def __init__(self):
        self.is_paused = False
        self.entity_selected = False

        self.on_grid_toggle = None
        self.on_pause_toggle = None
        self.on_edit_entity = None

        self.layout = arcade.gui.UIBoxLayout(space_between=8, vertical=True)
        self._build()

    def _build(self):
        """Build widget layout."""
        # Section label
        label = arcade.gui.UILabel(
            text="Display Options",
            font_size=10,
            text_color=arcade.color.DARK_GRAY,
        )
        self.layout.add(label)

        # Grid toggle
        self.grid_button = arcade.gui.UIFlatButton(
            text="Grid: ON",
            width=220,
            height=35,
        )
        self.grid_button.on_click = self._toggle_grid
        self.layout.add(self.grid_button)

        # Pause toggle
        self.pause_button = arcade.gui.UIFlatButton(
            text="Pause: OFF",
            width=220,
            height=35,
        )
        self.pause_button.on_click = self._toggle_pause
        self.layout.add(self.pause_button)

        # Edit entity button
        self.edit_button = arcade.gui.UIFlatButton(
            text="Edit Entity",
            width=220,
            height=35,
        )
        self.edit_button.on_click = self._on_edit_entity_button
        self.edit_button.disabled = True
        self.layout.add(self.edit_button)

    def _toggle_grid(self, event):
        """Toggle grid display."""
        if self.on_grid_toggle:
            self.on_grid_toggle()

    def _toggle_pause(self, event):
        """Toggle pause state."""
        self.is_paused = not self.is_paused
        self.pause_button.text = f"Pause: {'ON' if self.is_paused else 'OFF'}"
        if self.on_pause_toggle:
            self.on_pause_toggle()

    def _on_edit_entity_button(self, event):
        """Handle edit entity button click."""
        if self.on_edit_entity:
            self.on_edit_entity()

    def set_grid_enabled(self, enabled: bool):
        """Set grid display state."""
        self.grid_button.text = f"Grid: {'ON' if enabled else 'OFF'}"

    def set_pause_enabled(self, enabled: bool):
        """Set pause state programmatically."""
        self.is_paused = enabled
        self.pause_button.text = f"Pause: {'ON' if enabled else 'OFF'}"

    def set_entity_selected(self, selected: bool, entity_name: str = "Entity"):
        """Set entity selection state and update edit button."""
        self.entity_selected = selected
        self.edit_button.disabled = not (selected and self.is_paused)
        if selected:
            self.edit_button.text = f"Edit {entity_name}"
        else:
            self.edit_button.text = "Edit Entity"
            self.edit_button.disabled = True

    def update_edit_button_availability(self):
        """Update edit button availability based on pause and selection state."""
        self.edit_button.disabled = not (self.entity_selected and self.is_paused)

    def get_layout(self) -> arcade.gui.UIBoxLayout:
        """Get the widget layout."""
        return self.layout


__all__: list[str] = ["DisplayControls"]
