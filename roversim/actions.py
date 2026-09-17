"""Structured action types produced by the command parser.

The parser turns a raw text command into a list of these action
objects, which the simulator then executes one at a time.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class MoveAction:
    """Move the rover forward or backward along its current heading.

    direction: "forward" or "backward"
    distance: distance to travel, in meters (always >= 0)
    """

    direction: str
    distance: float

    def __post_init__(self):
        if self.direction not in ("forward", "backward"):
            raise ValueError(f"invalid move direction: {self.direction!r}")
        if self.distance < 0:
            raise ValueError("distance must be non-negative")

    def describe(self) -> str:
        return f"move {self.direction} {self.distance:g} meters"


@dataclass(frozen=True)
class TurnAction:
    """Turn the rover in place.

    direction: "left" or "right"
    degrees: rotation amount in degrees (always >= 0). "turn around"
        is represented as a 180 degree turn.
    """

    direction: str
    degrees: float

    def __post_init__(self):
        if self.direction not in ("left", "right"):
            raise ValueError(f"invalid turn direction: {self.direction!r}")
        if self.degrees < 0:
            raise ValueError("degrees must be non-negative")

    def describe(self) -> str:
        return f"turn {self.direction} {self.degrees:g} degrees"


@dataclass(frozen=True)
class StopAction:
    """Bring the rover to a halt. A no-op on position/heading, but is
    recorded in history like any other action."""

    def describe(self) -> str:
        return "stop"
