"""Independent exact normal-equation oracle; no production imports."""
from fractions import Fraction


def solve(points):
    n = len(points)
    sx = sum(Fraction(x) for x, _ in points)
    sy = sum(Fraction(y) for _, y in points)
    sxx = sum(Fraction(x) ** 2 for x, _ in points)
    sxy = sum(Fraction(x) * Fraction(y) for x, y in points)
    determinant = n * sxx - sx ** 2
    if not n or not determinant:
        raise ValueError("singular normal equations")
    return ((sy * sxx - sx * sxy) / determinant,
            (n * sxy - sx * sy) / determinant)


def score(points, model):
    a, b = model
    return sum((Fraction(y) - a - b * x) ** 2 for x, y in points) / len(points)


def comparison(train, holdout, ood):
    base = solve(train)
    candidates = [(base[0] + offset, base[1]) for offset in (0, 1, 2)]
    selected = min(range(3), key=lambda i: (score(holdout, candidates[i]), i))
    models = {"train-only": base, "fit-leakage": solve(train + holdout),
              "selection-leakage": candidates[selected]}
    return {name: {"intercept": str(a), "slope": str(b),
                   "mse": {key: str(score(points, (a, b)))
                           for key, points in (("train", train), ("holdout", holdout), ("ood", ood))},
                   "selected_offset": selected if name == "selection-leakage" else None}
            for name, (a, b) in models.items()}
