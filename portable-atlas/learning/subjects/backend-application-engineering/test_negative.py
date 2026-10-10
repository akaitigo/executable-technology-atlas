"""Oracle sensitivity using disposable copies, never changing original evidence."""
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
        self.original = ROOT / json.loads((ROOT / "current.json").read_text())["directory"]
        self.temp = tempfile.TemporaryDirectory(prefix="oracle-negative-", dir=ROOT)
        self.copy = Path(self.temp.name) / "copy"
        shutil.copytree(self.original, self.copy)

    def tearDown(self):
        self.temp.cleanup()

    def normal(self):
        return next(r for r in checker.oracle(self.copy)["rows"] if r["id"] == "atomic-normal")

    def test_missing_outbox_detected_by_actual_sql(self):
        with sqlite3.connect(self.copy / "atomic-normal/service.sqlite") as db:
            db.execute("DELETE FROM outbox")
        self.assertFalse(self.normal()["match"])
        self.assertEqual(self.normal()["order_without_outbox"], ["a"])

    def test_changed_quantity_detected_by_hand_rows(self):
        with sqlite3.connect(self.copy / "atomic-normal/service.sqlite") as db:
            db.execute("UPDATE orders SET quantity=99")
        self.assertFalse(self.normal()["match"])

    def test_fabricated_response_detected(self):
        path = self.copy / "atomic-normal/trace.json"
        trace = json.loads(path.read_text())
        next(x for x in trace if x["event"] == "response")["status"] = 500
        path.write_text(json.dumps(trace))
        self.assertFalse(self.normal()["match"])

    def test_checker_is_read_only(self):
        def snapshot():
            return {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                    for p in ROOT.rglob("*") if p.is_file()}
        before = snapshot()
        run = subprocess.run([sys.executable, "checker.py"], cwd=ROOT, text=True, capture_output=True)
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual(before, snapshot())


if __name__ == "__main__":
    unittest.main(verbosity=2)
