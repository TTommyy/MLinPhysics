import arcade.gui
import numpy as np

from physics_sim.core import Entity
from physics_sim.ui.utils import format_vector_for_display, parse_vector_from_text


class EntityEditorPanel:
    """Persistent entity editor panel for adding/editing entities."""

    def __init__(self, button_width: int = 220):
        self.button_width = button_width
        self.mode = "idle"  # idle, add, edit
        self.entity_class = None
        self.entity_instance = None
        self.editor_parameters = {}
        self.editor_input_fields: dict[str, arcade.gui.UIInputText] = {}
        self.editor_color_buttons: dict[str, arcade.gui.UIFlatButton] = {}
        self.editor_current_colors: dict[str, tuple[int, int, int]] = {}
        self.editor_vector_fields: dict[str, arcade.gui.UIInputText] = {}

        self.layout = arcade.gui.UIBoxLayout(space_between=5, vertical=True)
        self.on_save = None
        self._build_idle()

    def _build_idle(self):
        """Build idle state UI."""
        self.layout.clear()
        self.editor_input_fields.clear()
        self.editor_color_buttons.clear()
        self.editor_current_colors.clear()
        self.editor_vector_fields.clear()

    def _build_add_mode(self):
        """Build add mode UI with entity parameters."""
        self.layout.clear()
        self.editor_input_fields.clear()
        self.editor_color_buttons.clear()
        self.editor_current_colors.clear()
        self.editor_vector_fields.clear()

        if not self.entity_class:
            return

        title = arcade.gui.UILabel(
            text=f"Add {self.entity_class.__name__}",
            font_size=12,
            bold=True,
            text_color=arcade.color.BLACK,
        )
        self.layout.add(title)
        self.layout.add(arcade.gui.UISpace(height=5))

        # Get default parameters from class method
        self.editor_parameters = self.entity_class.get_default_parameters()

        # Add input fields
        for param_name, param_meta in self.editor_parameters.items():
            param_type = param_meta.get("type")
            label = param_meta.get("label", param_name)
            default = param_meta.get("default")

            if param_type in ["color", "vector"]:
                self._add_vector_field(param_name, label, default)
            else:
                self._add_input_field(param_name, label, default)

    def _build_edit_mode(self):
        """Build edit mode UI with entity data."""
        self.layout.clear()
        self.editor_input_fields.clear()
        self.editor_color_buttons.clear()
        self.editor_current_colors.clear()
        self.editor_vector_fields.clear()

        if not self.entity_instance:
            return

        title = arcade.gui.UILabel(
            text=f"Edit {self.entity_instance.__class__.__name__}",
            font_size=12,
            bold=True,
            text_color=arcade.color.BLACK,
        )
        self.layout.add(title)
        self.layout.add(arcade.gui.UISpace(height=5))

        # Get parameters
        self.editor_parameters = self.entity_instance.get_settable_parameters()

        # Add input fields
        for param_name, param_meta in self.editor_parameters.items():
            param_type = param_meta.get("type")
            label = param_meta.get("label", param_name)
            default = param_meta.get("default")

            if param_type in ["color", "vector"]:
                self._add_vector_field(param_name, label, default)
            else:
                self._add_input_field(param_name, label, default)

        self.layout.add(arcade.gui.UISpace(height=10))

        # Add Save button for edit mode
        button_row = arcade.gui.UIBoxLayout(space_between=5, vertical=False)

        save_btn = arcade.gui.UIFlatButton(
            text="Save", width=self.button_width // 2 - 3, height=30
        )
        save_btn.on_click = self._on_save_clicked
        button_row.add(save_btn)

        delete_btn = arcade.gui.UIFlatButton(
            text="Delete", width=self.button_width // 2 - 3, height=30
        )
        delete_btn.on_click = self._on_delete_clicked
        button_row.add(delete_btn)

        self.layout.add(button_row)

    def _add_input_field(self, param_name: str, label: str, default_value):
        """Add an input field."""
        field_box = arcade.gui.UIBoxLayout(space_between=2, vertical=True)

        lbl = arcade.gui.UILabel(
            text=label,
            font_size=9,
            text_color=arcade.color.BLACK_LEATHER_JACKET,
        )
        field_box.add(lbl)

        inp = arcade.gui.UIInputText(
            text=str(default_value),
            width=self.button_width,
            height=25,
            text_color=arcade.color.BLACK_BEAN,
        )
        self.editor_input_fields[param_name] = inp
        field_box.add(inp)

        self.layout.add(field_box)

    def _add_vector_field(self, param_name: str, label: str, default_value: list):
        """Add a vector field for [x, y] input."""
        field_box = arcade.gui.UIBoxLayout(space_between=2, vertical=True)

        lbl = arcade.gui.UILabel(
            text=label,
            font_size=9,
            text_color=arcade.color.BLACK_LEATHER_JACKET,
        )
        field_box.add(lbl)

        text_value = format_vector_for_display(default_value)

        inp = arcade.gui.UIInputText(
            text=text_value,
            width=self.button_width,
            height=25,
            text_color=arcade.color.BLACK_BEAN,
        )
        self.editor_vector_fields[param_name] = inp
        field_box.add(inp)

        self.layout.add(field_box)

    def _on_color_click(self, event, param_name: str):
        """Cycle through colors."""
        r, g, b = self.editor_current_colors[param_name]
        r = (r + 50) % 256
        self.editor_current_colors[param_name] = (r, g, b)
        self.editor_color_buttons[param_name].text = f"RGB({r},{g},{b})"

    def _on_save_clicked(self, event):
        """Handle save button click."""
        if self.on_save:
            params = self.get_parameters()
            self.on_save(params)

    def _on_delete_clicked(self, event):
        """Handle delete button click."""
        # This will be handled by the simulator
        pass

    def set_entity_type(self, entity_class: type):
        """Set entity type for adding."""
        self.entity_class = entity_class
        self.entity_instance = None
        self.mode = "add"
        self._build_add_mode()

    def set_entity_instance(self, entity):
        """Set entity instance for editing."""
        self.entity_instance = entity
        self.entity_class = None
        self.mode = "edit"
        self._build_edit_mode()

    def clear(self):
        """Reset to idle state."""
        self.mode = "idle"
        self.entity_class = None
        self.entity_instance = None
        self._build_idle()

    def get_parameters(self) -> dict[str, object]:
        """Get current parameter values."""
        data: dict[str, object] = {}

        # Parse regular input fields
        for name, field in self.editor_input_fields.items():
            meta = self.editor_parameters[name]
            typ = meta.get("type")
            if typ == "float":
                data[name] = float(field.text)
            elif typ == "int":
                data[name] = int(field.text)
            else:
                data[name] = field.text

        # Parse color fields
        for name, color in self.editor_current_colors.items():
            data[name] = color

        # Parse vector fields
        for name, field in self.editor_vector_fields.items():
            try:
                data[name] = parse_vector_from_text(field.text)
            except ValueError:
                # Keep old value if parsing fails
                pass

        return data

    def get_entity_object(self, position: np.ndarray) -> Entity | None:
        """Build and return a fully constructed entity.

        Args:
            position: Position for the entity (from click location)

        Returns:
            Fully constructed entity ready to add to engine, or None
        """
        params = self.get_parameters()

        if self.mode == "add" and self.entity_class:
            # Create new entity using constructor
            return self.entity_class(position=position, **params)
        elif self.mode == "edit" and self.entity_instance:
            # Update existing entity instance
            self.entity_instance.update_physics_data(params)
            return self.entity_instance

        return None

    def get_layout(self) -> arcade.gui.UIBoxLayout:
        """Get the widget layout."""
        return self.layout


__all__: list[str] = ["EntityEditorPanel"]
