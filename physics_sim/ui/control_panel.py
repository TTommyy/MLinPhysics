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
        self.editor_ui_manager = arcade.gui.UIManager()

        # State
        self.selected_engine = "numpy"
        self.add_mode = False
        self.available_entity_types: list[type] = []
        self.selected_entity_type_index = 0
        self.is_paused: bool = False
        self.entity_selected: bool = False

        # Entity editor state
        self.editor_visible = False
        self.editor_entity = None
        self.editor_entity_class = None
        self.editor_parameters = {}
        self.editor_input_fields: dict[str, arcade.gui.UIInputText] = {}
        self.editor_color_buttons: dict[str, arcade.gui.UIFlatButton] = {}
        self.editor_current_colors: dict[str, tuple[int, int, int]] = {}

        # Callbacks
        self.on_engine_change = None
        self.on_add_mode_toggle = None
        self.on_object_type_change = None
        self.on_grid_toggle = None
        self.on_debug_toggle = None
        self.on_pause_toggle = None
        self.on_entity_save = None
        self.on_entity_delete = None

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
            text="Type: (no engine)",
            width=220,
            height=35,
        )
        self.object_type_button.on_click = self._cycle_object_type
        v_box.add(self.object_type_button)

        # Display controls section
        display_label = arcade.gui.UILabel(
            text="Display Options",
            font_size=10,
            text_color=arcade.color.DARK_GRAY,
        )
        v_box.add(display_label)

        self.grid_button = arcade.gui.UIFlatButton(
            text="Grid: ON",
            width=220,
            height=35,
        )
        self.grid_button.on_click = self._toggle_grid
        v_box.add(self.grid_button)

        self.debug_button = arcade.gui.UIFlatButton(
            text="Debug: ON",
            width=220,
            height=35,
        )
        self.debug_button.on_click = self._toggle_debug
        v_box.add(self.debug_button)

        self.pause_button = arcade.gui.UIFlatButton(
            text="Pause: OFF",
            width=220,
            height=35,
        )
        self.pause_button.on_click = self._toggle_pause
        v_box.add(self.pause_button)

        self.edit_button = arcade.gui.UIFlatButton(
            text="Edit Entity",
            width=220,
            height=35,
        )
        self.edit_button.on_click = self._on_edit_entity_button
        self.edit_button.disabled = True
        v_box.add(self.edit_button)

        # Spacer
        v_box.add(arcade.gui.UISpace(height=10))

        # Entity editor section (initially hidden)
        self.editor_section = arcade.gui.UIBoxLayout(space_between=6, vertical=True)
        self.editor_anchor = v_box  # Store reference to parent
        # Editor will be added dynamically

        # Status indicator
        self.status_label = arcade.gui.UILabel(
            text="● Normal",
            font_size=11,
            text_color=arcade.color.DARK_GREEN,
        )
        v_box.add(self.status_label)

        # Spacer
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
        """Cycle through available entity types from engine."""
        if not self.available_entity_types:
            return

        self.selected_entity_type_index = (self.selected_entity_type_index + 1) % len(
            self.available_entity_types
        )
        entity_class = self.available_entity_types[self.selected_entity_type_index]
        self.object_type_button.text = f"Type: {entity_class.__name__}"
        self._update_status()
        if self.on_object_type_change:
            self.on_object_type_change(entity_class)

    def _toggle_grid(self, event):
        """Toggle grid display."""
        if self.on_grid_toggle:
            self.on_grid_toggle()

    def _toggle_debug(self, event):
        """Toggle debug info display."""
        if self.on_debug_toggle:
            self.on_debug_toggle()

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

    def _update_status(self):
        """Update status label based on current mode."""
        if self.add_mode:
            if self.available_entity_types:
                entity_name = self.available_entity_types[
                    self.selected_entity_type_index
                ].__name__
                self.status_label.text = f"● Adding {entity_name}"
            else:
                self.status_label.text = "● Adding (no types)"
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

    def set_grid_enabled(self, enabled: bool):
        """Set grid display state.

        Args:
            enabled: Whether grid is enabled
        """
        self.grid_button.text = f"Grid: {'ON' if enabled else 'OFF'}"

    def set_debug_enabled(self, enabled: bool):
        """Set debug info display state.

        Args:
            enabled: Whether debug info is enabled
        """
        self.debug_button.text = f"Debug: {'ON' if enabled else 'OFF'}"

    def set_pause_enabled(self, enabled: bool):
        """Set pause state programmatically.

        Args:
            enabled: Whether pause is enabled
        """
        self.is_paused = enabled
        self.pause_button.text = f"Pause: {'ON' if enabled else 'OFF'}"

    def set_entity_selected(self, selected: bool, entity_name: str = "Entity"):
        """Set entity selection state and update edit button.

        Args:
            selected: Whether an entity is selected
            entity_name: Name of the selected entity (for display)
        """
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

    def set_available_entity_types(self, entity_types: list[type]):
        """Set available entity types from the physics engine.

        Args:
            entity_types: List of entity classes supported by the engine
        """
        self.available_entity_types = entity_types
        self.selected_entity_type_index = 0
        if entity_types:
            self.object_type_button.text = f"Type: {entity_types[0].__name__}"
        else:
            self.object_type_button.text = "Type: (no types)"
        self._update_status()

    def get_selected_entity_type(self) -> type | None:
        """Get currently selected entity type.

        Returns:
            Selected entity class or None if no types available
        """
        if self.available_entity_types:
            return self.available_entity_types[self.selected_entity_type_index]
        return None

    def show_entity_editor(
        self, entity_class: type | None = None, entity_instance=None
    ):
        """Show entity editor for creating or editing an entity.

        Args:
            entity_class: Entity class for creation
            entity_instance: Entity instance for editing
        """
        self.editor_visible = True
        self.editor_entity = entity_instance
        self.editor_entity_class = entity_class

        # Get parameters
        if entity_instance:
            self.editor_parameters = entity_instance.get_settable_parameters()
            mode = "Edit"
            entity_name = entity_instance.__class__.__name__
        elif entity_class:
            from physics_sim.core import Vector2D

            temp = entity_class(position=Vector2D(0, 0), velocity=Vector2D(0, 0))
            self.editor_parameters = temp.get_settable_parameters()
            mode = "Create"
            entity_name = entity_class.__name__
        else:
            return

        # Clear previous editor
        self._clear_editor()

        # Build new editor
        self.editor_section = arcade.gui.UIBoxLayout(space_between=6, vertical=True)

        # Title
        title = arcade.gui.UILabel(
            text=f"--- {mode} {entity_name} ---",
            font_size=10,
            bold=True,
            text_color=arcade.color.DARK_BLUE,
        )
        self.editor_section.add(title)

        # Parameters
        for param_name, param_meta in self.editor_parameters.items():
            param_type = param_meta.get("type")
            label = param_meta.get("label", param_name)
            default = param_meta.get("default")

            if param_type == "color":
                self._add_color_field(param_name, label, default)
            else:
                self._add_input_field(param_name, label, default)

        # Buttons
        button_row = arcade.gui.UIBoxLayout(space_between=5, vertical=False)

        save_btn = arcade.gui.UIFlatButton(text="Save", width=65, height=28)
        save_btn.on_click = self._on_editor_save
        button_row.add(save_btn)

        cancel_btn = arcade.gui.UIFlatButton(text="Cancel", width=65, height=28)
        cancel_btn.on_click = self._on_editor_cancel
        button_row.add(cancel_btn)

        if entity_instance:
            del_btn = arcade.gui.UIFlatButton(text="Del", width=45, height=28)
            del_btn.on_click = self._on_editor_delete
            button_row.add(del_btn)

        self.editor_section.add(button_row)

        # Add to editor UI manager with anchoring
        anchor = arcade.gui.UIAnchorLayout()
        anchor.add(
            child=self.editor_section,
            anchor_x="left",
            anchor_y="bottom",
            align_x=15,
            align_y=50,
        )
        self.editor_ui_manager.add(anchor)
        self.editor_ui_manager.enable()

    def _add_input_field(self, param_name: str, label: str, default_value):
        """Add an input field to editor section."""
        row = arcade.gui.UIBoxLayout(space_between=4, vertical=True)

        lbl = arcade.gui.UILabel(
            text=label, font_size=8, text_color=arcade.color.DARK_GRAY
        )
        row.add(lbl)

        inp = arcade.gui.UIInputText(text=str(default_value), width=210, height=24)
        self.editor_input_fields[param_name] = inp
        row.add(inp)

        self.editor_section.add(row)

    def _add_color_field(
        self, param_name: str, label: str, default_value: tuple[int, int, int]
    ):
        """Add a color field to editor section."""
        row = arcade.gui.UIBoxLayout(space_between=4, vertical=True)

        lbl = arcade.gui.UILabel(
            text=label, font_size=8, text_color=arcade.color.DARK_GRAY
        )
        row.add(lbl)

        self.editor_current_colors[param_name] = default_value
        btn = arcade.gui.UIFlatButton(
            text=f"RGB({default_value[0]},{default_value[1]},{default_value[2]})",
            width=210,
            height=24,
        )
        btn.on_click = lambda e, n=param_name: self._on_color_click(e, n)
        self.editor_color_buttons[param_name] = btn
        row.add(btn)

        self.editor_section.add(row)

    def _on_color_click(self, event, param_name: str):
        """Cycle through colors."""
        r, g, b = self.editor_current_colors[param_name]
        r = (r + 50) % 256
        self.editor_current_colors[param_name] = (r, g, b)
        self.editor_color_buttons[param_name].text = f"RGB({r},{g},{b})"

    def _on_editor_save(self, event):
        """Handle save button in editor."""
        try:
            data: dict[str, object] = {}
            for name, field in self.editor_input_fields.items():
                meta = self.editor_parameters[name]
                typ = meta.get("type")
                if typ == "float":
                    data[name] = float(field.text)
                elif typ == "int":
                    data[name] = int(field.text)
                else:
                    data[name] = field.text
            for name, color in self.editor_current_colors.items():
                data[name] = color

            if self.on_entity_save:
                # Callback receives: (data, entity_instance, entity_class)
                self.on_entity_save(data, self.editor_entity, self.editor_entity_class)
            self.hide_entity_editor()
        except ValueError as e:
            print(f"Invalid input: {e}")

    def _on_editor_delete(self, event):
        """Handle delete button in editor."""
        if self.on_entity_delete:
            self.on_entity_delete(self.editor_entity)
        self.hide_entity_editor()

    def _on_editor_cancel(self, event):
        """Handle cancel button in editor."""
        self.hide_entity_editor()

    def hide_entity_editor(self):
        """Hide the entity editor."""
        self.editor_visible = False
        self.editor_ui_manager.disable()
        self._clear_editor()

    def _clear_editor(self):
        """Clear editor fields."""
        self.editor_input_fields.clear()
        self.editor_color_buttons.clear()
        self.editor_current_colors.clear()
        self.editor_section = arcade.gui.UIBoxLayout(space_between=6, vertical=True)
        self.editor_ui_manager.clear()

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

        # Draw entity editor if visible
        if self.editor_visible:
            # Draw editor background box using draw_lrbt_rectangle_filled
            arcade.draw_lrbt_rectangle_filled(
                10,  # left
                self.panel_width - 10,  # right
                50,  # bottom
                350,  # top
                (230, 230, 240),  # color
            )
            # Draw editor UI
            self.editor_ui_manager.draw()

    def enable(self):
        """Enable the UI manager."""
        self.ui_manager.enable()

    def disable(self):
        """Disable the UI manager."""
        self.ui_manager.disable()
