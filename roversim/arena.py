"""A small bundled 2D arena definition with a few circular obstacles.

The simulator uses this to perform obstacle-aware safety checks: if a
commanded move would carry the rover into an obstacle, the rover stops
short at the obstacle's boundary instead of clipping through it.
"""

from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class Obstacle:
    """A circular obstacle in the arena.

    x, y: center position in meters
    radius: obstacle radius in meters
    name: human-readable label used in safety-stop explanations
    """

    x: float
    y: float
    radius: float
    name: str = "obstacle"


@dataclass(frozen=True)
class Arena:
    """A 2D arena: just a bag of obstacles for now."""

    obstacles: List[Obstacle]


# A small default arena bundled with the simulator. Coordinates are in
# meters, with the rover starting at the origin (0, 0) facing heading
# 0 degrees (the +x direction).
DEFAULT_ARENA = Arena(
    obstacles=[
        Obstacle(x=5.0, y=0.0, radius=1.0, name="crate"),
        Obstacle(x=0.0, y=5.0, radius=0.75, name="rock"),
        Obstacle(x=-4.0, y=-4.0, radius=1.5, name="wall segment"),
    ]
)
