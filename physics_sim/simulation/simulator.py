import arcade

from physics_sim.core import PhysicsEngine, Vector2D
from physics_sim.rendering import ArcadeRenderer
from physics_sim.simulation.config import SimulationConfig
from physics_sim.ui import (
    ControlPanel,
    EntitySelector,
    InventoryPanel,
    PlaceholderPanel,
)


class Simulator(arcade.Window):
    """Main simulation controller using Arcade's game loop.

    Integrates:
    - Physics engine (pluggable via dependency injection)
    - Renderer (Arcade-based visualization)
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

        # Create renderer with viewport region
        viewport = self.layout.viewport
        self.renderer = ArcadeRenderer(
            region=viewport, sim_width=config.sim_width, sim_height=config.sim_height
        )
        self.renderer.show_debug = config.show_debug_info

        # Create UI components with layout regions
        self.control_panel = ControlPanel(self.layout.control_panel)
        self.inventory_panel = InventoryPanel(self.layout.inventory_panel)

        # Create placeholder panels
        self.top_placeholder = PlaceholderPanel(
            self.layout.top_placeholder, "Top Panel (Future)", (220, 220, 240)
        )
        self.bottom_placeholder = PlaceholderPanel(
            self.layout.bottom_placeholder, "Bottom Panel (Future)", (220, 220, 240)
        )

        # Entity selection and editing
        self.entity_selector = EntitySelector()

        # Setup control panel callbacks
        self.control_panel.on_engine_change = self._on_engine_change
        self.control_panel.on_add_mode_toggle = self._on_add_mode_toggle
        self.control_panel.on_grid_toggle = self._on_grid_toggle
        self.control_panel.on_debug_toggle = self._on_debug_toggle
        self.control_panel.on_pause_toggle = self._on_pause_toggle
        self.control_panel.on_entity_save = self._on_entity_saved
        self.control_panel.on_entity_delete = self._on_entity_deleted
        self.control_panel.on_edit_entity = self._on_edit_entity_button

        # Add mode state
        self.add_mode = False

        # Track FPS
        self._fps_timer = 0.0
        self._fps_counter = 0
        self._current_fps = fps

        arcade.set_background_color(arcade.color.WHITE)

    def setup(self):
        """Initialize simulation state (called after window creation)."""
        # Enable control panel UI manager
        self.control_panel.enable()

        # Set initial button states
        self.control_panel.set_grid_enabled(self.renderer.show_grid)
        self.control_panel.set_debug_enabled(self.renderer.show_debug)

        # Load available entity types from engine
        entity_types = self.engine.get_supported_entity_types()
        self.control_panel.set_available_entity_types(entity_types)

        # Maximize window on startup
        self.maximize()

    def pause(self) -> None:
        """Toggle pause state of the simulation."""
        self.engine.toggle_pause()
        self.renderer.toggle_pause()

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

        # Render placeholder panels
        self.top_placeholder.render()
        self.bottom_placeholder.render()

        # Render simulation viewport
        # Draw viewport background (white)
        viewport = self.layout.viewport
        arcade.draw_lrbt_rectangle_filled(
            viewport.left,
            viewport.right,
            viewport.bottom,
            viewport.top,
            arcade.color.WHITE,
        )

        # Render grid (if enabled)
        self.renderer.render_grid()

        # Render entities
        entities = self.engine.get_entities()
        self.renderer.render_entities(entities)

        # Render UI panels (on top)
        self.control_panel.render()
        engine_name = self.engine.__class__.__name__.replace("PhysicsEngine", "")
        self.inventory_panel.render(entities, self._current_fps, engine_name)

    def on_key_press(self, key: int, modifiers: int):
        """Handle keyboard input.

        Args:
            key: Key code that was pressed
            modifiers: Bitwise AND of modifier keys (shift, ctrl, etc.)
        """
        # Toggle debug info with F1
        if key == arcade.key.F1:
            self.renderer.toggle_debug()

        # Toggle grid with G
        elif key == arcade.key.G:
            self.renderer.toggle_grid()

        # Toggle add mode with A
        elif key == arcade.key.A:
            self.add_mode = not self.add_mode
            self.control_panel.set_add_mode(self.add_mode)

        # Close window with ESC (or exit add mode if active)
        elif key == arcade.key.ESCAPE:
            if self.add_mode:
                self.add_mode = False
                self.control_panel.set_add_mode(False)
            else:
                self.close()

        # Cycle object type with Tab (when in add mode)
        elif key == arcade.key.TAB and self.add_mode:
            # Simulate button click to cycle through entity types
            self.control_panel._cycle_object_type(None)

        # TODO: Add more controls
        # - Space: Pause/resume simulation
        # - R: Reset simulation
        # - C: Clear all entities
        # - 1-9: Switch between preset scenarios

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
            phys_x = self.renderer.screen_to_physics_x(x)
            phys_y = self.renderer.screen_to_physics_y(y)
            click_pos = Vector2D(phys_x, phys_y)

            # In pause mode: allow entity selection
            if self.engine.is_paused():
                entities = self.engine.get_entities()
                selected = self.entity_selector.select_entity(click_pos, entities)
                if selected:
                    entity_type = selected.get_physics_data().get("type", "Entity")
                    self.control_panel.set_entity_selected(True, entity_type)
                else:
                    self.control_panel.set_entity_selected(False)
                return

            # In add mode: create new entity
            if not self.add_mode:
                return

            entity_class = self.control_panel.get_selected_entity_type()
            if entity_class:
                # Store position for later use in _on_entity_saved
                self._pending_entity_position = Vector2D(phys_x, phys_y)
                # Show editor for creating new entity
                self.control_panel.show_entity_editor(entity_class=entity_class)

    def on_mouse_drag(
        self, x: float, y: float, dx: float, dy: float, buttons: int, modifiers: int
    ):
        """Handle mouse drag events.

        Args:
            x: Current screen X coordinate
            y: Current screen Y coordinate
            dx: Change in X
            dy: Change in Y
            buttons: Which mouse buttons are pressed
            modifiers: Bitwise AND of modifier keys
        """
        # TODO: Implement ball launching (drag to set velocity)
        #
        # On drag start: create temporary ball
        # During drag: show trajectory preview
        # On release: set velocity based on drag vector and add to simulation
        pass

    def add_entity(self, entity):
        """Convenience method to add entity to physics engine."""
        self.engine.add_entity(entity)

    def clear_entities(self):
        """Remove all entities from simulation."""
        self.engine.clear()

    def on_mouse_scroll(self, x: int, y: int, scroll_x: int, scroll_y: int):
        """Handle mouse scroll for inventory panel scrolling.

        Args:
            x: Mouse X position
            y: Mouse Y position
            scroll_x: Scroll amount X
            scroll_y: Scroll amount Y
        """
        self.inventory_panel.on_mouse_scroll(x, y, scroll_x, scroll_y)

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
        self.control_panel.set_available_entity_types(entity_types)

        print(f"Engine switched to: {engine_name}")

    def _on_add_mode_toggle(self, enabled: bool):
        """Handle add mode toggle from control panel.

        Args:
            enabled: Whether add mode is enabled
        """
        self.add_mode = enabled

    def _on_grid_toggle(self):
        """Handle grid toggle from control panel."""
        self.renderer.toggle_grid()
        self.control_panel.set_grid_enabled(self.renderer.show_grid)

    def _on_debug_toggle(self):
        """Handle debug info toggle from control panel."""
        self.renderer.toggle_debug()
        self.control_panel.set_debug_enabled(self.renderer.show_debug)

    def _on_pause_toggle(self):
        """Handle pause toggle from control panel."""
        self.pause()
        # Clear selection and update UI when toggling pause
        if not self.engine.is_paused():
            self.entity_selector.clear_selection()
            self.control_panel.set_entity_selected(False)

    def _on_edit_entity_button(self):
        """Handle edit entity button click."""
        entity = self.entity_selector.get_selected_entity()
        if entity:
            self.control_panel.show_entity_editor(entity_instance=entity)

    def _on_entity_saved(self, data: dict, entity_instance, entity_class: type):
        """Handle entity save from control panel editor.

        Args:
            data: Updated parameter values
            entity_instance: Existing entity (None for creation)
            entity_class: Entity class (used for creation)
        """
        if entity_instance:
            # Editing existing entity
            entity_instance.update_physics_data(data)
        else:
            # Creating new entity - get position from pending_entity_position
            position = getattr(self, "_pending_entity_position", Vector2D(0, 0))

            # Handle velocity
            velocity_x = data.get("velocity_x", 0.0)
            velocity_y = data.get("velocity_y", 0.0)
            velocity = Vector2D(velocity_x, velocity_y)
            mass = data.get("mass", 1.0)

            # Create entity
            entity = entity_class(
                position=position,
                velocity=velocity,
                mass=mass,
            )

            # Apply other parameters
            entity.update_physics_data(data)

            # Add to engine
            self.engine.add_entity(entity)

    def _on_entity_deleted(self, entity_id: str):
        """Handle entity deletion."""
        self.engine.remove_entity(entity_id)
        self.entity_selector.clear_selection()
        self.control_panel.set_entity_selected(False)

    def run(self):
        """Start the simulation."""
        self.setup()
        arcade.run()
