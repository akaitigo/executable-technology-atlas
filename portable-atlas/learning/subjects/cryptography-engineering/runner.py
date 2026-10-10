"""Public synthetic HMAC lesson. Not a production endpoint or key manager."""
import sys
sys.dont_write_bytecode = True
import argparse
import hashlib
import hmac
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent
VERSION = "hmac-replay-lesson-v1"


def mac_tag(key, message):
    if not isinstance(key, bytes) or not isinstance(message, bytes):
        raise TypeError("key and message must be bytes")
    if not key:
        raise ValueError("lesson rejects empty key, not a key-strength check")
    return hmac.new(key, message, digestmod=hashlib.sha256).digest()


def verify_tag(key, message, supplied_hex):
    # Full 32-byte tag only: this is a lesson contract, not all HMAC profiles.
    expected = mac_tag(key, message)
    if not isinstance(supplied_hex, str) or not re.fullmatch(r"[0-9a-fA-F]{64}", supplied_hex):
        return {"accepted": False, "reason": "invalid-tag-format"}
    matched = hmac.compare_digest(expected, bytes.fromhex(supplied_hex))
    return {"accepted": matched, "reason": "valid" if matched else "mismatch"}


class ReplayGuard:
    """Single-process synthetic signed-ID guard; no durable/distributed promise."""
    def __init__(self):
        self.seen = set()

    def accept(self, key, message, tag):
        checked = verify_tag(key, message, tag)
        if not checked["accepted"]:
            return {"accepted": False, "reason": "mac-rejected"}
        try:
            def unique_pairs(pairs):
                result = {}
                for k, v in pairs:
                    if k in result:
                        raise ValueError("duplicate JSON key")
                    result[k] = v
                return result
            envelope = json.loads(message.decode("utf-8"), object_pairs_hook=unique_pairs)
            if not isinstance(envelope, dict) or set(envelope) != {"message_id", "operation", "resource"}:
                raise ValueError("invalid envelope")
            if any(not isinstance(v, str) or not v for v in envelope.values()):
                raise ValueError("invalid fields")
        except (ValueError, UnicodeDecodeError):
            return {"accepted": False, "reason": "invalid-envelope"}
        # The id is authenticated inside message bytes, not an unsigned header.
        msg_id = envelope["message_id"]
        if msg_id in self.seen:
            return {"accepted": False, "reason": "duplicate-id"}
        self.seen.add(msg_id)
        return {"accepted": True, "reason": "accepted"}


def run_lesson():
    fixture = json.loads((ROOT / "fixture.json").read_text(encoding="utf-8"))
    oracle = json.loads((ROOT / "oracle.json").read_text(encoding="utf-8"))
    key = fixture["key_utf8"].encode("utf-8")
    message = fixture["message_utf8"].encode("utf-8")
    baseline = mac_tag(key, message).hex()
    tampered_tag = ("0" if baseline[0] != "0" else "1") + baseline[1:]
    rows = []
    for scenario in fixture["scenario_ids"]:
        k, m, tag = key, message, baseline
        guard = ReplayGuard()
        seed = None
        if scenario == "message-tamper":
            m = fixture["tampered_message_utf8"].encode("utf-8")
        elif scenario == "wrong-key":
            k = fixture["wrong_key_utf8"].encode("utf-8")
        elif scenario == "tag-tamper":
            tag = tampered_tag
        elif scenario == "replay":
            seed = guard.accept(key, message, baseline)
        elif scenario == "truncated-tag":
            tag = baseline[:-2]
        elif scenario == "malformed-tag":
            tag = "zz" + baseline[2:]
        elif scenario != "valid":
            raise ValueError("unknown scenario")
        before = sorted(guard.seen)
        rows.append({
            "id": scenario, "key_hex": k.hex(), "message_utf8": m.decode("utf-8"),
            "message_hex": m.hex(), "supplied_tag_hex": tag,
            "recomputed_tag_hex": mac_tag(k, m).hex(),
            "message_sha256": hashlib.sha256(m).hexdigest(),
            "mac": verify_tag(k, m, tag), "guard": guard.accept(k, m, tag),
            "seed_result": seed, "seen_before": before, "seen_after": sorted(guard.seen)
        })
    vectors = []
    for vector in oracle["vectors"]:
        actual = mac_tag(bytes.fromhex(vector["key_hex"]), bytes.fromhex(vector["message_hex"])).hex()
        vectors.append({**vector, "actual_tag_hex": actual, "matched": actual == vector["expected_tag_hex"]})
    return {"schema_version": 1, "runner_version": VERSION, "algorithm": "HMAC-SHA256",
            "key_notice": fixture["key_notice"], "baseline_tag_hex": baseline,
            "rfc_vectors": vectors, "scenarios": rows,
            "guard_scope": "fresh per scenario; single-process authenticated message_id set; replay seeded with one accepted request",
            "timing_measured": False, "subject_completion": "not-claimed"}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenario", choices=json.loads((ROOT / "fixture.json").read_text())["scenario_ids"])
    args = parser.parse_args()
    result = run_lesson()
    if args.scenario:
        result = next(row for row in result["scenarios"] if row["id"] == args.scenario)
    print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
