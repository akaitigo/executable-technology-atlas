"""Independent literal G/H matrices and exhaustive nearest-codeword oracle.

Does not import the encoder, decoder, parity positions, or checks from lesson.
Columns use this module's stated positional convention, not the MIT layout.
"""
G = ((1, 1, 1, 0, 0, 0, 0), (1, 0, 0, 1, 1, 0, 0),
     (0, 1, 0, 1, 0, 1, 0), (1, 1, 0, 1, 0, 0, 1))
H = ((1, 0, 1, 0, 1, 0, 1), (0, 1, 1, 0, 0, 1, 1), (0, 0, 0, 1, 1, 1, 1))


def matrix_encode(message):
    return "".join(str(sum(int(message[i]) * G[i][j] for i in range(4)) % 2) for j in range(7))


def matrix_syndrome(received):
    vector = [sum(row[j] * int(received[j]) for j in range(7)) % 2 for row in H]
    return sum(value * 2 ** i for i, value in enumerate(vector))


def nearest_codewords(received):
    distances = [(sum(a != b for a, b in zip(received, word)), word)
                 for word in (matrix_encode(f"{n:04b}") for n in range(16))]
    minimum = min(distance for distance, _ in distances)
    return {"distance": minimum, "words": sorted(word for distance, word in distances if distance == minimum)}
