import arcade
import arcade.gui

from physics_sim.core import LayoutRegion
from physics_sim.ui.control_panel import (
    DisplayControls,
    EntityEditorPanel,
    PlacementControls,
    StatusDisplay,
)
from physics_sim.ui.sections.base_section import BaseSection

SPLIT_PCT = 0.5


class ControlPanelSection(BaseSection):
    """Left control panel section with GUI widgets split into controls and editor."""

    def __init__(
        self,
        control_region: LayoutRegion,
    ):
        super().__init__(control_region, background_color=(245, 245, 245))

        # Split the control panel internally
        split_height = int(control_region.height * SPLIT_PCT)

        # Top section for controls
        self.controls_region = LayoutRegion(
            x=control_region.x,
            y=control_region.y + (control_region.height - split_height),
            width=control_region.width,
            height=split_height,
        )

        # Bottom section for entity editor
        self.editor_region = LayoutRegion(
            x=control_region.x,
            y=control_region.y,
            width=control_region.width,
            height=control_region.height - split_height,
        )

        # UI Managers
        self.ui_manager = arcade.gui.UIManager()
        self.editor_ui_manager = arcade.gui.UIManager()

        # Calculate button width from region (with padding)
        button_width = max(120, control_region.width - 50)

        # Widget components
        self.placement_controls = PlacementControls(button_width)
        self.display_controls = DisplayControls(button_width)
        self.status_display = StatusDisplay()
        self.entity_editor = EntityEditorPanel(button_width)

        # We'll setup UI after we know the window dimensions
        self._ui_needs_setup = True

    def _setup_ui(self, window_height: int):
        """Setup UI layout for controls section."""
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
        v_box.add(self.display_controls.get_layout())
        v_box.add(arcade.gui.UISpace(height=10))

        v_box.add(self.status_display.get_layout())
        v_box.add(arcade.gui.UISpace(height=15))

        v_box.add(self.placement_controls.get_layout())
        v_box.add(arcade.gui.UISpace(height=10))

        # Create anchor positioned at the top of controls region
        anchor = arcade.gui.UIAnchorLayout()
        # Calculate offset from window top to controls region top
        offset_from_top = -(window_height - self.controls_region.top) - 20
        anchor.add(
            child=v_box,
            anchor_x="left",
            anchor_y="top",
            align_x=15,
            align_y=offset_from_top,
        )

        self.ui_manager.add(anchor)

    def _setup_editor_ui(self, window_height: int):
        """Setup entity editor UI for editor section."""
        editor_box = arcade.gui.UIBoxLayout(space_between=8, vertical=True)

        # Title
        title = arcade.gui.UILabel(
            text="ENTITY EDITOR",
            font_size=16,
            bold=True,
            text_color=arcade.color.BLACK,
        )
        editor_box.add(title)
        editor_box.add(arcade.gui.UISpace(height=5))

        # Add editor panel layout
        editor_box.add(self.entity_editor.get_layout())

        # Create anchor positioned at the top of editor region
        editor_anchor = arcade.gui.UIAnchorLayout()
        # Calculate offset from window top to editor region top
        offset_from_top = -(window_height - self.editor_region.top) - 20
        editor_anchor.add(
            child=editor_box,
            anchor_x="left",
            anchor_y="top",
            align_x=15,
            align_y=offset_from_top,
        )

        self.editor_ui_manager.add(editor_anchor)


    def on_draw(self):
        """Draw the control panel section with internal split layout."""
        # Setup UI if needed (on first draw when we have window context)
        if self._ui_needs_setup:
            window = arcade.get_window()
            if window:
                self._setup_ui(window.height)
                self._setup_editor_ui(window.height)
                self._ui_needs_setup = False

        # Draw controls section (top)
        arcade.draw_lrbt_rectangle_filled(
            self.controls_region.left,
            self.controls_region.right,
            self.controls_region.bottom,
            self.controls_region.top,
            arcade.color.LIGHT_STEEL_BLUE,
        )

        # Draw editor section (bottom)
        arcade.draw_lrbt_rectangle_filled(
            self.editor_region.left,
            self.editor_region.right,
            self.editor_region.bottom,
            self.editor_region.top,
            arcade.color.WHITE_SMOKE,
        )

        # Draw separator line between sections
        arcade.draw_line(
            self.editor_region.left,
            self.editor_region.top,
            self.editor_region.right,
            self.editor_region.top,
            arcade.color.BLACK_LEATHER_JACKET,
            4,
        )

        # Draw right border for entire panel
        arcade.draw_line(
            self.region.right,
            self.region.bottom,
            self.region.right,
            self.region.top,
            (200, 200, 200),
            2,
        )

        # Draw UI elements
        self.ui_manager.draw()
        self.editor_ui_manager.draw()

    def on_update(self, delta_time: float):
        """Update section."""
        pass

    def enable(self):
        """Enable UI managers."""
        self.ui_manager.enable()
        self.editor_ui_manager.enable()

    def disable(self):
        """Disable UI managers."""
        self.ui_manager.disable()
        self.editor_ui_manager.disable()


__all__: list[str] = ["ControlPanelSection"]
