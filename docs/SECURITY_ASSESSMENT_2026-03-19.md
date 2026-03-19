# Security Assessment & Attack Simulation (Defensive)

**Date:** 2026-03-19  
**Scope:** `hksc-python`, `hksc-autonomous`, `hksc-electron`, `hksc-verifier-contract`  
**Mode:** Defensive security review (no destructive exploitation)

## 1) What was scanned

1. Python dependency vulnerability audit (`pip-audit`) on `hksc-python/requirements.txt`.
2. Static application security testing (`bandit`) on Python source.
3. Dependency audit attempt (`npm audit`) for both Node subprojects.
4. Unsafe-pattern grep review for command execution and risky APIs.

## 2) Results summary

- `pip-audit` reported **no known vulnerabilities** for Python dependencies.
- `bandit` reported multiple **Low** findings and one **Medium** finding:
  - Command execution surface via `subprocess.run(...)` across autonomous agents.
  - `try/except/pass` blocks reducing observability.
  - Use of `random.random()` in cryptographic flow (addressed in this assessment's code updates).
  - API binding to `0.0.0.0` in Flask startup path (addressed in this assessment's code updates).
- `npm audit` could not run because both Node projects currently have no lockfile (`ENOLOCK`).

## 3) Defensive attack simulation scenarios

> ⚠️ The simulations below are **defensive/tabletop** scenarios intended for resilience testing, not offensive compromise guidance.

### Scenario A — Unauthorized remote API exposure
- **Threat:** Service exposed on all interfaces could be reached from unintended networks.
- **Likely impact:** Data leakage, brute-force probing, request flooding.
- **Current mitigation introduced:** Default bind host changed to `127.0.0.1`; host/port now controlled via environment variables.
- **Validation idea:** Start backend and verify it listens only on loopback by default.

### Scenario B — Predictable adversarial toggles in key-derivation path
- **Threat:** Non-cryptographic PRNG in security-sensitive transitions may reduce unpredictability.
- **Likely impact:** Reduced entropy and potentially more predictable state transitions.
- **Current mitigation introduced:** Replaced PRNG-based toggle with deterministic hash-based toggle derived from `adv_seed + step`.
- **Validation idea:** Re-run encrypt/decrypt round-trip tests and verify deterministic behavior for same seed.

### Scenario C — CI/automation command injection surface
- **Threat:** Autonomous agents invoke many system commands (`pip`, `git`, `gh`, `pytest`).
- **Likely impact:** If upstream inputs are untrusted, attacker-controlled arguments could trigger unsafe execution.
- **Recommended control:** Add strict allow-lists for commands/arguments and sanitize any dynamic inputs before execution.

## 4) Immediate hardening actions completed in code

1. Added deterministic adversarial-step function derived from SHA3-256 (`adv_seed`, `step`).
2. Replaced non-crypto shuffle source with `secrets.SystemRandom()` for knight-move ordering.
3. Changed Flask startup defaults to loopback-only (`127.0.0.1`) with env overrides:
   - `HKSC_API_HOST`
   - `HKSC_API_PORT`

## 5) Recommended next steps

1. Generate lockfiles for Node projects and run `npm audit` in CI.
2. Add authenticated API access (token or mTLS) before any non-local deployment.
3. Introduce rate limiting and request size limits for Flask endpoints.
4. Add security regression checks (Bandit + pip-audit) to GitHub Actions.
5. For autonomous agents, constrain `subprocess` calls with explicit command allow-lists.

