"""Read-only calculator/oracle checks. No evidence rewrite."""
import sys
sys.dont_write_bytecode = True
import json
import unittest
from runner import ROOT, ReplayGuard, mac_tag, run_lesson, verify_tag


class LessonTests(unittest.TestCase):
    def test_rfc_oracle(self):
        vectors = json.loads((ROOT / "oracle.json").read_text())["vectors"]
        self.assertEqual(len(vectors), 2)
        for v in vectors:
            with self.subTest(vector=v["id"]):
                self.assertEqual(mac_tag(bytes.fromhex(v["key_hex"]), bytes.fromhex(v["message_hex"])).hex(), v["expected_tag_hex"])

    def test_all_scenarios_independent_expected(self):
        expected = json.loads((ROOT / "oracle.json").read_text())["scenario_expected"]
        run = run_lesson()
        self.assertEqual({r["id"] for r in run["scenarios"]}, set(expected))
        for row in run["scenarios"]:
            with self.subTest(scenario=row["id"]):
                self.assertEqual(row["mac"]["reason"], expected[row["id"]]["mac"])
                self.assertEqual(row["guard"]["reason"], expected[row["id"]]["guard"])
        self.assertTrue(all(v["matched"] for v in run["rfc_vectors"]))

    def test_replay_mac_has_no_memory(self):
        key, message = b"public-test-key", b'{"message_id":"a","operation":"read","resource":"x"}'
        tag = mac_tag(key, message).hex()
        self.assertTrue(verify_tag(key, message, tag)["accepted"])
        self.assertTrue(verify_tag(key, message, tag)["accepted"])
        g = ReplayGuard()
        self.assertTrue(g.accept(key, message, tag)["accepted"])
        self.assertEqual(g.accept(key, message, tag)["reason"], "duplicate-id")
        self.assertTrue(ReplayGuard().accept(key, message, tag)["accepted"])

    def test_rejection_does_not_poison_state(self):
        row = next(r for r in run_lesson()["scenarios"] if r["id"] == "valid")
        key, msg, tag = bytes.fromhex(row["key_hex"]), bytes.fromhex(row["message_hex"]), row["supplied_tag_hex"]
        g = ReplayGuard()
        self.assertFalse(g.accept(key, msg + b" ", tag)["accepted"])
        self.assertEqual(g.seen, set())
        self.assertTrue(g.accept(key, msg, tag)["accepted"])

    def test_signed_id_not_unsigned_alias(self):
        key = b"public-test-key"
        g = ReplayGuard()
        a = b'{"message_id":"a","operation":"read","resource":"x"}'
        b = b'{"resource":"x", "operation":"read", "message_id":"a"}'
        self.assertTrue(g.accept(key, a, mac_tag(key, a).hex())["accepted"])
        self.assertEqual(g.accept(key, b, mac_tag(key, b).hex())["reason"], "duplicate-id")
        fresh = b'{"message_id":"b","operation":"read","resource":"x"}'
        self.assertTrue(g.accept(key, fresh, mac_tag(key, fresh).hex())["accepted"])

    def test_tag_format_and_hex_case(self):
        key, msg = b"public-test-key", b"x"
        tag = mac_tag(key, msg).hex()
        self.assertTrue(verify_tag(key, msg, tag.upper())["accepted"])
        for bad in ("", None, 1, b"00", tag[:-2], tag + "00", " " + tag, "z" * 64):
            with self.subTest(tag=repr(bad)):
                self.assertEqual(verify_tag(key, msg, bad)["reason"], "invalid-tag-format")

    def test_empty_message_allowed_but_empty_key_rejected(self):
        key = b"public-test-key"
        self.assertEqual(len(mac_tag(key, b"")), 32)
        self.assertTrue(verify_tag(key, b"", mac_tag(key, b"").hex())["accepted"])
        with self.assertRaises(ValueError):
            mac_tag(b"", b"x")

    def test_types_rejected(self):
        for key, msg in (("key", b"x"), (b"key", "x"), (None, b"x"), (b"key", None)):
            with self.subTest(key=key, msg=msg), self.assertRaises(TypeError):
                mac_tag(key, msg)

    def test_authenticated_bad_envelope_rejected(self):
        key = b"public-test-key"
        for msg in (b"", b"\xff", b"[]", b"{}", b'{"message_id":"","operation":"r","resource":"x"}',
                    b'{"message_id":"a","message_id":"b","operation":"r","resource":"x"}'):
            with self.subTest(message=msg):
                g = ReplayGuard()
                self.assertEqual(g.accept(key, msg, mac_tag(key, msg).hex())["reason"], "invalid-envelope")
                self.assertEqual(g.seen, set())

    def test_message_and_tag_bytes_really_change(self):
        rows = {r["id"]: r for r in run_lesson()["scenarios"]}
        self.assertNotEqual(rows["valid"]["message_hex"], rows["message-tamper"]["message_hex"])
        self.assertNotEqual(rows["valid"]["key_hex"], rows["wrong-key"]["key_hex"])
        self.assertNotEqual(rows["valid"]["supplied_tag_hex"], rows["tag-tamper"]["supplied_tag_hex"])
        self.assertEqual(rows["valid"]["supplied_tag_hex"], rows["replay"]["supplied_tag_hex"])
        self.assertEqual(rows["replay"]["seen_before"], ["demo-001"])

    def test_deterministic_and_no_timing_claim(self):
        self.assertEqual(run_lesson(), run_lesson())
        self.assertFalse(run_lesson()["timing_measured"])


if __name__ == "__main__":
    unittest.main()
