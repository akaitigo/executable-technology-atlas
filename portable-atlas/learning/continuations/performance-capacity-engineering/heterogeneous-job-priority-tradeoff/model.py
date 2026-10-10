#!/usr/bin/env python3
"""固定3仕事の有限モデル。CPU負荷や秒単位の実測は行わない。"""
import argparse
import json
from fractions import Fraction

COST = {"A": 5, "B": 1, "C": 1}
ORDERS = ("ABC", "ACB", "BAC", "BCA", "CAB", "CBA")


def schedule(order):
    if not isinstance(order, str) or order not in ORDERS:
        raise ValueError("REFUSED_INPUT: A・B・Cを一度ずつ含む6順序だけを受け付けます")
    now = 0
    jobs = {}
    for name in order:
        start = now
        now += COST[name]
        jobs[name] = {"arrival": 0, "service": COST[name], "start": start,
                      "finish": now, "wait": start, "response": now}
    total = sum(job["finish"] for job in jobs.values())
    return {"order": order, "jobs": jobs, "sum_completion": total,
            "mean_completion": str(Fraction(total, 3)),
            "mean_wait": str(Fraction(sum(job["wait"] for job in jobs.values()), 3)),
            "max_completion": max(job["finish"] for job in jobs.values()),
            "makespan": now, "throughput": str(Fraction(3, now)),
            "time_unit": "model tick", "benchmark": False}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--order", default="ABC", choices=ORDERS)
    args = parser.parse_args()
    print(json.dumps(schedule(args.order), ensure_ascii=False, indent=2))
