"""Atlas saved-value check against the pre-implementation literal table. No producer import."""
from copy import deepcopy
from fractions import Fraction


def exact(left, right):
    if type(left) is not type(right):
        return False
    if isinstance(left, dict):
        return left.keys() == right.keys() and all(exact(left[k], right[k]) for k in left)
    if isinstance(left, list):
        return len(left) == len(right) and all(exact(a, b) for a, b in zip(left, right))
    return left == right


def check_results(saved, cases, expected):
    checked = 0

    def eq(a, b, context):
        nonlocal checked
        checked += 1
        if not exact(a, b):
            raise AssertionError(context)

    eq(saved["mode"], "finite_synthetic_calculation", "mode")
    eq(saved["quantiles"], cases["quantiles"], "quantiles")
    eq(len(saved["cases"]), 5, "case count")
    for actual, request, hand in zip(saved["cases"], cases["cases"], expected["cases"]):
        cid = request["id"]
        eq(actual["id"], cid, "case order")
        eq(hand["id"], cid, "hand order")
        eq(actual["label"], request["label"], cid + " label")
        eq(actual["inputBefore"], request, cid + " before")
        eq(actual["inputAfter"], request, cid + " after")
        eq(actual["histogram"], {"edges": request["edges"], "counts": hand["counts"],
                                "cumulative": hand["cumulative"], "n": hand["n"]}, cid + " histogram")
        eq(len(actual["results"]), 4, cid + " row count")
        for j, (row, q) in enumerate(zip(actual["results"], cases["quantiles"])):
            eq(row["q"], q, cid + " q")
            eq(row["aggregateInput"], {"edges": request["edges"], "counts": hand["counts"], "q": q}, cid + " aggregate only")
            index = hand["bucketIndexes"][j]
            interval = None if index is None else {"lower": request["edges"][index], "upper": request["edges"][index + 1],
                                                  "lowerInclusive": index == 0, "upperInclusive": True}
            wanted = {"state": "empty" if index is None else "estimated", "n": hand["n"], "rank": hand["ranks"][j],
                      "bucketIndex": index, "interval": interval,
                      "countBefore": None if index is None else sum(hand["counts"][:index]),
                      "bucketCount": None if index is None else hand["counts"][index], "estimate": hand["estimates"][j]}
            eq(row["aggregateOutput"], wanted, cid + " full aggregate response")
            eq(row["rawNearestRank"], hand["raw"][j], cid + " raw")
            eq(row["signedError"], hand["errors"][j], cid + " signed error")
            error = hand["errors"][j]
            comparison = "empty" if error is None else "equal" if Fraction(error) == 0 else "above" if Fraction(error) > 0 else "below"
            eq(row["comparison"], comparison, cid + " comparison")
    a, b = saved["cases"][:2]
    eq([r["aggregateInput"] for r in a["results"]], [r["aggregateInput"] for r in b["results"]], "same aggregate inputs")
    eq([r["aggregateOutput"] for r in a["results"]], [r["aggregateOutput"] for r in b["results"]], "same aggregate outputs")
    eq([r["rawNearestRank"] for r in a["results"]] == [r["rawNearestRank"] for r in b["results"]], False, "different raw answers")
    return {"passed": True, "relations": checked, "cases": 5, "quantileRows": 20, "inputSchemaExecutions": 0}


def check_mutations(saved, cases, expected):
    mutations = []
    def trial(name, alter):
        changed = deepcopy(saved)
        alter(changed)
        try:
            check_results(changed, cases, expected)
        except (AssertionError, KeyError, IndexError, TypeError, ValueError):
            mutations.append({"name": name, "rejected": True})
        else:
            raise AssertionError("missed mutation: " + name)
    trial("missing-case", lambda x: x["cases"].pop())
    trial("count", lambda x: x["cases"][0]["histogram"]["counts"].__setitem__(0, 3))
    trial("boundary-membership", lambda x: x["cases"][3]["results"][1]["aggregateOutput"]["interval"].__setitem__("upperInclusive", False))
    trial("estimate", lambda x: x["cases"][0]["results"][2]["aggregateOutput"].__setitem__("estimate", "11"))
    trial("lost-negative-sign", lambda x: x["cases"][1]["results"][2].__setitem__("signedError", "3"))
    trial("empty-to-zero", lambda x: x["cases"][4]["results"][0]["aggregateOutput"].__setitem__("estimate", "0"))
    trial("raw-injection", lambda x: x["cases"][0]["results"][0]["aggregateInput"].__setitem__("raw", [1,2,11,12]))
    trial("bool-as-integer", lambda x: x["cases"][0]["inputAfter"]["values"].__setitem__(0, True))
    return mutations
