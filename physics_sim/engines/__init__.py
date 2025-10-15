__all__: list[str] = ["NumpyPhysicsEngine", "PymunkPhysicsEngine"]

from .numpy_engine import NumpyPhysicsEngine

try:
    from .pymunk_engine import PymunkPhysicsEngine
except ImportError:
    # Pymunk not installed, create a stub class
    class PymunkPhysicsEngine:
        def __init__(self, *args, **kwargs):
            raise ImportError(
                "Pymunk is not installed. Install with: pip install pymunk"
            )
