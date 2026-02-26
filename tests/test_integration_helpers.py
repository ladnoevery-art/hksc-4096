import json
import tempfile
import unittest

from hksc_web3 import load_verifier_abi, normalize_proof


class TestIntegrationHelpers(unittest.TestCase):
    def test_load_abi(self):
        with tempfile.NamedTemporaryFile("w+", suffix=".json") as f:
            json.dump([{"name": "verifyProof", "type": "function"}], f)
            f.flush()
            abi = load_verifier_abi(f.name)
        self.assertEqual(abi[0]["name"], "verifyProof")

    def test_normalize_proof(self):
        proof = {
            "A": ["1", "2"],
            "B": [["3", "4"], ["5", "6"]],
            "C": ["7", "8"],
        }
        a, b, c = normalize_proof(proof)
        self.assertEqual(a, [1, 2])
        self.assertEqual(b, [[3, 4], [5, 6]])
        self.assertEqual(c, [7, 8])


if __name__ == "__main__":
    unittest.main()
