import math
import io
import json
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path
from simulator import PRESETS, simulate


class SimulationTest(unittest.TestCase):
    def test_all_presets_match_independent_oracle(self):
        for name, inputs in PRESETS.items():
            with self.subTest(name=name):
                result = simulate(**inputs)
                self.assertTrue(result["summary"]["oracle_pass"])
                self.assertEqual(len(result["samples"]), 41)
                self.assertTrue(all(math.isfinite(row["y"]) for row in result["samples"]))

    def test_expected_behaviors(self):
        results = {name: simulate(**inputs) for name, inputs in PRESETS.items()}
        self.assertAlmostEqual(results["stable"]["samples"][1]["y"], .2)
        self.assertAlmostEqual(results["oscillation"]["samples"][1]["y"], 1.)
        self.assertAlmostEqual(results["oscillation"]["samples"][2]["y"], .5)
        self.assertAlmostEqual(results["boundary"]["samples"][2]["y"], 0.)
        self.assertGreater(abs(results["divergence"]["summary"]["final_y"]), 100000)
        self.assertLess(abs(results["stable"]["summary"]["final_y"]-2/3), 1e-6)
        for name in ("stable", "oscillation", "boundary", "divergence"):
            self.assertEqual(results[name]["summary"]["linear_euler_class"], name)
        sat = results["saturation"]
        self.assertEqual(sat["summary"]["saturated_updates"], 40)
        self.assertTrue(all(abs(row["u"]) <= .35 for row in sat["samples"]))
        self.assertAlmostEqual(sat["summary"]["final_y"], .35*(1-.9**40))

    def test_step_halving_reduces_continuous_error(self):
        errors = []
        for dt, steps in ((.1, 10), (.05, 20), (.025, 40)):
            row = simulate(dt=dt, steps=steps)["samples"][-1]
            errors.append(abs(row["y"]-row["continuous_unsaturated"]))
        self.assertGreater(errors[0], errors[1])
        self.assertGreater(errors[1], errors[2])

    def test_gain_and_step_together_determine_euler_factor(self):
        self.assertEqual(simulate(gain=12, dt=.2)["summary"]["linear_euler_class"], "divergence")
        self.assertEqual(simulate(gain=12, dt=.05)["summary"]["linear_euler_class"], "stable")

    def test_general_clip_does_not_claim_linear_oracle(self):
        result = simulate(gain=2, dt=.8, limit=.8)
        self.assertIsNone(result["summary"]["oracle_pass"])
        self.assertTrue(all(abs(row["u"]) <= .8 for row in result["samples"]))

    def test_invalid_input_refused(self):
        for inputs in ({"gain": float("nan")}, {"dt": float("inf")}, {"gain": -1},
                       {"dt": 0}, {"steps": 101}, {"steps": True}, {"limit": -.1}):
            with self.subTest(inputs=inputs), self.assertRaises(ValueError):
                simulate(**inputs)


if __name__ == "__main__":
    if sys.argv[1:] == ["--record"]:
        started = datetime.now(timezone.utc).isoformat()
        output = io.StringIO()
        suite = unittest.defaultTestLoader.loadTestsFromTestCase(SimulationTest)
        result = unittest.TextTestRunner(stream=output, verbosity=2).run(suite)
        completed = datetime.now(timezone.utc).isoformat()
        raw = output.getvalue()
        folder = Path(__file__).resolve().parent / "observations"
        folder.mkdir(exist_ok=True)
        (folder / "tests.txt").write_text(raw, encoding="utf-8")
        (folder / "tests.json").write_text(json.dumps({
            "command": ["python3", "test_simulator.py", "--record"],
            "started_at": started, "completed_at": completed,
            "tests_run": result.testsRun, "failures": len(result.failures),
            "errors": len(result.errors), "skipped": len(result.skipped),
            "successful": result.wasSuccessful(), "raw_output": "tests.txt",
        }, indent=2) + "\n", encoding="utf-8")
        print(raw, end="")
        sys.exit(0 if result.wasSuccessful() else 1)
    else:
        unittest.main(verbosity=2)
