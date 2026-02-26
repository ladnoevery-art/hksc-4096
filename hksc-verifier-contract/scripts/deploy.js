const { ethers, run, network } = require("hardhat");
const fs = require('fs');
const path = require('path');

async function main() {
  console.log("🚀 Deploying HKSC_Verifier contract...");
  
  // Get deployer
  const [deployer] = await ethers.getSigners();
  console.log("📡 Deploying with account:", deployer.address);
  console.log("💰 Account balance:", (await ethers.provider.getBalance(deployer.address)).toString());

  // Deploy contract
  const HKSC_Verifier = await ethers.getContractFactory("HKSC_Verifier");
  const verifier = await HKSC_Verifier.deploy();
  
  await verifier.waitForDeployment();
  
  const contractAddress = await verifier.getAddress();
  console.log("✅ HKSC_Verifier deployed to:", contractAddress);
  console.log("🔗 Network:", network.name);
  
  // Save deployment info
  const deploymentInfo = {
    contractAddress,
    network: network.name,
    chainId: network.config.chainId,
    deployer: deployer.address,
    timestamp: new Date().toISOString(),
    blockNumber: await ethers.provider.getBlockNumber()
  };
  
  const deploymentPath = path.join(__dirname, '..', 'deployments');
  if (!fs.existsSync(deploymentPath)) {
    fs.mkdirSync(deploymentPath, { recursive: true });
  }
  
  fs.writeFileSync(
    path.join(deploymentPath, `${network.name}-deployment.json`),
    JSON.stringify(deploymentInfo, null, 2)
  );
  
  // Verify on Etherscan if not localhost
  if (network.name !== "hardhat" && network.name !== "localhost") {
    console.log("⏳ Waiting for block confirmations...");
    await verifier.deploymentTransaction().wait(5);
    
    console.log("🔍 Verifying contract on Etherscan...");
    try {
      await run("verify:verify", {
        address: contractAddress,
        constructorArguments: []
      });
      console.log("✅ Contract verified!");
    } catch (error) {
      console.log("⚠️ Verification failed:", error.message);
    }
  }
  
  console.log("\n📋 Deployment Summary:");
  console.log("======================");
  console.log("Contract:", contractAddress);
  console.log("Network:", network.name);
  console.log("Explorer:", getExplorerUrl(network.name, contractAddress));
  
  return deploymentInfo;
}

function getExplorerUrl(network, address) {
  const explorers = {
    mainnet: `https://etherscan.io/address/${address}`,
    sepolia: `https://sepolia.etherscan.io/address/${address}`,
    arbitrum: `https://arbiscan.io/address/${address}`,
    base: `https://basescan.org/address/${address}`
  };
  return explorers[network] || "N/A";
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error("❌ Deployment failed:", error);
    process.exit(1);
  });
