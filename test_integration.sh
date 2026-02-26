#!/bin/bash
set -e

echo "🧪 Running HKSC-4096 Integration Tests..."

# 1. Kiểm tra mã hóa/giải mã
echo "Test 1: Encryption/Decryption Cycle..."
echo "Hello, HKSC-4096!" > test_input.txt
python3 hksc4096.py encrypt -i test_input.txt -o test_encrypted.bin -p "secret_passphrase"
python3 hksc4096.py decrypt -i test_encrypted.bin -o test_output.txt -p "secret_passphrase"

if cmp -s test_input.txt test_output.txt; then
    echo "✅ Encryption/Decryption: PASSED"
else
    echo "❌ Encryption/Decryption: FAILED"
    exit 1
fi

# 2. Kiểm tra tạo witness
echo "Test 2: Witness Generation..."
python3 generate_witness_json.py --steps 256 --output input_256.json
if [ -f input_256.json ]; then
    echo "✅ Witness Generation: PASSED"
else
    echo "❌ Witness Generation: FAILED"
    exit 1
fi

# 3. Kiểm tra ZK setup
echo "Test 3: ZK Setup Pipeline..."
bash hksc_zk_setup.sh
if [ -f zk_artifacts/verification_key.json ]; then
    echo "✅ ZK Setup: PASSED"
else
    echo "❌ ZK Setup: FAILED"
    exit 1
fi

echo "🎉 All Integration Tests Passed!"
rm test_input.txt test_encrypted.bin test_output.txt
