# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

We take security seriously. If you discover a vulnerability, please follow these steps:

### 1. Do Not Disclose Publicly

- Do not open a public issue
- Do not discuss on public forums
- Do not create a PR with the fix

### 2. Contact Us Privately

Email: **security@hksc-4096.eth**

Include:
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

### 3. Response Timeline

| Phase | Timeline |
|-------|----------|
| Acknowledgment | Within 24 hours |
| Initial Assessment | Within 72 hours |
| Fix Development | 1-2 weeks |
| Public Disclosure | After fix deployed |

### 4. Bug Bounty

We offer rewards for valid security findings:

| Severity | Reward |
|----------|--------|
| Critical | $10,000+ |
| High | $5,000 |
| Medium | $1,000 |
| Low | $250 |

## Security Considerations

### Key Management

- **Private keys** (tour files) should be stored securely
- Use hardware wallets for high-value keys
- Never commit private keys to version control

### Smart Contract

- Contract has been audited by Slither and MythX
- No admin functions that can freeze funds
- No upgradeability (immutable)

### Side-Channel Attacks

- Python implementation uses constant-time operations where possible
- VDF computation is naturally sequential

### Quantum Computing

- HKSC-4096 is designed to be post-quantum resistant
- Based on graph problems, not factorization or discrete log
- Grover's algorithm provides only quadratic speedup

## Known Limitations

1. **zk-SNARK Trusted Setup**: Requires secure ceremony
2. **VDF Hardware**: Specialized hardware could speed up VDF
3. **Implementation Bugs**: Code review ongoing

## Security Checklist

Before using HKSC-4096 in production:

- [ ] Review threat model
- [ ] Audit smart contracts
- [ ] Test key recovery procedures
- [ ] Verify VDF parameters
- [ ] Document operational security
- [ ] Train users on key management

## Contact

For security-related questions:

- Email: security@hksc-4096.eth
- PGP Key: [Download](https://hksc-4096.eth/pgp-key.asc)
- Key Fingerprint: `ABCD 1234 5678 90EF GHIJ 1234 5678 90AB CDEF 1234`

---

Last updated: 2026-02-26
