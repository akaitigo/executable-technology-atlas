#!/usr/bin/env python3
"""Atlas: simulate permission denial and silent ineffective adjustment; no JVM or OS priority change."""
import json
import os
from unittest.mock import Mock
from priority_launcher import priority_gate

results = []
for label, getter, setter, expected in [
    ("set-permission-denied", Mock(return_value=0), Mock(side_effect=PermissionError("controlled EPERM")), False),
    ("set-returned-but-no-effect", Mock(side_effect=[0, 0]), Mock(), False),
    ("readback-denied", Mock(side_effect=[0, PermissionError("controlled readback denied")]), Mock(), False),
    ("verified-ten", Mock(side_effect=[0, 10]), Mock(), True),
    ("already-lower-priority", Mock(side_effect=[15, 15]), Mock(), True),
]:
    observed = priority_gate(getter, setter)
    assert observed["verified_before_exec"] is expected
    if label == "already-lower-priority":
        setter.assert_not_called()
    elif label != "readback-denied":
        setter.assert_called_once_with(os.PRIO_PROCESS, 0, 10)
    results.append({"case": label, "passed": True, "observed": observed})
print(json.dumps({"project": "Atlas", "simulated_only": True, "new_compiler_or_jvm": 0, "os_priority_changes": 0, "cases": results}, indent=2))
