import os

import numpy as np
import psutil

from physics_sim import Ball, DragForce, LinearGravityForce, NumpyPhysicsEngine


def print_memory(step):
    process = psutil.Process(os.getpid())
    print(f"Step {step}: {process.memory_info().rss / 1024 / 1024:.2f} MB")


def test_engine_performance(n_balls: int, n_steps: int = 2000):
    engine = NumpyPhysicsEngine(bounds=(20.0, 15.0))
    engine.add_force(LinearGravityForce(np.array([0.0, -9.81])))
    engine.add_force(DragForce(linear=True))

    for i in range(n_balls):
        x = (i % 20) + 1.0
        y = ((i // 20) % 10) + 1.0
        ball = Ball(
            position=np.array([x, y]),
            velocity=np.array([np.random.uniform(-5, 5), np.random.uniform(-5, 5)]),
            radius=0.15,
            mass=1.0,
            color=(255, 0, 0),
            restitution=0.9,
        )
        engine.add_entity(ball)

    print(f"Running {n_steps} physics steps with {n_balls} balls...")
    dt = 1.0 / 60.0

    for step in range(n_steps):
        engine.step(dt)
        if step is not None:
            print_memory(step)


if __name__ == "__main__":
    test_engine_performance(500, n_steps=100)
