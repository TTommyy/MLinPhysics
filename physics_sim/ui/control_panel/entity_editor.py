import logging

import numpy as np
from kivy.metrics import dp
from kivy.uix.checkbox import CheckBox

from physics_sim.core import Entity
from physics_sim.ui.utils import (
    format_number,
    format_vector_for_display,
    parse_vector_from_text,
    sanitize_color,
)
from physics_sim.ui.widgets import (
    BUTTON_DANGER_COLOR,
    MUTED_TEXT_COLOR,
    ColorSwatch,
    FlatButton,
    InputField,
    TextLabel,
    hbox,
    vbox,
)

logger = logging.getLogger(__name__)

ERROR_COLOR = (192, 57, 43)


def _format_scalar(value, param_type: str | None) -> str:
    if param_type == "int":
        try:
            return str(int(value))
        except (TypeError, ValueError):
            return str(value)
    return format_number(value)


def _clamp(value, meta: dict):
    lo, hi = meta.get("min"), meta.get("max")
    if lo is not None and value < lo:
        value = type(value)(lo)
    if hi is not None and value > hi:
        value = type(value)(hi)
    return value


class EntityEditorPanel:
    """Persistent entity editor panel for adding/editing entities."""

    def __init__(self, button_width: int | None = None):
        self.button_width = button_width
        self.mode = "idle"  # idle, add, edit
        self.entity_class = None
        self.entity_instance = None
        self.editor_parameters: dict[str, dict] = {}
        self.editor_input_fields: dict[str, InputField] = {}
        self.editor_vector_fields: dict[str, InputField] = {}
        self.editor_color_fields: dict[str, InputField] = {}
        self.editor_bool_fields: dict[str, CheckBox] = {}
        self.editor_color_swatches: dict[str, ColorSwatch] = {}
        # Kept for API compatibility with the previous implementation
        self.editor_color_buttons: dict = {}
        self.editor_current_colors: dict[str, tuple[int, int, int]] = {}
        self.validation_errors: list[str] = []

        self.layout = vbox(spacing=5)
        self.on_save = None
        self.on_delete = None
        self._build_idle()

    # ------------------------------------------------------------------ building
    def _reset(self):
        self.layout.clear_widgets()
        self.editor_input_fields.clear()
        self.editor_vector_fields.clear()
        self.editor_color_fields.clear()
        self.editor_bool_fields.clear()
        self.editor_color_swatches.clear()
        self.editor_color_buttons.clear()
        self.editor_current_colors.clear()
        self.validation_errors = []
        self.error_label = None

    def _build_idle(self):
        """Build idle state UI."""
        self._reset()
        self.editor_parameters = {}
        self.layout.add_widget(
            TextLabel(
                "Turn on Add Mode and click in the viewport to place an entity, "
                "or pause the simulation and click an entity to edit it.",
                font_size=12,
                color=MUTED_TEXT_COLOR,
            )
        )

    def _build_fields(self):
        for param_name, param_meta in self.editor_parameters.items():
            param_type = param_meta.get("type")
            label = param_meta.get("label", param_name)
            default = param_meta.get("default")
            if param_type == "color":
                self._add_color_field(param_name, label, default)
            elif param_type == "vector":
                self._add_vector_field(param_name, label, default)
            elif param_type == "bool":
                self._add_bool_field(param_name, label, default)
            else:
                self._add_input_field(param_name, label, default)
        self.error_label = TextLabel("", font_size=11, color=ERROR_COLOR, min_height=0)
        self.layout.add_widget(self.error_label)

    def _build_add_mode(self):
        """Build add mode UI with entity parameters."""
        self._reset()
        if not self.entity_class:
            return
        self.layout.add_widget(
            TextLabel(f"Add {self.entity_class.__name__}", font_size=14, bold=True)
        )
        self.layout.add_widget(
            TextLabel(
                "Click in the viewport to place it.",
                font_size=11,
                color=MUTED_TEXT_COLOR,
            )
        )
        self.editor_parameters = self.entity_class.get_default_parameters()
        self._build_fields()

    def _build_edit_mode(self):
        """Build edit mode UI with entity data."""
        self._reset()
        if not self.entity_instance:
            return
        self.layout.add_widget(
            TextLabel(
                f"Edit {self.entity_instance.__class__.__name__} "
                f"[{self.entity_instance.id}]",
                font_size=14,
                bold=True,
            )
        )
        self.editor_parameters = self.entity_instance.get_settable_parameters()
        self._build_fields()

        button_row = hbox(spacing=6)
        save_btn = FlatButton("Save")
        save_btn.bind(on_release=self._on_save_clicked)
        delete_btn = FlatButton("Delete", color=BUTTON_DANGER_COLOR)
        delete_btn.bind(on_release=self._on_delete_clicked)
        button_row.add_widget(save_btn)
        button_row.add_widget(delete_btn)
        self.save_button = save_btn
        self.delete_button = delete_btn
        self.layout.add_widget(button_row)

    def _add_label(self, label: str):
        self.layout.add_widget(TextLabel(label, font_size=12))

    def _new_input(self, text: str) -> InputField:
        inp = InputField(text=text)
        inp.bind(on_text_validate=self._on_text_validate)
        return inp

    def _add_input_field(self, param_name: str, label: str, default_value):
        """Add a scalar input field."""
        self._add_label(label)
        param_type = self.editor_parameters[param_name].get("type")
        inp = self._new_input(_format_scalar(default_value, param_type))
        self.editor_input_fields[param_name] = inp
        self.layout.add_widget(inp)

    def _add_vector_field(self, param_name: str, label: str, default_value):
        """Add a vector field for [x, y] input."""
        self._add_label(label)
        inp = self._new_input(format_vector_for_display(default_value))
        self.editor_vector_fields[param_name] = inp
        self.layout.add_widget(inp)

    def _add_color_field(self, param_name: str, label: str, default_value):
        """Add an RGB color field with live preview."""
        self._add_label(f"{label} [R, G, B] (0-255)")
        color = sanitize_color(default_value)
        self.editor_current_colors[param_name] = color
        row = hbox(spacing=6, height=dp(30))
        inp = self._new_input(format_vector_for_display(color))
        swatch = ColorSwatch(color)
        inp.bind(text=lambda _inst, text, name=param_name: self._on_color_text(name, text))
        row.add_widget(inp)
        row.add_widget(swatch)
        self.editor_color_fields[param_name] = inp
        self.editor_color_swatches[param_name] = swatch
        self.layout.add_widget(row)

    def _add_bool_field(self, param_name: str, label: str, default_value):
        row = hbox(spacing=6, height=dp(30))
        cb = CheckBox(active=bool(default_value), size_hint_x=None, width=dp(30), color=(0, 0, 0, 1))
        row.add_widget(cb)
        row.add_widget(TextLabel(label, font_size=12))
        self.editor_bool_fields[param_name] = cb
        self.layout.add_widget(row)

    def _on_color_text(self, param_name: str, text: str):
        try:
            values = parse_vector_from_text(text)
            if len(values) < 3:
                return
            color = sanitize_color(values)
        except ValueError:
            return
        self.editor_current_colors[param_name] = color
        swatch = self.editor_color_swatches.get(param_name)
        if swatch is not None:
            swatch.set_color(color)

    def _on_text_validate(self, *_):
        if self.mode == "edit":
            self._on_save_clicked(None)

    # ------------------------------------------------------------------ callbacks
    def _on_save_clicked(self, *_):
        """Handle save button click."""
        if self.on_save:
            params = self.get_parameters()
            self.on_save(params)

    def _on_delete_clicked(self, *_):
        """Handle delete button click."""
        if self.on_delete and self.entity_instance is not None:
            self.on_delete(self.entity_instance.id)

    # ------------------------------------------------------------------ public API
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

    def _report_errors(self):
        if self.error_label is not None:
            self.error_label.text = "\n".join(self.validation_errors)

    def get_parameters(self) -> dict[str, object]:
        """Get current parameter values parsed from the input widgets.

        Invalid input falls back to the parameter's current/default value and
        numeric values are clamped to the parameter's min/max range.
        """
        data: dict[str, object] = {}
        errors: list[str] = []

        for name, field in self.editor_input_fields.items():
            meta = self.editor_parameters[name]
            typ = meta.get("type")
            label = meta.get("label", name)
            try:
                if typ == "int":
                    value = int(float(field.text))
                elif typ == "float":
                    value = float(field.text)
                    if not np.isfinite(value):
                        raise ValueError
                else:
                    data[name] = field.text
                    continue
                clamped = _clamp(value, meta)
                if clamped != value:
                    errors.append(f"{label}: clamped to {_format_scalar(clamped, typ)}")
                data[name] = clamped
            except (TypeError, ValueError):
                errors.append(f"{label}: invalid number, kept previous value")
                data[name] = meta.get("default")

        for name, field in self.editor_color_fields.items():
            meta = self.editor_parameters[name]
            try:
                values = parse_vector_from_text(field.text)
                if len(values) != 3:
                    raise ValueError
                data[name] = sanitize_color(values)
            except ValueError:
                errors.append(f"{meta.get('label', name)}: expected [R, G, B]")
                data[name] = sanitize_color(meta.get("default"))
            self.editor_current_colors[name] = data[name]

        for name, field in self.editor_vector_fields.items():
            meta = self.editor_parameters[name]
            default = list(meta.get("default") or [])
            try:
                values = parse_vector_from_text(field.text)
                if default and len(values) != len(default):
                    raise ValueError
                if not all(np.isfinite(values)):
                    raise ValueError
                data[name] = values
            except ValueError:
                errors.append(f"{meta.get('label', name)}: invalid vector, kept previous value")
                data[name] = [float(v) for v in default]

        for name, cb in self.editor_bool_fields.items():
            data[name] = bool(cb.active)

        self.validation_errors = errors
        self._report_errors()
        return data

    def get_entity_object(
        self, position: np.ndarray, entity_id: str | None = None
    ) -> Entity | None:
        """Build and return a fully constructed entity.

        Args:
            position: Position for the entity (from click location)
            entity_id: Optional explicit (unique) id for a newly created entity

        Returns:
            Fully constructed entity ready to add to engine, or None
        """
        params = self.get_parameters()

        if self.mode == "add" and self.entity_class:
            params.pop("position", None)
            if "velocity" in params:
                params["velocity"] = np.asarray(params["velocity"], dtype=np.float64)
            if entity_id is not None:
                params["entity_id"] = entity_id
            return self.entity_class(
                position=np.asarray(position, dtype=np.float64), **params
            )
        elif self.mode == "edit" and self.entity_instance:
            self.entity_instance.update_physics_data(params)
            return self.entity_instance

        return None

    def get_layout(self):
        """Get the widget layout."""
        return self.layout


__all__: list[str] = ["EntityEditorPanel"]
