"""Copy-only oracle sensitivity checks; original DBs and evidence remain intact."""
import hashlib
import json
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
sys.dont_write_bytecode = True
import checker

ROOT = Path(__file__).resolve().parent


class OracleSensitivity(unittest.TestCase):
    def setUp(self):
        source = ROOT / json.loads((ROOT / "current.json").read_text())["directory"]
        self.temp = tempfile.TemporaryDirectory(prefix="oracle-negative-", dir=ROOT)
        self.copy = Path(self.temp.name) / "copy"
        shutil.copytree(source, self.copy)

    def tearDown(self):
        self.temp.cleanup()

    def case(self, key):
        return next(r for r in checker.oracle(self.copy)["runs"] if r["id"] == key)

    def test_changed_cents_detected(self):
        with sqlite3.connect(self.copy / "normal-up/after-1.sqlite") as db:
            db.execute("UPDATE orders SET amount_cents=1231 WHERE id='a'")
        self.assertFalse(self.case("normal-up")["steps"][0]["matches_expected"])

    def test_rollback_schema_drift_detected(self):
        with sqlite3.connect(self.copy / "failure-after-drop/after-1.sqlite") as db:
            db.execute("ALTER TABLE orders ADD COLUMN ghost TEXT")
        row = self.case("failure-after-drop")["steps"][0]
        self.assertFalse(row["matches_expected"])
        self.assertFalse(row["row_schema_unchanged"])

    def test_original_seed_change_detected(self):
        with sqlite3.connect(self.copy / "roundtrip/before.sqlite") as db:
            db.execute("UPDATE orders SET amount_text='99.00' WHERE id='a'")
        self.assertFalse(self.case("roundtrip")["before_matches_expected"])

    def test_forged_refusal_outcome_detected(self):
        path = self.copy / "lossy-refused/step-1-trace.json"
        trace = json.loads(path.read_text())
        next(x for x in trace if x["event"] == "refused")["event"] = "migrated"
        path.write_text(json.dumps(trace))
        self.assertFalse(self.case("lossy-refused")["steps"][0]["matches_expected"])

    def test_default_checker_is_read_only(self):
        def snapshot():
            return {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                    for p in ROOT.rglob("*") if p.is_file()}
        before = snapshot()
        run = subprocess.run([sys.executable, "checker.py"], cwd=ROOT, text=True, capture_output=True)
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual(before, snapshot())


if __name__ == "__main__":
    unittest.main(verbosity=2)
