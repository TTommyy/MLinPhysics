import logging

import arcade
import numpy as np

from physics_sim.core import PhysicsEngine
from physics_sim.simulation.config import SimulationConfig
from physics_sim.ui import EntitySelector
from physics_sim.ui.sections import (
    ControlPanelSection,
    DebugInfoSection,
    EnergyManagerSection,
    InventoryPanelSection,
    ViewportSection,
)

logger = logging.getLogger(__name__)


class Simulator(arcade.Window):
    """Main simulation controller using Arcade's game loop.

    Integrates:
    - Physics engine (pluggable via dependency injection)
    - Section-based UI architecture
    - Input handling
    - Update/render loop
    """

    def __init__(
        self,
        config: SimulationConfig,
        engine: PhysicsEngine,
        fps: float = 60.0,
    ):
        """
        Args:
            config: Simulation configuration
            engine: Physics engine instance (numpy )
        """
        super().__init__(
            width=config.screen_width,
            height=config.screen_height,
            title=config.window_title,
            update_rate=(1 / fps),
        )

        self._config = config
        self.engine = engine

        # Create layout manager
        self.layout = config.create_layout_manager()

        # Create sections (manually managed)
        self.control_section = ControlPanelSection(
            self.layout.control_panel,
            initial_engine="numpy",
        )
        self.viewport_section = ViewportSection(
            self.layout.viewport, config.sim_width, config.sim_height
        )
        self.inventory_section = InventoryPanelSection(self.layout.inventory_panel)
        self.debug_info_section = DebugInfoSection(self.layout.top_placeholder)
        self.energy_manager_section = EnergyManagerSection(
            self.layout.bottom_placeholder
        )

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

        # Track energy
        self._energy_timer = 0.0
        self._simulation_time = 0.0

        arcade.set_background_color(arcade.color.PLATINUM)

    def _setup_callbacks(self):
        """Setup control panel callbacks."""
        self.control_section.placement_controls.on_add_mode_toggle = (
            self._on_add_mode_toggle
        )
        self.control_section.placement_controls.on_object_type_change = (
            self._on_object_type_change
        )
        self.control_section.display_controls.on_grid_toggle = self._on_grid_toggle
        self.control_section.display_controls.on_pause_toggle = self._on_pause_toggle
        self.control_section.display_controls.on_edit_entity = (
            self._on_edit_entity_button
        )
        self.control_section.entity_editor.on_save = self._on_entity_editor_save

    def setup(self):
        """Initialize simulation state (called after window creation)."""
        logger.info("Setting up simulator")

        # Enable UI sections
        self.control_section.enable()
        self.inventory_section.enable()

        # Set initial button states
        self.control_section.display_controls.set_grid_enabled(
            self.viewport_section.renderer.show_grid
        )

        # Load available entity types from engine
        entity_types = self.engine.get_supported_entity_types()
        logger.info(
            f"Loaded {len(entity_types)} entity types: {[t.__name__ for t in entity_types]}"
        )
        self.control_section.placement_controls.set_available_entity_types(entity_types)

        # Maximize window on startup
        self.maximize()
        logger.info("Simulator setup complete")

    def pause(self) -> None:
        """Toggle pause state of the simulation."""
        self.engine.toggle_pause()
        self.viewport_section.renderer.toggle_pause()

    def on_update(self, delta_time: float):
        """Update physics simulation.

        Args:
            delta_time: Time elapsed since last update (seconds)
        """
        # Use fixed timestep for deterministic physics
        self.engine.step(self._config.timestep)

        # Update simulation time
        if not self.engine.is_paused():
            self._simulation_time += self._config.timestep

        # Update FPS calculation
        self._fps_counter += 1
        self._fps_timer += delta_time
        if self._fps_timer >= 1.0:
            self._current_fps = self._fps_counter / self._fps_timer
            self._fps_counter = 0
            self._fps_timer = 0.0

        # Update energy tracking
        self._energy_timer += delta_time
        if self._energy_timer >= self._config.energy_calc_interval:
            energies = self.engine.get_energies()
            self.energy_manager_section.add_energy_sample(
                ke=energies["kinetic"],
                pe=energies["potential"],
                total=energies["total"],
                time=self._simulation_time,
            )
            inventory_data = self.engine.get_inventory_data()
            self.inventory_section.render_with_data(inventory_data)
            self._energy_timer = 0.0

    def on_draw(self):
        """Render the simulation."""
        self.clear()

        # Draw all sections manually
        self.viewport_section.on_draw()
        self.debug_info_section.on_draw()
        self.energy_manager_section.on_draw()
        self.control_section.on_draw()
        self.inventory_section.on_draw()

        # Render viewport entities using data from engine
        render_data = self.engine.get_render_data()
        self.viewport_section.render_with_data(render_data)

        # Render debug info
        entity_counts = self.engine.get_entity_counts_by_type()
        self.debug_info_section.render_with_data(
            fps=self._current_fps,
            entity_counts=entity_counts,
        )

    def on_key_press(self, key: int, modifiers: int):
        """Handle keyboard input.

        Args:
            key: Key code that was pressed
            modifiers: Bitwise AND of modifier keys (shift, ctrl, etc.)
        """
        logger.debug(f"Key pressed: {key} (modifiers: {modifiers})")

        # Toggle grid with G
        if key == arcade.key.G:
            logger.info("Toggling grid display")
            self.viewport_section.renderer.toggle_grid()
            self.control_section.display_controls.set_grid_enabled(
                self.viewport_section.renderer.show_grid
            )

        # Toggle add mode with A
        elif key == arcade.key.A:
            self.add_mode = not self.add_mode
            logger.info(f"Add mode toggled: {self.add_mode}")
            self.control_section.placement_controls.set_add_mode(self.add_mode)
            self.control_section.update_status()

        # Close window with ESC (or exit add mode if active)
        elif key == arcade.key.ESCAPE:
            if self.add_mode:
                logger.info("Exiting add mode via ESC")
                self.add_mode = False
                self.control_section.placement_controls.set_add_mode(False)
                self.control_section.update_status()
            else:
                logger.info("Closing window via ESC")
                self.close()

        # Cycle object type with Tab (when in add mode)
        elif key == arcade.key.TAB and self.add_mode:
            logger.info("Cycling entity type")
            self.control_section.placement_controls.cycle_type()
            self.control_section.update_status()

    def on_mouse_press(self, x: float, y: float, button: int, modifiers: int):
        """Handle mouse clicks.

        Args:
            x: Screen X coordinate
            y: Screen Y coordinate
            button: Mouse button that was clicked
            modifiers: Bitwise AND of modifier keys
        """
        logger.debug(f"Mouse click: button={button}, screen=({x:.1f}, {y:.1f})")

        if button == arcade.MOUSE_BUTTON_LEFT:
            # Convert screen coordinates to physics coordinates
            renderer = self.viewport_section.renderer
            phys_x = renderer.screen_to_physics_x(x)
            phys_y = renderer.screen_to_physics_y(y)
            click_pos = np.array([phys_x, phys_y])

            logger.debug(f"Physics coords: ({phys_x:.2f}, {phys_y:.2f})")
            logger.debug(
                f"Add mode: {self.add_mode}, Paused: {self.engine.is_paused()}"
            )

            # In add mode: create new entity (takes priority)
            if self.add_mode:
                entity_class = (
                    self.control_section.placement_controls.get_selected_entity_type()
                )
                logger.info(f"Add mode active, selected entity type: {entity_class}")
                if entity_class:
                    try:
                        # Get fully constructed entity from editor
                        entity = self.control_section.entity_editor.get_entity_object(
                            click_pos
                        )

                        if entity:
                            # Add to engine
                            self.engine.add_entity(entity)
                            logger.info(
                                f"Created {entity_class.__name__} at ({phys_x:.2f}, {phys_y:.2f})"
                            )
                        else:
                            logger.error("Failed to create entity from editor")
                    except Exception as e:
                        logger.error(f"Failed to create entity: {e}")
                else:
                    logger.warning("Add mode active but no entity type selected")
                return

            # In pause mode: allow entity selection
            if self.engine.is_paused():
                logger.debug("Paused mode: attempting entity selection")
                render_data = self.engine.get_render_data()
                selected_id = self.entity_selector.select_entity(click_pos, render_data)
                if selected_id:
                    # Get entity for editing
                    entity = self.engine.get_entity_for_editing(selected_id)
                    if entity:
                        entity_type = entity.__class__.__name__
                        logger.info(f"Entity selected: {entity_type}")
                        self.control_section.display_controls.set_entity_selected(
                            True, entity_type
                        )
                        # Load entity into editor for editing
                        self.control_section.entity_editor.set_entity_instance(entity)
                else:
                    logger.debug("No entity selected at click position")
                    self.control_section.display_controls.set_entity_selected(False)
                    # Clear editor if nothing selected
                    if not self.add_mode:
                        self.control_section.entity_editor.clear()

    def on_mouse_scroll(self, x: int, y: int, scroll_x: int, scroll_y: int):
        """Handle mouse scroll for inventory panel scrolling.

        Args:
            x: Mouse X position
            y: Mouse Y position
            scroll_x: Scroll amount X
            scroll_y: Scroll amount Y
        """
        self.inventory_section.on_mouse_scroll(x, y, scroll_x, scroll_y)

    def add_entity(self, entity):
        """Convenience method to add entity to physics engine."""
        logger.info(
            f"Adding entity: {entity.__class__.__name__} at position {entity.position}"
        )
        self.engine.add_entity(entity)

    def clear_entities(self):
        """Remove all entities from simulation."""
        self.engine.clear()

    def _on_add_mode_toggle(self, enabled: bool):
        """Handle add mode toggle from control panel.

        Args:
            enabled: Whether add mode is enabled
        """
        self.add_mode = enabled
        logger.info(f"Add mode: {enabled}")

        if enabled:
            # Show entity editor in add mode
            entity_class = (
                self.control_section.placement_controls.get_selected_entity_type()
            )
            if entity_class:
                self.control_section.entity_editor.set_entity_type(entity_class)
        else:
            # Clear entity editor when exiting add mode
            self.control_section.entity_editor.clear()

        self.control_section.update_status()

    def _on_object_type_change(self, entity_class: type):
        """Handle object type change from control panel.

        Args:
            entity_class: Selected entity class
        """
        logger.info(f"Entity type changed to: {entity_class.__name__}")

        # Update entity editor if in add mode
        if self.add_mode:
            self.control_section.entity_editor.set_entity_type(entity_class)

        self.control_section.update_status()

    def _on_grid_toggle(self):
        """Handle grid toggle from control panel."""
        self.viewport_section.renderer.toggle_grid()
        self.control_section.display_controls.set_grid_enabled(
            self.viewport_section.renderer.show_grid
        )

    def _on_pause_toggle(self):
        """Handle pause toggle from control panel."""
        self.pause()
        # Clear selection and update UI when toggling pause
        if not self.engine.is_paused():
            self.entity_selector.clear_selection()
            self.control_section.display_controls.set_entity_selected(False)
        # Update edit button availability
        self.control_section.display_controls.update_edit_button_availability()

    def _on_edit_entity_button(self):
        """Handle edit entity button click."""
        entity_id = self.entity_selector.get_selected_entity()
        if entity_id:
            entity = self.engine.get_entity_for_editing(entity_id)
            if entity:
                logger.info(f"Loading entity for editing: {entity.__class__.__name__}")
                self.control_section.entity_editor.set_entity_instance(entity)

    def _on_entity_editor_save(self, params: dict):
        """Handle save from entity editor panel.

        Args:
            params: Dictionary of updated entity parameters
        """
        logger.info("Saving entity from editor")
        entity = self.control_section.entity_editor.entity_instance
        if entity:
            try:
                # Update entity object from params
                entity.update_physics_data(params)
                # Update arrays in engine from modified entity object
                success = self.engine.update_entity_from_object(entity)
                if success:
                    logger.info(f"Entity updated: {entity.__class__.__name__}")
                else:
                    logger.error("Failed to update entity in engine")
            except Exception as e:
                logger.error(f"Failed to update entity: {e}")

    def run(self):
        """Start the simulation."""
        self.setup()
        arcade.run()
