import arcade
import arcade.gui

from physics_sim.core import Vector2D


class EntityEditorView(arcade.View):
    """Full-screen overlay view for entity creation and editing."""

    def __init__(
        self,
        simulator_view,
        entity_class: type | None = None,
        entity_instance=None,
    ):
        super().__init__()
        self.simulator_view = simulator_view
        self.entity_class = entity_class
        self.entity_instance = entity_instance

        # UI Manager
        self.ui_manager = arcade.gui.UIManager()

        # Editor state
        self.editor_parameters = {}
        self.editor_input_fields: dict[str, arcade.gui.UIInputText] = {}
        self.editor_color_buttons: dict[str, arcade.gui.UIFlatButton] = {}
        self.editor_current_colors: dict[str, tuple[int, int, int]] = {}

        self._setup_ui()

    def _setup_ui(self):
        """Setup the editor UI."""
        # Get parameters
        if self.entity_instance:
            self.editor_parameters = self.entity_instance.get_settable_parameters()
            mode = "Edit"
            entity_name = self.entity_instance.__class__.__name__
        elif self.entity_class:
            temp = self.entity_class(position=Vector2D(0, 0), velocity=Vector2D(0, 0))
            self.editor_parameters = temp.get_settable_parameters()
            mode = "Create"
            entity_name = self.entity_class.__name__
        else:
            return

        # Create modal dialog
        v_box = arcade.gui.UIBoxLayout(space_between=10, vertical=True)

        # Title
        title = arcade.gui.UILabel(
            text=f"{mode} {entity_name}",
            font_size=18,
            bold=True,
            text_color=arcade.color.DARK_BLUE,
        )
        v_box.add(title)
        v_box.add(arcade.gui.UISpace(height=10))

        # Parameters
        for param_name, param_meta in self.editor_parameters.items():
            param_type = param_meta.get("type")
            label = param_meta.get("label", param_name)
            default = param_meta.get("default")

            if param_type == "color":
                self._add_color_field(v_box, param_name, label, default)
            else:
                self._add_input_field(v_box, param_name, label, default)

        v_box.add(arcade.gui.UISpace(height=20))

        # Buttons
        button_row = arcade.gui.UIBoxLayout(space_between=10, vertical=False)

        save_btn = arcade.gui.UIFlatButton(text="Save", width=100, height=40)
        save_btn.on_click = self._on_save
        button_row.add(save_btn)

        cancel_btn = arcade.gui.UIFlatButton(text="Cancel", width=100, height=40)
        cancel_btn.on_click = self._on_cancel
        button_row.add(cancel_btn)

        if self.entity_instance:
            del_btn = arcade.gui.UIFlatButton(text="Delete", width=100, height=40)
            del_btn.on_click = self._on_delete
            button_row.add(del_btn)

        v_box.add(button_row)

        # Create panel background
        panel = arcade.gui.UIBoxLayout(space_between=0, vertical=True)
        panel.add(v_box.with_padding(all=20))

        # Center the panel
        anchor = arcade.gui.UIAnchorLayout()
        anchor.add(
            child=panel.with_background(color=(240, 240, 250)),
            anchor_x="center",
            anchor_y="center",
        )

        self.ui_manager.add(anchor)

    def _add_input_field(self, container, param_name: str, label: str, default_value):
        """Add an input field to container."""
        field_box = arcade.gui.UIBoxLayout(space_between=5, vertical=True)

        lbl = arcade.gui.UILabel(
            text=label,
            font_size=10,
            text_color=arcade.color.DARK_GRAY,
        )
        field_box.add(lbl)

        inp = arcade.gui.UIInputText(text=str(default_value), width=350, height=30)
        self.editor_input_fields[param_name] = inp
        field_box.add(inp)

        container.add(field_box)

    def _add_color_field(
        self,
        container,
        param_name: str,
        label: str,
        default_value: tuple[int, int, int],
    ):
        """Add a color field to container."""
        field_box = arcade.gui.UIBoxLayout(space_between=5, vertical=True)

        lbl = arcade.gui.UILabel(
            text=label,
            font_size=10,
            text_color=arcade.color.DARK_GRAY,
        )
        field_box.add(lbl)

        self.editor_current_colors[param_name] = default_value
        btn = arcade.gui.UIFlatButton(
            text=f"RGB({default_value[0]},{default_value[1]},{default_value[2]})",
            width=350,
            height=30,
        )
        btn.on_click = lambda e, n=param_name: self._on_color_click(e, n)
        self.editor_color_buttons[param_name] = btn
        field_box.add(btn)

        container.add(field_box)

    def _on_color_click(self, event, param_name: str):
        """Cycle through colors."""
        r, g, b = self.editor_current_colors[param_name]
        r = (r + 50) % 256
        self.editor_current_colors[param_name] = (r, g, b)
        self.editor_color_buttons[param_name].text = f"RGB({r},{g},{b})"

    def _on_save(self, event):
        """Handle save button."""
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

            if self.entity_instance:
                # Editing existing entity
                self.entity_instance.update_physics_data(data)
            else:
                # Creating new entity
                position = getattr(
                    self.simulator_view, "_pending_entity_position", Vector2D(0, 0)
                )

                velocity_x = data.get("velocity_x", 0.0)
                velocity_y = data.get("velocity_y", 0.0)
                velocity = Vector2D(velocity_x, velocity_y)
                mass = data.get("mass", 1.0)

                entity = self.entity_class(
                    position=position,
                    velocity=velocity,
                    mass=mass,
                )

                entity.update_physics_data(data)
                self.simulator_view.engine.add_entity(entity)

            self._close()
        except ValueError as e:
            print(f"Invalid input: {e}")

    def _on_delete(self, event):
        """Handle delete button."""
        if self.entity_instance:
            self.simulator_view.engine.remove_entity(self.entity_instance.id)
            self.simulator_view.entity_selector.clear_selection()
            # Update control panel to reflect no selection
            control_section = self.simulator_view.section_manager.get_first_section(
                "ControlPanelSection"
            )
            if control_section:
                control_section.display_controls.set_entity_selected(False)
        self._close()

    def _on_cancel(self, event):
        """Handle cancel button."""
        self._close()

    def _close(self):
        """Close the editor and return to simulator."""
        self.ui_manager.disable()
        self.window.show_view(self.simulator_view)

    def on_show_view(self):
        """Called when view is shown."""
        self.ui_manager.enable()
        arcade.set_background_color(arcade.color.WHITE)

    def on_hide_view(self):
        """Called when view is hidden."""
        self.ui_manager.disable()

    def on_draw(self):
        """Draw the editor view."""
        self.clear()

        # Draw dimmed background by rendering simulator
        self.simulator_view.on_draw()

        # Draw semi-transparent overlay
        arcade.draw_lrbt_rectangle_filled(
            0,
            self.window.width,
            0,
            self.window.height,
            (0, 0, 0, 180),
        )

        # Draw UI
        self.ui_manager.draw()

    def on_key_press(self, symbol: int, modifiers: int):
        """Handle key press."""
        if symbol == arcade.key.ESCAPE:
            self._close()


__all__: list[str] = ["EntityEditorView"]
