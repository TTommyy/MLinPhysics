import logging
from typing import Any

import numpy as np
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.checkbox import CheckBox
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label

from physics_sim.core import LayoutRegion
from physics_sim.ui.sections.base_section import BaseSection
from physics_sim.ui.utils import (
    format_number,
    format_vector_for_display,
    parse_vector_from_text,
)
from physics_sim.ui.widgets import (
    BUTTON_ACTIVE_COLOR,
    MUTED_TEXT_COLOR,
    FlatButton,
    InputField,
    Panel,
    TextLabel,
    VerticalScroll,
    hbox,
    vbox,
)

logger = logging.getLogger(__name__)

PANEL_BG = (135, 206, 250)  # light sky blue
EDITOR_BG = (225, 240, 252)
INACTIVE_COLOR = (127, 140, 141)
ERROR_COLOR = (192, 57, 43)


class ForceManagerSection(BaseSection):
    """Top panel for (de)activating forces and editing their parameters."""

    def __init__(
        self,
        region: LayoutRegion | None = None,
        forces: list[type] | None = None,
        items_per_page: int = 3,
        **kwargs,
    ):
        super().__init__(region, background_color=PANEL_BG, **kwargs)
        self.orientation = "horizontal"
        self.padding = [dp(8), dp(6)]
        self.spacing = dp(8)

        self.items_per_page = max(1, int(items_per_page))
        self._available_force_types: list[type] = list(forces or [])
        self.total_pages = max(
            1, (len(self._available_force_types) + self.items_per_page - 1) // self.items_per_page
        )
        self.current_page = 0
        self._active_forces: dict[str, object] = {}

        # Editing state
        self.edited_force_instance: object | None = None
        self.force_parameters: dict[str, dict[str, Any]] = {}
        self.validation_errors: list[str] = []

        # Widget references
        self.force_checkboxes: dict[str, FlatButton] = {}
        self.edit_buttons: dict[str, FlatButton] = {}
        self.force_param_fields: dict[str, InputField] = {}
        self.force_vector_fields: dict[str, InputField] = {}
        self.force_bool_fields: dict[str, CheckBox] = {}
        self._cached_field_values: dict[str, str] = {}

        # Callbacks
        self.on_force_toggle = None
        self.on_force_params_update = None

        self._build_skeleton()
        self._build_ui()

    # ------------------------------------------------------------------ skeleton
    def _build_skeleton(self):
        left = BoxLayout(orientation="vertical", size_hint_x=0.42, spacing=dp(4))
        left.add_widget(TextLabel("FORCE MANAGER", font_size=16, bold=True))
        self.list_scroll = VerticalScroll(spacing=4)
        left.add_widget(self.list_scroll)

        pager = hbox(spacing=6, height=dp(28))
        self.prev_button = FlatButton("Prev", height=dp(28))
        self.prev_button.bind(on_release=self._on_prev_page)
        self.page_label = Label(
            text="Page 1/1", color=(0, 0, 0, 1), font_size=13, size_hint_x=0.8
        )
        self.next_button = FlatButton("Next", height=dp(28))
        self.next_button.bind(on_release=self._on_next_page)
        pager.add_widget(self.prev_button)
        pager.add_widget(self.page_label)
        pager.add_widget(self.next_button)
        left.add_widget(pager)

        self.editor_panel = Panel(
            background_color=EDITOR_BG,
            border_color=(120, 160, 200),
            orientation="vertical",
            size_hint_x=0.58,
            padding=[dp(6), dp(4)],
        )
        self.editor_scroll = VerticalScroll(spacing=4)
        self.editor_panel.add_widget(self.editor_scroll)

        self.add_widget(left)
        self.add_widget(self.editor_panel)

    # ------------------------------------------------------------------ building
    def _update_page_text(self) -> None:
        self.page_label.text = f"Page {self.current_page + 1}/{self.total_pages}"
        self.prev_button.disabled = self.current_page == 0
        self.next_button.disabled = self.current_page >= self.total_pages - 1

    def _save_field_values(self):
        if self.edited_force_instance:
            self._cached_field_values.clear()
            for name, field in {**self.force_param_fields, **self.force_vector_fields}.items():
                self._cached_field_values[name] = field.text

    def _build_ui(self):
        """Build complete UI: force list (left) and parameter editor (right)."""
        self._build_force_list()
        self._build_parameter_editor()

    def _build_force_list(self):
        """Build force rows (toggle button, name, edit button) for current page."""
        content = self.list_scroll.content
        content.clear_widgets()
        self.force_checkboxes.clear()
        self.edit_buttons.clear()

        for force_class in self._get_current_page_forces():
            force_name = force_class.get_name()
            is_active = force_name in self._active_forces

            row = hbox(spacing=6, height=dp(30))
            toggle = FlatButton(
                "ON" if is_active else "OFF",
                color=BUTTON_ACTIVE_COLOR if is_active else INACTIVE_COLOR,
                size_hint_x=None,
                width=dp(48),
                height=dp(30),
            )
            toggle.bind(on_release=lambda _b, fc=force_class: self._on_checkbox_click(fc))
            row.add_widget(toggle)
            self.force_checkboxes[force_name] = toggle

            row.add_widget(TextLabel(force_name, font_size=13, bold=True, min_height=dp(30)))

            edit_btn = FlatButton("Edit", size_hint_x=None, width=dp(56), height=dp(30))
            if is_active:
                force_instance = self._active_forces[force_name]
                edit_btn.bind(
                    on_release=lambda _b, fi=force_instance: self._on_force_label_click(fi)
                )
            else:
                edit_btn.disabled = True
            row.add_widget(edit_btn)
            self.edit_buttons[force_name] = edit_btn
            content.add_widget(row)

        self._update_page_text()

    def _build_parameter_editor(self):
        """Build the parameter editor for the force being edited."""
        content = self.editor_scroll.content
        content.clear_widgets()
        self.force_param_fields.clear()
        self.force_vector_fields.clear()
        self.force_bool_fields.clear()
        self.error_label = None

        if not self.edited_force_instance:
            self.force_parameters = {}
            content.add_widget(TextLabel("Force Parameters", font_size=14, bold=True))
            content.add_widget(
                TextLabel(
                    "Activate a force with its ON/OFF button, then press Edit to "
                    "change its parameters.",
                    font_size=12,
                    color=MUTED_TEXT_COLOR,
                )
            )
            return

        force_name = type(self.edited_force_instance).get_name()
        content.add_widget(TextLabel(f"Edit {force_name}", font_size=14, bold=True))

        self.force_parameters = self.edited_force_instance.get_settable_parameters()
        grid = GridLayout(cols=2, spacing=[dp(8), dp(2)], size_hint_y=None)
        grid.bind(minimum_height=grid.setter("height"))
        for param_name, meta in self.force_parameters.items():
            param_type = meta.get("type")
            label = meta.get("label", param_name)
            default = meta.get("default")
            cell = vbox(spacing=2)
            if param_type == "bool":
                row = hbox(spacing=4, height=dp(30))
                cb = CheckBox(
                    active=bool(default), size_hint_x=None, width=dp(30), color=(0, 0, 0, 1)
                )
                row.add_widget(cb)
                row.add_widget(TextLabel(label, font_size=12))
                self.force_bool_fields[param_name] = cb
                cell.add_widget(TextLabel("", font_size=4, min_height=dp(18)))
                cell.add_widget(row)
            else:
                cell.add_widget(TextLabel(label, font_size=12))
                if param_type == "vector":
                    text = self._cached_field_values.get(
                        param_name, format_vector_for_display(default)
                    )
                    inp = InputField(text=text)
                    self.force_vector_fields[param_name] = inp
                else:
                    if param_type == "int":
                        default_text = str(default)
                    else:
                        default_text = format_number(default)
                    inp = InputField(
                        text=self._cached_field_values.get(param_name, default_text)
                    )
                    self.force_param_fields[param_name] = inp
                inp.bind(on_text_validate=self._on_save_clicked)
                cell.add_widget(inp)
            grid.add_widget(cell)
        content.add_widget(grid)

        self.error_label = TextLabel("", font_size=11, color=ERROR_COLOR, min_height=0)
        content.add_widget(self.error_label)

        buttons = hbox(spacing=6, height=dp(30))
        save_btn = FlatButton("Save", height=dp(30))
        save_btn.bind(on_release=self._on_save_clicked)
        cancel_btn = FlatButton("Cancel", color=INACTIVE_COLOR, height=dp(30))
        cancel_btn.bind(on_release=self._on_cancel_clicked)
        buttons.add_widget(save_btn)
        buttons.add_widget(cancel_btn)
        content.add_widget(buttons)

    # ------------------------------------------------------------------ events
    def _on_prev_page(self, *_):
        if self.current_page > 0:
            self.current_page -= 1
            self._build_force_list()

    def _on_next_page(self, *_):
        if self.current_page < self.total_pages - 1:
            self.current_page += 1
            self._build_force_list()

    def _on_checkbox_click(self, force_class: type):
        """Toggle a force on/off."""
        force_name = force_class.get_name()
        is_active = force_name in self._active_forces
        if self.on_force_toggle:
            self.on_force_toggle(force_class, not is_active)

    def _on_force_label_click(self, force_instance: object):
        """Enter edit mode for a force."""
        self.set_force_for_editing(force_instance)

    def _on_save_clicked(self, *_):
        if self.edited_force_instance:
            params = self.get_force_parameters()
            if self.on_force_params_update:
                self.on_force_params_update(self.edited_force_instance, params)
            self._cached_field_values.clear()
            # Reload editor with the (possibly normalised) values from the force
            self._build_parameter_editor()
            if self.error_label is not None and self.validation_errors:
                self.error_label.text = "\n".join(self.validation_errors)

    def _on_cancel_clicked(self, *_):
        self._cached_field_values.clear()
        self.edited_force_instance = None
        self._build_parameter_editor()

    # ------------------------------------------------------------------ public API
    def _get_current_page_forces(self) -> list[type]:
        start_idx = self.current_page * self.items_per_page
        end_idx = min(start_idx + self.items_per_page, len(self._available_force_types))
        return self._available_force_types[start_idx:end_idx]

    def set_available_force_types(self, force_types: list[type]):
        logger.info(f"set_available_force_types: {len(force_types)} types")
        self._available_force_types = list(force_types)
        self.total_pages = max(
            1, (len(force_types) + self.items_per_page - 1) // self.items_per_page
        )
        self.current_page = min(self.current_page, self.total_pages - 1)
        self._build_force_list()

    def update_active_forces(self, active_forces: list[object]):
        """Sync UI with the forces currently active in the engine."""
        new_active = {type(f).get_name(): f for f in active_forces}
        changed = {k: id(v) for k, v in new_active.items()} != {
            k: id(v) for k, v in self._active_forces.items()
        }
        self._active_forces = new_active

        if self.edited_force_instance:
            edited_name = type(self.edited_force_instance).get_name()
            if new_active.get(edited_name) is not self.edited_force_instance:
                # Force was removed (or replaced) -> close editor
                self._cached_field_values.clear()
                self.edited_force_instance = None
                self._build_parameter_editor()

        if changed:
            self._build_force_list()

    def set_force_for_editing(self, force_instance: object):
        self._cached_field_values.clear()
        self.edited_force_instance = force_instance
        self._build_parameter_editor()

    def get_force_parameters(self) -> dict[str, Any]:
        """Parse parameter values from the input widgets."""
        data: dict[str, Any] = {}
        errors: list[str] = []

        for name, field in self.force_param_fields.items():
            meta = self.force_parameters[name]
            typ = meta.get("type")
            try:
                if typ == "float":
                    value = float(field.text)
                    if not np.isfinite(value):
                        raise ValueError
                elif typ == "int":
                    value = int(float(field.text))
                elif typ == "bool":
                    value = field.text.strip().lower() in ("true", "1", "yes", "on")
                else:
                    value = field.text
                if typ in ("float", "int"):
                    lo, hi = meta.get("min"), meta.get("max")
                    if lo is not None and value < lo:
                        value = type(value)(lo)
                        errors.append(f"{meta.get('label', name)}: clamped to min")
                    if hi is not None and value > hi:
                        value = type(value)(hi)
                        errors.append(f"{meta.get('label', name)}: clamped to max")
                data[name] = value
            except (ValueError, TypeError):
                errors.append(f"{meta.get('label', name)}: invalid value, kept previous")
                data[name] = meta.get("default")

        for name, field in self.force_vector_fields.items():
            meta = self.force_parameters[name]
            default = meta.get("default")
            try:
                values = parse_vector_from_text(field.text)
                if default is not None and len(values) != len(list(default)):
                    raise ValueError
                data[name] = values
            except ValueError:
                errors.append(f"{meta.get('label', name)}: invalid vector, kept previous")
                data[name] = default

        for name, cb in self.force_bool_fields.items():
            data[name] = bool(cb.active)

        self.validation_errors = errors
        return data

    def on_draw(self):
        """Kept for API compatibility (Kivy widgets draw themselves)."""
        pass


__all__: list[str] = ["ForceManagerSection"]
