import arcade

from physics_sim.core import PhysicsEngine, Vector2D
from physics_sim.simulation.config import SimulationConfig
from physics_sim.ui import EntitySelector
from physics_sim.ui.sections import (
    ControlPanelSection,
    InventoryPanelSection,
    PlaceholderSection,
    ViewportSection,
)
from physics_sim.ui.views import EntityEditorView


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
            engine: Physics engine instance (numpy or pymunk)
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
            self.layout.control_panel, initial_engine="numpy"
        )
        self.viewport_section = ViewportSection(
            self.layout.viewport, config.sim_width, config.sim_height
        )
        self.inventory_section = InventoryPanelSection(self.layout.inventory_panel)
        self.top_placeholder = PlaceholderSection(
            self.layout.top_placeholder, "Top Panel (Future)"
        )
        self.bottom_placeholder = PlaceholderSection(
            self.layout.bottom_placeholder, "Bottom Panel (Future)"
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

        arcade.set_background_color(arcade.color.WHITE)

    def _setup_callbacks(self):
        """Setup control panel callbacks."""
        self.control_section.engine_controls.on_engine_change = self._on_engine_change
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

    def setup(self):
        """Initialize simulation state (called after window creation)."""
        # Enable control panel UI
        self.control_section.enable()

        # Set initial button states
        self.control_section.display_controls.set_grid_enabled(
            self.viewport_section.renderer.show_grid
        )

        # Load available entity types from engine
        entity_types = self.engine.get_supported_entity_types()
        self.control_section.placement_controls.set_available_entity_types(entity_types)

        # Maximize window on startup
        self.maximize()

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

        # Update FPS calculation
        self._fps_counter += 1
        self._fps_timer += delta_time
        if self._fps_timer >= 1.0:
            self._current_fps = self._fps_counter / self._fps_timer
            self._fps_counter = 0
            self._fps_timer = 0.0

    def on_draw(self):
        """Render the simulation."""
        self.clear()

        # Draw all sections manually
        self.viewport_section.on_draw()
        self.top_placeholder.on_draw()
        self.bottom_placeholder.on_draw()
        self.control_section.on_draw()
        self.inventory_section.on_draw()

        # Render viewport entities
        entities = self.engine.get_entities()
        self.viewport_section.render_with_data(entities)

        # Render inventory with data
        engine_name = self.engine.__class__.__name__.replace("PhysicsEngine", "")
        self.inventory_section.render_with_data(
            entities, self._current_fps, engine_name
        )

    def on_key_press(self, key: int, modifiers: int):
        """Handle keyboard input.

        Args:
            key: Key code that was pressed
            modifiers: Bitwise AND of modifier keys (shift, ctrl, etc.)
        """
        # Toggle grid with G
        if key == arcade.key.G:
            self.viewport_section.renderer.toggle_grid()
            self.control_section.display_controls.set_grid_enabled(
                self.viewport_section.renderer.show_grid
            )

        # Toggle add mode with A
        elif key == arcade.key.A:
            self.add_mode = not self.add_mode
            self.control_section.placement_controls.set_add_mode(self.add_mode)
            self.control_section.update_status()

        # Close window with ESC (or exit add mode if active)
        elif key == arcade.key.ESCAPE:
            if self.add_mode:
                self.add_mode = False
                self.control_section.placement_controls.set_add_mode(False)
                self.control_section.update_status()
            else:
                self.close()

        # Cycle object type with Tab (when in add mode)
        elif key == arcade.key.TAB and self.add_mode:
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
        if button == arcade.MOUSE_BUTTON_LEFT:
            # Convert screen coordinates to physics coordinates
            renderer = self.viewport_section.renderer
            phys_x = renderer.screen_to_physics_x(x)
            phys_y = renderer.screen_to_physics_y(y)
            click_pos = Vector2D(phys_x, phys_y)

            # In pause mode: allow entity selection
            if self.engine.is_paused():
                entities = self.engine.get_entities()
                selected = self.entity_selector.select_entity(click_pos, entities)
                if selected:
                    entity_type = selected.get_physics_data().get("type", "Entity")
                    self.control_section.display_controls.set_entity_selected(
                        True, entity_type
                    )
                else:
                    self.control_section.display_controls.set_entity_selected(False)
                return

            # In add mode: create new entity
            if not self.add_mode:
                return

            entity_class = (
                self.control_section.placement_controls.get_selected_entity_type()
            )
            if entity_class:
                # Store position for later use in editor
                self._pending_entity_position = Vector2D(phys_x, phys_y)
                # Show entity editor view
                self.show_entity_editor(entity_class=entity_class)

    def on_mouse_scroll(self, x: int, y: int, scroll_x: int, scroll_y: int):
        """Handle mouse scroll for inventory panel scrolling.

        Args:
            x: Mouse X position
            y: Mouse Y position
            scroll_x: Scroll amount X
            scroll_y: Scroll amount Y
        """
        self.inventory_section.on_mouse_scroll(x, y, scroll_x, scroll_y)

    def show_entity_editor(
        self, entity_class: type | None = None, entity_instance=None
    ):
        """Show entity editor view.

        Args:
            entity_class: Entity class for creation
            entity_instance: Entity instance for editing
        """
        editor_view = EntityEditorView(self, entity_class, entity_instance)
        self.show_view(editor_view)

    def add_entity(self, entity):
        """Convenience method to add entity to physics engine."""
        self.engine.add_entity(entity)

    def clear_entities(self):
        """Remove all entities from simulation."""
        self.engine.clear()

    def _on_engine_change(self, engine_name: str):
        """Handle engine change request from control panel.

        Args:
            engine_name: Name of the new engine ("numpy" or "pymunk")
        """
        # Update config
        self._config.engine_type = engine_name

        # Clear all entities
        self.engine.clear()

        # Create new engine based on selected type
        if engine_name == "numpy":
            from physics_sim import DragForce, GravityForce, NumpyPhysicsEngine

            new_engine = NumpyPhysicsEngine(
                gravity=self._config.gravity,
                bounds=(self._config.sim_width, self._config.sim_height),
            )
            new_engine.add_force(GravityForce(self._config.gravity))
            new_engine.add_force(DragForce())
        else:  # pymunk
            from physics_sim import DragForce, PymunkPhysicsEngine

            new_engine = PymunkPhysicsEngine(
                gravity=self._config.gravity,
                bounds=(self._config.sim_width, self._config.sim_height),
            )
            new_engine.add_force(DragForce())

        # Replace the engine
        self.engine = new_engine

        # Reload entity types for new engine
        entity_types = new_engine.get_supported_entity_types()
        self.control_section.placement_controls.set_available_entity_types(entity_types)

        print(f"Engine switched to: {engine_name}")

    def _on_add_mode_toggle(self, enabled: bool):
        """Handle add mode toggle from control panel.

        Args:
            enabled: Whether add mode is enabled
        """
        self.add_mode = enabled
        self.control_section.update_status()

    def _on_object_type_change(self, entity_class: type):
        """Handle object type change from control panel.

        Args:
            entity_class: Selected entity class
        """
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
        entity = self.entity_selector.get_selected_entity()
        if entity:
            self.show_entity_editor(entity_instance=entity)

    def run(self):
        """Start the simulation."""
        self.setup()
        arcade.run()
