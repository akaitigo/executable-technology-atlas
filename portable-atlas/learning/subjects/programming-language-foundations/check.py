"""stdout only. Default batch observes expected errors; custom failures exit 2."""
import argparse
import json
from interpreter import CASES, analyze, batch

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--ast-json")
    parser.add_argument("--case", choices=list(CASES))
    args = parser.parse_args()
    if args.ast_json is not None and args.case is not None:
        parser.error("--ast-json and --case are mutually exclusive")
    try:
        if args.ast_json is not None:
            result = analyze(json.loads(args.ast_json))
        elif args.case:
            result = analyze(CASES[args.case])
        else:
            result = batch()
    except (json.JSONDecodeError, RecursionError) as error:
        result = {"status": "rejected", "error": {"code": "invalid-json", "message": str(error)}}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    failed = result.get("status") == "rejected" or "normal" in result and result["normal"]["status"] != "passed"
    raise SystemExit(2 if failed else 0)
