import arcade.gui


class DisplayControls:
    """Widget group for display and simulation controls."""

    def __init__(self, button_width: int = 220):
        self.is_paused = False
        self.button_width = button_width

        self.on_grid_toggle = None
        self.on_pause_toggle = None

        self.layout = arcade.gui.UIBoxLayout(space_between=8, vertical=True)
        self._build()

    def _build(self):
        """Build widget layout."""
        # Section label
        label = arcade.gui.UILabel(
            text="Display Options",
            font_size=10,
            text_color=arcade.color.BLACK_LEATHER_JACKET,
        )
        self.layout.add(label)

        # Grid toggle
        self.grid_button = arcade.gui.UIFlatButton(
            text="Grid: ON",
            width=self.button_width,
            height=35,
        )
        self.grid_button.on_click = self._toggle_grid
        self.layout.add(self.grid_button)

        # Pause toggle
        self.pause_button = arcade.gui.UIFlatButton(
            text="Pause: OFF",
            width=self.button_width,
            height=35,
        )
        self.pause_button.on_click = self._toggle_pause
        self.layout.add(self.pause_button)

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

    def set_grid_enabled(self, enabled: bool):
        """Set grid display state."""
        self.grid_button.text = f"Grid: {'ON' if enabled else 'OFF'}"

    def set_pause_enabled(self, enabled: bool):
        """Set pause state programmatically."""
        self.is_paused = enabled
        self.pause_button.text = f"Pause: {'ON' if enabled else 'OFF'}"

    def get_layout(self) -> arcade.gui.UIBoxLayout:
        """Get the widget layout."""
        return self.layout


__all__: list[str] = ["DisplayControls"]
