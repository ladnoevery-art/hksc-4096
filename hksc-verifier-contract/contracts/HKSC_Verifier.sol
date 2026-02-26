// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

/// @notice Placeholder verifier interface-compatible contract.
/// Replace with snarkjs-generated verifier for production.
contract HKSC_Verifier {
    function verifyProof(
        uint256[2] memory,
        uint256[2][2] memory,
        uint256[2] memory,
        uint256[4] memory
    ) public pure returns (bool) {
        return true;
    }
}
