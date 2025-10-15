import numpy as np


class Vector2D:
    """2D vector with numpy-backed calculations for physics operations."""

    def __init__(self, x: float, y: float):
        self._data = np.array([x, y], dtype=np.float64)

    @property
    def x(self) -> float:
        return float(self._data[0])

    @x.setter
    def x(self, value: float):
        self._data[0] = value

    @property
    def y(self) -> float:
        return float(self._data[1])

    @y.setter
    def y(self, value: float):
        self._data[1] = value

    def __add__(self, other: "Vector2D") -> "Vector2D":
        result = Vector2D(0, 0)
        result._data = self._data + other._data
        return result

    def __sub__(self, other: "Vector2D") -> "Vector2D":
        result = Vector2D(0, 0)
        result._data = self._data - other._data
        return result

    def __mul__(self, scalar: float) -> "Vector2D":
        result = Vector2D(0, 0)
        result._data = self._data * scalar
        return result

    def __rmul__(self, scalar: float) -> "Vector2D":
        return self.__mul__(scalar)

    def __truediv__(self, scalar: float) -> "Vector2D":
        result = Vector2D(0, 0)
        result._data = self._data / scalar
        return result

    def __neg__(self) -> "Vector2D":
        result = Vector2D(0, 0)
        result._data = -self._data
        return result

    def magnitude(self) -> float:
        return float(np.linalg.norm(self._data))

    def normalized(self) -> "Vector2D":
        mag = self.magnitude()
        if mag == 0:
            return Vector2D(0, 0)
        return self / mag

    def dot(self, other: "Vector2D") -> float:
        return float(np.dot(self._data, other._data))

    def copy(self) -> "Vector2D":
        return Vector2D(self.x, self.y)

    def __repr__(self) -> str:
        return f"Vector2D({self.x:.2f}, {self.y:.2f})"

    def to_tuple(self) -> tuple[float, float]:
        return (self.x, self.y)
