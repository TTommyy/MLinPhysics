from kivy.graphics import Color, Ellipse, InstructionGroup, Line, Rectangle

from physics_sim.ui.utils import color_to_rgba

OUTLINE_COLOR = (0.0, 0.0, 0.0, 1.0)
SELECTION_COLOR = (1.0, 0.85, 0.0, 1.0)


class ShapeRendererMixin:
    """Mixin for rendering entity shapes (circles, rectangles) on a Kivy canvas.

    Canvas instructions are pooled per entity slot and updated in place every
    frame; the pool is rebuilt only when the number/kind of entities changes.
    """

    entities_group: InstructionGroup

    def _init_shape_renderer(self) -> None:
        self._entity_pool: list[dict] = []
        self._entity_pool_kinds: list[str] = []
        self.selected_entity_id: str | None = None

    @staticmethod
    def _shape_kind(render_data: dict) -> str | None:
        render_type = render_data.get("render_type", render_data.get("type"))
        if render_type in ("circle", "circle_static"):
            return "circle"
        if render_type == "rectangle":
            return "rectangle"
        return None

    def _rebuild_entity_pool(self, kinds: list[str]) -> None:
        self.entities_group.clear()
        self._entity_pool = []
        for kind in kinds:
            fill_color = Color(0.5, 0.5, 0.5, 1)
            outline_color = Color(*OUTLINE_COLOR)
            if kind == "circle":
                shape = Ellipse(pos=(0, 0), size=(0, 0))
                outline = Line(circle=(0, 0, 1), width=1.0)
            else:
                shape = Rectangle(pos=(0, 0), size=(0, 0))
                outline = Line(rectangle=(0, 0, 0, 0), width=1.0)
            for instr in (fill_color, shape, outline_color, outline):
                self.entities_group.add(instr)
            self._entity_pool.append({
                "kind": kind,
                "fill_color": fill_color,
                "shape": shape,
                "outline_color": outline_color,
                "outline": outline,
            })
        self._entity_pool_kinds = list(kinds)

    def render_entities(self, render_data: list[dict]) -> None:
        """Render entities from engine render-data dicts."""
        items = [(d, self._shape_kind(d)) for d in render_data]
        items = [(d, k) for d, k in items if k is not None]
        kinds = [k for _, k in items]
        if kinds != self._entity_pool_kinds:
            self._rebuild_entity_pool(kinds)
        for slot, (data, _) in zip(self._entity_pool, items):
            self._update_entity_slot(slot, data)

    def _render_entity(self, render_data: dict) -> None:
        """Render a single entity (convenience wrapper)."""
        self.render_entities([render_data])

    def _update_entity_slot(self, slot: dict, data: dict) -> None:
        pos_x, pos_y = data["position"]
        sx = self.physics_to_screen_x(float(pos_x))
        sy = self.physics_to_screen_y(float(pos_y))
        selected = (
            self.selected_entity_id is not None
            and data.get("id") == self.selected_entity_id
        )
        slot["fill_color"].rgba = color_to_rgba(data.get("color"))
        slot["outline_color"].rgba = SELECTION_COLOR if selected else OUTLINE_COLOR
        render_type = data.get("render_type")
        if slot["kind"] == "circle":
            r = max(0.5, float(data["radius"]) * self.scale)
            slot["shape"].pos = (sx - r, sy - r)
            slot["shape"].size = (2 * r, 2 * r)
            width = 1.5 if render_type == "circle" else 2.0
            slot["outline"].width = 3.0 if selected else width
            slot["outline"].circle = (sx, sy, r)
        else:
            w = max(1.0, float(data["width"]) * self.scale)
            h = max(1.0, float(data["height"]) * self.scale)
            slot["shape"].pos = (sx - w / 2, sy - h / 2)
            slot["shape"].size = (w, h)
            slot["outline"].width = 3.0 if selected else 1.5
            slot["outline"].rectangle = (sx - w / 2, sy - h / 2, w, h)
