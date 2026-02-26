import os
import unittest

from hksc4096 import HKSC4096Cipher, HKSCError, HKSCPlanner, PlannerConfig


class TestHKSC4096(unittest.TestCase):
    def setUp(self):
        self.base = dict(salt=bytes(range(16)), nonce=bytes(range(16, 32)))

    def test_round_trip_small(self):
        cipher = HKSC4096Cipher("correct horse battery staple")
        data = b"hello HKSC-4096"
        encrypted = cipher.encrypt(data, **self.base)
        decrypted = cipher.decrypt(encrypted)
        self.assertEqual(decrypted, data)

    def test_round_trip_with_dynamic_ratio(self):
        cfg = PlannerConfig(ratio_mode="dynamic", dynamic_schedule=((200, 1, 1), (200, 1, 8), (200, 7, 1)))
        cipher = HKSC4096Cipher("pass", planner_config=cfg)
        data = os.urandom(5000)
        encrypted = cipher.encrypt(data, **self.base)
        decrypted = cipher.decrypt(encrypted)
        self.assertEqual(decrypted, data)

    def test_planner_mismatch_fails(self):
        c1 = HKSC4096Cipher("pw", planner_config=PlannerConfig(piece="knight", agents=1))
        c2 = HKSC4096Cipher("pw", planner_config=PlannerConfig(piece="queen", agents=2))
        ct = c1.encrypt(b"secret", **self.base)
        with self.assertRaises(HKSCError):
            c2.decrypt(ct)

    def test_wrong_passphrase_fails(self):
        cipher = HKSC4096Cipher("good")
        ct = cipher.encrypt(b"abc", **self.base)
        with self.assertRaises(HKSCError):
            HKSC4096Cipher("bad").decrypt(ct)

    def test_planner_deterministic(self):
        cfg = PlannerConfig(ratio_mode="knight_more", ratio_den=7, agents=3)
        p1 = HKSCPlanner(b"seed", cfg).run_transcript(256)
        p2 = HKSCPlanner(b"seed", cfg).run_transcript(256)
        self.assertEqual(p1, p2)


if __name__ == "__main__":
    unittest.main()
