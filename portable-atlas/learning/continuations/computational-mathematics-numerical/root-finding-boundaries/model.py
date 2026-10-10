"""Finite exact-rational root iterations. No I/O, external solver, or eval."""
from fractions import Fraction as F

FIXTURE = {
    'schema': 'atlas-root-boundaries-fixture-v1', 'arithmetic': 'exact-rational',
    'max_updates': 4, 'width_tolerance': '1/8',
    'residual_tolerance': '1/16', 'step_tolerance': '1/16',
    'cases': [
        {'id': 'cubic-cycle', 'polynomial': 'cubic', 'bracket': ['-2', '0'], 'x0': '0'},
        {'id': 'cubic-local', 'polynomial': 'cubic', 'bracket': ['-2', '0'], 'x0': '-2'},
        {'id': 'zero-derivative', 'polynomial': 'quadratic', 'bracket': ['1', '2'], 'x0': '0'},
        {'id': 'bad-bracket', 'polynomial': 'quadratic', 'bracket': ['2', '3'], 'x0': '1'},
        {'id': 'exact-endpoint', 'polynomial': 'square', 'bracket': ['0', '1'], 'x0': '0'}]}


class InvalidInput(ValueError):
    updates = 0


def typed_equal(a, b):
    if type(a) is not type(b):
        return False
    if isinstance(a, dict):
        return a.keys() == b.keys() and all(typed_equal(a[k], b[k]) for k in a)
    if isinstance(a, list):
        return len(a) == len(b) and all(typed_equal(x, y) for x, y in zip(a, b))
    return a == b


def f(poly, x):
    if poly == 'cubic':
        return x*x*x - 2*x + 2
    if poly == 'quadratic':
        return x*x - 2
    if poly == 'square':
        return x*x
    raise InvalidInput('UNKNOWN_POLYNOMIAL')


def df(poly, x):
    return 3*x*x - 2 if poly == 'cubic' else 2*x


def bisection(poly, endpoints, limit, width_tol):
    a, b = map(F, endpoints)
    fa, fb = f(poly, a), f(poly, b)
    endpoint = a if fa == 0 else b if fb == 0 else None
    valid = endpoint is not None or fa*fb < 0
    validation = dict(a=str(a), b=str(b), fa=str(fa), fb=str(fb),
                      bracket_valid=valid, endpoint_root=None if endpoint is None else str(endpoint))
    if not valid:
        return dict(validation=validation, rows=[], status='INVALID_BRACKET', updates=0,
                    estimate=None, residual=None, width=None, radius=None)
    exact = endpoint is not None
    if exact:
        a = b = endpoint
        fa = fb = F(0)
    rows = []
    probe = pf = None
    k = 0
    while True:
        estimate = (a+b)/2
        fe = f(poly, estimate)  # diagnostic at the retained interval midpoint
        width = b-a
        status = ('EXACT_ROOT' if exact else 'BRACKET_WIDTH_MET' if width <= width_tol
                  else 'ITERATION_LIMIT' if k >= limit else 'CONTINUE')
        rows.append(dict(k=k, probe=None if probe is None else str(probe),
                         probe_f=None if pf is None else str(pf),
                         a=str(a), b=str(b), fa=str(fa), fb=str(fb),
                         estimate=str(estimate), f=str(fe), residual=str(abs(fe)),
                         width=str(width), radius=str(width/2), width_met=width <= width_tol,
                         status=status))
        if status != 'CONTINUE':
            return dict(validation=validation, rows=rows, status=status, updates=k,
                        estimate=str(estimate), residual=str(abs(fe)), width=str(width), radius=str(width/2))
        probe, pf = estimate, fe
        if pf == 0:
            a = b = probe
            fa = fb = F(0)
            exact = True
        elif fa*pf < 0:
            b, fb = probe, pf
        else:
            a, fa = probe, pf
        k += 1


def newton(poly, initial, limit, residual_tol, step_tol):
    x, delta, k, rows = F(initial), None, 0, []
    while True:
        fx, dx = f(poly, x), df(poly, x)
        step = None if delta is None else abs(delta)
        residual_met = abs(fx) <= residual_tol
        step_met = None if step is None else step <= step_tol
        status = ('EXACT_ROOT' if fx == 0 else 'LOCAL_TOLERANCES_MET' if k >= 1 and residual_met and step_met
                  else 'ZERO_DERIVATIVE' if dx == 0 else 'ITERATION_LIMIT' if k >= limit else 'CONTINUE')
        rows.append(dict(k=k, x=str(x), f=str(fx), df=str(dx),
                         delta=None if delta is None else str(delta), step=None if step is None else str(step),
                         residual=str(abs(fx)), residual_met=residual_met, step_met=step_met, status=status))
        if status != 'CONTINUE':
            return dict(rows=rows, status=status, updates=k, estimate=str(x), residual=str(abs(fx)),
                        step=None if step is None else str(step))
        delta = -fx/dx
        x += delta
        k += 1


def calculate(request):
    # Fixed/type-aware validation occurs before either method is entered.
    if not typed_equal(request, FIXTURE):
        raise InvalidInput('FIXED_INPUT_REQUIRED')
    cases = []
    for case in request['cases']:
        cases.append(dict(id=case['id'],
            bisection=bisection(case['polynomial'], case['bracket'], request['max_updates'], F(request['width_tolerance'])),
            newton=newton(case['polynomial'], case['x0'], request['max_updates'],
                          F(request['residual_tolerance']), F(request['step_tolerance']))))
    bs = sum(c['bisection']['updates'] for c in cases)
    ns = sum(c['newton']['updates'] for c in cases)
    return dict(schema='atlas-root-boundaries-values-v1', cases=cases,
                counts=dict(cases=len(cases), methods=len(cases)*2,
                            rows=sum(len(c[m]['rows']) for c in cases for m in ('bisection','newton')),
                            updates=bs+ns, bisection_updates=bs, newton_updates=ns))
