from kivy.metrics import dp
from kivy.uix.label import Label
from kivy.utils import escape_markup

from physics_sim.core import LayoutRegion
from physics_sim.ui.sections.base_section import BaseSection
from physics_sim.ui.utils import color_to_rgba, format_number, format_vector_for_display
from physics_sim.ui.widgets import (
    MUTED_TEXT_COLOR,
    FlatButton,
    Panel,
    TextLabel,
    VerticalScroll,
    hbox,
)

PANEL_BG = (22, 160, 133)  # green sea
CARD_BG = (250, 250, 250)
HEADER_COLOR = (41, 128, 185)
LABEL_COLOR = (0, 120, 120)
FORCE_COLOR = (192, 57, 43)


def _vec(values) -> str:
    return format_vector_for_display(values).replace("[", "(").replace("]", ")")


class InventoryPanelSection(BaseSection):
    """Right panel section displaying the entity inventory with pagination."""

    def __init__(self, region: LayoutRegion | None = None, items_per_page: int = 5, **kwargs):
        super().__init__(region, background_color=PANEL_BG, **kwargs)
        self.orientation = "vertical"
        self.padding = [dp(8), dp(8)]
        self.spacing = dp(6)

        # Pagination state
        self.current_page = 0
        self.items_per_page = max(1, int(items_per_page))
        self.total_pages = 1

        # Cache for inventory data and rendered entities
        self._cached_inventory_data: list[dict] = []
        self._cached_page_entities: list[dict] = []
        self.card_widgets: list[Panel] = []

        self._build()
        self._refresh_page()

    # ------------------------------------------------------------------ build
    def _build(self):
        self.title_label = TextLabel(
            "INVENTORY", font_size=17, bold=True, color=(255, 255, 255)
        )
        self.add_widget(self.title_label)
        self.summary_label = TextLabel(
            "Entities: 0", font_size=12, color=(240, 240, 240)
        )
        self.add_widget(self.summary_label)

        self.cards_scroll = VerticalScroll(spacing=8)
        self.add_widget(self.cards_scroll)

        row = hbox(spacing=6, height=dp(34))
        self.prev_button = FlatButton("Prev", size_hint_x=0.8)
        self.prev_button.bind(on_release=self._on_prev_page)
        self.page_label = Label(
            text="Page 1/1",
            color=(1, 1, 1, 1),
            font_size=13,
            bold=True,
            size_hint_x=1.2,
        )
        self.next_button = FlatButton("Next", size_hint_x=0.8)
        self.next_button.bind(on_release=self._on_next_page)
        row.add_widget(self.prev_button)
        row.add_widget(self.page_label)
        row.add_widget(self.next_button)
        self.add_widget(row)

    # ------------------------------------------------------------------ paging
    def _on_prev_page(self, *_):
        """Handle previous page button click."""
        if self.current_page > 0:
            self.current_page -= 1
            self._update_page_from_cache()

    def _on_next_page(self, *_):
        """Handle next page button click."""
        if self.current_page < self.total_pages - 1:
            self.current_page += 1
            self._update_page_from_cache()

    def go_to_page(self, page: int):
        """Jump to a page (clamped to the valid range)."""
        self.current_page = max(0, min(int(page), self.total_pages - 1))
        self._update_page_from_cache()

    def _recompute_pages(self):
        count = len(self._cached_inventory_data)
        self.total_pages = max(1, (count + self.items_per_page - 1) // self.items_per_page)
        self.current_page = max(0, min(self.current_page, self.total_pages - 1))
        start = self.current_page * self.items_per_page
        end = min(start + self.items_per_page, count)
        self._cached_page_entities = self._cached_inventory_data[start:end]

    def _update_page_from_cache(self):
        """Update the displayed page entities from cached data."""
        self._recompute_pages()
        self._refresh_page()
        self.cards_scroll.scroll_y = 1

    def render_with_data(self, inventory_data: list[dict]):
        """Update the inventory with fresh data from the engine."""
        self._cached_inventory_data = list(inventory_data or [])
        self._recompute_pages()
        self._refresh_page()

    # ------------------------------------------------------------------ cards
    def _refresh_page(self):
        count = len(self._cached_inventory_data)
        self.summary_label.text = f"Entities: {count}"
        self.page_label.text = f"Page {self.current_page + 1}/{self.total_pages}"
        self.prev_button.disabled = self.current_page <= 0
        self.next_button.disabled = self.current_page >= self.total_pages - 1

        content = self.cards_scroll.content
        content.clear_widgets()
        self.card_widgets = []
        if not self._cached_page_entities:
            content.add_widget(
                TextLabel("No dynamic entities", font_size=12, color=(240, 240, 240))
            )
            return
        start = self.current_page * self.items_per_page
        for offset, data in enumerate(self._cached_page_entities):
            card = self._build_card(start + offset + 1, data)
            self.card_widgets.append(card)
            content.add_widget(card)

    @staticmethod
    def _field(label: str, value: str) -> TextLabel:
        r, g, b, _ = color_to_rgba(LABEL_COLOR)
        hex_color = "%02x%02x%02x" % (int(r * 255), int(g * 255), int(b * 255))
        return TextLabel(
            f"[color={hex_color}]{escape_markup(label)}:[/color] {escape_markup(value)}",
            font_size=12,
            markup=True,
        )

    def _build_card(self, index: int, data: dict) -> Panel:
        card = Panel(
            background_color=CARD_BG,
            border_color=(200, 200, 200),
            orientation="vertical",
            size_hint_y=None,
            padding=[dp(8), dp(6)],
            spacing=dp(1),
        )
        card.bind(minimum_height=card.setter("height"))
        card.entity_id = data.get("id")

        card.add_widget(
            TextLabel(
                f"#{index} {data.get('type', 'Entity')}",
                font_size=13,
                bold=True,
                color=HEADER_COLOR,
            )
        )
        card.add_widget(self._field("ID", str(data.get("id", ""))[:10]))
        if "mass" in data:
            card.add_widget(self._field("Mass", f"{format_number(data['mass'])} kg"))
        if "radius" in data:
            card.add_widget(self._field("Radius", f"{format_number(data['radius'])} m"))
        if "restitution" in data:
            card.add_widget(self._field("Restitution", format_number(data["restitution"])))
        if "position" in data:
            card.add_widget(self._field("Pos", f"{_vec(data['position'])} m"))
        if "velocity" in data:
            card.add_widget(self._field("Vel", f"{_vec(data['velocity'])} m/s"))
        if "speed" in data:
            card.add_widget(self._field("Speed", f"{format_number(data['speed'])} m/s"))
        if "acceleration" in data:
            card.add_widget(self._field("Acc", f"{_vec(data['acceleration'])} m/s²"))

        forces = data.get("applied_forces", [])
        if forces:
            card.add_widget(TextLabel("Forces:", font_size=12, bold=True, color=FORCE_COLOR))
            for force in forces:
                card.add_widget(
                    TextLabel(
                        f"  • {force.get('name', '?')}: "
                        f"{format_number(force.get('magnitude', 0.0))} N "
                        f"{_vec(force.get('vector', (0.0, 0.0)))}",
                        font_size=11,
                        color=MUTED_TEXT_COLOR,
                    )
                )
        return card

    def on_mouse_scroll(self, x: int, y: int, scroll_x: int, scroll_y: int):
        """Mouse wheel scrolling is handled by the cards ScrollView."""
        pass

    def on_draw(self):
        """Kept for API compatibility (Kivy widgets draw themselves)."""
        pass


__all__: list[str] = ["InventoryPanelSection"]
