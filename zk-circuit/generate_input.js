const fs = require('fs');
const { poseidon } = require('circomlibjs');

/**
 * Generate input JSON for HKSC ZK circuit
 * @param {Array} tour - Array of [x, y, z] positions
 * @returns {Object} Input JSON for circuit
 */
function generateCircuitInput(tour) {
    const N = 256; // Circuit size
    
    if (tour.length < N) {
        throw new Error(`Tour must have at least ${N} positions`);
    }
    
    // Take first N positions
    const steps = tour.slice(0, N);
    
    // Flatten for Poseidon
    const flatSteps = steps.flat();
    
    // Compute tour hash
    const tourHash = poseidon(flatSteps);
    
    // Solved hash (same as tour hash for self-solving)
    const solvedHash = tourHash;
    
    const input = {
        tourHash: tourHash.toString(),
        startPos: steps[0],
        endPos: steps[N - 1],
        solvedHash: solvedHash.toString(),
        knightSteps: steps
    };
    
    return input;
}

// CLI usage
if (require.main === module) {
    const tourFile = process.argv[2] || '../hksc-python/onion_private/hksc_private_tour_4096.txt';
    
    // Read tour from file
    const tourData = fs.readFileSync(tourFile, 'utf8');
    const tour = tourData.trim().split('\n').map(line => {
        const [x, y, z] = line.split(',').map(Number);
        return [x, y, z];
    });
    
    console.log(`📖 Loaded tour with ${tour.length} positions`);
    
    const input = generateCircuitInput(tour);
    
    fs.writeFileSync('build/input.json', JSON.stringify(input, null, 2));
    console.log('✅ Input written to build/input.json');
}

module.exports = { generateCircuitInput };
