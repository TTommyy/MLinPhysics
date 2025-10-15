# Physics Simulation Framework

A modular, production-grade 2D physics simulation framework built with Python. Features pluggable physics engines (custom NumPy-based and Pymunk), clean architecture, and beautiful visualization with Arcade.

## 🎯 Features

- **Pluggable Physics Engines**: Swap between custom NumPy implementation and Pymunk library
- **Clean Architecture**: Modular design with separation of concerns
- **Visual Simulation**: Real-time rendering with Arcade library
- **Educational**: Learn physics simulation from first principles
- **Extensible**: Easy to add new entities, forces, and behaviors

## 🏗️ Architecture

```
physics_sim/
├── core/           # Abstract interfaces and base classes
│   ├── vector.py      # Vector2D with numpy backend
│   ├── entity.py      # Entity and PhysicalEntity base classes
│   └── engine.py      # PhysicsEngine abstract interface
├── engines/        # Physics engine implementations
│   ├── numpy_engine.py   # Custom implementation from scratch
│   └── pymunk_engine.py  # Pymunk library wrapper
├── entities/       # Simulation entities
│   ├── ball.py        # Ball entity with factory methods
│   └── obstacle.py    # [TODO] Static/dynamic obstacles
├── rendering/      # Visualization
│   ├── renderer.py    # Arcade-based renderer
│   └── camera.py      # [TODO] Camera controls
├── simulation/     # Simulation control
│   ├── config.py      # Configuration dataclass
│   └── simulator.py   # Main simulation loop
└── input/          # [TODO] Advanced input handling
    └── handler.py     # Mouse/keyboard controls
```

## 🚀 Quick Start

### Installation

```bash
# Clone or download the project
cd Physics

# Install dependencies
pip install -e .
```

### Running Examples

**Basic Cannonball Demo** (matches original JavaScript version):
```bash
python examples/basic_cannonball.py
```

**Compare Physics Engines**:
```bash
# NumPy engine (custom implementation)
python examples/compare_engines.py numpy

# Pymunk engine (library-based)
python examples/compare_engines.py pymunk
```

**Many Balls Stress Test**:
```bash
# 50 balls with NumPy engine
python examples/many_balls.py 50 numpy

# 100 balls with Pymunk engine
python examples/many_balls.py 100 pymunk
```

**Main Entry Point** (with CLI):
```bash
# Basic demo
python main.py

# Choose engine
python main.py --engine pymunk

# Many balls demo
python main.py --demo many --count 30

# Custom window size
python main.py --width 1600 --height 900
```

## 🎮 Controls

- **F1**: Toggle debug information overlay
- **ESC**: Exit simulation

## 📚 Usage Examples

### Creating a Simple Simulation

```python
from physics_sim import (
    Vector2D,
    Ball,
    NumpyPhysicsEngine,
    SimulationConfig,
    Simulator,
)

# Configure simulation
config = SimulationConfig(
    screen_width=1200,
    screen_height=800,
    gravity=Vector2D(0, -10),
)

# Create physics engine
engine = NumpyPhysicsEngine(
    gravity=config.gravity,
    bounds=(config.sim_width, config.sim_height),
)

# Add entities
ball = Ball(
    position=Vector2D(5, 10),
    velocity=Vector2D(3, 5),
    radius=0.3,
    color=(255, 100, 100),
)
engine.add_entity(ball)

# Run simulation
simulator = Simulator(config, engine)
simulator.run()
```

### Switching Physics Engines

```python
from physics_sim import NumpyPhysicsEngine, PymunkPhysicsEngine

# Use custom NumPy engine
engine = NumpyPhysicsEngine(gravity, bounds)

# Or use Pymunk engine (same interface!)
engine = PymunkPhysicsEngine(gravity, bounds)

# Rest of code stays the same - Strategy pattern!
```

### Factory Methods for Quick Entity Creation

```python
from physics_sim import Ball, Vector2D

# Create a cannonball with preset values
ball = Ball.create_cannonball()

# Create a ball with custom position/velocity
ball = Ball.create_cannonball(
    position=Vector2D(2, 2),
    velocity=Vector2D(5, 10),
)

# Create a random ball
ball = Ball.create_random(bounds=(20, 13))
```

## 🔬 Physics Engines Comparison

### NumPy Engine (Custom Implementation)

**Pros:**
- Educational - see physics implementation from scratch
- Full control over algorithms
- No external physics library needed
- Great for learning

