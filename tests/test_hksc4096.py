import os
import unittest

from hksc4096 import HKSC4096Cipher


class TestHKSC4096(unittest.TestCase):
    def setUp(self):
        self.cipher = HKSC4096Cipher("correct horse battery staple")
        self.salt = bytes(range(16))
        self.nonce = bytes(range(16, 32))

    def test_round_trip_small(self):
        data = b"hello HKSC-4096"
        encrypted = self.cipher.encrypt(data, salt=self.salt, nonce=self.nonce)
        decrypted = self.cipher.decrypt(encrypted)
        self.assertEqual(decrypted, data)

    def test_round_trip_empty(self):
        data = b""
        encrypted = self.cipher.encrypt(data, salt=self.salt, nonce=self.nonce)
        decrypted = self.cipher.decrypt(encrypted)
        self.assertEqual(decrypted, data)

    def test_round_trip_block_plus(self):
        data = os.urandom(5000)
        encrypted = self.cipher.encrypt(data, salt=self.salt, nonce=self.nonce)
        decrypted = self.cipher.decrypt(encrypted)
        self.assertEqual(decrypted, data)

    def test_wrong_passphrase_fails(self):
        data = b"secret"
        encrypted = self.cipher.encrypt(data, salt=self.salt, nonce=self.nonce)
        wrong = HKSC4096Cipher("bad passphrase")
        with self.assertRaises(Exception):
            wrong.decrypt(encrypted)


if __name__ == "__main__":
    unittest.main()
