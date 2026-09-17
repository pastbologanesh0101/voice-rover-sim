"""Unit tests for the voice-controlled rover simulator.

Run with either:
    python -m pytest
    python -m unittest discover
"""

import math
import unittest

from roversim import (
    Arena,
    MoveAction,
    Obstacle,
    ParseError,
    RoverSimulator,
    StopAction,
    TurnAction,
    parse_command,
)


class TestCommandParsing(unittest.TestCase):
    def test_simple_forward_move_parses(self):
        actions = parse_command("move forward 5 meters")
        self.assertEqual(actions, [MoveAction(direction="forward", distance=5.0)])

    def test_simple_backward_move_parses(self):
        actions = parse_command("move backward 2 meters")
        self.assertEqual(actions, [MoveAction(direction="backward", distance=2.0)])

    def test_simple_left_turn_parses(self):
        actions = parse_command("turn left 90 degrees")
        self.assertEqual(actions, [TurnAction(direction="left", degrees=90.0)])

    def test_simple_right_turn_parses(self):
        actions = parse_command("turn right 45 degrees")
        self.assertEqual(actions, [TurnAction(direction="right", degrees=45.0)])

    def test_stop_command_parses(self):
        actions = parse_command("stop")
        self.assertEqual(actions, [StopAction()])

    def test_synonym_variations_parse_to_same_action(self):
        variants = [
            "move forward 5 meters",
            "go ahead 5 meters",
            "move ahead 5 m",
            "go forward 5 metres",
        ]
        expected = MoveAction(direction="forward", distance=5.0)
        for text in variants:
            with self.subTest(text=text):
                self.assertEqual(parse_command(text), [expected])

        backward_variants = [
            "move backward 3 meters",
            "go back 3 meters",
            "move reverse 3 meters",
        ]
        expected_backward = MoveAction(direction="backward", distance=3.0)
        for text in backward_variants:
            with self.subTest(text=text):
                self.assertEqual(parse_command(text), [expected_backward])

    def test_compound_then_command_parses_ordered_sequence(self):
        actions = parse_command(
            "go backward 2 meters then turn right 45 degrees"
        )
        self.assertEqual(
            actions,
            [
                MoveAction(direction="backward", distance=2.0),
                TurnAction(direction="right", degrees=45.0),
            ],
        )

    def test_compound_and_command_parses_ordered_sequence(self):
        actions = parse_command(
            "move forward 3 meters and turn left 90 degrees then stop"
        )
        self.assertEqual(
            actions,
            [
                MoveAction(direction="forward", distance=3.0),
                TurnAction(direction="left", degrees=90.0),
                StopAction(),
            ],
        )

    def test_turn_around_parses_as_180_degree_turn(self):
        actions = parse_command("turn around")
        self.assertEqual(len(actions), 1)
        action = actions[0]
        self.assertIsInstance(action, TurnAction)
        self.assertEqual(action.degrees, 180.0)

    def test_unrecognized_command_raises_parse_error(self):
        with self.assertRaises(ParseError):
            parse_command("do a barrel roll")

    def test_unrecognized_command_does_not_crash_or_noop(self):
        # A ParseError is a clear, expected exception -- not a crash,
        # and not a silent no-op (empty list) either.
        try:
            result = parse_command("fly to the moon")
        except ParseError:
            pass
        else:
            self.fail(f"expected ParseError, got a result instead: {result!r}")


class TestSimulatorKinematics(unittest.TestCase):
    def test_forward_move_updates_position_for_known_heading(self):
        sim = RoverSimulator(arena=Arena(obstacles=[]))
        # heading 0 degrees means facing +x
        sim.execute(MoveAction(direction="forward", distance=4.0))
        x, y = sim.state.position()
        self.assertAlmostEqual(x, 4.0, places=6)
        self.assertAlmostEqual(y, 0.0, places=6)

    def test_backward_move_updates_position_for_known_heading(self):
        sim = RoverSimulator(arena=Arena(obstacles=[]))
        sim.execute(MoveAction(direction="backward", distance=4.0))
        x, y = sim.state.position()
        self.assertAlmostEqual(x, -4.0, places=6)
        self.assertAlmostEqual(y, 0.0, places=6)

    def test_turn_updates_heading_with_normalization_wraparound(self):
        sim = RoverSimulator(arena=Arena(obstacles=[]), start_heading=350.0)
        sim.execute(TurnAction(direction="left", degrees=20.0))
        # 350 + 20 = 370 -> wraps to 10
        self.assertAlmostEqual(sim.state.heading, 10.0, places=6)

        sim2 = RoverSimulator(arena=Arena(obstacles=[]), start_heading=10.0)
        sim2.execute(TurnAction(direction="right", degrees=30.0))
        # 10 - 30 = -20 -> wraps to 340
        self.assertAlmostEqual(sim2.state.heading, 340.0, places=6)

    def test_move_collides_with_obstacle_and_stops_at_boundary(self):
        obstacle = Obstacle(x=5.0, y=0.0, radius=1.0, name="test-crate")
        arena = Arena(obstacles=[obstacle])
        rover_radius = 0.3
        sim = RoverSimulator(arena=arena, rover_radius=rover_radius)

        entry = sim.execute(MoveAction(direction="forward", distance=10.0))

        expected_stop_distance = 5.0 - (obstacle.radius + rover_radius)
        x, y = sim.state.position()
        self.assertAlmostEqual(x, expected_stop_distance, places=6)
        self.assertAlmostEqual(y, 0.0, places=6)
        self.assertIsNotNone(entry.safety_stop_reason)
        self.assertIn("test-crate", entry.safety_stop_reason)

    def test_move_short_of_obstacle_does_not_trigger_safety_stop(self):
        obstacle = Obstacle(x=5.0, y=0.0, radius=1.0, name="test-crate")
        arena = Arena(obstacles=[obstacle])
        sim = RoverSimulator(arena=arena, rover_radius=0.3)

        entry = sim.execute(MoveAction(direction="forward", distance=2.0))

        x, y = sim.state.position()
        self.assertAlmostEqual(x, 2.0, places=6)
        self.assertIsNone(entry.safety_stop_reason)

    def test_command_history_records_executed_sequence(self):
        sim = RoverSimulator(arena=Arena(obstacles=[]))
        actions = parse_command(
            "move forward 3 meters then turn left 90 degrees then stop"
        )
        sim.execute_all(actions)

        self.assertEqual(len(sim.history), 3)
        self.assertIn("move forward 3", sim.history[0].action_description)
        self.assertIn("turn left 90", sim.history[1].action_description)
        self.assertIn("stop", sim.history[2].action_description)

        # History records position/heading progressively.
        self.assertAlmostEqual(sim.history[0].position[0], 3.0, places=6)
        self.assertAlmostEqual(sim.history[1].heading, 90.0, places=6)


if __name__ == "__main__":
    unittest.main()
