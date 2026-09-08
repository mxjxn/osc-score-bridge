import importlib.util
import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("osc_score_parser", ROOT / "parser.py")
PARSER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PARSER)


class ParserTests(unittest.TestCase):
    def test_parses_synth_node_and_control_updates(self):
        fixture = ROOT / "tests" / "fixtures" / "parser.osc"
        tracks = PARSER.parse_osc_file(fixture)
        self.assertEqual(tracks["lead.freq"], [(0.0, 440.0), (0.5, 660.0)])
        self.assertEqual(tracks["lead.amp"], [(0.0, 0.25)])
        self.assertEqual(tracks["control_3"], [(1.0, 0.75)])

    def test_summary_reports_range_and_duration(self):
        summary = PARSER.get_track_summary({"x": [(1.0, 4.0), (2.5, -1.0)]})[0]
        self.assertEqual(summary["event_count"], 2)
        self.assertEqual(summary["min_val"], -1.0)
        self.assertEqual(summary["max_val"], 4.0)
        self.assertEqual(summary["duration"], 1.5)


if __name__ == "__main__":
    unittest.main()
