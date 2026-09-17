"""2D kinematic rover simulator with obstacle-aware safety stops.

Kinematics are deliberately simple:
  - "move forward/backward N meters" translates the rover N meters
    along (or opposite to) its current heading vector.
  - "turn left/right N degrees" rotates the rover's heading in place
    by N degrees (left = counter-clockwise, right = clockwise),
    normalized into [0, 360).

Before actually applying a move, the simulator checks whether the
straight-line path would enter any bundled arena obstacle. If so, the
rover is stopped exactly at the obstacle's safety boundary (obstacle
radius + rover radius) instead of passing through it, and a
human-readable reason is recorded.
"""

import math
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

from .actions import MoveAction, StopAction, TurnAction
from .arena import Arena, DEFAULT_ARENA


@dataclass
class RoverState:
    """The rover's current pose."""

    x: float = 0.0
    y: float = 0.0
    heading: float = 0.0  # degrees, 0 = facing +x, increases counter-clockwise

    def position(self) -> Tuple[float, float]:
        return (self.x, self.y)


@dataclass
class HistoryEntry:
    """One executed action plus the resulting rover state."""

    action_description: str
    position: Tuple[float, float]
    heading: float
    safety_stop_reason: Optional[str] = None

    def __str__(self) -> str:
        x, y = self.position
        base = f"{self.action_description} -> position=({x:.2f}, {y:.2f}), heading={self.heading:.1f} deg"
        if self.safety_stop_reason:
            base += f" [SAFETY STOP: {self.safety_stop_reason}]"
        return base


def _normalize_heading(degrees: float) -> float:
    return degrees % 360.0


class RoverSimulator:
    """A stateful 2D rover simulator.

    Holds the rover's current pose, an arena of obstacles, and a
    running history of executed actions. Each call to run either a
    single action (`execute`) or a list of actions (`execute_all`)
    appends to `self.history`.
    """

    def __init__(
        self,
        arena: Arena = DEFAULT_ARENA,
        rover_radius: float = 0.3,
        start_x: float = 0.0,
        start_y: float = 0.0,
        start_heading: float = 0.0,
    ):
        self.arena = arena
        self.rover_radius = rover_radius
        self.state = RoverState(x=start_x, y=start_y, heading=_normalize_heading(start_heading))
        self.history: List[HistoryEntry] = []

    # -- public API ---------------------------------------------------

    def execute(self, action) -> HistoryEntry:
        if isinstance(action, MoveAction):
            entry = self._execute_move(action)
        elif isinstance(action, TurnAction):
            entry = self._execute_turn(action)
        elif isinstance(action, StopAction):
            entry = self._execute_stop(action)
        else:
            raise TypeError(f"unknown action type: {type(action)!r}")
        self.history.append(entry)
        return entry

    def execute_all(self, actions) -> List[HistoryEntry]:
        return [self.execute(action) for action in actions]

    # -- internals ------------------------------------------------------

    def _execute_turn(self, action: TurnAction) -> HistoryEntry:
        delta = action.degrees if action.direction == "left" else -action.degrees
        self.state.heading = _normalize_heading(self.state.heading + delta)
        return HistoryEntry(
            action_description=action.describe(),
            position=self.state.position(),
            heading=self.state.heading,
        )

    def _execute_stop(self, action: StopAction) -> HistoryEntry:
        return HistoryEntry(
            action_description=action.describe(),
            position=self.state.position(),
            heading=self.state.heading,
        )

    def _execute_move(self, action: MoveAction) -> HistoryEntry:
        heading_rad = math.radians(self.state.heading)
        heading_vec = (math.cos(heading_rad), math.sin(heading_rad))
        if action.direction == "forward":
            move_vec = heading_vec
        else:  # backward
            move_vec = (-heading_vec[0], -heading_vec[1])

        allowed_distance, reason = self._check_collision(
            self.state.x, self.state.y, move_vec, action.distance
        )

        self.state.x += move_vec[0] * allowed_distance
        self.state.y += move_vec[1] * allowed_distance

        return HistoryEntry(
            action_description=action.describe(),
            position=self.state.position(),
            heading=self.state.heading,
            safety_stop_reason=reason,
        )

    def _check_collision(
        self,
        start_x: float,
        start_y: float,
        move_vec: Tuple[float, float],
        distance: float,
    ) -> Tuple[float, Optional[str]]:
        """Return (allowed_distance, reason_or_None).

        Walks the straight-line path of length `distance` from
        (start_x, start_y) along unit vector `move_vec`, and finds the
        closest point (if any) where the rover would first touch an
        obstacle's safety boundary (obstacle.radius + rover_radius).
        If found and closer than `distance`, the rover is stopped
        exactly there.
        """
        best_t: Optional[float] = None
        best_obstacle = None

        dx, dy = move_vec
        for obstacle in self.arena.obstacles:
            total_radius = obstacle.radius + self.rover_radius
            fx = start_x - obstacle.x
            fy = start_y - obstacle.y

            # |f + t*d|^2 = total_radius^2  (d is a unit vector, so a = 1)
            b = 2 * (fx * dx + fy * dy)
            c = (fx * fx + fy * fy) - total_radius * total_radius
            discriminant = b * b - 4 * c
            if discriminant < 0:
                continue  # path never comes within range of this obstacle

            sqrt_disc = math.sqrt(discriminant)
            t_enter = (-b - sqrt_disc) / 2
            t_exit = (-b + sqrt_disc) / 2

            # We only care about entering the boundary from outside.
            if t_enter < 0:
                # Already inside/behind the boundary at t=0 relative to
                # travel start, or the entry point is behind us -- if
                # t_exit is still ahead and >= 0 we are already inside
                # the obstacle, which shouldn't normally happen; skip.
                continue

            if t_enter > distance:
                continue  # collision point is beyond the requested move

            if best_t is None or t_enter < best_t:
                best_t = t_enter
                best_obstacle = obstacle

        if best_t is None:
            return distance, None

        reason = (
            f"path blocked by {best_obstacle.name} at "
            f"({best_obstacle.x:g}, {best_obstacle.y:g}); stopped {best_t:.2f}m "
            f"into a requested {distance:.2f}m move"
        )
        return max(best_t, 0.0), reason
