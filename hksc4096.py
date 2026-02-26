"""HKSC-4096: HyperKnight Supercube Cryptosystem (16x16x16).

This implementation has two practical layers:
1) HKSC4096Cipher: authenticated file encryption using 4096-byte supercube blocks.
2) HKSCPlanner: deterministic simulation engine for the Rubik/Knight scheduling ideas
   (3 base cases + dynamic ratio + multi-agent + piece variants as abstractions).

The planner is used to derive additional domain-separated key material, so the
"path + schedule" logic can influence encryption in a reproducible way.
"""

from __future__ import annotations

from dataclasses import dataclass
import argparse
import getpass
import hashlib
import hmac
import json
import os
import struct
from typing import Iterable, Sequence

CUBE_SIDE = 16
BLOCK_SIZE = CUBE_SIDE**3  # 4096
SURFACE_CELLS = 6 * CUBE_SIDE * CUBE_SIDE  # 1536 stickers on 6 faces for 16x16
MAGIC = b"HKSC2"


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
    rounds: int = 10
    scrypt_n: int = 2**14
    scrypt_r: int = 8
    scrypt_p: int = 1


@dataclass(frozen=True)
class PlannerConfig:
    piece: str = "knight"  # knight|bishop|rook|queen|king (abstracted mobility classes)
    agents: int = 1
    ratio_mode: str = "equal"  # equal|knight_less|knight_more|dynamic
    ratio_num: int = 1
    ratio_den: int = 1
    dynamic_schedule: tuple[tuple[int, int, int], ...] = ((512, 1, 1), (512, 1, 3), (512, 3, 1))
    adversarial_interval: int = 50
    adversarial_chance_pct: int = 7


