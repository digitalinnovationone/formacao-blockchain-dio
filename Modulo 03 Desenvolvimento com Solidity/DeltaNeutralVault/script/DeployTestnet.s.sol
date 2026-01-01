// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "forge-std/Script.sol";
import "forge-std/console.sol";
import "../DeltaNeutralVaultV1Testnet.sol";

/**
 * @title DeployTestnetScript
 * @notice Script de deploy para DeltaNeutralVaultV1Testnet no Arbitrum Sepolia
 * @dev APENAS ARBITRUM SEPOLIA (Chain ID 421614)
 *
 * Uso:
 *   forge script script/DeployTestnet.s.sol:DeployTestnetScript \
 *     --rpc-url arbitrum_sepolia \
 *     --broadcast \
 *     --verify \
 *     -vvvv
 *
 * Dry run (simulação):
 *   forge script script/DeployTestnet.s.sol:DeployTestnetScript \
 *     --rpc-url arbitrum_sepolia \
 *     -vvvv
 */
contract DeployTestnetScript is Script {

    // =====================================================
    // CONFIGURAÇÃO - ARBITRUM SEPOLIA
    // =====================================================

    // Arbitrum Sepolia Chain ID
    uint256 constant ARBITRUM_SEPOLIA_CHAIN_ID = 421614;

    // Asset base (WETH)
    address constant WETH = 0x980B62Da83eFf3D4576C647993b0c1D7faf17c73;

    // Tokens do par
    address constant TOKEN0 = 0x980B62Da83eFf3D4576C647993b0c1D7faf17c73; // WETH
    address constant TOKEN1 = 0x75faf114eafb1BDbe2F0316DF893fd58CE46AA4d; // USDC testnet

    // Uniswap v3 Arbitrum Sepolia
    address constant UNISWAP_POOL = 0x0000000000000000000000000000000000000000; // TODO: Pool real
    address constant POSITION_MANAGER = 0xC36442b4a4522E871399CD717aBDD847Ab11FE88;
    address constant SWAP_ROUTER = 0x101F443B4d1b059569D643917553c771E1b9663E;

    // 1inch (usar Uniswap como fallback em testnet)
    address constant ONEINCH_ROUTER = 0x101F443B4d1b059569D643917553c771E1b9663E;

    // Chainlink BTC/USD Arbitrum Sepolia
    address constant CHAINLINK_FEED = 0x56a43EB56Da12C0dc1D972ACb089c06a5dEF8e69;

    // Fees iniciais (basis points)
    uint16 constant PERFORMANCE_FEE = 1000;  // 10% (max 15%)
    uint16 constant MANAGEMENT_FEE = 500;    // 5% (max 10%)
    uint16 constant ENTRY_FEE = 0;           // 0% (fixo)
    uint16 constant EXIT_FEE = 0;            // 0% (fixo)
    uint16 constant SWAP_FEE = 500;          // 5% (max 10%)
    uint16 constant KEEPER_FEE = 300;        // 3% (max 5%)

    // =====================================================
    // MAIN DEPLOY FUNCTION
    // =====================================================

    function run() external {
        // Header
        console.log("");
        console.log("========================================================");
        console.log("   DeltaNeutralVault TESTNET Deploy - Foundry");
        console.log("   Arbitrum Sepolia - Chain ID 421614");
        console.log("========================================================");
        console.log("");

        // Verificar chain ID
        uint256 chainId = block.chainid;
        console.log("Chain ID:", chainId);

        if (chainId != ARBITRUM_SEPOLIA_CHAIN_ID) {
            console.log("");
            console.log("ERROR: Este script so funciona no Arbitrum Sepolia!");
            console.log("Chain ID esperado: 421614");
            console.log("Chain ID atual:", chainId);
            console.log("");
            revert("Wrong network");
        }

        // Get deployer
        uint256 deployerPrivateKey = vm.envUint("PRIVATE_KEY");
        address deployer = vm.addr(deployerPrivateKey);
        address treasury = deployer; // Treasury = deployer

        console.log("Deployer:", deployer);
        console.log("Balance:", deployer.balance / 1e18, "ETH");
        console.log("Treasury:", treasury);
        console.log("");

        // Verificar saldo mínimo
        if (deployer.balance < 0.01 ether) {
            console.log("WARNING: Saldo baixo! Pegue mais ETH:");
            console.log("https://www.alchemy.com/faucets/arbitrum-sepolia");
            console.log("");
        }

        // Verificar pool
        if (UNISWAP_POOL == address(0)) {
            console.log("WARNING: Pool Uniswap nao configurado!");
            console.log("Pode ser necessario criar pool WETH/USDC primeiro.");
            console.log("Continuando deploy (pode falhar)...");
            console.log("");
        }

        // =====================================================
        // DEPLOY
        // =====================================================

        console.log("Deploying DeltaNeutralVaultV1Testnet...");
        console.log("--------------------------------------------------------");

        vm.startBroadcast(deployerPrivateKey);

        DeltaNeutralVaultV1Testnet vault = new DeltaNeutralVaultV1Testnet(
            WETH,
            TOKEN0,
            TOKEN1,
            UNISWAP_POOL,
            POSITION_MANAGER,
            SWAP_ROUTER,
            ONEINCH_ROUTER,
            CHAINLINK_FEED,
            treasury
        );

        console.log("Vault deployed:", address(vault));
        console.log("");

        // =====================================================
        // CONFIGURAR FEES
        // =====================================================

        console.log("Configurando fees...");

        vault.setFees(
            PERFORMANCE_FEE,
            MANAGEMENT_FEE,
            ENTRY_FEE,
            EXIT_FEE,
            SWAP_FEE,
            KEEPER_FEE
        );

        console.log("Fees configuradas:");
        console.log("  - Performance:", PERFORMANCE_FEE / 100, "%");
        console.log("  - Management:", MANAGEMENT_FEE / 100, "%");
        console.log("  - Entry:", ENTRY_FEE / 100, "%");
        console.log("  - Exit:", EXIT_FEE / 100, "%");
        console.log("  - Swap:", SWAP_FEE / 100, "%");
        console.log("  - Keeper:", KEEPER_FEE / 100, "%");
        console.log("");

        // =====================================================
        // CONFIGURAR KEEPER
        // =====================================================

        console.log("Configurando keeper...");

        vault.setKeeper(deployer);

        console.log("Keeper configurado:", deployer);
        console.log("(Mude depois com vault.setKeeper())");
        console.log("");

        vm.stopBroadcast();

        // =====================================================
        // INFORMAÇÕES TESTNET
        // =====================================================

        console.log("Configuracoes TESTNET ativas:");
        console.log("--------------------------------------------------------");
        console.log("  MIN_DEPOSIT: 0.0001 ETH");
        console.log("  TIMELOCK: 5 minutes");
        console.log("  MAX_SLIPPAGE: 10%");
        console.log("");
        console.log("Funcoes de teste disponiveis:");
        console.log("  - testnet_emergencyWithdrawAll()");
        console.log("  - testnet_forceRebalance(price, tickL, tickU)");
        console.log("  - testnet_simulateRebalance(price)");
        console.log("  - testnet_accrueManagementFee(seconds)");
        console.log("  - testnet_getPositionInfo()");
        console.log("  - testnet_resetHighWaterMark()");
        console.log("");

        // =====================================================
        // RESUMO FINAL
        // =====================================================

        console.log("========================================================");
        console.log("   DEPLOY TESTNET COMPLETO!");
        console.log("========================================================");
        console.log("");
        console.log("Salve estas informacoes:");
        console.log("--------------------------------------------------------");
        console.log("Vault Address:", address(vault));
        console.log("Network: Arbitrum Sepolia (421614)");
        console.log("Deployer:", deployer);
        console.log("Treasury:", treasury);
        console.log("Keeper:", deployer);
        console.log("--------------------------------------------------------");
        console.log("");

        // =====================================================
        // PRÓXIMOS PASSOS
        // =====================================================

        console.log("Proximos passos:");
        console.log("");
        console.log("1. Configurar keeper bot:");
        console.log("   cd keeper-bot");
        console.log("   cp .env.testnet .env");
        console.log("   nano .env  # Adicionar VAULT_ADDRESS");
        console.log("");
        console.log("2. Verificar contrato (se usou --verify):");
        console.log("   https://sepolia.arbiscan.io/address/%s", address(vault));
        console.log("");
        console.log("3. Testar funcoes testnet:");
        console.log("   cast call %s \"testnet_getPositionInfo()\" --rpc-url arbitrum_sepolia", address(vault));
        console.log("");
        console.log("4. Depositar fundos de teste:");
        console.log("   # Primeiro aprovar WETH");
        console.log("   # Depois deposit(amount, receiver)");
        console.log("");
        console.log("5. Rodar keeper bot:");
        console.log("   cd keeper-bot");
        console.log("   DRY_RUN=true npm start");
        console.log("");
        console.log("Suporte:");
        console.log("  - Explorer: https://sepolia.arbiscan.io");
        console.log("  - Faucet: https://www.alchemy.com/faucets/arbitrum-sepolia");
        console.log("  - Docs: ../TESTNET_GUIDE.md");
        console.log("");

        // Salvar deployment info em arquivo
        _saveDeploymentInfo(address(vault), deployer, treasury);
    }

    // =====================================================
    // HELPER: SALVAR DEPLOYMENT INFO
    // =====================================================

    function _saveDeploymentInfo(
        address vaultAddress,
        address deployer,
        address treasury
    ) internal {
        string memory json = "deployment";

        vm.serializeString(json, "network", "arbitrum-sepolia");
        vm.serializeUint(json, "chainId", ARBITRUM_SEPOLIA_CHAIN_ID);
        vm.serializeAddress(json, "vault", vaultAddress);
        vm.serializeAddress(json, "deployer", deployer);
        vm.serializeAddress(json, "treasury", treasury);
        vm.serializeAddress(json, "keeper", deployer);
        vm.serializeUint(json, "timestamp", block.timestamp);
        string memory finalJson = vm.serializeUint(json, "blockNumber", block.number);

        string memory filename = string.concat(
            "deployments/testnet-foundry-",
            vm.toString(block.timestamp),
            ".json"
        );

        vm.writeJson(finalJson, filename);

        console.log("Deployment info salvo em:", filename);
        console.log("");
    }
}