**Cons:**
- Basic Euler integration (less accurate)
- Manual collision detection (simpler)
- No advanced features (constraints, joints)

**Implementation Details:**
- Euler integration: `v = v + a*dt`, `p = p + v*dt`
- Boundary collision detection
- Gravity application
- Elastic collisions with restitution

### Pymunk Engine (Library-Based)

**Pros:**
- Production-ready physics
- Accurate rigid body dynamics
- Efficient collision detection
- Advanced features (constraints, friction)

**Cons:**
- External dependency
- Less transparent (black box)
- Overkill for simple simulations

**Implementation Details:**
- Chipmunk2D physics library
- Verlet integration
- Spatial hashing for collisions
- Constraint solver

## 🎓 Design Patterns Used

1. **Strategy Pattern**: Swappable physics engines with common interface
2. **Factory Pattern**: Entity creation methods (`Ball.create_cannonball()`)
3. **Dependency Injection**: Engine passed to simulator
4. **Template Method**: `PhysicsEngine.step()` defines algorithm structure
5. **Facade Pattern**: `Simulator` provides simple interface to complex subsystems

## 🔮 Future Features (Placeholders Included)

### 1. Multiple Ball Management
```python
# TODO: Efficient container for many entities
# Location: physics_sim/simulation/entity_manager.py
```

### 2. Interactive Controls
```python
# TODO: Mouse click to spawn balls
# TODO: Drag to launch balls with velocity
# TODO: Select and manipulate entities
# Location: physics_sim/input/handler.py
```

### 3. Obstacles and Shapes
```python
# TODO: Static walls, platforms
# TODO: Dynamic obstacles
# TODO: Polygon shapes
# Location: physics_sim/entities/obstacle.py
```

### 4. Advanced Physics
```python
# TODO: Air resistance/drag
# TODO: Surface friction
# TODO: Different material properties
# Location: Both engine implementations
```

### 5. Ball-to-Ball Collisions
```python
# TODO: Elastic collision resolution
# TODO: Inelastic collisions
# TODO: Collision callbacks
# Location: physics_sim/engines/numpy_engine.py
```

### 6. Camera Controls
```python
# TODO: Pan and zoom
# TODO: Follow entity
# TODO: Smooth interpolation
# Location: physics_sim/rendering/camera.py
```

## 📖 Learning Resources

### Physics Concepts
- [Euler Integration](https://en.wikipedia.org/wiki/Euler_method)
- [Elastic Collisions](https://en.wikipedia.org/wiki/Elastic_collision)
- [Rigid Body Dynamics](https://en.wikipedia.org/wiki/Rigid_body_dynamics)

### Libraries Used
- [Arcade Documentation](https://api.arcade.academy/)
- [NumPy Documentation](https://numpy.org/doc/)
- [Pymunk Documentation](https://www.pymunk.org/)

### Related Projects
- [Ten Minute Physics](https://matthias-research.github.io/pages/tenMinutePhysics/) - Original inspiration
- [Box2D](https://box2d.org/) - Popular 2D physics engine

## 🧪 Testing (TODO)

```bash
# Run tests
pytest

# Run with coverage
pytest --cov=physics_sim
```

## 🤝 Contributing

This is an educational project. Feel free to:
- Implement TODO features
- Add new physics phenomena
- Optimize algorithms
- Improve documentation

## 📝 License

MIT License - Original JavaScript code by Matthias Müller (Ten Minute Physics)
Python implementation follows the same open-source spirit.

## 🙏 Acknowledgments

- [Matthias Müller](https://matthias-research.github.io/) - Ten Minute Physics tutorials
- Arcade, NumPy, and Pymunk communities

## 💡 Tips for Learning

1. **Start with NumPy engine**: Understand basic physics simulation
2. **Compare with Pymunk**: See how professional engines work
3. **Read the code**: Heavily commented for educational purposes
4. **Implement TODOs**: Best way to learn is by doing
5. **Experiment**: Change gravity, restitution, masses - see what happens!

## 🐛 Known Limitations

- NumPy engine uses simple Euler integration (can be unstable at high velocities)
- No ball-to-ball collisions in NumPy engine yet
- No spatial partitioning (all entities checked every frame)
- Fixed timestep only (no variable timestep support)

## 📊 Performance Notes

- NumPy engine: ~60 FPS with 50-100 balls
- Pymunk engine: ~60 FPS with 500+ balls
- Bottleneck is rendering, not physics (on most systems)

---

**Happy Simulating! 🎱**

