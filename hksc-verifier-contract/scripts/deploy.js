async function main() {
  const Verifier = await ethers.getContractFactory('HKSC_Verifier');
  const verifier = await Verifier.deploy();
  await verifier.waitForDeployment();
  console.log('HKSC_Verifier deployed to:', verifier.target);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
