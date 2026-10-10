"""Independent oracle rejects altered copies; normal checker remains read-only."""
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

    def row(self, key):
        return next(r for r in checker.oracle(self.copy)["runs"] if r["id"] == key)

    def test_sqlite_price_drift_detected(self):
        with sqlite3.connect(self.copy / "port-sqlite-normal/orders.sqlite") as db:
            db.execute("UPDATE orders SET total=200")
        row = self.row("port-sqlite-normal")
        self.assertFalse(row["matches_fixed_expected"])
        self.assertFalse(row["contract_conforms"])

    def test_memory_missing_row_detected(self):
        (self.copy / "port-memory-normal/memory-final.json").write_text("[]\n")
        self.assertFalse(self.row("port-memory-normal")["matches_fixed_expected"])

    def test_exception_translation_forgery_detected(self):
        path = self.copy / "port-sqlite-unavailable/trace.json"
        trace = json.loads(path.read_text())
        next(x for x in trace if x["event"] == "response")["status"] = 201
        path.write_text(json.dumps(trace))
        self.assertFalse(self.row("port-sqlite-unavailable")["matches_fixed_expected"])

    def test_source_dependency_violation_detected(self):
        with tempfile.TemporaryDirectory(prefix="dependency-negative-", dir=ROOT) as directory:
            clone = Path(directory)
            for name in ("ports.py", "domain.py", "adapters.py", "bad.py", "worker.py"):
                shutil.copyfile(ROOT / name, clone / name)
            path = clone / "domain.py"
            path.write_text(path.read_text() + "\nimport adapters\n")
            original_root = checker.ROOT
            try:
                checker.ROOT = clone
                dependencies = {e["to"] for e in checker.dependency_graph()["edges"] if e["from"] == "domain.py"}
                self.assertNotEqual(dependencies, {"ports"})
                self.assertIn("adapters", dependencies)
            finally:
                checker.ROOT = original_root

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
