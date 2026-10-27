"""Small cache of rasterized text textures for canvas based rendering."""

from kivy.core.text import Label as CoreLabel


class TextTextureCache:
    """Caches Kivy text textures keyed by text + style."""

    def __init__(self, max_items: int = 512):
        self._cache: dict[tuple, object] = {}
        self._max_items = max_items

    def get(
        self,
        text: str,
        font_size: float = 11,
        color: tuple[float, float, float, float] = (0, 0, 0, 1),
        bold: bool = False,
    ):
        key = (text, float(font_size), tuple(color), bool(bold))
        texture = self._cache.get(key)
        if texture is None:
            if len(self._cache) >= self._max_items:
                self._cache.clear()
            label = CoreLabel(text=text, font_size=font_size, color=color, bold=bold)
            label.refresh()
            texture = label.texture
            self._cache[key] = texture
        return texture
