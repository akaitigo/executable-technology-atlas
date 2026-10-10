"""Only routes to existing resources; does not run or mutate the lesson."""
import json
import sys

SUPPORTED = {"ports-adapters", "contract", "dependency-direction", "exception-translation", "input-boundary"}
topic = sys.argv[1] if len(sys.argv) == 2 else ""
if topic in SUPPORTED:
    result = {"status": "supported", "scope": "finite stdlib hexagonal lesson", "read": "../../README.md", "check": "../../runner.py", "ui": "../../index.html"}
else:
    result = {"status": "unsupported", "topic": topic, "reason": "architecture全quality attribute・本番DI・分散architectureは未教材", "next": "../../coverage.json"}
print(json.dumps(result, ensure_ascii=False))
