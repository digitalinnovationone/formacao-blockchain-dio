/**
 * Deploy Script para DeltaNeutralVaultV1Testnet
 *
 * ⚠️ APENAS ARBITRUM SEPOLIA (Chain ID 421614)
 *
 * Deploy otimizado para testnet com:
 * - MIN_DEPOSIT reduzido (0.0001 ETH)
 * - TIMELOCK reduzido (5 minutos)
 * - Funções de teste habilitadas
 * - Configurações relaxadas para debugging
 *
 * Uso:
 *   npx hardhat run scripts/deploy-testnet.js --network arbitrumSepolia
 */

const hre = require("hardhat");

async function main() {
    console.log("\n╔═══════════════════════════════════════════════════════╗");
    console.log("║   DeltaNeutralVault TESTNET Deploy                   ║");
    console.log("║   Arbitrum Sepolia - Chain ID 421614                 ║");
    console.log("╚═══════════════════════════════════════════════════════╝\n");

    // =====================================================
    // VERIFICAR NETWORK
    // =====================================================

    const network = await hre.ethers.provider.getNetwork();
    console.log(`📡 Network: ${network.name}`);
    console.log(`🆔 Chain ID: ${network.chainId}`);

    if (network.chainId !== 421614n) {
        console.error("\n❌ ERRO: Este script só pode ser usado no Arbitrum Sepolia (Chain ID 421614)!");
        console.error("   Use: npx hardhat run scripts/deploy-testnet.js --network arbitrumSepolia\n");
        process.exit(1);
    }

    // =====================================================
    // CONFIGURAÇÃO - ARBITRUM SEPOLIA
    // =====================================================

    console.log("\n📋 Configuração Testnet:");
    console.log("────────────────────────────────────────────────────────");

    const config = {
        // Asset base (WETH no Arbitrum Sepolia)
        asset: "0x980B62Da83eFf3D4576C647993b0c1D7faf17c73", // WETH Arbitrum Sepolia

        // Tokens do par (WETH/USDC)
        token0: "0x980B62Da83eFf3D4576C647993b0c1D7faf17c73", // WETH
        token1: "0x75faf114eafb1BDbe2F0316DF893fd58CE46AA4d", // USDC (testnet)

        // Uniswap v3 Arbitrum Sepolia
        uniswapPool: "0x0000000000000000000000000000000000000000", // TODO: Verificar pool real
        positionManager: "0xC36442b4a4522E871399CD717aBDD847Ab11FE88", // NonfungiblePositionManager
        swapRouter: "0x101F443B4d1b059569D643917553c771E1b9663E", // SwapRouter

        // 1inch (usar Uniswap se não houver 1inch em testnet)
        oneInchRouter: "0x101F443B4d1b059569D643917553c771E1b9663E", // Fallback para SwapRouter

        // Chainlink Price Feed BTC/USD Arbitrum Sepolia
        chainlinkPriceFeed: "0x56a43EB56Da12C0dc1D972ACb089c06a5dEF8e69",

        // Treasury (deployer por padrão)
        treasury: "", // Será preenchido com deployer

        // Fees iniciais (basis points)
        fees: {
            performance: 1000,  // 10% (max 15% em testnet)
            management: 500,    // 5% (max 10%)
            entry: 0,           // 0% (fixo)
            exit: 0,            // 0% (fixo)
            swap: 500,          // 5% (max 10%)
            keeper: 300         // 3% (max 5%)
        }
    };

    // =====================================================
    // DEPLOYER INFO
    // =====================================================

    const [deployer] = await hre.ethers.getSigners();
    console.log(`\n👤 Deployer: ${deployer.address}`);

    const balance = await hre.ethers.provider.getBalance(deployer.address);
    console.log(`💰 Saldo: ${hre.ethers.formatEther(balance)} ETH`);

    if (balance < hre.ethers.parseEther("0.01")) {
        console.warn("\n⚠️  AVISO: Saldo baixo! Pegue mais ETH no faucet:");
        console.warn("   https://www.alchemy.com/faucets/arbitrum-sepolia\n");
    }

    // Treasury = deployer se não especificado
    if (!config.treasury) {
        config.treasury = deployer.address;
    }

    // =====================================================
    // VERIFICAR POOL UNISWAP
    // =====================================================

    console.log("\n🔍 Verificando pool Uniswap...");

    if (config.uniswapPool === "0x0000000000000000000000000000000000000000") {
        console.log("\n⚠️  Pool Uniswap não configurado!");
        console.log("   Opções:");
        console.log("   1. Criar pool WETH/USDC no Uniswap v3 Arbitrum Sepolia");
        console.log("   2. Usar pool existente e atualizar endereço no script");
        console.log("\n   Para criar pool:");
        console.log("   - Visite: https://app.uniswap.org");
        console.log("   - Conecte na Arbitrum Sepolia");
        console.log("   - Crie pool WETH/USDC com fee 0.3%");
        console.log("   - Adicione liquidez inicial");
        console.log("   - Copie endereço do pool\n");

        // Por enquanto, continuar (pode dar erro no constructor)
        console.log("⏭️  Continuando deploy (pode falhar se pool não existir)...\n");
    }

    // =====================================================
    // DEPLOY CONTRATO TESTNET
    // =====================================================

    console.log("\n📦 Deploying DeltaNeutralVaultV1Testnet...");
    console.log("────────────────────────────────────────────────────────");

    const DeltaNeutralVaultTestnet = await hre.ethers.getContractFactory("DeltaNeutralVaultV1Testnet");

    console.log("⏳ Aguardando deploy...");

    const vault = await DeltaNeutralVaultTestnet.deploy(
        config.asset,
        config.token0,
        config.token1,
        config.uniswapPool,
        config.positionManager,
        config.swapRouter,
        config.oneInchRouter,
        config.chainlinkPriceFeed,
        config.treasury
    );

    await vault.waitForDeployment();
    const vaultAddress = await vault.getAddress();

    console.log(`✅ Vault deployed: ${vaultAddress}`);

    // =====================================================
    // CONFIGURAR FEES
    // =====================================================

    console.log("\n⚙️  Configurando fees...");

    const tx = await vault.setFees(
        config.fees.performance,
        config.fees.management,
        config.fees.entry,
        config.fees.exit,
        config.fees.swap,
        config.fees.keeper
    );
    await tx.wait();

    console.log("✅ Fees configuradas:");
    console.log(`   - Performance: ${config.fees.performance / 100}%`);
    console.log(`   - Management: ${config.fees.management / 100}%`);
    console.log(`   - Entry: ${config.fees.entry / 100}%`);
    console.log(`   - Exit: ${config.fees.exit / 100}%`);
    console.log(`   - Swap: ${config.fees.swap / 100}%`);
    console.log(`   - Keeper: ${config.fees.keeper / 100}%`);

    // =====================================================
    // CONFIGURAR KEEPER (deployer inicial)
    // =====================================================

    console.log("\n🤖 Configurando keeper...");

    const txKeeper = await vault.setKeeper(deployer.address);
    await txKeeper.wait();

    console.log(`✅ Keeper configurado: ${deployer.address}`);
    console.log("   (Você pode mudar depois com vault.setKeeper())");

    // =====================================================
    // INFORMAÇÕES TESTNET
    // =====================================================

    console.log("\n📊 Configurações TESTNET ativas:");
    console.log("────────────────────────────────────────────────────────");
    console.log(`   MIN_DEPOSIT: ${hre.ethers.formatEther("100000000000000")} ETH (0.0001)`);
    console.log(`   TIMELOCK: 5 minutes (vs 2 days produção)`);
    console.log(`   MAX_SLIPPAGE: 10% (vs 3% produção)`);
    console.log("\n🧪 Funções de teste disponíveis:");
    console.log("   - testnet_emergencyWithdrawAll()");
    console.log("   - testnet_forceRebalance(price, tickL, tickU)");
    console.log("   - testnet_simulateRebalance(price)");
    console.log("   - testnet_accrueManagementFee(seconds)");
    console.log("   - testnet_getPositionInfo()");
    console.log("   - testnet_resetHighWaterMark()");

    // =====================================================
    // RESUMO FINAL
    // =====================================================

    console.log("\n╔═══════════════════════════════════════════════════════╗");
    console.log("║   ✅ DEPLOY TESTNET COMPLETO!                        ║");
    console.log("╚═══════════════════════════════════════════════════════╝\n");

    console.log("📝 Salve estas informações:\n");
    console.log("────────────────────────────────────────────────────────");
    console.log(`Vault Address: ${vaultAddress}`);
    console.log(`Network: Arbitrum Sepolia (${network.chainId})`);
    console.log(`Deployer: ${deployer.address}`);
    console.log(`Treasury: ${config.treasury}`);
    console.log(`Keeper: ${deployer.address}`);
    console.log("────────────────────────────────────────────────────────");

    console.log("\n📋 Próximos passos:\n");
    console.log("1️⃣  Configurar keeper bot:");
    console.log(`   cd keeper-bot`);
    console.log(`   cp .env.testnet .env`);
    console.log(`   nano .env  # Adicionar VAULT_ADDRESS=${vaultAddress}`);
    console.log("");
    console.log("2️⃣  Testar funções testnet:");
    console.log(`   npx hardhat console --network arbitrumSepolia`);
    console.log(`   > const vault = await ethers.getContractAt("DeltaNeutralVaultV1Testnet", "${vaultAddress}")`);
    console.log(`   > await vault.testnet_getPositionInfo()`);
    console.log("");
    console.log("3️⃣  Verificar contrato no Arbiscan:");
    console.log(`   npx hardhat verify --network arbitrumSepolia ${vaultAddress} \\\n     "${config.asset}" "${config.token0}" "${config.token1}" \\\n     "${config.uniswapPool}" "${config.positionManager}" \\\n     "${config.swapRouter}" "${config.oneInchRouter}" \\\n     "${config.chainlinkPriceFeed}" "${config.treasury}"`);
    console.log("");
    console.log("4️⃣  Depositar fundos de teste:");
    console.log(`   # Primeiro aprovar WETH`);
    console.log(`   # Depois deposit(amount, receiver)`);
    console.log("");
    console.log("5️⃣  Rodar keeper bot:");
    console.log(`   cd keeper-bot`);
    console.log(`   DRY_RUN=true npm start  # Testar primeiro!`);
    console.log("");

    console.log("🆘 Suporte:");
    console.log("   - Explorer: https://sepolia.arbiscan.io");
    console.log("   - Faucet: https://www.alchemy.com/faucets/arbitrum-sepolia");
    console.log("   - Docs: ../TESTNET_GUIDE.md");
    console.log("");

    // =====================================================
    // SALVAR DEPLOYMENT INFO
    // =====================================================

    const deploymentInfo = {
        network: "arbitrum-sepolia",
        chainId: Number(network.chainId),
        vault: vaultAddress,
        deployer: deployer.address,
        treasury: config.treasury,
        keeper: deployer.address,
        config: config,
        timestamp: new Date().toISOString(),
        blockNumber: await hre.ethers.provider.getBlockNumber()
    };

    const fs = require("fs");
    const path = require("path");

    const deployDir = path.join(__dirname, "../deployments");
    if (!fs.existsSync(deployDir)) {
        fs.mkdirSync(deployDir, { recursive: true });
    }

    const filename = `testnet-${Date.now()}.json`;
    fs.writeFileSync(
        path.join(deployDir, filename),
        JSON.stringify(deploymentInfo, null, 2)
    );

    console.log(`💾 Deployment info salvo em: deployments/${filename}\n`);
}

// =====================================================
// ERROR HANDLING
// =====================================================

main()
    .then(() => process.exit(0))
    .catch((error) => {
        console.error("\n❌ ERRO NO DEPLOY:\n");
        console.error(error);

        console.log("\n🔧 Troubleshooting:\n");
        console.log("1. Verifique se tem saldo suficiente (min 0.01 ETH)");
        console.log("2. Verifique se está usando --network arbitrumSepolia");
        console.log("3. Verifique se PRIVATE_KEY está correto no .env");
        console.log("4. Verifique se pool Uniswap existe (pode precisar criar)");
        console.log("5. Consulte logs detalhados acima\n");

        process.exit(1);
    });
