import itertools
import unittest
from lesson import INVALID, decode, encode, experiment, observation_set
from oracle import G, H, matrix_encode, matrix_syndrome, nearest_codewords


class HammingTest(unittest.TestCase):
    def test_known_codewords(self):
        for message, word in (("0000", "0000000"), ("1000", "1110000"),
                              ("0001", "1101001"), ("1011", "0110011"), ("1111", "1111111")):
            self.assertEqual(encode(message), word)
            self.assertEqual(matrix_encode(message), word)

    def test_all_16_no_error(self):
        for n in range(16):
            row = experiment({"message": f"{n:04b}", "errors": []})
            self.assertEqual(row["syndrome"], 0)
            self.assertIsNone(row["flipped_position"])
            self.assertTrue(row["ground_truth_matches"])

    def test_all_112_single_bit_cases(self):
        rows = observation_set()["single_bit"]
        self.assertEqual(len(rows), 112)
        self.assertEqual({(r["input"]["message"], r["input"]["errors"][0]) for r in rows},
                         {(f"{n:04b}", p) for n in range(16) for p in range(1, 8)})
        for row in rows:
            self.assertEqual(row["syndrome"], row["input"]["errors"][0])
            self.assertEqual(row["flipped_position"], row["syndrome"])
            self.assertEqual(row["corrected"], row["encoded"])
            self.assertEqual(row["recovered"], row["input"]["message"])
            self.assertEqual(row["post_syndrome"], 0)

    def test_matrix_orthogonality_and_distance(self):
        for row in G:
            self.assertEqual([sum(x * y for x, y in zip(row, check)) % 2 for check in H], [0, 0, 0])
        codebook = {matrix_encode(f"{n:04b}") for n in range(16)}
        self.assertEqual(len(codebook), 16)
        self.assertEqual(min(sum(a != b for a, b in zip(x, y)) for x, y in itertools.combinations(codebook, 2)), 3)

    def test_all_128_received_words_against_independent_oracles(self):
        for n in range(128):
            received = f"{n:07b}"
            result = decode(received)
            self.assertEqual(result["syndrome"], matrix_syndrome(received))
            self.assertEqual(nearest_codewords(received)["words"], [result["corrected"]])

    def test_double_bit_miscorrection_not_secded(self):
        row = experiment({"message": "0000", "errors": [1, 2]})
        self.assertEqual(row["received"], "1100000")
        self.assertEqual(row["syndrome"], 3)
        self.assertEqual(row["flipped_position"], 3)
        self.assertEqual(row["corrected"], "1110000")
        self.assertEqual(row["recovered"], "1000")
        self.assertEqual(row["post_syndrome"], 0)
        self.assertFalse(row["ground_truth_matches"])
        self.assertFalse(row["guarantee_applies"])
        self.assertEqual(row["oracle"]["nearest"], {"distance": 1, "words": ["1110000"]})

    def test_zero_syndrome_does_not_imply_original(self):
        result = decode("1110000")
        self.assertEqual(result["syndrome"], 0)
        self.assertEqual(result["recovered"], "1000")

    def test_invalid_input_and_decoder_word(self):
        for data in INVALID:
            with self.subTest(data=data), self.assertRaises(ValueError):
                experiment(data)
        for value in (None, "000000", "00000000", "xxxxxxx"):
            with self.assertRaises(ValueError):
                decode(value)

    def test_rejection_then_valid_recovery(self):
        with self.assertRaises(ValueError):
            experiment({"message": "0000", "errors": [8]})
        self.assertTrue(experiment({"message": "0000", "errors": [7]})["ground_truth_matches"])


if __name__ == "__main__":
    unittest.main()
