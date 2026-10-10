"""Bounded read-only logical cache. No host CPU cache or timing measurement."""
import copy

VERSION = "bounded-direct-mapped-read-v1"
LIMITS = {"address_bits": 8, "capacity_max": 64, "line_max": 16, "reads_max": 64}


def config(capacity=16, line=4, addresses=None):
    return {"capacity_bytes": capacity, "line_bytes": line, "address_bits": 8,
            "addresses": [0, 16, 0, 16] if addresses is None else addresses}


CASES = {
    "conflict": config(),
    "spatial": config(addresses=[0, 1, 2, 3, 4, 5, 4, 15]),
    "offset_conflict": config(addresses=[0, 1, 16, 17, 0, 1]),
    "one_line": config(1, 1, [0, 255, 255, 0]),
    "upper_boundary": config(64, 16, [0, 15, 16, 31, 48, 63, 255, 240]),
    "empty": config(addresses=[]),
    "invalid_capacity": config(12, 4),
    "invalid_line": config(16, 3),
    "line_exceeds_capacity": config(4, 8),
    "invalid_address": config(addresses=[0, 256]),
}


class InputError(ValueError):
    def __init__(self, field, message):
        self.field, self.message = field, message
        super().__init__(message)


def validate(spec):
    if not isinstance(spec, dict) or set(spec) != set(config()):
        raise InputError("input", "capacity_bytes/line_bytes/address_bits/addressesのみ必要")
    for field, maximum in [("capacity_bytes", 64), ("line_bytes", 16)]:
        value = spec[field]
        if type(value) is not int or not 1 <= value <= maximum or value & (value - 1):
            raise InputError(field, "1..%dの2の冪integer（bool不可）" % maximum)
    if spec["line_bytes"] > spec["capacity_bytes"]:
        raise InputError("line_bytes", "line sizeはcapacity以下")
    if type(spec["address_bits"]) is not int or spec["address_bits"] != 8:
        raise InputError("address_bits", "この教材は8-bit byte addressだけ")
    addresses = spec["addresses"]
    if not isinstance(addresses, list) or len(addresses) > 64:
        raise InputError("addresses", "0..64 readのlistだけ")
    for i, address in enumerate(addresses):
        if type(address) is not int or not 0 <= address <= 255:
            raise InputError("addresses[%d]" % i, "0..255のinteger byte address（bool不可）")


def memory_byte(address):
    return (17 * address + 3) % 256


def simulate(spec, ignore_tag=False):
    """ignore_tag deliberately breaks correctness; it is not another valid cache."""
    validate(spec)  # fail before any read; no partial successful result on invalid input
    width = spec["line_bytes"]
    count = spec["capacity_bytes"] // width
    offset_bits, index_bits = width.bit_length() - 1, count.bit_length() - 1
    lines = [{"valid": False, "tag": None, "block": None, "bytes": []} for _ in range(count)]
    events, seen = [], set()
    hits = misses = evictions = wrong = 0
    for step, address in enumerate(spec["addresses"]):
        block = address >> offset_bits
        index = block & (count - 1)
        tag = block >> index_bits
        offset = address & (width - 1)
        before = copy.deepcopy(lines)
        selected = lines[index]
        tag_match = selected["valid"] and selected["tag"] == tag
        hit = selected["valid"] and (ignore_tag or tag_match)
        evicted = selected["block"] if not hit and selected["valid"] else None
        reason = "valid-and-tag-match" if tag_match else "invalid-line" if not selected["valid"] else "tag-mismatch"
        if hit:
            hits += 1
        else:
            misses += 1
            if evicted is not None:
                evictions += 1
            base = block * width
            lines[index] = {"valid": True, "tag": tag, "block": block,
                            "bytes": [memory_byte(base + j) for j in range(width)]}
        observed = lines[index]["bytes"][offset]
        expected = memory_byte(address)
        wrong += int(observed != expected)
        events.append({"step": step + 1, "address": address,
                       "block": block, "index": index, "tag": tag, "offset": offset,
                       "requested_range": [block * width, block * width + width - 1],
                       "before": before, "after": copy.deepcopy(lines),
                       "tag_match": tag_match, "hit": hit, "decision_reason": reason,
                       "tag_check_bypassed": ignore_tag and selected["valid"] and not tag_match,
                       "seen_block_before": block in seen,
                       "evicted_block": evicted,
                       "empty_lines_before": sum(not x["valid"] for x in before),
                       "memory_bytes_fetched": 0 if hit else width,
                       "expected_byte": expected, "observed_byte": observed,
                       "data_correct": observed == expected})
        seen.add(block)
    return {"policy": "broken-ignore-tag" if ignore_tag else "valid-and-tag",
            "geometry": {"line_count": count, "offset_bits": offset_bits,
                         "index_bits": index_bits, "tag_bits": 8 - offset_bits - index_bits},
            "initial_lines": [{"valid": False, "tag": None, "block": None, "bytes": []} for _ in range(count)],
            "trace": events, "final_lines": copy.deepcopy(lines),
            "summary": {"reads": len(events), "hits": hits, "misses": misses,
                        "evictions": evictions, "wrong_bytes": wrong,
                        "hit_rate": hits / len(events) if events else None,
                        "memory_bytes_fetched": misses * width}}


def analyze(spec):
    try:
        return {"input": copy.deepcopy(spec), "status": "passed",
                "normal": simulate(spec), "broken": simulate(spec, ignore_tag=True), "error": None}
    except InputError as error:
        return {"input": copy.deepcopy(spec), "status": "rejected", "normal": None, "broken": None,
                "error": {"field": error.field, "message": error.message}, "trace": []}


def batch():
    return {"model_version": VERSION, "classification": "logical-simulator-not-CPU-cache-measurement",
            "limits": LIMITS, "memory": "byte(a)=(17*a+3)%256; synthetic, read-only, 256 bytes",
            "cases": {name: analyze(spec) for name, spec in CASES.items()}}
