"""Route only to existing finite module resources. No execution or mutation."""
import json
import sys

SUPPORTED = {"transaction", "validation", "rollback", "outbox", "connection-lifetime"}
topic = sys.argv[1] if len(sys.argv) == 2 else ""
if topic in SUPPORTED:
    result = {"status": "supported", "scope": "finite SQLite lesson", "read": "../../README.md", "check": "../../runner.py", "ui": "../../index.html"}
else:
    result = {"status": "unsupported", "topic": topic, "reason": "現moduleは実framework・DI production・並行性能を実行していない", "next": "../../coverage.json"}
print(json.dumps(result, ensure_ascii=False))
