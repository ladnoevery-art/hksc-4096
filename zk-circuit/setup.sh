#!/bin/bash

# HKSC-4096 ZK Circuit Setup Script
# This script sets up the zk-SNARK circuit for HKSC-4096

set -e

echo "🔧 HKSC-4096 ZK Circuit Setup"
echo "=============================="

# Check dependencies
echo "📋 Checking dependencies..."

if ! command -v circom &> /dev/null; then
    echo "❌ circom not found. Installing..."
    curl -L https://github.com/iden3/circom/releases/download/v2.1.9/circom-linux-amd64 -o /usr/local/bin/circom
    chmod +x /usr/local/bin/circom
fi

if ! command -v snarkjs &> /dev/null; then
    echo "❌ snarkjs not found. Installing..."
    npm install -g snarkjs
fi

echo "✅ Dependencies OK"

# Create directories
mkdir -p build
mkdir -p keys
mkdir -p proofs

# Compile circuit
echo "🔨 Compiling circuit..."
circom hksc_tour.circom --r1cs --wasm --sym -o build/

echo "✅ Circuit compiled"
echo "   - R1CS: build/hksc_tour.r1cs"
echo "   - WASM: build/hksc_tour_js/hksc_tour.wasm"
echo "   - SYM: build/hksc_tour.sym"

# Trusted Setup (Powers of Tau)
echo "🔐 Starting trusted setup..."

# Phase 1
echo "   Phase 1: Powers of Tau..."
snarkjs powersoftau new bn128 14 pot14_0000.ptau -v
snarkjs powersoftau contribute pot14_0000.ptau pot14_0001.ptau --name="HKSC Phase 1" -v -e="random text"
snarkjs powersoftau prepare phase2 pot14_0001.ptau pot14_final.ptau -v

echo "✅ Phase 1 complete"

# Phase 2
echo "   Phase 2: Circuit-specific..."
snarkjs groth16 setup build/hksc_tour.r1cs pot14_final.ptau keys/hksc_tour_0000.zkey
snarkjs zkey contribute keys/hksc_tour_0000.zkey keys/hksc_tour_final.zkey --name="HKSC Final" -e="more randomness"
snarkjs zkey export verificationkey keys/hksc_tour_final.zkey keys/verification_key.json

echo "✅ Phase 2 complete"
echo "   - Proving key: keys/hksc_tour_final.zkey"
echo "   - Verification key: keys/verification_key.json"

# Export Solidity verifier
echo "📄 Exporting Solidity verifier..."
snarkjs zkey export solidityverifier keys/hksc_tour_final.zkey ../hksc-verifier-contract/contracts/HKSC_Verifier_Auto.sol

echo "✅ Solidity verifier exported"

# Cleanup
echo "🧹 Cleaning up..."
rm -f pot14_0000.ptau pot14_0001.ptau

echo ""
echo "=============================="
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Generate witness: node build/hksc_tour_js/generate_witness.js"
echo "2. Create proof: snarkjs groth16 prove"
echo "3. Verify proof: snarkjs groth16 verify"
echo ""
