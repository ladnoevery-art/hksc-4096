"""HKSC-4096: HyperKnight Supercube Cryptosystem (16x16x16 cells).

This module implements an experimental block cryptosystem inspired by a
3D knight traversal over a 4096-cell supercube.
"""

from __future__ import annotations

from dataclasses import dataclass
import argparse
import getpass
import hashlib
import hmac
import os
import struct
from typing import Iterable, List

CUBE_SIDE = 16
BLOCK_SIZE = CUBE_SIDE ** 3  # 4096 bytes
MAGIC = b"HKSC1"


def _index_to_xyz(index: int) -> tuple[int, int, int]:
    z, rem = divmod(index, CUBE_SIDE * CUBE_SIDE)
    y, x = divmod(rem, CUBE_SIDE)
    return x, y, z


def _xyz_to_index(x: int, y: int, z: int) -> int:
    return z * CUBE_SIDE * CUBE_SIDE + y * CUBE_SIDE + x


def _knight_offsets_3d() -> list[tuple[int, int, int]]:
    offsets = set()
    for zero_axis in range(3):
        axes = [0, 1, 2]
        axes.remove(zero_axis)
        for a, b in ((2, 1), (1, 2)):
            for sa in (-1, 1):
                for sb in (-1, 1):
                    v = [0, 0, 0]
                    v[axes[0]] = sa * a
                    v[axes[1]] = sb * b
                    offsets.add(tuple(v))
    return sorted(offsets)


KNIGHT_OFFSETS = _knight_offsets_3d()


class HKSCError(Exception):
    pass


@dataclass(frozen=True)
class HKSCConfig:
    rounds: int = 8
    scrypt_n: int = 2**14
    scrypt_r: int = 8
    scrypt_p: int = 1


