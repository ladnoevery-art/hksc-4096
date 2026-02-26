# HKSC-4096 Architecture

## Overview
HKSC-4096 is organized into separable layers so crypto core, API bridge, and blockchain integrations can evolve independently.

## Layers
1. **Core cryptosystem (`hksc4096.py`)**
   - `HKSC4096Cipher`: authenticated block encryption over 4096-byte blocks.
   - `HKSCPlanner`: deterministic transcript generator encoding scheduling parameters (piece, agents, ratio mode, dynamic schedule, adversarial cadence).
   - Planner hash is bound in ciphertext header to prevent silent config drift.

2. **Integration bridge (`hksc_bridge.py`)**
   - Flask API factory for desktop/web frontends.
   - Endpoints for simulation/encrypt/decrypt with JSON payloads + Base64 transport.

3. **Verifier integration (`hksc_web3.py`)**
   - ABI loading + proof normalization.
   - Optional on-chain-compatible `verifyProof` call using `eth_call`.

4. **Contract scaffold (`hksc-verifier-contract`)**
   - Placeholder verifier contract and deploy script for pipeline wiring.
   - Must be replaced by generated Groth16 verifier before production.

## Data flow
1. User provides passphrase + planner config.
2. `scrypt` derives master key.
3. Planner transcript digest is derived and mixed into per-round keystream.
4. 3D keyed knight permutation + substitution rounds produce ciphertext body.
5. Header includes planner hash and metadata.
6. HMAC-SHA3-256 authenticates header+body.

## Security boundaries
- Core cipher can run without Flask/web3 dependencies.
- Web3 is lazy-imported to avoid implicit chain/network coupling.
- Placeholder smart contract is intentionally non-production and clearly marked.

## CI/Security pipeline
- Python unit tests workflow for functional regressions.
- Contract security workflow combining Slither + Echidna + Mythril.
- CodeQL code scanning workflow for Python + JavaScript.
- Dependabot for GitHub Actions and npm ecosystem updates.


## Autonomous Development Plan (Guarded)
- `automation/policy.yaml` defines decision boundaries, escalation rules, and worst-case simulation lanes.
- `automation/autonomy_engine.py` runs health checks, simulation checks, and emits machine-readable status reports.
- `.github/workflows/autonomous-control-loop.yml` executes every 6 hours to continuously monitor and recommend next actions.
- The system is intentionally **safe-autonomy**: it can suggest/prepare low-risk actions, but high-risk domains still require human escalation.
