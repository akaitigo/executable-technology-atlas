"""Independent codeword enumeration and radius-one distance decoding. No codec import."""
from itertools import product, combinations

# Literal parity-check row positions; bit layout is the fixed lesson convention.
PARITY_ROWS = ((1, 3, 5, 7), (2, 3, 6, 7), (4, 5, 6, 7))


def codebook(length):
    result = {}
    for word in product((0, 1), repeat=length):
        if any(sum(word[p - 1] for p in row) % 2 for row in PARITY_ROWS):
            continue
        if length == 8 and sum(word) % 2:
            continue
        message = ''.join(str(word[p - 1]) for p in (3, 5, 6, 7))
        if message in result:
            raise AssertionError('multiple valid words for a message')
        result[message] = ''.join(map(str, word))
    return result


def distance(left, right):
    if len(left) != len(right):
        raise ValueError('length mismatch')
    return sum(a != b for a, b in zip(left, right))


def minimum_distance(book):
    return min(distance(a, b) for a, b in combinations(book.values(), 2))


def nearest(received, book):
    distances = [{'message': m, 'word': w, 'distance': distance(received, w)} for m, w in book.items()]
    minimum = min(row['distance'] for row in distances)
    winners = [row for row in distances if row['distance'] == minimum]
    accepted = minimum <= 1 and len(winners) == 1
    chosen = winners[0] if accepted else None
    positions = [] if chosen is None else [i for i, (a, b) in enumerate(zip(received, chosen['word']), 1) if a != b]
    flip = positions[0] if positions else None
    action = ('reject_double' if not accepted else 'pass_checks' if flip is None
              else 'correct_p8' if flip == 8 else 'correct_1to7')
    return {'minimumDistance': minimum, 'nearestCount': len(winners), 'nearestWords': winners,
            'action': action, 'flip': flip, 'corrected': chosen['word'] if chosen else None,
            'decoded': chosen['message'] if chosen else None}