class HKSC4096Cipher:
    def __init__(self, passphrase: str, config: HKSCConfig | None = None):
        if not passphrase:
            raise ValueError("Passphrase must not be empty")
        self.passphrase = passphrase.encode("utf-8")
        self.config = config or HKSCConfig()

    def _derive_master_key(self, salt: bytes) -> bytes:
        return hashlib.scrypt(
            self.passphrase,
            salt=salt,
            n=self.config.scrypt_n,
            r=self.config.scrypt_r,
            p=self.config.scrypt_p,
            dklen=64,
        )

    def _hash_stream(self, seed: bytes, domain: bytes, length: int) -> bytes:
        out = bytearray()
        counter = 0
        while len(out) < length:
            counter_bytes = struct.pack(">Q", counter)
            out.extend(hashlib.sha256(seed + domain + counter_bytes).digest())
            counter += 1
        return bytes(out[:length])

    def _build_permutation(self, seed: bytes) -> list[int]:
        # Keyed 3D knight walk with fallback jumps ensures full 4096-cell coverage.
        visited = [False] * BLOCK_SIZE
        perm: list[int] = []
        score_stream = self._hash_stream(seed, b"perm", BLOCK_SIZE * 8)

        start = int.from_bytes(score_stream[:8], "big") % BLOCK_SIZE
        current = start

        for step in range(BLOCK_SIZE):
            visited[current] = True
            perm.append(current)
            if step == BLOCK_SIZE - 1:
                break

            cx, cy, cz = _index_to_xyz(current)
            candidates = []
            for dx, dy, dz in KNIGHT_OFFSETS:
                nx, ny, nz = cx + dx, cy + dy, cz + dz
                if 0 <= nx < CUBE_SIDE and 0 <= ny < CUBE_SIDE and 0 <= nz < CUBE_SIDE:
                    ni = _xyz_to_index(nx, ny, nz)
                    if not visited[ni]:
                        # Warnsdorff-like score with keyed tie-break
                        onward = 0
                        for ddx, ddy, ddz in KNIGHT_OFFSETS:
                            tx, ty, tz = nx + ddx, ny + ddy, nz + ddz
                            if 0 <= tx < CUBE_SIDE and 0 <= ty < CUBE_SIDE and 0 <= tz < CUBE_SIDE:
                                ti = _xyz_to_index(tx, ty, tz)
                                if not visited[ti]:
                                    onward += 1
                        key_bias = score_stream[(step * 7) % len(score_stream)]
                        candidates.append((onward, key_bias, ni))

            if candidates:
                candidates.sort(key=lambda t: (t[0], t[1]))
                current = candidates[0][2]
            else:
                # Fallback: select next unvisited cell via keyed pseudo-random jumps.
                jump = int.from_bytes(score_stream[(step * 8) % len(score_stream):(step * 8) % len(score_stream) + 8], "big")
                current = jump % BLOCK_SIZE
                while visited[current]:
                    current = (current + 1) % BLOCK_SIZE

        return perm

    def _round_keystream(self, seed_stream: bytes, nonce: bytes, round_index: int) -> bytes:
        domain = b"round" + bytes([round_index]) + nonce
        return self._hash_stream(seed_stream, domain, BLOCK_SIZE)

    @staticmethod
    def _pad(data: bytes) -> bytes:
        pad_len = (-len(data)) % BLOCK_SIZE
        return data + (b"\x00" * pad_len)

    def encrypt(self, plaintext: bytes, *, salt: bytes | None = None, nonce: bytes | None = None) -> bytes:
        salt = salt or os.urandom(16)
        nonce = nonce or os.urandom(16)
        if len(salt) != 16 or len(nonce) != 16:
            raise ValueError("salt and nonce must be 16 bytes each")

        master = self._derive_master_key(salt)
        perm = self._build_permutation(master[:32])

        padded = self._pad(plaintext)
        blocks = [bytearray(padded[i:i + BLOCK_SIZE]) for i in range(0, len(padded), BLOCK_SIZE)]

        for block_id, block in enumerate(blocks):
            for r in range(self.config.rounds):
                ks = self._round_keystream(master[32:], nonce + struct.pack(">I", block_id), r)

                transformed = bytearray(BLOCK_SIZE)
                for i in range(BLOCK_SIZE):
                    delta = (i * 17 + r * 31 + block_id * 13) & 0xFF
                    transformed[i] = ((block[i] + delta) & 0xFF) ^ ks[i]

                permuted = bytearray(BLOCK_SIZE)
                for i, p in enumerate(perm):
                    permuted[p] = transformed[i]
                block = permuted
            blocks[block_id] = block

        header = MAGIC + salt + nonce + bytes([self.config.rounds]) + struct.pack(">Q", len(plaintext))
        body = b"".join(blocks)
        tag = hmac.new(master[48:], header + body, hashlib.sha256).digest()
        return header + body + tag

    def decrypt(self, ciphertext: bytes) -> bytes:
        min_header = len(MAGIC) + 16 + 16 + 1 + 8
        if len(ciphertext) < min_header:
            raise HKSCError("Ciphertext too short")

        pos = 0
        magic = ciphertext[pos:pos + len(MAGIC)]
        pos += len(MAGIC)
        if magic != MAGIC:
            raise HKSCError("Invalid magic")

        salt = ciphertext[pos:pos + 16]
        pos += 16
        nonce = ciphertext[pos:pos + 16]
        pos += 16
        rounds = ciphertext[pos]
        pos += 1
        original_len = struct.unpack(">Q", ciphertext[pos:pos + 8])[0]
        pos += 8

        if len(ciphertext) < pos + 32:
            raise HKSCError("Ciphertext too short for authentication tag")
        body = ciphertext[pos:-32]
        tag = ciphertext[-32:]
        if not body or len(body) % BLOCK_SIZE != 0:
            raise HKSCError("Invalid ciphertext body length")

        master = self._derive_master_key(salt)
        expected_tag = hmac.new(master[48:], ciphertext[:pos] + body, hashlib.sha256).digest()
        if not hmac.compare_digest(tag, expected_tag):
            raise HKSCError("Authentication failed: wrong passphrase or tampered data")
        perm = self._build_permutation(master[:32])

        blocks = [bytearray(body[i:i + BLOCK_SIZE]) for i in range(0, len(body), BLOCK_SIZE)]

        for block_id, block in enumerate(blocks):
            for r in range(rounds - 1, -1, -1):
                ks = self._round_keystream(master[32:], nonce + struct.pack(">I", block_id), r)

                unpermuted = bytearray(BLOCK_SIZE)
                for i in range(BLOCK_SIZE):
                    unpermuted[i] = block[perm[i]]

                restored = bytearray(BLOCK_SIZE)
                for i in range(BLOCK_SIZE):
                    delta = (i * 17 + r * 31 + block_id * 13) & 0xFF
                    restored[i] = ((unpermuted[i] ^ ks[i]) - delta) & 0xFF
                block = restored
            blocks[block_id] = block

        plaintext = b"".join(blocks)
        if original_len > len(plaintext):
            raise HKSCError("Invalid original length in header")
        return plaintext[:original_len]


def _parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="HKSC-4096 file encryption utility")
    sub = parser.add_subparsers(dest="cmd", required=True)

    enc = sub.add_parser("encrypt", help="Encrypt a file")
    enc.add_argument("-i", "--input", required=True, help="Input file")
    enc.add_argument("-o", "--output", required=True, help="Output file")
    enc.add_argument("-p", "--passphrase", help="Passphrase (unsafe on shell history)")

    dec = sub.add_parser("decrypt", help="Decrypt a file")
    dec.add_argument("-i", "--input", required=True, help="Input file")
    dec.add_argument("-o", "--output", required=True, help="Output file")
    dec.add_argument("-p", "--passphrase", help="Passphrase (unsafe on shell history)")

    return parser.parse_args(argv)


def main(argv: Iterable[str] | None = None) -> int:
    args = _parse_args(argv)
    passphrase = args.passphrase or getpass.getpass("Passphrase: ")
    cipher = HKSC4096Cipher(passphrase)

    with open(args.input, "rb") as f:
        data = f.read()

    if args.cmd == "encrypt":
        out = cipher.encrypt(data)
    else:
        out = cipher.decrypt(data)

    with open(args.output, "wb") as f:
        f.write(out)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
