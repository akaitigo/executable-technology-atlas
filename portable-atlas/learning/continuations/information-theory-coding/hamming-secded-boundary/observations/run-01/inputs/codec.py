"""Small deterministic code model. Decoders accept a received word only."""


def bits(word, length):
    if not isinstance(word, str) or len(word) != length or any(c not in '01' for c in word):
        raise ValueError(f'{length} binary digits required')
    return [int(c) for c in word]


def text(values):
    return ''.join(str(v) for v in values)


def encode(message, scheme='secded8'):
    d1, d2, d3, d4 = bits(message, 4)
    result = [d1 ^ d2 ^ d4, d1 ^ d3 ^ d4, d1, d2 ^ d3 ^ d4, d2, d3, d4]
    if scheme == 'secded8':
        result.append(sum(result) % 2)
    elif scheme != 'hamming7':
        raise ValueError('unknown scheme')
    return text(result)


def syndrome(values):
    result = 0
    for position, bit in enumerate(values[:7], 1):
        if bit:
            result ^= position
    return result


def output(received, values, s, q, action, flip):
    corrected = values.copy()
    if flip is not None:
        corrected[flip - 1] ^= 1
    refused = action == 'reject_double'
    return {'received': received, 'syndrome': s, 'syndromeBits': f'{s:03b}', 'overall': q,
            'action': action, 'flip': flip,
            'corrected': None if refused else text(corrected),
            'decoded': None if refused else text([corrected[i] for i in (2, 4, 5, 6)]),
            'postSyndrome': None if refused else syndrome(corrected),
            'postOverall': None if refused or q is None else sum(corrected) % 2}


def decode7(received):
    values = bits(received, 7)
    s = syndrome(values)
    return output(received, values, s, None, 'correct_1to7' if s else 'pass_checks', s or None)


def decode8(received):
    values = bits(received, 8)
    s, q = syndrome(values), sum(values) % 2
    if s == 0 and q == 0:
        action, flip = 'pass_checks', None
    elif s != 0 and q == 1:
        action, flip = 'correct_1to7', s
    elif s == 0 and q == 1:
        action, flip = 'correct_p8', 8
    else:
        action, flip = 'reject_double', None
    return output(received, values, s, q, action, flip)


def flip_positions(word, positions):
    values = bits(word, len(word))
    if not isinstance(positions, (list, tuple)) or any(type(p) is not int or not 1 <= p <= len(word) for p in positions):
        raise ValueError('positions must be integers within the codeword')
    if len(set(positions)) != len(positions):
        raise ValueError('positions must be distinct')
    for position in positions:
        values[position - 1] ^= 1
    return text(values)
