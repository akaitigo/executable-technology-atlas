"""Atlas finite histogram; local interpolation rule, not a product API."""
from fractions import Fraction

EDGES = ([0, 10, 20, 40], [0, 5, 10, 15, 20, 40])
QUANTILES = ("0", "1/2", "3/4", "1")


def validate_values(values):
    if type(values) is not list or len(values) > 8:
        raise ValueError("finite values list required")
    if any(type(x) is not int or not 0 <= x <= 40 for x in values):
        raise ValueError("integer values in 0..40 required")


def validate_edges(edges):
    if type(edges) is not list or any(type(x) is not int for x in edges) or edges not in EDGES:
        raise ValueError("fixed finite edges required")


def aggregate(values, edges):
    validate_values(values)
    validate_edges(edges)
    counts = [0] * (len(edges) - 1)
    for value in values:
        for i, upper in enumerate(edges[1:]):
            if value <= upper:
                counts[i] += 1
                break
    cumulative = []
    for count in counts:
        cumulative.append((cumulative[-1] if cumulative else 0) + count)
    return {"edges": list(edges), "counts": counts, "cumulative": cumulative, "n": len(values)}


def estimate_from_counts(edges, counts, q):
    """Only aggregated inputs; no case ID, raw values, min, max or oracle."""
    validate_edges(edges)
    if type(counts) is not list or len(counts) != len(edges) - 1:
        raise ValueError("one count for each interval required")
    if any(type(c) is not int or c < 0 for c in counts) or sum(counts) > 8:
        raise ValueError("finite nonnegative integer counts required")
    if type(q) is not str or q not in QUANTILES:
        raise ValueError("fixed quantile required")
    n = sum(counts)
    if n == 0:
        return {"state": "empty", "n": 0, "rank": None, "bucketIndex": None,
                "interval": None, "countBefore": None, "bucketCount": None, "estimate": None}
    target = Fraction(q) * n
    rank = max(1, (target.numerator + target.denominator - 1) // target.denominator)
    before = 0
    for i, count in enumerate(counts):
        if count and (q == "0" or before + count >= target):
            low, high = edges[i:i + 2]
            estimate = Fraction(low) if q == "0" else low + (high - low) * (target - before) / count
            return {"state": "estimated", "n": n, "rank": rank, "bucketIndex": i,
                    "interval": {"lower": low, "upper": high, "lowerInclusive": i == 0, "upperInclusive": True},
                    "countBefore": before, "bucketCount": count, "estimate": str(estimate)}
        before += count
    raise AssertionError("valid nonempty counts must select a bucket")


def raw_nearest_rank(values, q):
    validate_values(values)
    if type(q) is not str or q not in QUANTILES:
        raise ValueError("fixed quantile required")
    if not values:
        return None
    target = Fraction(q) * len(values)
    rank = max(1, (target.numerator + target.denominator - 1) // target.denominator)
    return str(sorted(values)[rank - 1])
