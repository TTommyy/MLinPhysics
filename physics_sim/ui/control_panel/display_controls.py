from physics_sim.ui.widgets import (
    BUTTON_ACTIVE_COLOR,
    BUTTON_COLOR,
    FlatButton,
    TextLabel,
    vbox,
)


def _state_color(enabled: bool):
    return BUTTON_ACTIVE_COLOR if enabled else BUTTON_COLOR


class DisplayControls:
    """Widget group for display and simulation controls."""

    def __init__(self, button_width: int | None = None):
        self.is_paused = False
        self.button_width = button_width

        self.on_grid_toggle = None
        self.on_pause_toggle = None
        self.on_forces_toggle = None
        self.on_edit_entity = None

        self.layout = vbox(spacing=6)
        self._build()

    def _build(self):
        """Build widget layout."""
        self.layout.add_widget(TextLabel("Display Options", font_size=13, bold=True))

        self.grid_button = FlatButton("Grid: ON", color=_state_color(True))
        self.grid_button.bind(on_release=self._toggle_grid)
        self.layout.add_widget(self.grid_button)

        self.forces_button = FlatButton("Forces: OFF", color=_state_color(False))
        self.forces_button.bind(on_release=self._toggle_forces)
        self.layout.add_widget(self.forces_button)

        self.pause_button = FlatButton("Pause: OFF", color=_state_color(False))
        self.pause_button.bind(on_release=self._toggle_pause)
        self.layout.add_widget(self.pause_button)

    def _toggle_grid(self, *_):
        """Toggle grid display."""
        if self.on_grid_toggle:
            self.on_grid_toggle()

    def _toggle_pause(self, *_):
        """Toggle pause state."""
        self.set_pause_enabled(not self.is_paused)
        if self.on_pause_toggle:
            self.on_pause_toggle()

    def _toggle_forces(self, *_):
        """Toggle forces overlay display."""
        if self.on_forces_toggle:
            self.on_forces_toggle()

    def set_grid_enabled(self, enabled: bool):
        """Set grid display state."""
        self.grid_button.text = f"Grid: {'ON' if enabled else 'OFF'}"
        self.grid_button.set_color(_state_color(enabled))

    def set_pause_enabled(self, enabled: bool):
        """Set pause state programmatically."""
        self.is_paused = enabled
        self.pause_button.text = f"Pause: {'ON' if enabled else 'OFF'}"
        self.pause_button.set_color(_state_color(enabled))

    def set_forces_enabled(self, enabled: bool):
        """Set forces overlay state."""
        self.forces_button.text = f"Forces: {'ON' if enabled else 'OFF'}"
        self.forces_button.set_color(_state_color(enabled))

    def get_layout(self):
        """Get the widget layout."""
        return self.layout


__all__: list[str] = ["DisplayControls"]
