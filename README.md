# HKSC-4096

HyperKnight Supercube Cryptosystem (`16x16x16 = 4096` cells).

Bản này nâng cấp theo hướng **có thể sử dụng thực tế** và nối tiếp roadmap bạn đưa:
- Cipher + planner deterministic (core crypto),
- Flask bridge cho desktop/web UI,
- Web3 helper cho on-chain verifier,
- CI workflows cho Python test + Slither gatekeeper,
- Scaffold contract verifier để thay bằng bản xuất từ `snarkjs`.

## 1) Core crypto

`hksc4096.py` gồm:
- `HKSC4096Cipher`: mã hóa block 4096 bytes, keyed 3D knight-walk permutation.
- `HKSCPlanner`: mô phỏng ratio/case logic (equal, knight_less, knight_more, dynamic), piece variants, multi-agent, adversarial events.
- planner hash được bind vào header; decrypt sai planner config sẽ bị từ chối.

## 2) CLI

### Encrypt / Decrypt
```bash
python hksc4096.py encrypt -i plain.bin -o secret.hksc -p "my-pass" \
  --piece knight --agents 2 --ratio-mode dynamic \
  --dynamic-schedule "512:1:1,512:1:8,512:7:1"

python hksc4096.py decrypt -i secret.hksc -o recovered.bin -p "my-pass" \
  --piece knight --agents 2 --ratio-mode dynamic \
  --dynamic-schedule "512:1:1,512:1:8,512:7:1"
```

### Planner simulation
```bash
python hksc4096.py simulate --seed demo --cells 1024 \
  --piece queen --agents 3 --ratio-mode knight_more --ratio-den 7
```

### Flask bridge (cho Electron/React)
```bash
pip install flask
python hksc4096.py serve --host 127.0.0.1 --port 5000
```

API chính:
- `POST /api/simulate`
- `POST /api/encrypt`
- `POST /api/decrypt`

## 3) Web3 verifier integration

`hksc_web3.py` cung cấp:
- `load_verifier_abi(...)`
- `normalize_proof(...)`
- `onchain_verify_zk_proof(...)` (eth_call verifyProof)

Contract scaffold nằm tại `hksc-verifier-contract/`.

> Lưu ý: `contracts/HKSC_Verifier.sol` hiện là placeholder. Trước production phải thay bằng file export từ `snarkjs zkey export solidityverifier ...`.

## 4) CI/CD

- `.github/workflows/python-tests.yml`: chạy unit tests.
- `.github/workflows/ci-slither.yml`: Slither security gatekeeper cho contract.

## 5) Test local

```bash
python -m unittest discover -s tests -v
```

## Security note

- Đây là thiết kế experimental/R&D.
- Planner là abstraction hash-chain, không phải full Rubik group solver.
- Không dùng cho dữ liệu tối mật production nếu chưa audit độc lập.


## 6) Whitepaper & architecture docs

- `docs/WHITEPAPER.md`: engineering draft, threat model, composition, roadmap.
- `docs/ARCHITECTURE.md`: component boundaries, data-flow, and CI/security design.

## 7) Security pipeline (expanded)

- `contract-security.yml`: Slither + Echidna + Mythril in one pipeline.
- `codeql.yml`: code scanning for Python + JavaScript/TypeScript.
- `.github/dependabot.yml`: weekly dependency updates for GitHub Actions + npm.

## 8) Enable repository security alerts (GitHub settings)

In **Settings → Security & analysis**, enable:
- Dependabot alerts
- Dependabot security updates
- Code scanning alerts
- Secret scanning (and push protection if available)
