"""No evidence writes. Custom rejected input exits 2; instructional batch exits 0."""
import argparse
import json
from cache import analyze, batch

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-json", help="exact capacity_bytes/line_bytes/address_bits/addresses object")
    args = parser.parse_args()
    try:
        result = analyze(json.loads(args.input_json)) if args.input_json is not None else batch()
    except json.JSONDecodeError as error:
        result = {"status": "rejected", "error": {"field": "json", "message": str(error)}, "trace": []}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(2 if result.get("status") == "rejected" else 0)
