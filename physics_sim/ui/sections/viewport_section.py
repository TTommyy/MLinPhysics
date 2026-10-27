from kivy.uix.stencilview import StencilView

from physics_sim.core import Force, LayoutRegion
from physics_sim.rendering import KivyRenderer


class ViewportSection(StencilView):
    """Central viewport rendering the physics simulation.

    A ``StencilView`` clips all drawing to the viewport so entities that move
    outside never paint over the neighbouring panels.
    """

    def __init__(
        self,
        region: LayoutRegion | None = None,
        sim_width: float = 20.0,
        sim_height: float = 10.0,
        **kwargs,
    ):
        super().__init__(**kwargs)
        region = region or LayoutRegion(0, 0, 100, 100)
        if region.width > 0 and region.height > 0:
            self.pos = (region.x, region.y)
            self.size = (region.width, region.height)

        self.renderer = KivyRenderer(
            region=LayoutRegion(int(self.x), int(self.y), int(self.width), int(self.height)),
            sim_width=sim_width,
            sim_height=sim_height,
        )
        self.canvas.add(self.renderer.instructions)

        # Callback: on_click(x, y, button) with coordinates in widget space
        self.on_click = None
        self.bind(pos=self._on_geometry, size=self._on_geometry)

    @property
    def region(self) -> LayoutRegion:
        return self.renderer.region

    def _on_geometry(self, *_):
        self.renderer.set_region(self.x, self.y, self.width, self.height)

    def on_touch_down(self, touch):
        if not self.collide_point(*touch.pos):
            return super().on_touch_down(touch)
        button = getattr(touch, "button", "left") or "left"
        if button.startswith("scroll"):
            return super().on_touch_down(touch)
        if self.on_click:
            self.on_click(touch.x, touch.y, button)
        return True

    def on_draw(self):
        """Kept for API compatibility; rendering happens via render_with_data."""
        pass

    def render_with_data(
        self, render_data: list[dict], forces: list[Force] | None = None
    ):
        """Render grid and simulation entities from engine data dicts."""
        self.renderer.render_grid()
        self.renderer.render_entities(render_data)

    def on_update(self, delta_time: float):
        pass


__all__: list[str] = ["ViewportSection"]
