import logging
import uuid

import numpy as np
from kivy.app import App
from kivy.clock import Clock
from kivy.config import Config
from kivy.core.window import Window
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput

from physics_sim.core import PhysicsEngine
from physics_sim.forces import get_supported_forces
from physics_sim.simulation.config import SimulationConfig
from physics_sim.ui import EntitySelector
from physics_sim.ui.sections import (
    ControlPanelSection,
    EnergyManagerSection,
    ForceManagerSection,
    InventoryPanelSection,
    ViewportSection,
)

logger = logging.getLogger(__name__)

BACKGROUND_COLOR = (229 / 255, 228 / 255, 226 / 255, 1)  # platinum

# Kivy key codes used for shortcuts
KEY_NAMES = {27: "escape", 9: "tab", 103: "g", 102: "f", 97: "a", 32: "space"}


class Simulator(App):
    """Main simulation controller built on Kivy.

    Integrates:
    - Physics engine (pluggable via dependency injection)
    - Panel based UI (control panel, force manager, viewport, energy, inventory)
    - Input handling (mouse + keyboard)
    - Update/render loop driven by ``kivy.clock.Clock``
    """

    def __init__(
        self,
        config: SimulationConfig,
        engine: PhysicsEngine,
        fps: float = 60.0,
        **kwargs,
    ):
        """
        Args:
            config: Simulation configuration
            engine: Physics engine instance (numpy)
            fps: Target update/draw rate
        """
        super().__init__(**kwargs)
        self.title = config.window_title
        self._config = config
        self.engine = engine
        self._fps = fps
        self._is_setup = False
        self._update_event = None
        force_types = get_supported_forces()

        # ESC is handled by the simulator (exit add mode first, then quit)
        Config.set("kivy", "exit_on_escape", "0")

        # Layout manager (percentages / initial geometry)
        self.layout = config.create_layout_manager()

        # Sections
        self.control_section = ControlPanelSection(self.layout.control_panel)
        self.viewport_section = ViewportSection(
            self.layout.viewport, config.sim_width, config.sim_height
        )
        self.inventory_section = InventoryPanelSection(self.layout.inventory_panel)
        self.force_manager_section = ForceManagerSection(
            self.layout.top_placeholder, forces=force_types
        )
        self.energy_manager_section = EnergyManagerSection(
            self.layout.bottom_placeholder
        )
        self.root_widget = self._build_root()

        # Entity selection
        self.entity_selector = EntitySelector()

        # Setup callbacks
        self._setup_callbacks()

        # Add mode state
        self.add_mode = False

        # Track FPS
        self._fps_timer = 0.0
        self._fps_counter = 0
        self._current_fps = fps

        # Track energy / inventory refresh
        self._energy_timer = 0.0
        self._inventory_timer = 0.0
        self._simulation_time = 0.0
        self._forces_render_cache: dict | None = None

    # ------------------------------------------------------------------ layout
    def _build_root(self) -> BoxLayout:
        cfg = self._config
        cp = cfg.control_panel_width_pct
        inv = cfg.inventory_panel_width_pct
        vp = cfg.viewport_height_pct
        top = (1.0 - vp) / 2

        root = BoxLayout(orientation="horizontal")
        middle = BoxLayout(orientation="vertical", size_hint_x=max(0.05, 1.0 - cp - inv))

        self.control_section.size_hint_x = cp
        self.inventory_section.size_hint_x = inv
        self.force_manager_section.size_hint_y = top
        self.viewport_section.size_hint_y = vp
        self.energy_manager_section.size_hint_y = 1.0 - vp - top

        middle.add_widget(self.force_manager_section)
        middle.add_widget(self.viewport_section)
        middle.add_widget(self.energy_manager_section)

        root.add_widget(self.control_section)
        root.add_widget(middle)
        root.add_widget(self.inventory_section)
        root.size = (cfg.screen_width, cfg.screen_height)
        return root

    def _setup_callbacks(self):
        """Wire UI callbacks to simulator handlers."""
        placement = self.control_section.placement_controls
        display = self.control_section.display_controls
        editor = self.control_section.entity_editor

        placement.on_add_mode_toggle = self._on_add_mode_toggle
        placement.on_object_type_change = self._on_object_type_change
        display.on_grid_toggle = self._on_grid_toggle
        display.on_pause_toggle = self._on_pause_toggle
        display.on_forces_toggle = self._on_forces_toggle
        display.on_edit_entity = self._on_edit_entity_button
        editor.on_save = self._on_entity_editor_save
        editor.on_delete = self._on_entity_editor_delete

        self.force_manager_section.on_force_toggle = self._on_force_toggle
        self.force_manager_section.on_force_params_update = self._on_force_params_update

        self.viewport_section.on_click = self._on_viewport_click

    # ------------------------------------------------------------------ app
    def setup(self):
        """Initialize simulation state (idempotent)."""
        if self._is_setup:
            return
        logger.info("Setting up simulator")

        self.control_section.display_controls.set_grid_enabled(
            self.viewport_section.renderer.show_grid
        )
        self.control_section.display_controls.set_forces_enabled(
            self.viewport_section.renderer.show_forces
        )
        self.control_section.display_controls.set_pause_enabled(self.engine.is_paused())

        entity_types = self.engine.get_supported_entity_types()
        logger.info(
            f"Loaded {len(entity_types)} entity types: {[t.__name__ for t in entity_types]}"
        )
        self.control_section.placement_controls.set_available_entity_types(entity_types)

        active_forces = self.engine.get_forces()
        logger.info(
            f"Active forces in engine: {[type(f).__name__ for f in active_forces]}"
        )
        self.force_manager_section.update_active_forces(active_forces)

        self._refresh_inventory()
        self._update_status()
        self._is_setup = True
        logger.info("Simulator setup complete")

    def build(self):
        self.setup()
        return self.root_widget

    def on_start(self):
        Window.clearcolor = BACKGROUND_COLOR
        Window.bind(on_key_down=self._on_window_key_down)
        try:
            Window.size = (self._config.screen_width, self._config.screen_height)
            Window.maximize()
        except Exception as e:  # pragma: no cover - window provider specific
            logger.debug(f"Could not resize/maximize window: {e}")
        self._update_event = Clock.schedule_interval(self.on_update, 1.0 / self._fps)

    def on_stop(self):
        if self._update_event is not None:
            self._update_event.cancel()
            self._update_event = None
        Window.unbind(on_key_down=self._on_window_key_down)

    def run(self):
        """Start the simulation."""
        self.setup()
        super().run()

    def close(self):
        self.stop()

    def pause(self) -> None:
        """Toggle pause state of the simulation."""
        self.engine.toggle_pause()
        self.viewport_section.renderer.toggle_pause()
        self.control_section.display_controls.set_pause_enabled(self.engine.is_paused())
        self._update_status()

    # ------------------------------------------------------------------ loop
    def on_update(self, delta_time: float):
        """Advance physics, refresh periodic UI data and redraw."""
        if not self.engine.is_paused():
            self.engine.step(self._config.timestep)
            self._simulation_time += self._config.timestep

        # FPS
        self._fps_counter += 1
        self._fps_timer += delta_time
        if self._fps_timer >= 1.0:
            self._current_fps = self._fps_counter / self._fps_timer
            self._fps_counter = 0
            self._fps_timer = 0.0

        # Energy tracking
        if not self.engine.is_paused():
            self._energy_timer += delta_time
            if self._energy_timer >= self._config.energy_calc_interval:
                self._sample_energy()
                self._energy_timer = 0.0

        # Inventory / forces refresh
        self._inventory_timer += delta_time
        if self._inventory_timer >= self._config.inventory_update_interval:
            self._refresh_inventory()
            self.force_manager_section.update_active_forces(self.engine.get_forces())
            self._refresh_forces_render_cache()
            self._inventory_timer = 0.0

        self.on_draw()

    def _sample_energy(self):
        energies = self.engine.get_energies()
        self.energy_manager_section.add_energy_sample(
            ke=energies["kinetic"],
            pe=energies["potential"],
            total=energies["total"],
            time=self._simulation_time,
        )

    def _refresh_inventory(self):
        self.inventory_section.render_with_data(self.engine.get_inventory_data())

    def _refresh_forces_render_cache(self):
        renderer = self.viewport_section.renderer
        if not renderer.show_forces:
            self._forces_render_cache = None
            return
        points_list = renderer.get_grid_sample_points()
        sample_points = np.asarray(points_list, dtype=np.float64).reshape(-1, 2)
        self._forces_render_cache = self.engine.get_forces_render_data(sample_points)

    def _update_status(self):
        self.control_section.update_status(self.add_mode, self.engine.is_paused())

    def on_draw(self):
        """Render the viewport and refresh live status information."""
        renderer = self.viewport_section.renderer
        renderer.selected_entity_id = self.entity_selector.get_selected_entity()

        # The sample grid depends on the viewport geometry; refresh if it changed.
        if renderer.show_forces and (
            self._forces_render_cache is None or not renderer._grid_sample_points
        ):
            self._refresh_forces_render_cache()
        renderer.render_forces_data(self._forces_render_cache)

        render_data = self.engine.get_render_data()
        self.viewport_section.render_with_data(render_data)

        self.control_section.status_display.update_debug_info(
            fps=self._current_fps,
            entity_counts=self.engine.get_entity_counts_by_type(),
        )

    # ------------------------------------------------------------------ input
    def _any_text_input_focused(self) -> bool:
        for widget in self.root_widget.walk(restrict=True):
            if isinstance(widget, TextInput) and widget.focus:
                return True
        return False

    def _on_window_key_down(self, window, key, scancode, codepoint, modifiers):
        name = KEY_NAMES.get(key)
        if name is None:
            return False
        if name != "escape" and self._any_text_input_focused():
            return False  # let text inputs receive typed characters
        return bool(self.on_key_press(name, modifiers))

    def on_key_press(self, key, modifiers=None):
        """Handle keyboard shortcuts.

        Args:
            key: Key name ("g", "f", "a", "escape", "tab", "space") or Kivy key code
            modifiers: Active modifier keys
        Returns:
            True if the key was handled
        """
        if isinstance(key, int):
            key = KEY_NAMES.get(key, "")
        key = str(key).lower()
        logger.debug(f"Key pressed: {key} (modifiers: {modifiers})")

        if key == "g":
            self._on_grid_toggle()
        elif key == "f":
            self._on_forces_toggle()
        elif key == "space":
            self._on_pause_toggle()
        elif key == "a":
            self.control_section.placement_controls.set_add_mode(not self.add_mode)
            self._on_add_mode_toggle(not self.add_mode)
        elif key == "escape":
            if self.add_mode:
                logger.info("Exiting add mode via ESC")
                self.control_section.placement_controls.set_add_mode(False)
                self._on_add_mode_toggle(False)
            else:
                logger.info("Closing window via ESC")
                self.close()
        elif key == "tab" and self.add_mode:
            self.control_section.placement_controls.cycle_type()
        else:
            return False
        return True

    def _on_viewport_click(self, x: float, y: float, button: str):
        self.on_mouse_press(x, y, button, [])

    def on_mouse_press(self, x: float, y: float, button="left", modifiers=None):
        """Handle mouse clicks in the viewport.

        Args:
            x: Screen X coordinate (viewport widget space)
            y: Screen Y coordinate (viewport widget space)
            button: Mouse button ("left", "right", ...)
            modifiers: Active modifier keys
        """
        logger.debug(f"Mouse click: button={button}, screen=({x:.2f}, {y:.2f})")
        if button not in ("left", 1):
            return

        renderer = self.viewport_section.renderer
        phys_x = renderer.screen_to_physics_x(x)
        phys_y = renderer.screen_to_physics_y(y)
        click_pos = np.array([phys_x, phys_y], dtype=np.float64)

        if self.add_mode:
            self._add_entity_at(click_pos)
            return

        if self.engine.is_paused():
            render_data = self.engine.get_render_data()
            selected_id = self.entity_selector.select_entity(click_pos, render_data)
            if selected_id:
                self._load_entity_into_editor(selected_id)
            else:
                logger.debug("No entity selected at click position")
                self.control_section.entity_editor.clear()

    def _add_entity_at(self, click_pos: np.ndarray):
        entity_class = self.control_section.placement_controls.get_selected_entity_type()
        if not entity_class:
            logger.warning("Add mode active but no entity type selected")
            return
        width, height = self.engine.bounds
        if not (0 <= click_pos[0] <= width and 0 <= click_pos[1] <= height):
            logger.info("Click outside simulation bounds; entity not added")
            return
        try:
            entity = self.control_section.entity_editor.get_entity_object(
                click_pos, entity_id=self._generate_entity_id()
            )
            if entity is None:
                logger.error("Failed to create entity from editor")
                return
            self.engine.add_entity(entity)
            logger.info(
                f"Created {entity_class.__name__} at ({click_pos[0]:.2f}, {click_pos[1]:.2f})"
            )
            self._refresh_inventory()
        except Exception as e:
            logger.error(f"Failed to create entity: {e}")

    def _existing_entity_ids(self) -> set[str]:
        return {str(d["id"]) for d in self.engine.get_render_data()}

    def _generate_entity_id(self) -> str:
        """Create an 8-char entity id not used by any entity in the engine.

        (The default ``Entity`` id is a truncated memory address which can
        collide for entities created in quick succession.)
        """
        existing = self._existing_entity_ids()
        while True:
            candidate = uuid.uuid4().hex[:8]
            if candidate not in existing:
                return candidate

    def _load_entity_into_editor(self, entity_id: str) -> bool:
        entity = self.engine.get_entity_for_editing(entity_id)
        if entity is None:
            return False
        logger.info(f"Entity selected: {entity.__class__.__name__}")
        self.control_section.entity_editor.set_entity_instance(entity)
        return True

    def on_mouse_scroll(self, x: int, y: int, scroll_x: int, scroll_y: int):
        self.inventory_section.on_mouse_scroll(x, y, scroll_x, scroll_y)

    # ------------------------------------------------------------------ entities
    def add_entity(self, entity):
        """Convenience method to add entity to physics engine."""
        if entity.id in self._existing_entity_ids():
            entity.id = self._generate_entity_id()
        logger.info(
            f"Adding entity: {entity.__class__.__name__} at position {entity.position}"
        )
        self.engine.add_entity(entity)
        self._refresh_inventory()

    def clear_entities(self):
        """Remove all entities from simulation."""
        self.engine.clear()
        self.entity_selector.clear_selection()
        self.control_section.entity_editor.clear()
        self._refresh_inventory()

    # ------------------------------------------------------------------ UI callbacks
    def _on_add_mode_toggle(self, enabled: bool):
        self.add_mode = enabled
        logger.info(f"Add mode: {enabled}")
        if enabled:
            self.entity_selector.clear_selection()
            entity_class = self.control_section.placement_controls.get_selected_entity_type()
            if entity_class:
                self.control_section.entity_editor.set_entity_type(entity_class)
        else:
            self.control_section.entity_editor.clear()
        self._update_status()

    def _on_object_type_change(self, entity_class: type):
        logger.info(f"Entity type changed to: {entity_class.__name__}")
        if self.add_mode:
            self.control_section.entity_editor.set_entity_type(entity_class)

    def _on_grid_toggle(self):
        self.viewport_section.renderer.toggle_grid()
        self.control_section.display_controls.set_grid_enabled(
            self.viewport_section.renderer.show_grid
        )

    def _on_pause_toggle(self):
        self.pause()
        if not self.engine.is_paused():
            self.entity_selector.clear_selection()
            if self.control_section.entity_editor.mode == "edit":
                self.control_section.entity_editor.clear()
        self._refresh_inventory()

    def _on_edit_entity_button(self):
        """Reload the selected entity into the editor."""
        entity_id = self.entity_selector.get_selected_entity()
        if entity_id:
            self._load_entity_into_editor(entity_id)

    def _on_forces_toggle(self):
        renderer = self.viewport_section.renderer
        renderer.toggle_forces()
        self.control_section.display_controls.set_forces_enabled(renderer.show_forces)
        self._refresh_forces_render_cache()

    def _on_entity_editor_save(self, params: dict):
        logger.info("Saving entity from editor")
        editor = self.control_section.entity_editor
        entity = editor.entity_instance
        if not entity:
            return
        try:
            entity.update_physics_data(params)
            success = self.engine.update_entity_from_object(entity)
            if success:
                logger.info(f"Entity updated: {entity.__class__.__name__}")
                errors = list(editor.validation_errors)
                # Reload from the engine so the editor reflects stored values
                self._load_entity_into_editor(entity.id)
                if errors:
                    editor.validation_errors = errors
                    editor._report_errors()
                self._refresh_inventory()
            else:
                logger.error("Failed to update entity in engine")
        except Exception as e:
            logger.error(f"Failed to update entity: {e}")

    def _on_entity_editor_delete(self, entity_id):
        logger.info(f"Delete entity {entity_id} from engine")
        if not entity_id:
            return
        try:
            self.engine.remove_entity(entity_id)
        except Exception as e:
            logger.error(f"Failed to remove entity: {e}")
            return
        if self.entity_selector.get_selected_entity() == entity_id:
            self.entity_selector.clear_selection()
        self.control_section.entity_editor.clear()
        self._refresh_inventory()

    def _on_force_toggle(self, force_class: type, enabled: bool):
        force_name = force_class.__name__
        logger.info(f"Force toggle: {force_name} -> {enabled}")

        if enabled:
            self.engine.add_force(force_class())
            logger.info(f"Added force: {force_name}")
        else:
            for force in list(self.engine.get_forces()):
                if type(force).__name__ == force_name:
                    self.engine.remove_force(force)
                    logger.info(f"Removed force: {force_name}")
                    break

        self.force_manager_section.update_active_forces(self.engine.get_forces())
        self._refresh_forces_render_cache()

    def _on_force_params_update(self, force_instance, params: dict):
        force_name = type(force_instance).__name__
        logger.info(f"Updating force parameters: {force_name}")
        if force_instance.update_parameters(params):
            logger.info(f"Force parameters updated: {force_name}")
        else:
            logger.error(f"Failed to update force parameters: {force_name}")

        self.force_manager_section.update_active_forces(self.engine.get_forces())
        self._refresh_forces_render_cache()
