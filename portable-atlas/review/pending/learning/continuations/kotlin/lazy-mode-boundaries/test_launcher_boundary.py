#!/usr/bin/env python3
"""Atlas: simulate launcher refusal/exec failure, without starting a child or changing priority."""
import contextlib
import io
import json
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch
import priority_launcher

results = []
with tempfile.TemporaryDirectory(prefix="atlas-launcher-check-") as directory:
    record = Path(directory) / "priority.json"
    for label, verified, exec_error, expected_exit in [
        ("priority-denied-target-not-called", False, None, 77),
        ("exec-failed-target-not-started", True, FileNotFoundError("controlled missing target"), 78),
    ]:
        error_text = io.StringIO()
        with patch.object(sys, "argv", ["launcher", str(record), "--", "/controlled/not-executed"]), \
             patch.object(priority_launcher, "priority_gate", return_value={"verified_before_exec": verified, "after": 10 if verified else None}), \
             patch.object(priority_launcher.os, "execvpe", side_effect=exec_error) as execute, \
             contextlib.redirect_stderr(error_text):
            exit_code = priority_launcher.main()
        saved = json.loads(record.read_text())
        assert exit_code == expected_exit and saved["target_started"] is False
        assert saved["exec_attempted"] is verified
        assert execute.call_count == int(verified)
        results.append({"case": label, "passed": True, "exit_code": exit_code, "saved": saved, "stderr": error_text.getvalue()})
print(json.dumps({"project": "Atlas", "simulated_only": True, "new_compiler_or_jvm": 0, "os_priority_changes": 0, "cases": results}, indent=2))
