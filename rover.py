#!/usr/bin/env python3
"""Voice Controlled Rover -- command-line entry point.

This is a 2D SOFTWARE SIMULATION. There is no real rover hardware and
no live microphone involved anywhere in this program. The "voice
command" is just a text string you pass on the command line, standing
in for text that a speech-to-text engine would have already produced
from spoken audio.

Usage:
    python rover.py "move forward 3 meters then turn left 90 degrees"

Each run starts the rover from a fresh state: position (0, 0), heading
0 degrees (facing +x). State is NOT persisted between runs -- every
invocation of this script is an independent simulation starting from
the same origin. (See README for why this choice was made.)
"""

import sys

from roversim import RoverSimulator, ParseError, parse_command


def run(command_text: str) -> int:
    try:
        actions = parse_command(command_text)
    except ParseError as exc:
        print(f"Could not understand command: {exc}", file=sys.stderr)
        return 1

    sim = RoverSimulator()
    print(f'Command: "{command_text}"')
    print(f"Parsed into {len(actions)} action(s):")
    for action in actions:
        print(f"  - {action.describe()}")
    print()

    print("Execution log:")
    for entry in sim.execute_all(actions):
        print(f"  {entry}")

    print()
    x, y = sim.state.position()
    print(f"Final position: ({x:.2f}, {y:.2f})")
    print(f"Final heading:  {sim.state.heading:.1f} degrees")

    safety_stops = [e for e in sim.history if e.safety_stop_reason]
    if safety_stops:
        print()
        print("Safety stops encountered:")
        for entry in safety_stops:
            print(f"  - {entry.safety_stop_reason}")

    return 0


def main(argv=None) -> int:
    argv = sys.argv if argv is None else argv
    if len(argv) < 2:
        print(f"usage: {argv[0]} \"<voice command text>\"", file=sys.stderr)
        return 2
    command_text = " ".join(argv[1:])
    return run(command_text)


if __name__ == "__main__":
    sys.exit(main())
