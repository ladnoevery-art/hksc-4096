# HKSC-4096 Whitepaper (Engineering Draft)

## Abstract
HKSC-4096 is an experimental cryptographic construction that combines a 4096-cell supercube permutation model with a deterministic planner transcript to provide configurable domain separation. The system aims to be practical for experimentation while preserving deterministic replay for verification, simulation, and integration workflows.

## Design goals
- Deterministic reproducibility for encryption/decryption under explicit planner configuration.
- Strict authentication failure on passphrase mismatch or planner mismatch.
- Practical integration paths (CLI, Flask API, contract verification scaffolding).
- Security-first pipeline support (static analysis, fuzzing, symbolic analysis, code scanning).

## Threat model (current)
The system defends against:
- Passive eavesdroppers reading ciphertext.
- Active tampering of ciphertext/header.
- Configuration drift between encrypt/decrypt environments.

The system does **not** claim formal proof security or replacement for audited standardized AEAD.

## Cryptographic composition
1. **KDF**: `scrypt(passphrase, salt)` derives key material.
2. **Permutation**: keyed 3D knight-walk over 16×16×16 coordinate space with fallback coverage.
3. **Round transform**: substitution + XOR keystream.
4. **Authentication**: HMAC-SHA3-256 over header+body.
5. **Planner binding**: planner configuration hash embedded in ciphertext header.

## Planner model
Planner digest is deterministic over:
- piece mobility class,
- agent count,
- ratio mode (`equal`, `knight_less`, `knight_more`, `dynamic`),
- dynamic schedule segments,
- adversarial timing settings.

Planner digest is mixed into keystream derivation and delta evolution, making ciphertext dependent on planner semantics.

## Interoperability
- CLI supports encrypt/decrypt/simulate/serve.
- Flask bridge supports JSON APIs for UI tooling.
- Web3 helper supports ABI-driven verifier invocation.
- Contract scaffold supports future replacement with generated Groth16 verifier.

## Security operations
Recommended baseline:
- Enforce branch protections.
- Require passing unit tests + security workflows.
- Enable Dependabot alerts + secret scanning + code scanning.
- Replace placeholder verifier before any public deployment.

## Limitations and roadmap
- No formal reduction proof.
- Planner currently hash-chain abstraction (not full Rubik group solver).
- Smart contract currently placeholder.

Roadmap:
1. Generated verifier contract + ABI pinning.
2. Cross-language test vectors.
3. Formal serialization spec.
4. Third-party audit.
