import importlib.util
import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("osc_protocol", ROOT / "protocol.py")
PROTOCOL = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PROTOCOL)


class ProtocolTests(unittest.TestCase):
    def test_split_due_events(self):
        due, future = PROTOCOL.split_due_events(
            [(None, "a", []), (10.0, "b", []), (30.0, "c", [])],
            now=20.0,
        )
        self.assertEqual([event[1] for event in due], ["a", "b"])
        self.assertEqual([event[1] for event in future], ["c"])

    def test_voice_end_prefers_explicit_duration(self):
        end_at = PROTOCOL.compute_voice_end(100.0, "sampler", {"duration": 0.75, "decay": 9})
        self.assertEqual(end_at, 100.75)

    def test_dashdrum_keeps_legacy_decay_lifetime(self):
        end_at = PROTOCOL.compute_voice_end(5.0, "dashDrum", {"decay": 0.2})
        self.assertEqual(end_at, 5.3)

    def test_expire_voices_cleans_tracks(self):
        voices = {
            1: {"track": "drums", "end_at": 1.0},
            2: {"track": "pad", "end_at": None},
        }
        tracks = {
            "drums": {"voices": {1: voices[1]}},
            "pad": {"voices": {2: voices[2]}},
        }
        affected = PROTOCOL.expire_voices(voices, tracks, now=2.0)
        self.assertEqual(affected, ["drums"])
        self.assertNotIn(1, voices)
        self.assertNotIn(1, tracks["drums"]["voices"])

    def test_reset_transport_clears_queued_and_active(self):
        scheduled = [(1.0, "/x", [])]
        voices = {1: {"track": "bass"}}
        tracks = {"bass": {"voices": {1: {}}}}
        touched = PROTOCOL.reset_transport_state(scheduled, voices, tracks)
        self.assertEqual(touched, ["bass"])
        self.assertEqual(scheduled, [])
        self.assertEqual(voices, {})
        self.assertEqual(tracks, {})

    def test_clamps_normalized_controls(self):
        self.assertEqual(PROTOCOL.clamp_normalized(-2), 0.0)
        self.assertEqual(PROTOCOL.clamp_normalized(3), 1.0)
        self.assertEqual(PROTOCOL.clamp_normalized(0.25), 0.25)
        self.assertIsNone(PROTOCOL.clamp_normalized(float("nan")))


if __name__ == "__main__":
    unittest.main()
