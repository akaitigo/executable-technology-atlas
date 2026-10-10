"""2 replica / 1 registerの決定的説明モデル。実network・実時計なし。"""
import copy
import hashlib
import itertools
import json
import platform
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MODES = ("arrival", "version-max")
INITIAL = {"value": "∅", "version": [0, ""]}


class Simulator:
    def __init__(self, mode="arrival"):
        if mode not in MODES:
            raise ValueError("未知のmerge modeです")
        self.mode = mode
        self.partition = True
        self.nodes = {node: {"clock": 0, "register": copy.deepcopy(INITIAL)} for node in ("A", "B")}
        self.messages, self.events, self.writes = {}, [], []
        self.record("start", partition=True)

    def record(self, action, **detail):
        self.events.append({"step": len(self.events), "action": action, **detail,
                            "partition": self.partition, "state": copy.deepcopy(self.nodes)})

    def write(self, node, value):
        if node not in self.nodes or not isinstance(value, str) or not value.strip() or len(value) > 24:
            raise ValueError("nodeはA/B、valueは1〜24文字です")
        state = self.nodes[node]
        state["clock"] += 1
        register = {"value": value, "version": [state["clock"], node]}
        state["register"] = copy.deepcopy(register)
        message_id = f"{node}{state['clock']}"
        if message_id in self.messages:
            raise ValueError("message ID重複")
        target = "B" if node == "A" else "A"
        self.messages[message_id] = {"id": message_id, "from": node, "to": target, "register": copy.deepcopy(register)}
        self.writes.append(copy.deepcopy(register))
        self.record("local-write-and-enqueue", node=node, value=value, version=register["version"], message_id=message_id)
        return message_id

    def heal(self):
        self.partition = False
        self.record("heal-model-link")

    def deliver(self, message_id):
        if self.partition:
            raise ValueError("partition中は配送できません")
        if message_id not in self.messages:
            raise ValueError("存在しないmessage IDです")
        message = self.messages[message_id]
        receiver = self.nodes[message["to"]]
        incoming = message["register"]
        receiver["clock"] = max(receiver["clock"], incoming["version"][0]) + 1
        accept = self.mode == "arrival" or tuple(incoming["version"]) > tuple(receiver["register"]["version"])
        if accept:
            receiver["register"] = copy.deepcopy(incoming)
        # messageは再配送できる。duplicateをno-opにするのはmerge ruleであって輸送の仮定ではない。
        self.record("deliver", message_id=message_id, target=message["to"], incoming=copy.deepcopy(incoming), accepted=accept)


def prepared(mode):
    simulator = Simulator(mode)
    simulator.write("A", "alpha")
    simulator.write("A", "alpha-2")
    simulator.write("B", "beta")
    return simulator


def independent_oracle(writes):
    """配送実装を呼ばず、全書込み集合の最大labelを期待値にする。"""
    ordered = sorted(copy.deepcopy(writes), key=lambda row: (row["version"][0], row["version"][1]))
    return ordered[-1] if ordered else copy.deepcopy(INITIAL)


def simulate(mode="arrival", order=None, duplicate=False):
    simulator = prepared(mode)
    order = ["A2", "A1", "B1"] if order is None else order
    if not isinstance(order, list) or len(order) != 3 or set(order) != set(simulator.messages):
        raise ValueError("orderはA1,A2,B1を各1回含む3要素です")
    if not isinstance(duplicate, bool):
        raise ValueError("duplicateはboolです")
    if duplicate:
        order = [*order, "A1"]  # 復旧後の遅れた古いmessageを再配送
    simulator.heal()
    for message_id in order:
        simulator.deliver(message_id)
    registers = {node: state["register"] for node, state in simulator.nodes.items()}
    expected = independent_oracle(simulator.writes)
    return {"input": {"mode": mode, "delivery_order": order, "duplicate_delayed_A1": duplicate,
                      "writes": simulator.writes},
            "events": simulator.events, "messages": list(simulator.messages.values()),
            "final_state": simulator.nodes,
            "summary": {"converged": registers["A"] == registers["B"],
                        "independent_max_oracle": expected,
                        "all_match_max_oracle": all(row == expected for row in registers.values()),
                        "discarded_values_under_max": [row["value"] for row in simulator.writes if row != expected],
                        "all_unique_messages_delivered": True,
                        "total_deliveries": len(order)},
            "boundary": "2 replica/1 registerのCPU simulation。実通信、実時計、consensus、CAP theoremの検証ではない。"}


def permutation_check():
    results = []
    for order in itertools.permutations(["A1", "A2", "B1"]):
        runs = {mode: simulate(mode, list(order)) for mode in MODES}
        results.append({"order": list(order), "arrival_converged": runs["arrival"]["summary"]["converged"],
                        "version_max_matches_oracle": runs["version-max"]["summary"]["all_match_max_oracle"],
                        "arrival_final": runs["arrival"]["final_state"],
                        "max_final": runs["version-max"]["final_state"]})
    return {"permutations": results, "count": len(results),
            "max_passed": sum(row["version_max_matches_oracle"] for row in results),
            "arrival_converged": sum(row["arrival_converged"] for row in results),
            "oracle_method": "sort all writes by (counter,replica_id), independent of deliver()"}


def observe(mode="arrival", order=None, duplicate=False, command=None):
    result = simulate(mode, order, duplicate)
    result["permutation_check"] = permutation_check()
    result["execution"] = {"observed_at": datetime.now(timezone.utc).isoformat(),
                           "python": platform.python_version(), "platform": platform.system()+" "+platform.machine(),
                           "source_sha256": hashlib.sha256((ROOT/"model.py").read_bytes()).hexdigest(),
                           "command": command, "simulation": True, "real_network": False,
                           "logical_labels_are_wall_clock": False}
    return result


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--record", action="store_true")
    args = parser.parse_args()
    command = ["python3", "model.py"] + (["--record"] if args.record else [])
    report = {mode: observe(mode=mode, command=command) for mode in MODES}
    payload = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    print(payload, end="")
    if args.record:
        folder = ROOT/"observations"
        folder.mkdir(exist_ok=True)
        (folder/"comparison.json").write_text(payload, encoding="utf-8")
