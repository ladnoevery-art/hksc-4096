# HKSC-4096 Quick Start Guide

## 🚀 Get Started in 5 Minutes

### Step 1: Install Dependencies

```bash
# Python backend
cd hksc-python
pip install -r requirements.txt

# Electron GUI
cd ../hksc-electron
npm install
```

### Step 2: Run Python Backend

```bash
cd hksc-python
python hksc_4096.py --flask
```

The Flask API will start at `http://localhost:5000`

### Step 3: Run Electron GUI

In a new terminal:

```bash
cd hksc-electron
npm start
```

The Electron app will automatically:
1. Start the Python backend
2. Open the GUI window
3. Connect to the API

## 📁 Project Structure

```
hksc-4096/
├── hksc-python/              # Python Backend (Core)
│   ├── hksc_4096.py         # Main implementation
│   └── requirements.txt
├── hksc-electron/            # Electron Desktop App
│   ├── src/App.jsx          # React + Three.js UI
│   ├── main.js              # Electron main process
│   └── package.json
├── hksc-verifier-contract/   # Smart Contracts
│   ├── contracts/HKSC_Verifier.sol
│   └── scripts/deploy.js
├── zk-circuit/              # ZK-SNARK Circuits
│   ├── hksc_tour.circom
│   └── setup.sh
└── docs/                    # Documentation
```

## 🔑 Key Features

### 1. Generate Keys

```python
from hksc_4096 import hksc_keygen

keys = hksc_keygen()
# Public: initial_fingerprint, start_pos, adv_seed, tour_hash
# Private: tour (4096 positions)
```

### 2. Encrypt/Decrypt

```python
from hksc_4096 import hksc_encrypt, hksc_decrypt

message = b"Secret message"
ciphertext = hksc_encrypt(keys["public"], message)
decrypted = hksc_decrypt(keys["private"], ciphertext)
```

### 3. 3D Visualization

```python
from hksc_4096 import visualize_knight_path, Pos3D

tour_pos = [Pos3D(*p) for p in keys["private"]["tour"]]
visualize_knight_path(tour_pos, save_as="path.png")
```

### 4. Rubik Onion (Multi-layer)

```python
from hksc_4096 import hksc_onion_encrypt

# 10 layers with VDF delays
onion = hksc_onion_encrypt(message, layers=10)
```

## 🧪 Testing

```bash
# Test Python backend
cd hksc-python
python -c "
from hksc_4096 import hksc_keygen, hksc_encrypt, hksc_decrypt

keys = hksc_keygen()
msg = b'Test'
ct = hksc_encrypt(keys['public'], msg)
dec = hksc_decrypt(keys['private'], ct)
assert msg == dec
print('✅ All tests passed!')
"
```

## 🌐 Deploy Smart Contract

```bash
cd hksc-verifier-contract
npm install
npx hardhat run scripts/deploy.js --network sepolia
```

## 🔗 API Endpoints

When running with `--flask`:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Check API status |
| `/api/keygen` | POST | Generate new keys |
| `/api/encrypt` | POST | Encrypt message |
| `/api/decrypt` | POST | Decrypt message |
| `/api/visualize` | POST | Generate 3D visualization |
| `/api/onion/encrypt` | POST | Create onion encryption |
| `/api/zk/proof` | POST | Generate ZK proof |

## 🛠️ Troubleshooting

### Python backend won't start

```bash
# Check if port 5000 is in use
lsof -i :5000

# Kill process using port 5000
kill -9 $(lsof -t -i :5000)
```

### Electron can't connect to Python

1. Make sure Python backend is running
2. Check firewall settings
3. Verify `http://localhost:5000` is accessible

### Missing dependencies

```bash
# Reinstall Python dependencies
pip install -r hksc-python/requirements.txt --force-reinstall

# Reinstall Node dependencies
rm -rf hksc-electron/node_modules
cd hksc-electron && npm install
```

## 📚 Next Steps

- Read [ARCHITECTURE.md](docs/ARCHITECTURE.md) for technical details
- Read [SECURITY.md](docs/SECURITY.md) for security considerations
- Check [README.md](README.md) for full documentation

## 💬 Support

- Email: security@hksc-4096.eth
- Issues: [GitHub Issues](https://github.com/yourusername/hksc-4096/issues)

---

**Happy encrypting! 🔐**
