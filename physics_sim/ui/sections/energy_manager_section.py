from kivy.graphics import Color, InstructionGroup, Line, Rectangle
from kivy.metrics import dp
from kivy.uix.widget import Widget

from physics_sim.core import LayoutRegion
from physics_sim.rendering._text_cache import TextTextureCache
from physics_sim.ui.sections.base_section import BaseSection
from physics_sim.ui.utils import color_to_rgba, format_number
from physics_sim.ui.widgets import TextLabel, hbox

KE_COLOR = (41, 128, 185)  # peter river
PE_COLOR = (192, 57, 43)  # pomegranate
TOTAL_COLOR = (39, 174, 96)  # nephritis
GRID_COLOR = (200, 200, 200)
AXIS_COLOR = (128, 128, 128)
TEXT_COLOR = (20, 20, 20)


class EnergyPlot(Widget):
    """Line plot of kinetic / potential / total energy over time."""

    margin_left = dp(64)
    margin_right = dp(14)
    margin_top = dp(18)
    margin_bottom = dp(32)
    num_h_lines = 5
    num_v_lines = 6

    def __init__(self, section: "EnergyManagerSection", **kwargs):
        super().__init__(**kwargs)
        self.section = section
        self._text_cache = TextTextureCache()
        self._group = InstructionGroup()
        self.canvas.add(self._group)
        self.bind(pos=self.redraw, size=self.redraw)

    def plot_bounds(self) -> tuple[float, float, float, float]:
        left = self.x + self.margin_left
        right = self.right - self.margin_right
        bottom = self.y + self.margin_bottom
        top = self.top - self.margin_top
        return left, right, bottom, top

    def _text(self, text: str, x: float, y: float, anchor_x="left", anchor_y="bottom", size=11, bold=False):
        texture = self._text_cache.get(text, size, color_to_rgba(TEXT_COLOR), bold)
        w, h = texture.size
        if anchor_x == "center":
            x -= w / 2
        elif anchor_x == "right":
            x -= w
        if anchor_y == "center":
            y -= h / 2
        elif anchor_y == "top":
            y -= h
        self._group.add(Color(1, 1, 1, 1))
        self._group.add(Rectangle(texture=texture, size=texture.size, pos=(x, y)))

    def redraw(self, *_):
        g = self._group
        g.clear()
        left, right, bottom, top = self.plot_bounds()
        width, height = right - left, top - bottom
        if width <= 10 or height <= 10:
            return

        s = self.section
        times = s.time_history
        series = [
            (s.kinetic_history, KE_COLOR),
            (s.potential_history, PE_COLOR),
            (s.total_history, TOTAL_COLOR),
        ]

        # Plot background, grid and border
        g.add(Color(1, 1, 1, 1))
        g.add(Rectangle(pos=(left, bottom), size=(width, height)))
        g.add(Color(*color_to_rgba(GRID_COLOR)))
        for i in range(self.num_h_lines + 1):
            y = bottom + height * i / self.num_h_lines
            g.add(Line(points=[left, y, right, y], width=1))
        for i in range(self.num_v_lines + 1):
            x = left + width * i / self.num_v_lines
            g.add(Line(points=[x, bottom, x, top], width=1))
        g.add(Color(*color_to_rgba(AXIS_COLOR)))
        g.add(Line(rectangle=(left, bottom, width, height), width=1.2))

        # Axis titles
        self._text("Energy (J)", self.x + dp(4), top + dp(2), size=11, bold=True)
        self._text("Time (s)", right, self.y + dp(2), anchor_x="right", size=11, bold=True)

        if len(times) < 2:
            self._text(
                "Waiting for data (simulation must be running)...",
                left + width / 2, bottom + height / 2, anchor_x="center", anchor_y="center",
            )
            return

        t_min, t_max = min(times), max(times)
        t_range = t_max - t_min if t_max > t_min else 1.0
        all_e = s.kinetic_history + s.potential_history + s.total_history
        e_min, e_max = min(all_e), max(all_e)
        e_range = e_max - e_min if e_max > e_min else 1.0
        pad = e_range * 0.1
        e_min -= pad
        e_max += pad
        e_range = e_max - e_min

        for i in range(self.num_h_lines + 1):
            y = bottom + height * i / self.num_h_lines
            value = e_min + e_range * i / self.num_h_lines
            self._text(format_number(value), left - dp(4), y, anchor_x="right", anchor_y="center", size=10)
        for i in range(0, self.num_v_lines + 1, 2):
            x = left + width * i / self.num_v_lines
            value = t_min + t_range * i / self.num_v_lines
            self._text(format_number(value), x, bottom - dp(2), anchor_x="center", anchor_y="top", size=10)

        for values, color in series:
            pts: list[float] = []
            for t, e in zip(times, values):
                pts.append(left + (t - t_min) / t_range * width)
                pts.append(bottom + (e - e_min) / e_range * height)
            g.add(Color(*color_to_rgba(color)))
            g.add(Line(points=pts, width=1.3))


class EnergyManagerSection(BaseSection):
    """Bottom panel displaying kinetic/potential/total energy over time."""

    def __init__(self, region: LayoutRegion | None = None, max_history: int = 300, **kwargs):
        super().__init__(region, background_color=(240, 240, 250), **kwargs)
        self.orientation = "vertical"
        self.padding = [dp(8), dp(6)]
        self.spacing = dp(4)
        self.max_history = max_history

        self.kinetic_history: list[float] = []
        self.potential_history: list[float] = []
        self.total_history: list[float] = []
        self.time_history: list[float] = []

        header = hbox(spacing=10, height=dp(24))
        header.add_widget(
            TextLabel("ENERGY TRACKING", font_size=16, bold=True, color=(0, 0, 139), size_hint_x=1.3)
        )
        self.ke_legend_label = TextLabel("KE: 0.00 J", font_size=13, bold=True, color=KE_COLOR)
        self.pe_legend_label = TextLabel("PE: 0.00 J", font_size=13, bold=True, color=PE_COLOR)
        self.total_legend_label = TextLabel(
            "Total: 0.00 J", font_size=13, bold=True, color=TOTAL_COLOR
        )
        for lbl in (self.ke_legend_label, self.pe_legend_label, self.total_legend_label):
            header.add_widget(lbl)
        self.add_widget(header)

        self.plot = EnergyPlot(self)
        self.add_widget(self.plot)

    def add_energy_sample(self, ke: float, pe: float, total: float, time: float):
        """Add an energy sample to history (and refresh plot + legend)."""
        self.kinetic_history.append(float(ke))
        self.potential_history.append(float(pe))
        self.total_history.append(float(total))
        self.time_history.append(float(time))

        if len(self.time_history) > self.max_history:
            del self.kinetic_history[0]
            del self.potential_history[0]
            del self.total_history[0]
            del self.time_history[0]

        self.ke_legend_label.text = f"KE: {format_number(ke)} J"
        self.pe_legend_label.text = f"PE: {format_number(pe)} J"
        self.total_legend_label.text = f"Total: {format_number(total)} J"
        self.plot.redraw()

    def clear_history(self):
        self.kinetic_history.clear()
        self.potential_history.clear()
        self.total_history.clear()
        self.time_history.clear()
        self.plot.redraw()

    def on_draw(self):
        """Kept for API compatibility (Kivy widgets draw themselves)."""
        pass


__all__: list[str] = ["EnergyManagerSection"]
