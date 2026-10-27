from kivy.metrics import dp

from physics_sim.core import LayoutRegion
from physics_sim.ui.control_panel import (
    DisplayControls,
    EntityEditorPanel,
    PlacementControls,
    StatusDisplay,
)
from physics_sim.ui.sections.base_section import BaseSection
from physics_sim.ui.widgets import Panel, TextLabel, VerticalScroll

SPLIT_PCT = 0.5

CONTROLS_BG = (176, 196, 222)  # light steel blue
EDITOR_BG = (245, 245, 245)  # white smoke


class ControlPanelSection(BaseSection):
    """Left control panel: controls (top) and entity editor (bottom).

    Both halves are scrollable so all widgets stay reachable regardless of
    the window size and never overlap each other.
    """

    def __init__(self, control_region: LayoutRegion | None = None, **kwargs):
        super().__init__(control_region, background_color=EDITOR_BG, **kwargs)
        self.orientation = "vertical"

        self.placement_controls = PlacementControls()
        self.display_controls = DisplayControls()
        self.status_display = StatusDisplay()
        self.entity_editor = EntityEditorPanel()

        # --- Controls (top half)
        self.controls_panel = Panel(
            background_color=CONTROLS_BG,
            border_color=(120, 120, 120),
            orientation="vertical",
            size_hint_y=SPLIT_PCT,
        )
        self.controls_scroll = VerticalScroll(spacing=8, padding=[dp(10), dp(8)])
        content = self.controls_scroll.content
        content.add_widget(TextLabel("CONTROLS", font_size=17, bold=True))
        content.add_widget(self.display_controls.get_layout())
        content.add_widget(self.status_display.get_layout())
        content.add_widget(self.placement_controls.get_layout())
        self.controls_panel.add_widget(self.controls_scroll)

        # --- Entity editor (bottom half)
        self.editor_panel = Panel(
            background_color=EDITOR_BG,
            border_color=(120, 120, 120),
            orientation="vertical",
            size_hint_y=1 - SPLIT_PCT,
        )
        self.editor_scroll = VerticalScroll(spacing=6, padding=[dp(10), dp(8)])
        self.editor_scroll.content.add_widget(
            TextLabel("ENTITY EDITOR", font_size=17, bold=True)
        )
        self.editor_scroll.content.add_widget(self.entity_editor.get_layout())
        self.editor_panel.add_widget(self.editor_scroll)

        self.add_widget(self.controls_panel)
        self.add_widget(self.editor_panel)

    def update_status(self, add_mode: bool | None = None, paused: bool | None = None):
        """Refresh the status/mode indicator."""
        if add_mode is None:
            add_mode = self.placement_controls.add_mode
        if paused is None:
            paused = self.display_controls.is_paused
        self.status_display.set_mode(add_mode, paused)

    def set_forces_toggle_handler(self, handler):
        self.display_controls.on_forces_toggle = handler

    def on_draw(self):
        """Kept for API compatibility (Kivy widgets draw themselves)."""
        pass


__all__: list[str] = ["ControlPanelSection"]
