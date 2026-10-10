"""Routes only to existing finite resources; no execution or mutation."""
import json
import sys

SUPPORTED = {"staged-migration", "reversible-mapping", "lossy-conversion", "refusal", "transaction-rollback"}
topic = sys.argv[1] if len(sys.argv) == 2 else ""
if topic in SUPPORTED:
    result = {"status": "supported", "scope": "finite SQLite v1/v2 lesson", "read": "../../README.md", "check": "../../runner.py", "ui": "../../index.html"}
else:
    result = {"status": "unsupported", "topic": topic, "reason": "本番zero downtime・他database・一般migration toolは未教材", "next": "../../coverage.json"}
print(json.dumps(result, ensure_ascii=False))
