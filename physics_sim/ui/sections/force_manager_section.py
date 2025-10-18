import logging
from typing import Any

import arcade
import arcade.gui

from physics_sim.core import LayoutRegion
from physics_sim.ui.sections.base_section import BaseSection
from physics_sim.ui.utils import format_vector_for_display, parse_vector_from_text

logger = logging.getLogger(__name__)


class ForceManagerSection(BaseSection):
    """Top panel section for managing forces with pagination and parameter editing."""

    def __init__(self, region: LayoutRegion, forces: list[type] = []):
        super().__init__(
            region,
            background_color=arcade.color.LIGHT_SKY_BLUE,
            border_color=arcade.color.GRAY,
        )
        logger.info(f"ForceManagerSection init: {region}")

        self.items_per_page = 1
        self.ui_manager = arcade.gui.UIManager()

        self._available_force_types: list[type] = forces
        self.total_pages = max(
            1, (len(forces) + self.items_per_page - 1) // self.items_per_page
        )
        self.current_page = 0
        self._active_forces: dict[str, object] = {}

        # Mode tracking: "view" (list with checkboxes) or "edit" (parameter editing)
        self.mode = "view"
        self.edited_force_instance: object | None = None
        self.force_parameters: dict[str, dict[str, Any]] = {}

        # UI button references
        self.force_checkboxes: dict[str, arcade.gui.UITextureButton] = {}
        self.prev_button: arcade.gui.UIFlatButton | None = None
        self.next_button: arcade.gui.UIFlatButton | None = None
        self.edit_buttons: dict[str, arcade.gui.UIFlatButton] = {}
        self.force_param_fields: dict[str, arcade.gui.UIInputText] = {}
        self.force_vector_fields: dict[str, arcade.gui.UIInputText] = {}

        self._page_text = arcade.Text(
            "Page 1/1",
            int(self.region.center_x),
            int(self.region.bottom + 15),
            arcade.color.BLACK,
            10,
            anchor_x="center",
            anchor_y="bottom",
        )
        self._force_name_texts: dict[str, arcade.Text] = {}
        self._force_param_label_texts: dict[str, arcade.Text] = {}
        self._edit_title_text: arcade.Text | None = None

        # Callbacks
        self.on_force_toggle = None
        self.on_force_params_update = None

        self._build_view_mode()

    def _update_page_text(self) -> None:
        """Update page label text and position."""
        self._page_text.text = f"Page {self.current_page + 1}/{self.total_pages}"
        self._page_text.x = int(self.region.center_x)
        self._page_text.y = int(self.region.bottom + 15)

    def _build_view_mode(self):
        """Build view mode UI with force list and pagination."""
        self.ui_manager.clear()
        self.force_checkboxes.clear()
        self.edit_buttons.clear()
        self.force_param_fields.clear()
        self.force_vector_fields.clear()
        self._force_name_texts.clear()
        self._force_param_label_texts.clear()
        self.mode = "view"

        # Create pagination buttons at bottom
        button_width = 70
        button_height = 20
        button_margin = 15
        button_y = self.region.bottom + 5

        self.prev_button = arcade.gui.UIFlatButton(
            text="Prev",
            width=button_width,
            height=button_height,
            x=int(self.region.left + button_margin),
            y=int(button_y),
        )
        self.prev_button.on_click = self._on_prev_page
        self.prev_button.disabled = self.current_page == 0
        self.ui_manager.add(self.prev_button)

        self.next_button = arcade.gui.UIFlatButton(
            text="Next",
            width=button_width,
            height=button_height,
            x=int(self.region.right - button_width - button_margin),
            y=int(button_y),
        )
        self.next_button.on_click = self._on_next_page
        self.next_button.disabled = self.current_page >= self.total_pages - 1
        self.ui_manager.add(self.next_button)

        # Add forces for current page
        page_forces = self._get_current_page_forces()
        logger.info(f"REBUILD: forces={[f.__name__ for f in page_forces]}")

        y_offset = self.region.top - 100
        for force_class in page_forces:
            force_name = force_class.__name__
            is_active = force_name in self._active_forces
            logger.info(f"REBUILD: {force_name}, active={is_active}")

            # Checkbox
            checkbox = arcade.gui.UITextureButton(
                x=int(self.region.left + 20),
                y=int(y_offset),
                width=24,
                height=24,
                texture=self._get_checkbox_texture(is_active),
            )
            checkbox.on_click = lambda e, fc=force_class: self._on_checkbox_click(fc)
            self.ui_manager.add(checkbox)
            self.force_checkboxes[force_name] = checkbox

            # Force name goes to text cache (drawn separately)
            self._force_name_texts[force_name] = arcade.Text(
                force_name,
                int(self.region.left + 55),
                int(y_offset),
                arcade.color.BLACK,
                12,
                bold=True,
                anchor_y="center",
            )

            # Edit button if force is active
            if is_active:
                force_instance = self._active_forces[force_name]
                edit_btn = arcade.gui.UIFlatButton(
                    text="Edit",
                    width=50,
                    height=24,
                    x=int(self.region.left + 160),
                    y=int(y_offset - 12),
                )
                edit_btn.on_click = (
                    lambda e, fi=force_instance: self._on_force_label_click(fi)
                )
                self.ui_manager.add(edit_btn)
                self.edit_buttons[force_name] = edit_btn

            y_offset -= 35

        # Update page text
        self._update_page_text()

    def _build_edit_mode(self):
        """Build edit mode UI with force parameter editing."""
        self.ui_manager.clear()
        self.force_checkboxes.clear()
        self.edit_buttons.clear()
        self.force_param_fields.clear()
        self.force_vector_fields.clear()
        self._force_name_texts.clear()
        self._force_param_label_texts.clear()
        self.mode = "edit"

        if not self.edited_force_instance:
            return

        force_name = type(self.edited_force_instance).__name__
        self._edit_title_text = arcade.Text(
            f"Edit {force_name}",
            int(self.region.left + 15),
            int(self.region.top - 25),
            arcade.color.DARK_BLUE,
            14,
            bold=True,
            anchor_y="top",
        )

        # Get parameters from force instance
        self.force_parameters = self.edited_force_instance.get_settable_parameters()

        # Create input fields for each parameter
        y_offset = self.region.top - 60
        for param_name, param_meta in self.force_parameters.items():
            param_type = param_meta.get("type")
            label = param_meta.get("label", param_name)
            default = param_meta.get("default")

            # Store label as Text object
            self._force_param_label_texts[param_name] = arcade.Text(
                label,
                int(self.region.left + 15),
                int(y_offset),
                arcade.color.BLACK,
                9,
                anchor_y="top",
            )

            if param_type == "vector":
                self._add_vector_field(param_name, default, y_offset)
            else:
                self._add_input_field(param_name, default, y_offset)

            y_offset -= 40

        # Add Save and Cancel buttons
        button_y = self.region.bottom + 5
        button_width = 80
        button_height = 25

        save_btn = arcade.gui.UIFlatButton(
            text="Save",
            width=button_width,
            height=button_height,
            x=int(self.region.left + 15),
            y=int(button_y),
        )
        save_btn.on_click = self._on_save_clicked
        self.ui_manager.add(save_btn)

        cancel_btn = arcade.gui.UIFlatButton(
            text="Cancel",
            width=button_width,
            height=button_height,
            x=int(self.region.left + button_width + 25),
            y=int(button_y),
        )
        cancel_btn.on_click = self._on_cancel_clicked
        self.ui_manager.add(cancel_btn)

    def _add_input_field(self, param_name: str, default_value: Any, y_offset: float):
        """Add an input field for a scalar parameter."""
        inp = arcade.gui.UIInputText(
            text=str(default_value),
            x=int(self.region.left + 15),
            y=int(y_offset - 30),
            width=200,
            height=20,
            text_color=arcade.color.BLACK_BEAN,
        )
        self.force_param_fields[param_name] = inp
        self.ui_manager.add(inp)

    def _add_vector_field(self, param_name: str, default_value: list, y_offset: float):
        """Add a vector input field for [x, y] parameters."""
        text_value = format_vector_for_display(default_value)
        inp = arcade.gui.UIInputText(
            text=text_value,
            x=int(self.region.left + 15),
            y=int(y_offset - 30),
            width=200,
            height=20,
            text_color=arcade.color.BLACK_BEAN,
        )
        self.force_vector_fields[param_name] = inp
        self.ui_manager.add(inp)

    def _on_prev_page(self, event):
        """Handle previous page button click."""
        if self.current_page > 0:
            self.current_page -= 1
            self._build_view_mode()

    def _on_next_page(self, event):
        """Handle next page button click."""
        if self.current_page < self.total_pages - 1:
            self.current_page += 1
            self._build_view_mode()

    def _on_checkbox_click(self, force_class: type):
        """Handle checkbox click to toggle force."""
        force_name = force_class.__name__
        is_active = force_name in self._active_forces
        logger.info(f"Checkbox clicked: {force_name}, current active={is_active}")
        if self.on_force_toggle:
            self.on_force_toggle(force_class, not is_active)

    def _on_force_label_click(self, force_instance: object):
        """Handle force label click to enter edit mode."""
        logger.info(f"Force selected for editing: {type(force_instance).__name__}")
        self.set_force_for_editing(force_instance)

    def _on_save_clicked(self, event):
        """Handle save button click in edit mode."""
        if self.edited_force_instance:
            params = self.get_force_parameters()
            if self.on_force_params_update:
                self.on_force_params_update(self.edited_force_instance, params)
            self._build_view_mode()

    def _on_cancel_clicked(self, event):
        """Handle cancel button click in edit mode."""
        self.edited_force_instance = None
        self._build_view_mode()

    def _get_checkbox_texture(self, checked: bool):
        """Get checkbox texture (colored square)."""
        color = arcade.color.GREEN if checked else arcade.color.LIGHT_GRAY
        return arcade.make_soft_square_texture(24, color, 255, 255)

    def _get_current_page_forces(self) -> list[type]:
        """Get forces for current page."""
        start_idx = self.current_page * self.items_per_page
        end_idx = min(start_idx + self.items_per_page, len(self._available_force_types))
        return self._available_force_types[start_idx:end_idx]

    def set_available_force_types(self, force_types: list[type]):
        """Set available force types to display."""
        logger.info(f"set_available_force_types: {len(force_types)} types")
        self._available_force_types = force_types
        self.total_pages = max(
            1, (len(force_types) + self.items_per_page - 1) // self.items_per_page
        )
        self.current_page = min(self.current_page, self.total_pages - 1)
        if self.mode == "view":
            self._build_view_mode()

    def update_active_forces(self, active_forces: list[object]):
        """Update the list of currently active force instances."""
        self._active_forces = {type(f).__name__: f for f in active_forces}
        if self.mode == "view":
            self._build_view_mode()

    def set_force_for_editing(self, force_instance: object):
        """Set a force instance for parameter editing."""
        self.edited_force_instance = force_instance
        self._build_edit_mode()

    def get_force_parameters(self) -> dict[str, Any]:
        """Get current parameter values from input fields."""
        data: dict[str, Any] = {}

        # Parse regular input fields
        for name, field in self.force_param_fields.items():
            meta = self.force_parameters[name]
            typ = meta.get("type")
            try:
                if typ == "float":
                    data[name] = float(field.text)
                elif typ == "int":
                    data[name] = int(field.text)
                elif typ == "bool":
                    data[name] = field.text.lower() in ("true", "1", "yes")
                else:
                    data[name] = field.text
            except (ValueError, TypeError):
                data[name] = meta.get("default")

        # Parse vector fields
        for name, field in self.force_vector_fields.items():
            try:
                data[name] = parse_vector_from_text(field.text)
            except ValueError:
                data[name] = self.force_parameters[name].get("default")

        return data

    def enable(self):
        """Enable UI interaction."""
        self.ui_manager.enable()

    def disable(self):
        """Disable UI interaction."""
        self.ui_manager.disable()

    def on_draw(self):
        """Draw the section."""
        self.draw_background()
        self.draw_border()
        self.ui_manager.draw()

        # Draw Text objects after UI manager (reliable macOS rendering)
        if self.mode == "view":
            self._page_text.draw()
            for text_obj in self._force_name_texts.values():
                text_obj.draw()
        elif self.mode == "edit":
            if self._edit_title_text:
                self._edit_title_text.draw()
            for text_obj in self._force_param_label_texts.values():
                text_obj.draw()

    def on_update(self, delta_time: float):
        """Update section."""
        pass


__all__: list[str] = ["ForceManagerSection"]
