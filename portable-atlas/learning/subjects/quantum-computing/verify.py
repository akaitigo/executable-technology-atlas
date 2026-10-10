# SPDX-License-Identifier: Apache-2.0
"""Independent small-matrix oracle plus provenance and invalid-input checks."""
import copy
import hashlib
import json
import math
import random
from pathlib import Path

import simulator

HERE = Path(__file__).resolve().parent
EPS = 1e-12


def near(actual, expected):
    if abs(actual - expected) > EPS:
        raise AssertionError(f"{actual} differs from {expected}")


def unpack(pair):
    return complex(pair[0], pair[1])


def multiply(a, b):
    return [[sum(a[i][k] * b[k][j] for k in range(2)) for j in range(2)] for i in range(2)]


def dagger(a):
    return [[complex(a[j][i]).conjugate() for j in range(2)] for i in range(2)]


# This oracle has no call to simulator.gate/evolve/snapshot. Matrix algebra
# models UρU† directly, rather than the implementation's branch-vector path.
R = math.sqrt(0.5)
MATRICES = {"H": [[R, R], [R, -R]], "Z": [[1, 0], [0, -1]], "S": [[1, 0], [0, 1j]]}
DECLARED = {"coherent": ["H", "H"], "dephased": ["H", "D", "H"],
            "phase_pi": ["H", "Z", "H"], "phase_half_pi": ["H", "S", "H"]}


def validate_result(result):
    assert result["qubits"] == 1 and result["model_version"] == simulator.VERSION
    assert set(result["circuits"]) == set(DECLARED)
    for name, operations in DECLARED.items():
        circuit = result["circuits"][name]
        assert circuit["operations"] == operations
        stages = circuit["stages"]
        assert len(stages) == len(operations) + 1
        rho = [[1 + 0j, 0j], [0j, 0j]]
        for index, stage in enumerate(stages):
            assert stage["operation"] == ("initial |0>" if index == 0 else operations[index - 1])
            if index:
                op = operations[index-1]
                if op == "D":
                    rho = [[rho[0][0], 0j], [0j, rho[1][1]]]
                else:
                    rho = multiply(multiply(MATRICES[op], rho), dagger(MATRICES[op]))
            density = [[unpack(x) for x in row] for row in stage["density_matrix"]]
            for i in range(2):
                for j in range(2):
                    near(density[i][j], rho[i][j])
                    near(density[i][j], density[j][i].conjugate())
                near(stage["probabilities"][i], rho[i][i].real)
            near(stage["trace"], 1)
            near(stage["coherence_magnitude"], abs(rho[0][1]))
            near(stage["purity"], sum(abs(x)**2 for row in rho for x in row))
            assert (density[0][0] * density[1][1] - density[0][1] * density[1][0]).real >= -EPS
            near(sum(branch["weight"] for branch in stage["branches"]), 1)
            rebuilt = [[0j, 0j], [0j, 0j]]
            for branch in stage["branches"]:
                assert 0 <= branch["weight"] <= 1 + EPS
                vector = [unpack(x) for x in branch["amplitudes"]]
                near(sum(abs(x)**2 for x in vector), 1)
                for i in range(2):
                    for j in range(2):
                        rebuilt[i][j] += branch["weight"] * vector[i] * vector[j].conjugate()
                for z, phase in zip(vector, branch["phases_radians"]):
                    if abs(z) <= EPS:
                        assert phase is None
                    else:
                        import cmath
                        near(phase, cmath.phase(z))
            for i in range(2):
                for j in range(2):
                    near(rebuilt[i][j], rho[i][j])
        sampled = circuit["sampling"]
        assert sampled["shots"] == 4096 and sampled["seed"] == 20261005
        rng = random.Random(sampled["seed"])
        count0 = sum(rng.random() < stages[-1]["probabilities"][0] for _ in range(sampled["shots"]))
        assert sampled["counts"] == [count0, sampled["shots"]-count0]
        for count, frequency in zip(sampled["counts"], sampled["frequencies"]):
            near(frequency, count / sampled["shots"])
    for name, expected in {"coherent": [1, 0], "dephased": [.5, .5], "phase_pi": [0, 1], "phase_half_pi": [.5, .5]}.items():
        for actual, analytic in zip(result["circuits"][name]["stages"][-1]["probabilities"], expected):
            near(actual, analytic)


def main():
    run = json.loads((HERE/"evidence/run.json").read_text())
    for name, expected in run["source_hashes"].items():
        assert "sha256:" + hashlib.sha256((HERE/name).read_bytes()).hexdigest() == expected, name
    for key in ("raw_stdout", "raw_stderr"):
        binding = run[key]
        assert "sha256:" + hashlib.sha256((HERE/binding["path"]).read_bytes()).hexdigest() == binding["digest"]
    assert json.loads((HERE/"evidence/stdout.json").read_text()) == run["result"]
    data = (HERE/"data.js").read_text().removeprefix("window.QUANTUM_OBSERVATION = ").removesuffix(";\n")
    assert json.loads(data) == run
    assert run["exit_code"] == 0 and run["attempts"] == 1 and run["retries"] == 0
    validate_result(run["result"])
    for matrix in MATRICES.values():
        identity = multiply(dagger(matrix), matrix)
        for i in range(2):
            for j in range(2):
                near(identity[i][j], int(i == j))
    for vector in ([1,0], [0,1], [R,1j*R], [0.6,0.8j]):
        actual = simulator.gate(simulator.gate(vector,"H"),"H")
        for x,y in zip(actual,vector):
            near(x,y)
    negatives = [
        lambda: simulator.gate([1,1], "H"),
        lambda: simulator.gate([0,0], "H"),
        lambda: simulator.gate([1,0], "CNOT"),
        lambda: simulator.gate([1,0,0,0], "H"),
        lambda: simulator.gate([float("nan"),0], "H"),
        lambda: simulator.gate([True,False], "H"),
        lambda: simulator.circuit("HH"),
        lambda: simulator.sample([.5,.5], 0, 1),
        lambda: simulator.sample([.5,.5], True, 1),
        lambda: simulator.sample([.5,.5], 10, "seed"),
        lambda: simulator.sample([.7,.7], 10, 1),
        lambda: simulator.evolve([(-1,[1,0]),(2,[0,1])],"H"),
        lambda: simulator.evolve([(.5,[1,0])],"D"),
    ]
    for check in negatives:
        try:
            check()
        except ValueError:
            pass
        else:
            raise AssertionError("invalid input accepted")
    mutations = [
        lambda d: d["circuits"]["dephased"]["stages"][-1].update(probabilities=[1,0]),
        lambda d: d["circuits"]["coherent"]["stages"][-1].update(purity=.5),
        lambda d: d["circuits"]["dephased"]["stages"][2]["density_matrix"][0].__setitem__(1,[.5,0]),
        lambda d: d["circuits"]["phase_pi"]["stages"][2]["branches"][0]["amplitudes"].__setitem__(1,[R,0]),
    ]
    for mutate in mutations:
        candidate = copy.deepcopy(run["result"])
        mutate(candidate)
        try:
            validate_result(candidate)
        except AssertionError:
            pass
        else:
            raise AssertionError("false simulator evidence accepted")
    print(f"PASS: independent 2x2 density oracle / analytic Born / H†H / H² / normalization / PRNG counts / raw+source+UI binding; invalid-input={len(negatives)} evidence-negative={len(mutations)}")


if __name__ == "__main__":
    main()