class HKSCPlanner:
    """Deterministic abstraction of Rubik x Knight scheduling constraints.

    We model the combined process as a transcript hash. This keeps runtime practical,
    while still honoring requested control knobs (ratio, dynamic ratio, piece type,
    multi-agent, adversarial events).
    """

    def __init__(self, seed: bytes, cfg: PlannerConfig):
        self.seed = seed
        self.cfg = cfg

    def _hash(self, *chunks: bytes) -> bytes:
        h = hashlib.sha3_512()
        for c in chunks:
            h.update(c)
        return h.digest()

    def _piece_weight(self) -> int:
        return {
            "knight": 37,
            "bishop": 23,
            "rook": 19,
            "queen": 53,
            "king": 11,
        }.get(self.cfg.piece, 37)

    def _twists_for_step(self, step: int, progress: int) -> int:
        if self.cfg.ratio_mode == "equal":
            return 1
        if self.cfg.ratio_mode == "knight_less":
            # Knight step triggers many twists (case 2, e.g. 1:8).
            return max(1, self.cfg.ratio_den // max(1, self.cfg.ratio_num))
        if self.cfg.ratio_mode == "knight_more":
            # Many knight steps per twist (case 3), so sparse twists.
            k = max(1, self.cfg.ratio_den)
            return 1 if (step + 1) % k == 0 else 0

        # dynamic: segments of (limit, num, den)
        done = progress
        for limit, num, den in self.cfg.dynamic_schedule:
            if done < limit:
                if num <= den:
                    return max(1, den // max(1, num))
                return 1 if (step + 1) % max(1, num // den) == 0 else 0
            done -= limit
        return 1

    def run_transcript(self, total_cells: int = BLOCK_SIZE) -> bytes:
        if self.cfg.agents < 1:
            raise HKSCError("agents must be >= 1")

        state = self._hash(b"HKSC-PLANNER", self.seed)
        visited = 0

        for step in range(total_cells):
            base = self._hash(state, struct.pack(">I", step))
            twists = self._twists_for_step(step, visited)
            adversarial = (
                self.cfg.adversarial_interval > 0
                and step > 0
                and step % self.cfg.adversarial_interval == 0
                and base[0] < self.cfg.adversarial_chance_pct * 255 // 100
            )

            # Multi-agent contributes broader coverage per system step.
            gain = min(self.cfg.agents, total_cells - visited)
            visited += gain

            state = self._hash(
                state,
                b"S",
                struct.pack(">H", self._piece_weight()),
                struct.pack(">H", self.cfg.agents),
                struct.pack(">H", twists),
                b"A" if adversarial else b"N",
                base,
            )

        return state


class HKSC4096Cipher:
    def __init__(
        self,
        passphrase: str,
        config: HKSCConfig | None = None,
        planner_config: PlannerConfig | None = None,
    ):
        if not passphrase:
            raise ValueError("Passphrase must not be empty")
        self.passphrase = passphrase.encode("utf-8")
        self.config = config or HKSCConfig()
        self.planner_config = planner_config or PlannerConfig()

    def _derive_master_key(self, salt: bytes) -> bytes:
        return hashlib.scrypt(
            self.passphrase,
            salt=salt,
            n=self.config.scrypt_n,
            r=self.config.scrypt_r,
            p=self.config.scrypt_p,
            dklen=96,
        )

    @staticmethod
    def _pad(data: bytes) -> bytes:
        pad_len = (-len(data)) % BLOCK_SIZE
        return data + (b"\x00" * pad_len)

    def _hash_stream(self, seed: bytes, domain: bytes, length: int) -> bytes:
        out = bytearray()
        counter = 0
        while len(out) < length:
            out.extend(hashlib.sha3_256(seed + domain + struct.pack(">Q", counter)).digest())
            counter += 1
        return bytes(out[:length])

    def _build_permutation(self, seed: bytes) -> list[int]:
        visited = [False] * BLOCK_SIZE
        perm: list[int] = []
        stream = self._hash_stream(seed, b"perm", BLOCK_SIZE * 8)
        current = int.from_bytes(stream[:8], "big") % BLOCK_SIZE

        for step in range(BLOCK_SIZE):
            visited[current] = True
            perm.append(current)
            if step == BLOCK_SIZE - 1:
                break

            cx, cy, cz = _index_to_xyz(current)
            candidates: list[tuple[int, int, int]] = []
            for dx, dy, dz in KNIGHT_OFFSETS:
                nx, ny, nz = cx + dx, cy + dy, cz + dz
                if 0 <= nx < CUBE_SIDE and 0 <= ny < CUBE_SIDE and 0 <= nz < CUBE_SIDE:
                    ni = _xyz_to_index(nx, ny, nz)
                    if visited[ni]:
                        continue
                    onward = 0
                    for ddx, ddy, ddz in KNIGHT_OFFSETS:
                        tx, ty, tz = nx + ddx, ny + ddy, nz + ddz
                        if 0 <= tx < CUBE_SIDE and 0 <= ty < CUBE_SIDE and 0 <= tz < CUBE_SIDE:
                            ti = _xyz_to_index(tx, ty, tz)
                            if not visited[ti]:
                                onward += 1
                    bias = stream[(step * 13) % len(stream)]
                    candidates.append((onward, bias, ni))

            if candidates:
                candidates.sort(key=lambda t: (t[0], t[1]))
                current = candidates[0][2]
                continue

            jump = int.from_bytes(stream[(step * 8) % len(stream): (step * 8) % len(stream) + 8], "big")
            current = jump % BLOCK_SIZE
            while visited[current]:
                current = (current + 1) % BLOCK_SIZE

        return perm

    def _planner_digest(self, planner_seed: bytes) -> bytes:
        planner = HKSCPlanner(planner_seed, self.planner_config)
        return planner.run_transcript(BLOCK_SIZE)

    def encrypt(self, plaintext: bytes, *, salt: bytes | None = None, nonce: bytes | None = None) -> bytes:
        salt = os.urandom(16) if salt is None else salt
        nonce = os.urandom(16) if nonce is None else nonce
        if len(salt) != 16 or len(nonce) != 16:
            raise ValueError("salt and nonce must be 16 bytes each")

        master = self._derive_master_key(salt)
        perm = self._build_permutation(master[:32])
        planner_digest = self._planner_digest(master[64:96])

        padded = self._pad(plaintext)
        blocks = [bytearray(padded[i : i + BLOCK_SIZE]) for i in range(0, len(padded), BLOCK_SIZE)]

        for block_id, block in enumerate(blocks):
            for r in range(self.config.rounds):
                domain = b"round" + bytes([r]) + nonce + struct.pack(">I", block_id)
                ks = self._hash_stream(master[32:64] + planner_digest, domain, BLOCK_SIZE)
                transformed = bytearray(BLOCK_SIZE)
                for i in range(BLOCK_SIZE):
                    delta = (i * 17 + r * 31 + block_id * 13 + planner_digest[i % len(planner_digest)]) & 0xFF
                    transformed[i] = ((block[i] + delta) & 0xFF) ^ ks[i]
                permuted = bytearray(BLOCK_SIZE)
                for i, p in enumerate(perm):
                    permuted[p] = transformed[i]
                block = permuted
            blocks[block_id] = block

        planner_json = json.dumps(self.planner_config.__dict__, sort_keys=True, separators=(",", ":")).encode("utf-8")
        planner_hash = hashlib.sha3_256(planner_json).digest()
        header = MAGIC + salt + nonce + bytes([self.config.rounds]) + planner_hash + struct.pack(">Q", len(plaintext))
        body = b"".join(blocks)
        tag = hmac.new(master[64:96], header + body, hashlib.sha3_256).digest()
        return header + body + tag

    def decrypt(self, ciphertext: bytes) -> bytes:
        min_header = len(MAGIC) + 16 + 16 + 1 + 32 + 8
        if len(ciphertext) < min_header + 32:
            raise HKSCError("Ciphertext too short")

        pos = 0
        if ciphertext[: len(MAGIC)] != MAGIC:
            raise HKSCError("Invalid magic")
        pos += len(MAGIC)

        salt = ciphertext[pos : pos + 16]
        pos += 16
        nonce = ciphertext[pos : pos + 16]
        pos += 16
        rounds = ciphertext[pos]
        pos += 1

        planner_hash = ciphertext[pos : pos + 32]
        pos += 32

        original_len = struct.unpack(">Q", ciphertext[pos : pos + 8])[0]
        pos += 8

        body = ciphertext[pos:-32]
        tag = ciphertext[-32:]
        if not body or len(body) % BLOCK_SIZE != 0:
            raise HKSCError("Invalid ciphertext body length")

        planner_json = json.dumps(self.planner_config.__dict__, sort_keys=True, separators=(",", ":")).encode("utf-8")
        expected_planner_hash = hashlib.sha3_256(planner_json).digest()
        if not hmac.compare_digest(planner_hash, expected_planner_hash):
            raise HKSCError("Planner configuration mismatch")

        master = self._derive_master_key(salt)
        expected_tag = hmac.new(master[64:96], ciphertext[: pos] + body, hashlib.sha3_256).digest()
        if not hmac.compare_digest(tag, expected_tag):
            raise HKSCError("Authentication failed: wrong passphrase or tampered data")

        perm = self._build_permutation(master[:32])
        planner_digest = self._planner_digest(master[64:96])

        blocks = [bytearray(body[i : i + BLOCK_SIZE]) for i in range(0, len(body), BLOCK_SIZE)]
        for block_id, block in enumerate(blocks):
            for r in range(rounds - 1, -1, -1):
                domain = b"round" + bytes([r]) + nonce + struct.pack(">I", block_id)
                ks = self._hash_stream(master[32:64] + planner_digest, domain, BLOCK_SIZE)
                unpermuted = bytearray(BLOCK_SIZE)
                for i in range(BLOCK_SIZE):
                    unpermuted[i] = block[perm[i]]
                restored = bytearray(BLOCK_SIZE)
                for i in range(BLOCK_SIZE):
                    delta = (i * 17 + r * 31 + block_id * 13 + planner_digest[i % len(planner_digest)]) & 0xFF
                    restored[i] = ((unpermuted[i] ^ ks[i]) - delta) & 0xFF
                block = restored
            blocks[block_id] = block

        plaintext = b"".join(blocks)
        if original_len > len(plaintext):
            raise HKSCError("Invalid original length in header")
        return plaintext[:original_len]


def _parse_dynamic_schedule(raw: str | None) -> tuple[tuple[int, int, int], ...]:
    if not raw:
        return PlannerConfig().dynamic_schedule
    parts = []
    for seg in raw.split(","):
        a, b, c = seg.split(":")
        parts.append((int(a), int(b), int(c)))
    return tuple(parts)


def _make_planner_config(args: argparse.Namespace) -> PlannerConfig:
    return PlannerConfig(
        piece=getattr(args, "piece", "knight"),
        agents=getattr(args, "agents", 1),
        ratio_mode=getattr(args, "ratio_mode", "equal"),
        ratio_num=getattr(args, "ratio_num", 1),
        ratio_den=getattr(args, "ratio_den", 1),
        dynamic_schedule=_parse_dynamic_schedule(getattr(args, "dynamic_schedule", None)),
        adversarial_interval=getattr(args, "adversarial_interval", 50),
        adversarial_chance_pct=getattr(args, "adversarial_chance_pct", 7),
    )


def _add_shared_planner_args(p: argparse.ArgumentParser) -> None:
    p.add_argument("--piece", default="knight", choices=["knight", "bishop", "rook", "queen", "king"])
    p.add_argument("--agents", type=int, default=1)
    p.add_argument("--ratio-mode", default="equal", choices=["equal", "knight_less", "knight_more", "dynamic"])
    p.add_argument("--ratio-num", type=int, default=1)
    p.add_argument("--ratio-den", type=int, default=1)
    p.add_argument("--dynamic-schedule", help="Format: limit:num:den,limit:num:den")
    p.add_argument("--adversarial-interval", type=int, default=50)
    p.add_argument("--adversarial-chance-pct", type=int, default=7)


def _parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="HKSC-4096 utility")
    sub = parser.add_subparsers(dest="cmd", required=True)

    enc = sub.add_parser("encrypt", help="Encrypt a file")
    enc.add_argument("-i", "--input", required=True)
    enc.add_argument("-o", "--output", required=True)
    enc.add_argument("-p", "--passphrase")
    _add_shared_planner_args(enc)

    dec = sub.add_parser("decrypt", help="Decrypt a file")
    dec.add_argument("-i", "--input", required=True)
    dec.add_argument("-o", "--output", required=True)
    dec.add_argument("-p", "--passphrase")
    _add_shared_planner_args(dec)

    sim = sub.add_parser("simulate", help="Simulate planner transcript only")
    sim.add_argument("--seed", default="demo-seed")
    sim.add_argument("--cells", type=int, default=BLOCK_SIZE)
    _add_shared_planner_args(sim)

    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)

    if args.cmd == "simulate":
        cfg = _make_planner_config(args)
        planner = HKSCPlanner(args.seed.encode("utf-8"), cfg)
        digest = planner.run_transcript(args.cells)
        print(json.dumps({"digest": digest.hex(), "cells": args.cells, "planner": cfg.__dict__}, indent=2))
        return 0

    passphrase = args.passphrase or getpass.getpass("Passphrase: ")
    planner_cfg = _make_planner_config(args)
    cipher = HKSC4096Cipher(passphrase, planner_config=planner_cfg)

    with open(args.input, "rb") as f:
        data = f.read()

    out = cipher.encrypt(data) if args.cmd == "encrypt" else cipher.decrypt(data)

    with open(args.output, "wb") as f:
        f.write(out)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
