import arcade
import arcade.gui


class ControlPanel:
    """Fixed left control panel with GUI widgets for engine selection and object placement.

    Provides:
    - Engine selector
    - Add mode toggle
    - Object type selector
    - Status indicator
    - Keyboard shortcuts reference
    """

    def __init__(self, screen_width: int, screen_height: int, panel_width: int = 250):
        """
        Args:
            screen_width: Window width in pixels
            screen_height: Window height in pixels
            panel_width: Width of the control panel
        """
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.panel_width = panel_width

        # UI Manager
        self.ui_manager = arcade.gui.UIManager()

        # State
        self.selected_engine = "numpy"
        self.add_mode = False
        self.selected_object_type = "Ball"

        # Callbacks
        self.on_engine_change = None
        self.on_add_mode_toggle = None
        self.on_object_type_change = None

        self._setup_ui()

    def _setup_ui(self):
        """Setup UI widgets."""
        # Create vertical box for layout
        v_box = arcade.gui.UIBoxLayout(space_between=8)

        # Title
        title = arcade.gui.UILabel(
            text="CONTROLS",
            font_size=16,
            bold=True,
            text_color=arcade.color.BLACK,
        )
        v_box.add(title)

        # Spacer
        spacer = arcade.gui.UISpace(height=5)
        v_box.add(spacer)

        # Engine section
        engine_label = arcade.gui.UILabel(
            text="Physics Engine",
            font_size=10,
            text_color=arcade.color.DARK_GRAY,
        )
        v_box.add(engine_label)

        self.engine_button = arcade.gui.UIFlatButton(
            text=self.selected_engine.upper(),
            width=220,
            height=35,
        )
        self.engine_button.on_click = self._toggle_engine
        v_box.add(self.engine_button)

        # Spacer
        v_box.add(arcade.gui.UISpace(height=10))

        # Add mode section
        add_mode_label = arcade.gui.UILabel(
            text="Object Placement",
            font_size=10,
            text_color=arcade.color.DARK_GRAY,
        )
        v_box.add(add_mode_label)

        self.add_mode_button = arcade.gui.UIFlatButton(
            text="Add Mode: OFF",
            width=220,
            height=35,
        )
        self.add_mode_button.on_click = self._toggle_add_mode
        v_box.add(self.add_mode_button)

        self.object_type_button = arcade.gui.UIFlatButton(
            text=f"Type: {self.selected_object_type}",
            width=220,
            height=35,
        )
        self.object_type_button.on_click = self._cycle_object_type
        v_box.add(self.object_type_button)

        # Spacer
        v_box.add(arcade.gui.UISpace(height=10))

        # Status indicator
        self.status_label = arcade.gui.UILabel(
            text="● Normal",
            font_size=11,
            text_color=arcade.color.DARK_GREEN,
        )
        v_box.add(self.status_label)

        # Spacer
        v_box.add(arcade.gui.UISpace(height=15))

        # Keyboard shortcuts
        shortcuts_title = arcade.gui.UILabel(
            text="Keyboard Shortcuts",
            font_size=10,
            text_color=arcade.color.DARK_GRAY,
        )
        v_box.add(shortcuts_title)

        shortcuts = [
            "A - Toggle add mode",
            "G - Toggle grid",
            "F1 - Toggle debug info",
            "TAB - Switch object type",
            "ESC - Exit mode/quit",
        ]

        for shortcut in shortcuts:
            label = arcade.gui.UILabel(
                text=shortcut,
                font_size=9,
                text_color=arcade.color.BLACK,
            )
            v_box.add(label)

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

    def _toggle_engine(self, event):
        """Toggle between numpy and pymunk engines."""
        self.selected_engine = "pymunk" if self.selected_engine == "numpy" else "numpy"
        self.engine_button.text = self.selected_engine.upper()
        if self.on_engine_change:
            self.on_engine_change(self.selected_engine)

    def _toggle_add_mode(self, event):
        """Toggle add mode on/off."""
        self.add_mode = not self.add_mode
        self.add_mode_button.text = f"Add Mode: {'ON' if self.add_mode else 'OFF'}"
        self._update_status()
        if self.on_add_mode_toggle:
            self.on_add_mode_toggle(self.add_mode)

    def _cycle_object_type(self, event):
        """Cycle through available object types."""
        types = ["Ball", "Obstacle"]
        current_idx = types.index(self.selected_object_type)
        self.selected_object_type = types[(current_idx + 1) % len(types)]
        self.object_type_button.text = f"Type: {self.selected_object_type}"
        self._update_status()
        if self.on_object_type_change:
            self.on_object_type_change(self.selected_object_type)

    def _update_status(self):
        """Update status label based on current mode."""
        if self.add_mode:
            self.status_label.text = f"● Adding {self.selected_object_type}"
            self.status_label.text_color = arcade.color.ORANGE
        else:
            self.status_label.text = "● Normal"
            self.status_label.text_color = arcade.color.DARK_GREEN

    def set_add_mode(self, enabled: bool):
        """Set add mode programmatically (e.g., from keyboard shortcut).

        Args:
            enabled: Whether to enable add mode
        """
        if self.add_mode != enabled:
            self.add_mode = enabled
            self.add_mode_button.text = f"Add Mode: {'ON' if self.add_mode else 'OFF'}"
            self._update_status()

    def render(self):
        """Render the control panel with background."""
        # Draw panel background
        arcade.draw_lrbt_rectangle_filled(
            0, self.panel_width, 0, self.screen_height, (245, 245, 245)
        )

        # Draw right border
        arcade.draw_line(
            self.panel_width,
            0,
            self.panel_width,
            self.screen_height,
            arcade.color.GRAY,
            2,
        )

        # Draw UI widgets
        self.ui_manager.draw()

    def enable(self):
        """Enable the UI manager."""
        self.ui_manager.enable()

    def disable(self):
        """Disable the UI manager."""
        self.ui_manager.disable()
