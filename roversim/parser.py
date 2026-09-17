"""Regex-based parser for voice-style rover movement commands.

The input to this parser is a plain text string, meant to represent
already-transcribed speech (e.g. from a speech-to-text engine). This
module does no audio processing at all -- it only understands text.

Supported grammar (case-insensitive, extra whitespace tolerated):

    move forward|ahead <number> meters
    move backward|back|reverse <number> meters
    go forward|ahead <number> meters
    go backward|back|reverse <number> meters
    turn left|right <number> degrees|deg
    turn around                          -> 180 degree turn
    stop

Multiple commands can be chained together with "then" or "and":

    "move forward 5 meters then turn left 90 degrees"
    "go backward 2 meters and turn right 45 degrees then stop"

Synonyms handled:
    forward  == ahead
    backward == back == reverse
    meters   == meter == metres == metre == m
    degrees  == deg
"""

import re

from .actions import MoveAction, StopAction, TurnAction


class ParseError(ValueError):
    """Raised when a command (or a segment of a compound command)
    cannot be understood. Callers should treat this as a normal,
    expected outcome for bad input -- not a crash."""


_FORWARD_WORDS = {"forward", "ahead"}
_BACKWARD_WORDS = {"backward", "back", "reverse"}

_SPLIT_RE = re.compile(r"\s*,?\s*\b(?:then|and)\b\s*", re.IGNORECASE)

_STOP_RE = re.compile(r"^\s*stop\s*$", re.IGNORECASE)

_TURN_AROUND_RE = re.compile(r"^\s*turn\s+around\s*$", re.IGNORECASE)

_MOVE_RE = re.compile(
    r"^\s*(?:(?:please\s+)?(?:move|go|drive)\s+)?"
    r"(forward|ahead|backward|back|reverse)\s+"
    r"([0-9]*\.?[0-9]+)\s*"
    r"(?:meters?|metres?|m)\s*$",
    re.IGNORECASE,
)

_TURN_RE = re.compile(
    r"^\s*turn\s+(left|right)\s+"
    r"([0-9]*\.?[0-9]+)\s*"
    r"(?:degrees?|deg)\s*$",
    re.IGNORECASE,
)


def _normalize_move_direction(word: str) -> str:
    word = word.lower()
    if word in _FORWARD_WORDS:
        return "forward"
    if word in _BACKWARD_WORDS:
        return "backward"
    raise ParseError(f"unrecognized movement direction: {word!r}")


def _parse_segment(segment: str):
    """Parse a single (non-compound) command segment into one Action.

    Raises ParseError if the segment isn't recognized.
    """
    text = segment.strip()
    if not text:
        raise ParseError("empty command segment")

    if _STOP_RE.match(text):
        return StopAction()

    if _TURN_AROUND_RE.match(text):
        return TurnAction(direction="right", degrees=180.0)

    move_match = _MOVE_RE.match(text)
    if move_match:
        direction_word, number = move_match.groups()
        direction = _normalize_move_direction(direction_word)
        return MoveAction(direction=direction, distance=float(number))

    turn_match = _TURN_RE.match(text)
    if turn_match:
        direction_word, number = turn_match.groups()
        direction = direction_word.lower()
        return TurnAction(direction=direction, degrees=float(number))

    raise ParseError(f"could not parse command segment: {segment!r}")


def parse_command(text: str):
    """Parse a (possibly compound) voice-style command string into an
    ordered list of Action objects.

    Compound commands are chained with "then" or "and", e.g.:
        "move forward 3 meters then turn left 90 degrees"

    Raises ParseError if the text, or any part of a compound command,
    cannot be understood. Never raises any other exception type and
    never silently returns an empty/no-op result for unrecognized
    text.
    """
    if text is None:
        raise ParseError("command text must not be None")

    stripped = text.strip()
    if not stripped:
        raise ParseError("command text must not be empty")

    segments = [s for s in _SPLIT_RE.split(stripped) if s.strip()]
    if not segments:
        raise ParseError(f"could not parse command: {text!r}")

    actions = [_parse_segment(segment) for segment in segments]
    return actions
