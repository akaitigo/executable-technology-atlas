"""教材の純粋関数。I/Oや外部サービスは持たない。"""
def clamp(value, lower=0, upper=10):
    if any(type(x) is not int for x in (value, lower, upper)) or lower > upper:
        raise ValueError('integer bounds required')
    return min(upper, max(lower, value))


def add(left, right):
    if type(left) is not int or type(right) is not int:
        raise ValueError('integers required')
    return left + right
