# HKSC Verifier Contract

This folder is a deploy scaffold for zk-proof verification.

## Replace before production
1. Generate verifier from snarkjs:
   - `snarkjs zkey export solidityverifier hksc_tour_final.zkey contracts/HKSC_Verifier.sol`
2. Compile/deploy with Hardhat.
3. Export ABI and configure `hksc_web3.py`.
