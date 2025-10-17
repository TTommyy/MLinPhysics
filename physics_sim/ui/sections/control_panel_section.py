import arcade
import arcade.gui

from physics_sim.core import LayoutRegion
from physics_sim.ui.control_panel import (
    DisplayControls,
    EngineControls,
    PlacementControls,
    StatusDisplay,
)
from physics_sim.ui.sections.base_section import BaseSection


class ControlPanelSection(BaseSection):
    """Left control panel section with GUI widgets."""

    def __init__(self, region: LayoutRegion, initial_engine: str = "numpy"):
        super().__init__(region, background_color=(245, 245, 245))

        # UI Manager
        self.ui_manager = arcade.gui.UIManager()

        # Widget components
        self.engine_controls = EngineControls(initial_engine)
        self.placement_controls = PlacementControls()
        self.display_controls = DisplayControls()
        self.status_display = StatusDisplay()

        self._setup_ui()

    def _setup_ui(self):
        """Setup UI layout."""
        v_box = arcade.gui.UIBoxLayout(space_between=8, vertical=True)

        # Title
        title = arcade.gui.UILabel(
            text="CONTROLS",
            font_size=16,
            bold=True,
            text_color=arcade.color.BLACK,
        )
        v_box.add(title)
        v_box.add(arcade.gui.UISpace(height=5))

        # Add widget groups
        v_box.add(self.engine_controls.get_layout())
        v_box.add(arcade.gui.UISpace(height=10))

        v_box.add(self.placement_controls.get_layout())
        v_box.add(arcade.gui.UISpace(height=10))

        v_box.add(self.display_controls.get_layout())
        v_box.add(arcade.gui.UISpace(height=10))

        v_box.add(self.status_display.get_layout())
        v_box.add(arcade.gui.UISpace(height=15))

        # Create anchor and add to UI manager
        anchor = arcade.gui.UIAnchorLayout()
        anchor.add(
            child=v_box,
            anchor_x="left",
            anchor_y="top",
            align_x=15,
            align_y=-20,
        )

        self.ui_manager.add(anchor)

    def update_status(self):
        """Update status based on current mode."""
        if self.placement_controls.add_mode:
            entity_type = self.placement_controls.get_selected_entity_type()
            if entity_type:
                self.status_display.set_adding(entity_type.__name__)
            else:
                self.status_display.set_status(
                    "● Adding (no types)", arcade.color.ORANGE
                )
        else:
            self.status_display.set_normal()

    def on_draw(self):
        """Draw the control panel section."""
        self.draw_background()
        self.draw_border(sides="right")
        self.ui_manager.draw()

    def on_update(self, delta_time: float):
        """Update section."""
        pass

    def enable(self):
        """Enable UI manager."""
        self.ui_manager.enable()

    def disable(self):
        """Disable UI manager."""
        self.ui_manager.disable()


__all__: list[str] = ["ControlPanelSection"]
