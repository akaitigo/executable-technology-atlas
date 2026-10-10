# SPDX-License-Identifier: Apache-2.0
"""One-qubit pure branch ensemble; no quantum hardware or external package."""
import cmath
import math
import random

VERSION = "one-qubit-interference-ensemble-v1"
TOLERANCE = 1e-12


def validate_vector(vector):
    if not isinstance(vector, (tuple, list)) or len(vector) != 2:
        raise ValueError("one-qubit vector requires exactly two amplitudes")
    if any(isinstance(x, bool) or not isinstance(x, (complex, float, int)) for x in vector):
        raise ValueError("amplitudes must be numeric complex values")
    if any(not math.isfinite(complex(x).real) or not math.isfinite(complex(x).imag) for x in vector):
        raise ValueError("amplitudes must be finite")
    if abs(sum(abs(x) ** 2 for x in vector) - 1) > TOLERANCE:
        raise ValueError("invalid normalization; no implicit normalization")


def validate_ensemble(branches):
    if not isinstance(branches, (list, tuple)) or not branches:
        raise ValueError("ensemble must have branches")
    total = 0
    for weight, vector in branches:
        if isinstance(weight, bool) or not isinstance(weight, (int, float)) or not math.isfinite(weight) or weight < 0:
            raise ValueError("invalid branch weight")
        validate_vector(vector)
        total += weight
    if abs(total - 1) > TOLERANCE:
        raise ValueError("branch weights must sum to one")


def gate(vector, name):
    validate_vector(vector)
    a, b = vector
    if name == "H":
        result = ((a + b) / math.sqrt(2), (a - b) / math.sqrt(2))
    elif name == "Z":
        result = (a, -b)
    elif name == "S":
        result = (a, 1j * b)
    else:
        raise ValueError("unsupported gate: only H/Z/S")
    validate_vector(result)
    return result


def evolve(branches, operation):
    validate_ensemble(branches)
    if operation == "D":
        # Nonselective standard-basis measurement: retain classical outcome
        # weights, discard outcome labels/relative coherence, not amplitudes
        # averaged into a spurious pure state.
        result = []
        for weight, vector in branches:
            for outcome, amplitude in enumerate(vector):
                probability = weight * abs(amplitude) ** 2
                if probability > 0:
                    result.append((probability, (1 + 0j, 0j) if outcome == 0 else (0j, 1 + 0j)))
    else:
        result = [(weight, gate(vector, operation)) for weight, vector in branches]
    validate_ensemble(result)
    return result


def pack_complex(value):
    return [complex(value).real, complex(value).imag]


def unpack_complex(pair):
    return complex(*pair)


def snapshot(branches, operation):
    validate_ensemble(branches)
    density = [[sum(w * v[i] * complex(v[j]).conjugate() for w, v in branches) for j in range(2)] for i in range(2)]
    return {
        "operation": operation,
        "branches": [{"weight": w, "amplitudes": [pack_complex(z) for z in v],
                      "phases_radians": [cmath.phase(z) if abs(z) > TOLERANCE else None for z in v]} for w, v in branches],
        "density_matrix": [[pack_complex(z) for z in row] for row in density],
        "probabilities": [density[i][i].real for i in range(2)],
        "coherence_magnitude": abs(density[0][1]),
        "purity": sum(abs(z) ** 2 for row in density for z in row),
        "trace": sum(density[i][i].real for i in range(2)),
    }


def sample(probabilities, shots, seed):
    if not isinstance(probabilities, (list, tuple)) or len(probabilities) != 2:
        raise ValueError("exactly two Born probabilities required")
    if any(isinstance(p, bool) or not isinstance(p, (float, int)) or not math.isfinite(p) or not 0 <= p <= 1 + TOLERANCE for p in probabilities):
        raise ValueError("invalid Born probabilities")
    if abs(sum(probabilities) - 1) > TOLERANCE:
        raise ValueError("Born probabilities must sum to one")
    if isinstance(shots, bool) or not isinstance(shots, int) or not 1 <= shots <= 100000:
        raise ValueError("shots must be an integer from 1 through 100000")
    if isinstance(seed, bool) or not isinstance(seed, int):
        raise ValueError("seed must be an integer")
    rng = random.Random(seed)
    counts = [0, 0]
    for _ in range(shots):
        counts[0 if rng.random() < probabilities[0] else 1] += 1
    return {"seed": seed, "shots": shots, "counts": counts, "frequencies": [x / shots for x in counts],
            "meaning": "independent preparations; seeded classical PRNG sampling, not quantum hardware"}


def circuit(operations, shots=4096, seed=20261005):
    if not isinstance(operations, (tuple, list)) or len(operations) > 16 or any(op not in ("H", "Z", "S", "D") for op in operations):
        raise ValueError("unsupported circuit operation/input")
    branches = [(1.0, (1 + 0j, 0j))]
    stages = [snapshot(branches, "initial |0>")]
    for operation in operations:
        branches = evolve(branches, operation)
        stages.append(snapshot(branches, operation))
    return {"operations": operations, "stages": stages, "sampling": sample(stages[-1]["probabilities"], shots, seed)}


def experiment():
    return {"model_version": VERSION, "qubits": 1, "tolerance": TOLERANCE,
            "circuits": {"coherent": circuit(["H", "H"]), "dephased": circuit(["H", "D", "H"]),
                         "phase_pi": circuit(["H", "Z", "H"]), "phase_half_pi": circuit(["H", "S", "H"])}}
