"""Reusable Kivy widgets shared by all UI panels."""

from kivy.graphics import Color, Line, Rectangle
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget

from physics_sim.ui.utils import color_to_rgba

__all__: list[str] = [
    "BackgroundMixin",
    "Panel",
    "TextLabel",
    "FlatButton",
    "InputField",
    "ColorSwatch",
    "VerticalScroll",
    "vbox",
    "hbox",
]

TEXT_COLOR = (30, 30, 30)
MUTED_TEXT_COLOR = (90, 90, 90)
BUTTON_COLOR = (52, 73, 94)
BUTTON_ACTIVE_COLOR = (39, 174, 96)
BUTTON_DANGER_COLOR = (192, 57, 43)


class BackgroundMixin:
    """Draws a solid background and optional border behind a widget."""

    def init_background(
        self,
        background_color=(245, 245, 245),
        border_color=(160, 160, 160),
        border_width: float = 1.0,
    ) -> None:
        with self.canvas.before:
            self._bg_color_instr = Color(*color_to_rgba(background_color))
            self._bg_rect_instr = Rectangle(pos=self.pos, size=self.size)
            self._border_color_instr = Color(
                *(color_to_rgba(border_color) if border_color else (0, 0, 0, 0))
            )
            self._border_instr = Line(rectangle=(0, 0, 0, 0), width=border_width)
        self.bind(pos=self._update_background, size=self._update_background)
        self._update_background()

    def set_background_color(self, color) -> None:
        self._bg_color_instr.rgba = color_to_rgba(color)

    def _update_background(self, *_):
        self._bg_rect_instr.pos = self.pos
        self._bg_rect_instr.size = self.size
        self._border_instr.rectangle = (self.x, self.y, self.width, self.height)


class Panel(BackgroundMixin, BoxLayout):
    """BoxLayout with background and border."""

    def __init__(
        self,
        background_color=(245, 245, 245),
        border_color=(160, 160, 160),
        border_width: float = 1.0,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.init_background(background_color, border_color, border_width)


class TextLabel(Label):
    """Dark, left aligned, auto-height (wrapping) label."""

    def __init__(
        self,
        text: str = "",
        font_size: float = 13,
        color=TEXT_COLOR,
        bold: bool = False,
        halign: str = "left",
        min_height: float | None = None,
        **kwargs,
    ):
        kwargs.setdefault("size_hint_y", None)
        kwargs.setdefault("markup", False)
        super().__init__(
            text=text,
            font_size=font_size,
            color=color_to_rgba(color),
            bold=bold,
            halign=halign,
            valign="middle",
            **kwargs,
        )
        self._min_height = dp(18) if min_height is None else min_height
        self.bind(width=self._update_text_size, texture_size=self._update_height)
        self._update_text_size()

    def _update_text_size(self, *_):
        self.text_size = (max(self.width, 1), None)

    def _update_height(self, *_):
        self.height = max(self._min_height, self.texture_size[1] + dp(2))


class FlatButton(Button):
    """Flat colored button."""

    def __init__(self, text: str = "", color=BUTTON_COLOR, height=None, **kwargs):
        kwargs.setdefault("size_hint_y", None)
        kwargs.setdefault("font_size", 13)
        super().__init__(
            text=text,
            background_normal="",
            background_down="",
            background_disabled_normal="",
            **kwargs,
        )
        self.height = dp(32) if height is None else height
        # Never let the caption overflow the button: shorten with an ellipsis
        self.shorten = True
        self.shorten_from = "right"
        self.halign = "center"
        self.valign = "middle"
        self.bind(size=self._update_text_size)
        self._update_text_size()
        self._base_color = color
        self.set_color(color)
        self.bind(state=self._on_state, disabled=self._on_state)

    def _update_text_size(self, *_):
        self.text_size = (max(1, self.width - dp(8)), max(1, self.height))

    def set_color(self, color) -> None:
        self._base_color = color
        self._on_state()

    def _on_state(self, *_):
        r, g, b, a = color_to_rgba(self._base_color)
        if self.disabled:
            self.background_color = (r, g, b, 0.35)
        elif self.state == "down":
            self.background_color = (r * 0.75, g * 0.75, b * 0.75, a)
        else:
            self.background_color = (r, g, b, a)


class InputField(TextInput):
    """Single line text input."""

    def __init__(self, text: str = "", **kwargs):
        kwargs.setdefault("size_hint_y", None)
        kwargs.setdefault("font_size", 13)
        super().__init__(text=text, multiline=False, write_tab=False, **kwargs)
        self.height = dp(30)
        self.padding = [dp(6), dp(6), dp(6), dp(6)]


class ColorSwatch(BackgroundMixin, Widget):
    """Small rectangle previewing an RGB color."""

    def __init__(self, color=(128, 128, 128), **kwargs):
        kwargs.setdefault("size_hint", (None, None))
        kwargs.setdefault("size", (dp(30), dp(30)))
        super().__init__(**kwargs)
        self.init_background(color, (0, 0, 0), 1.0)

    def set_color(self, color) -> None:
        self.set_background_color(color)


class VerticalScroll(ScrollView):
    """ScrollView hosting a vertical box whose height follows its content."""

    def __init__(self, spacing: float = 6, padding=0, **kwargs):
        kwargs.setdefault("do_scroll_x", False)
        kwargs.setdefault("bar_width", dp(8))
        kwargs.setdefault("scroll_type", ["bars"])
        kwargs.setdefault("bar_color", (0.3, 0.3, 0.3, 0.9))
        kwargs.setdefault("bar_inactive_color", (0.3, 0.3, 0.3, 0.5))
        super().__init__(**kwargs)
        self.content = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            spacing=dp(spacing),
            padding=padding,
        )
        self.content.bind(minimum_height=self.content.setter("height"))
        self.add_widget(self.content)


def vbox(spacing: float = 6, **kwargs) -> BoxLayout:
    """Vertical BoxLayout whose height follows its content."""
    kwargs.setdefault("size_hint_y", None)
    box = BoxLayout(orientation="vertical", spacing=dp(spacing), **kwargs)
    if box.size_hint_y is None:
        box.bind(minimum_height=box.setter("height"))
    return box


def hbox(spacing: float = 6, height=None, **kwargs) -> BoxLayout:
    """Horizontal BoxLayout with fixed height."""
    kwargs.setdefault("size_hint_y", None)
    box = BoxLayout(orientation="horizontal", spacing=dp(spacing), **kwargs)
    box.height = dp(32) if height is None else height
    return box
