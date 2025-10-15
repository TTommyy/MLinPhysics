import arcade

from physics_sim.core import PhysicsEngine, Vector2D
from physics_sim.entities import Ball, RectangleObstacle
from physics_sim.rendering import ArcadeRenderer
from physics_sim.simulation.config import SimulationConfig
from physics_sim.ui import ControlPanel, InventoryPanel


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

        # Create renderer with viewport awareness
        self.renderer = ArcadeRenderer(
            config.screen_width,
            config.screen_height,
            config.sim_width,
            config.sim_height,
            viewport_x=config.viewport_x,
            viewport_width=config.viewport_width,
        )
        self.renderer.show_debug = config.show_debug_info

        # Create UI components
        self.control_panel = ControlPanel(
            config.screen_width, config.screen_height, config.control_panel_width
        )
        self.inventory_panel = InventoryPanel(
            config.screen_width, config.screen_height, config.inventory_panel_width
        )

        # Setup control panel callbacks
        self.control_panel.on_engine_change = self._on_engine_change
        self.control_panel.on_add_mode_toggle = self._on_add_mode_toggle

        # Add mode state
        self.add_mode = False
        self.selected_object_type = "Ball"

        # Track FPS
        self._fps_timer = 0.0
        self._fps_counter = 0
        self._current_fps = fps

        arcade.set_background_color(arcade.color.WHITE)

    def setup(self):
        """Initialize simulation state (called after window creation)."""
        # Enable control panel UI manager
        self.control_panel.enable()

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

        # Render UI panels (background)
        self.control_panel.render()
        entities = self.engine.get_entities()
        self.inventory_panel.render(entities)

        # Render simulation viewport
        # Draw viewport background (white)
        arcade.draw_lrbt_rectangle_filled(
            self._config.viewport_x,
            self._config.viewport_x + self._config.viewport_width,
            0,
            self.height,
            arcade.color.WHITE,
        )

        # Render grid (if enabled)
        self.renderer.render_grid()

        # Render entities
        self.renderer.render_entities(entities)

        # Render debug overlay
        engine_name = self.engine.__class__.__name__.replace("PhysicsEngine", "")
        self.renderer.render_debug_info(
            self._current_fps,
            len(entities),
            engine_name,
        )

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
            self.selected_object_type = (
                "Obstacle" if self.selected_object_type == "Ball" else "Ball"
            )
            self.control_panel.selected_object_type = self.selected_object_type
            self.control_panel._update_status()

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
        if not self.add_mode:
            return

        if button == arcade.MOUSE_BUTTON_LEFT:
            # Convert screen coordinates to physics coordinates
            phys_x = self.renderer.screen_to_physics_x(x)
            phys_y = self.renderer.screen_to_physics_y(y)

            # Create object based on selected type
            if self.selected_object_type == "Ball":
                ball = Ball(
                    position=Vector2D(phys_x, phys_y),
                    velocity=Vector2D(0, 0),
                    radius=0.2,
                    mass=1.0,
                    color=(255, 0, 0),
                )
                self.engine.add_entity(ball)

            elif self.selected_object_type == "Obstacle":
                obstacle = RectangleObstacle(
                    position=Vector2D(phys_x, phys_y),
                    width=1.0,
                    height=0.5,
                    color=(100, 100, 100),
                )
                self.engine.add_entity(obstacle)

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
        # TODO: Implement hot-swapping of engines
        # For now, just update the config
        self._config.engine_type = engine_name
        print(f"Engine change requested: {engine_name}")
        print("Note: Restart simulation to apply engine change")

    def _on_add_mode_toggle(self, enabled: bool):
        """Handle add mode toggle from control panel.

        Args:
            enabled: Whether add mode is enabled
        """
        self.add_mode = enabled

    def run(self):
        """Start the simulation."""
        self.setup()
        arcade.run()
