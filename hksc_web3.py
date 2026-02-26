"""Web3 helpers for HKSC verifier integration.

This module keeps blockchain logic separate from the core cipher so users can
opt-in only when they need on-chain zk-proof verification.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Sequence


@dataclass(frozen=True)
class VerifierConfig:
    rpc_url: str
    verifier_address: str
    abi_path: str


def load_verifier_abi(path: str | Path) -> list[dict[str, Any]]:
    raw = Path(path).read_text(encoding="utf-8")
    data = json.loads(raw)
    if not isinstance(data, list):
        raise ValueError("Verifier ABI JSON must be a list")
    return data


def normalize_proof(proof: dict[str, Any]) -> tuple[list[int], list[list[int]], list[int]]:
    required = ("A", "B", "C")
    if any(k not in proof for k in required):
        raise ValueError("Proof must contain A, B, C")
    a, b, c = proof["A"], proof["B"], proof["C"]
    if len(a) != 2 or len(b) != 2 or len(c) != 2 or any(len(row) != 2 for row in b):
        raise ValueError("Invalid Groth16 proof shape")
    return [int(x) for x in a], [[int(x) for x in row] for row in b], [int(x) for x in c]


def onchain_verify_zk_proof(
    cfg: VerifierConfig,
    proof: dict[str, Any],
    public_inputs: Sequence[int],
) -> bool:
    """Call verifier.verifyProof(...) as eth_call (no state change)."""
    from web3 import Web3  # imported lazily to avoid hard dependency for non-web3 users

    w3 = Web3(Web3.HTTPProvider(cfg.rpc_url))
    if not w3.is_connected():
        raise RuntimeError("Cannot connect to EVM RPC")

    abi = load_verifier_abi(cfg.abi_path)
    contract = w3.eth.contract(address=cfg.verifier_address, abi=abi)
    a, b, c = normalize_proof(proof)
    return bool(contract.functions.verifyProof(a, b, c, list(map(int, public_inputs))).call())
