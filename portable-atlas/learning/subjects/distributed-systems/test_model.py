import copy
import io
import itertools
import json
import sys
import unittest
from datetime import datetime, timezone
from model import ROOT, Simulator, independent_oracle, observe, permutation_check, prepared, simulate


class ReplicaTest(unittest.TestCase):
    def test_partition_retains_local_writes_and_refuses_delivery(self):
        sim = prepared("version-max")
        self.assertEqual(sim.nodes["A"]["register"]["value"], "alpha-2")
        self.assertEqual(sim.nodes["B"]["register"]["value"], "beta")
        before = copy.deepcopy(sim.nodes)
        with self.assertRaises(ValueError):
            sim.deliver("A1")
        self.assertEqual(sim.nodes, before)

    def test_arrival_counterexample(self):
        run = simulate()
        self.assertFalse(run["summary"]["converged"])
        self.assertEqual(run["final_state"]["A"]["register"]["value"], "beta")
        self.assertEqual(run["final_state"]["B"]["register"]["value"], "alpha")

    def test_all_six_orders_match_independent_oracle(self):
        result = permutation_check()
        self.assertEqual(result["count"], 6)
        self.assertEqual(result["max_passed"], 6)
        self.assertEqual(result["arrival_converged"], 0)

    def test_duplicate_every_position_and_delayed_stale(self):
        # 4! positional schedules incl. duplicate A1, not just end-of-run replay.
        for order in itertools.permutations(["A1", "A2", "B1", "A1"]):
            sim = prepared("version-max")
            expected = independent_oracle(sim.writes)
            sim.heal()
            for message in order:
                sim.deliver(message)
            self.assertTrue(all(state["register"] == expected for state in sim.nodes.values()))
        self.assertTrue(simulate("version-max", duplicate=True)["summary"]["all_match_max_oracle"])

    def test_equal_counter_tie_breaks_by_replica_id(self):
        sim = Simulator("version-max")
        sim.write("A", "alpha")
        sim.write("B", "beta")
        sim.heal()
        sim.deliver("A1")
        sim.deliver("B1")
        self.assertEqual(sim.nodes["A"]["register"], {"value": "beta", "version": [1, "B"]})
        self.assertEqual(sim.nodes["A"]["register"], sim.nodes["B"]["register"])

    def test_clock_receive_then_write_and_old_message_ignored(self):
        sim = Simulator("version-max")
        sim.write("A", "first")
        sim.heal()
        sim.deliver("A1")
        message = sim.write("B", "after-receive")
        self.assertEqual(message, "B3")
        sim.deliver(message)
        sim.deliver("A1")
        self.assertEqual(sim.nodes["B"]["register"]["value"], "after-receive")

    def test_losing_values_are_not_recovered_by_convergence(self):
        report = simulate("version-max")
        self.assertEqual(report["summary"]["discarded_values_under_max"], ["alpha", "beta"])

    def test_invalid_inputs_do_not_mutate(self):
        for mode in ("consensus", "unknown"):
            with self.assertRaises(ValueError):
                Simulator(mode)
        sim = Simulator()
        before = copy.deepcopy(sim.nodes)
        for node, value in (("C", "value"), ("A", ""), ("A", "x"*25), ("A", 1)):
            with self.assertRaises(ValueError):
                sim.write(node, value)
            self.assertEqual(sim.nodes, before)
        for order in (["A1", "A1", "B1"], ["A1"], ["A1", "A2", "fake"]):
            with self.assertRaises(ValueError):
                simulate(order=order)
        sim.heal()
        with self.assertRaises(ValueError):
            sim.deliver("fake")
        with self.assertRaises(ValueError):
            simulate(duplicate="yes")

    def test_raw_trace_is_deterministic(self):
        self.assertEqual(simulate("version-max"), simulate("version-max"))
        self.assertFalse(observe()["execution"]["real_network"])


if __name__ == "__main__":
    if sys.argv[1:] == ["--record"]:
        started = datetime.now(timezone.utc).isoformat()
        output = io.StringIO()
        result = unittest.TextTestRunner(stream=output, verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(ReplicaTest))
        folder = ROOT/"observations"
        folder.mkdir(exist_ok=True)
        (folder/"tests.txt").write_text(output.getvalue(), encoding="utf-8")
        (folder/"tests.json").write_text(json.dumps({"command": ["python3", "test_model.py", "--record"],
            "started_at": started, "completed_at": datetime.now(timezone.utc).isoformat(),
            "tests_run": result.testsRun, "failures": len(result.failures), "errors": len(result.errors),
            "skipped": len(result.skipped), "successful": result.wasSuccessful()}, indent=2)+"\n", encoding="utf-8")
        print(output.getvalue(), end="")
        sys.exit(0 if result.wasSuccessful() else 1)
    else:
        unittest.main(verbosity=2)
