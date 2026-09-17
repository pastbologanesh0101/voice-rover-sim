# Voice Controlled Rover (2D Simulator)

**This is a 2D software simulation only.** There is no real rover hardware
here, and no live microphone or speech recognition either. "Voice commands"
in this project means plain text strings that *represent* already-transcribed
speech — e.g. what a speech-to-text engine would hand you after you said
"move forward three meters." This project starts from that text and is
responsible for everything downstream of it: parsing the text into a
structured movement command, and simulating a rover executing it on a 2D
grid with simple kinematics and obstacle avoidance.

If you're looking for actual microphone capture or general voice-assistant
skills, that's a different, separate project (`voice-assistant`). This repo
is specifically about parsing rover *movement* commands and simulating the
rover that follows them.

## What it actually does

1. **Command parser** (`roversim/parser.py`) — regex-based parsing of
   natural-language-ish movement commands into structured `Action` objects
   (`roversim/actions.py`). Handles reasonable phrasing variation (synonyms)
   and compound commands chained with "then" / "and".
2. **2D rover simulator** (`roversim/simulator.py`) — tracks rover position
   `(x, y)` and heading (degrees), executes parsed actions with simple
   kinematics, and checks each move against a small bundled arena of
   obstacles (`roversim/arena.py`). If a move would collide, the rover stops
   short at the obstacle's safety boundary and reports why, instead of
   clipping through it.
3. **History log** — every executed action is recorded with the resulting
   position/heading (and safety-stop reason, if any) in `sim.history`.
4. **CLI** (`rover.py`) — parses one command string from `argv`, runs it
   against a *fresh* rover simulation, and prints the resulting state.

## Supported command grammar

Case-insensitive, tolerant of extra whitespace.

```
move forward|ahead <number> meters|metres|m
move backward|back|reverse <number> meters|metres|m
go forward|ahead <number> meters
go backward|back|reverse <number> meters
turn left|right <number> degrees|deg
turn around                     -> a 180 degree turn
stop
```

`move` / `go` (optionally preceded by "please") are interchangeable verbs.
Chain multiple commands with **"then"** or **"and"**:

```
"go backward 2 meters then turn right 45 degrees"
"move forward 3 meters and turn left 90 degrees then stop"
```

Anything that doesn't match this grammar raises a `ParseError` with a clear
message — it never crashes and never silently does nothing.

## Simulation model

- The rover starts at position `(0, 0)` facing heading `0` degrees
  (the `+x` direction). Left turns increase heading (counter-clockwise),
  right turns decrease it (clockwise); heading is always normalized into
  `[0, 360)`.
- `move forward N meters` translates the rover `N` meters along its current
  heading vector; `move backward N meters` translates it `N` meters
  opposite that vector.
- A small bundled arena (`roversim/arena.py`, `DEFAULT_ARENA`) defines a few
  circular obstacles. Before applying a move, the simulator checks whether
  the straight-line path would enter any obstacle's safety boundary
  (obstacle radius + rover radius). If it would, the rover is stopped
  exactly at that boundary and the executed history entry carries a
  `safety_stop_reason` explaining which obstacle blocked it and how far the
  rover actually traveled.
- **State is not persisted between CLI runs.** Each invocation of
  `python rover.py "..."` starts a brand-new `RoverSimulator` at the origin.
  This was a deliberate choice to keep the CLI simple, stateless, and easy to
  test/reason about — every run is self-contained and reproducible. (The
  `RoverSimulator` class itself is perfectly happy to run many commands
  against one long-lived instance — see `execute_all` — if you want to script
  a persistent session; the CLI just doesn't do that automatically.)

## How to run

Requires only the Python standard library (`pytest` is used for tests but is
optional — `unittest` works too).

```bash
# Run a single compound command
python rover.py "move forward 3 meters then turn left 90 degrees"

# Run the test suite
python -m pytest tests/ -v
# or
python -m unittest discover -v
```

## Example session

```text
$ python rover.py "move forward 3 meters then turn left 90 degrees"
Command: "move forward 3 meters then turn left 90 degrees"
Parsed into 2 action(s):
  - move forward 3 meters
  - turn left 90 degrees

Execution log:
  move forward 3 meters -> position=(3.00, 0.00), heading=0.0 deg
  turn left 90 degrees -> position=(3.00, 0.00), heading=90.0 deg

Final position: (3.00, 0.00)
Final heading:  90.0 degrees
```

Driving straight into a bundled obstacle (there's a "crate" at `(5, 0)` with
radius 1m in the default arena):

```text
$ python rover.py "move forward 10 meters"
Command: "move forward 10 meters"
Parsed into 1 action(s):
  - move forward 10 meters

Execution log:
  move forward 10 meters -> position=(3.70, 0.00), heading=0.0 deg [SAFETY STOP: path blocked by crate at (5, 0); stopped 3.70m into a requested 10.00m move]

Final position: (3.70, 0.00)
Final heading:  0.0 degrees

Safety stops encountered:
  - path blocked by crate at (5, 0); stopped 3.70m into a requested 10.00m move
```

An unrecognized command fails clearly instead of crashing or doing nothing:

```text
$ python rover.py "do a barrel roll"
Could not understand command: could not parse command segment: 'do a barrel roll'
```

## Project layout

```
rover.py                   CLI entry point
roversim/
  actions.py                MoveAction / TurnAction / StopAction
  parser.py                 regex-based text -> Action(s) parser
  arena.py                  Obstacle / Arena + the bundled DEFAULT_ARENA
  simulator.py               RoverState / RoverSimulator / HistoryEntry
tests/
  test_rover.py              unit tests (pytest / unittest compatible)
.github/workflows/tests.yml  CI: runs the test suite on Python 3.11 and 3.12
```

## Tests

`tests/test_rover.py` covers, among other things:

- simple forward/backward/left/right/stop command parsing
- synonym variations (forward/ahead, backward/back/reverse, meters/m/metres)
  parsing to the same action
- compound "X then Y" / "X and Y" commands parsing into the correct ordered
  action sequence
- "turn around" parsing as a 180 degree turn
- unrecognized command text raising a clear `ParseError`
- forward/backward moves updating position correctly for a known heading
- turns updating heading correctly, including angle normalization/wraparound
  past 360 degrees
- a move that would collide with a bundled obstacle stopping short at the
  correct safety-boundary distance and reporting why
- command history correctly recording the sequence of executed actions

## License

MIT — see [LICENSE](LICENSE).
