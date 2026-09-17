"""Voice Controlled Rover - 2D software simulator.

This package implements a text/voice-style command parser and a simple
2D kinematic rover simulator with obstacle-aware safety stops.

IMPORTANT: this is a pure-software simulation. There is no real rover
hardware and no live microphone anywhere in this codebase. "Voice
commands" here means already-transcribed text strings that look like
what a speech-to-text engine would hand you (e.g. "move forward 3
meters then turn left 90 degrees"). Wiring in a real microphone/ASR
engine or a real motor controller is explicitly out of scope.
"""

from .parser import parse_command, ParseError
from .actions import MoveAction, TurnAction, StopAction
from .arena import Arena, Obstacle, DEFAULT_ARENA
from .simulator import RoverSimulator, RoverState, HistoryEntry

__all__ = [
    "parse_command",
    "ParseError",
    "MoveAction",
    "TurnAction",
    "StopAction",
    "Arena",
    "Obstacle",
    "DEFAULT_ARENA",
    "RoverSimulator",
    "RoverState",
    "HistoryEntry",
]
