from kivy.graphics import Color, InstructionGroup, Line, Rectangle

from physics_sim.core import LayoutRegion, Renderer

from ._forces_renderer_mixin import ForcesRendererMixin
from ._grid_renderer_mixin import GridRendererMixin
from ._pause_manager_mixin import PauseManagerMixin
from ._shape_renderer_mixin import ShapeRendererMixin
from ._text_cache import TextTextureCache

VIEWPORT_BG_COLOR = (229 / 255, 228 / 255, 226 / 255, 1)  # platinum
SIM_AREA_BG_COLOR = (250 / 255, 250 / 255, 250 / 255, 1)
SIM_AREA_BORDER_COLOR = (120 / 255, 120 / 255, 120 / 255, 1)


class KivyRenderer(
    ShapeRendererMixin,
    GridRendererMixin,
    ForcesRendererMixin,
    PauseManagerMixin,
    Renderer,
):
    """Renderer drawing the simulation with Kivy canvas instructions.

    Handles:
    - Coordinate system transformation (physics space -> widget space)
    - Entity rendering (circles, rectangles)
    - Grid rendering with coordinate labels
    - Force vector field and overlays

    The renderer owns an ``InstructionGroup`` (``self.instructions``) which is
    attached to a widget canvas (see ``ViewportSection``). Draw order is:
    background -> grid -> forces -> entities.
    """

    def __init__(self, region: LayoutRegion, sim_width: float, sim_height: float):
        """
        Args:
            region: Viewport region (in widget/window coordinates)
            sim_width: Simulation width in physics units
            sim_height: Simulation height in physics units
        """
        Renderer.__init__(
            self, max(region.width, 1), max(region.height, 1), sim_width, sim_height
        )
        self.region = LayoutRegion(region.x, region.y, region.width, region.height)
        self.sim_width = sim_width
        self.sim_height = sim_height
        self._paused = False
        self._offset_x = 0.0
        self._offset_y = 0.0
        self._text_cache = TextTextureCache()

        self.instructions = InstructionGroup()
        self.background_group = InstructionGroup()
        self.grid_group = InstructionGroup()
        self.forces_group = InstructionGroup()
        self.entities_group = InstructionGroup()
        for group in (
            self.background_group,
            self.grid_group,
            self.forces_group,
            self.entities_group,
        ):
            self.instructions.add(group)

        self._bg_color = Color(*VIEWPORT_BG_COLOR)
        self._bg_rect = Rectangle()
        self._sim_color = Color(*SIM_AREA_BG_COLOR)
        self._sim_rect = Rectangle()
        self._sim_border_color = Color(*SIM_AREA_BORDER_COLOR)
        self._sim_border = Line(rectangle=(0, 0, 0, 0), width=1.2)
        for instr in (
            self._bg_color,
            self._bg_rect,
            self._sim_color,
            self._sim_rect,
            self._sim_border_color,
            self._sim_border,
        ):
            self.background_group.add(instr)

        self._init_shape_renderer()
        self._init_grid_renderer()
        self._init_forces_renderer()
        self.set_region(region.x, region.y, region.width, region.height)

    # ------------------------------------------------------------------ geometry
    def set_region(self, x: float, y: float, width: float, height: float) -> None:
        """Update the on-screen region of the viewport (e.g. on resize)."""
        self.region = LayoutRegion(int(x), int(y), int(width), int(height))
        self.screen_width = self.region.width
        self.screen_height = self.region.height
        if self.region.width > 0 and self.region.height > 0:
            self.scale = min(
                self.region.width / self.sim_width, self.region.height / self.sim_height
            )
        else:
            self.scale = 1.0
        # Center the simulation area inside the viewport
        self._offset_x = max(0.0, (self.region.width - self.sim_width * self.scale) / 2)
        self._offset_y = max(0.0, (self.region.height - self.sim_height * self.scale) / 2)

        self._bg_rect.pos = (self.region.x, self.region.y)
        self._bg_rect.size = (self.region.width, self.region.height)
        sx, sy = self.physics_to_screen_x(0), self.physics_to_screen_y(0)
        sw, sh = self.sim_width * self.scale, self.sim_height * self.scale
        self._sim_rect.pos = (sx, sy)
        self._sim_rect.size = (sw, sh)
        self._sim_border.rectangle = (sx, sy, sw, sh)

        self.invalidate_grid()
        self.invalidate_forces()
        # Entities are re-positioned on the next render_entities call.

    def physics_to_screen_x(self, x: float) -> float:
        """Convert physics X coordinate to screen coordinate."""
        return self.region.left + self._offset_x + (x * self.scale)

    def physics_to_screen_y(self, y: float) -> float:
        """Convert physics Y coordinate to screen coordinate (Y grows upward)."""
        return self.region.bottom + self._offset_y + (y * self.scale)

    def screen_to_physics_x(self, x: float) -> float:
        """Convert screen X coordinate to physics coordinate."""
        return (x - self.region.left - self._offset_x) / self.scale

    def screen_to_physics_y(self, y: float) -> float:
        """Convert screen Y coordinate to physics coordinate."""
        return (y - self.region.bottom - self._offset_y) / self.scale

    def contains_screen_point(self, x: float, y: float) -> bool:
        return (
            self.region.left <= x <= self.region.right
            and self.region.bottom <= y <= self.region.top
        )

    # ------------------------------------------------------------------ toggles
    def toggle_grid(self) -> None:
        super().toggle_grid()
        self.invalidate_grid()
        self._grid_sample_points = None

    def toggle_forces(self) -> None:
        super().toggle_forces()
        if not self.show_forces:
            self.clear_forces()

    # ------------------------------------------------------------------ drawing
    def clear(self) -> None:
        """Clear all dynamic drawing (grid, forces, entities)."""
        self.grid_group.clear()
        self.forces_group.clear()
        self.entities_group.clear()
        self._entity_pool = []
        self._entity_pool_kinds = []
        self._grid_cache_key = None
        self._forces_cache_key = None

    def render_ui(self, ui_elements: list) -> None:
        """UI elements are regular Kivy widgets and render themselves."""
        pass
