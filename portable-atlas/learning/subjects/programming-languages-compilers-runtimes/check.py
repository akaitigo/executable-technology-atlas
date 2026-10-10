# SPDX-License-Identifier: Apache-2.0
"""Read-only entry point: stdout only, never writes evidence."""
import argparse
import json
from language import analyze, experiment

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--expr", help="bounded expression to inspect; stdout only")
    args = parser.parse_args()
    result = experiment() if args.expr is None else analyze(args.expr)
    print(json.dumps(result,ensure_ascii=False,indent=2))
    if result.get("status") == "error":
        raise SystemExit(2)
