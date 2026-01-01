// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "./DeltaNeutralVaultV1.sol";

/**
 * @title DeltaNeutralVaultV1Testnet
 * @notice Versão TESTNET do DeltaNeutralVault com funções de teste adicionais
 * @dev ⚠️ APENAS PARA DEVNET (Arbitrum Sepolia) - NUNCA USAR EM PRODUÇÃO!
 *
 * Alterações para facilitar desenvolvimento:
 * - MIN_DEPOSIT reduzido para 0.0001 ETH (vs 0.01 ETH produção)
 * - TIMELOCK_DURATION reduzido para 5 minutos (vs 2 dias produção)
 * - Slippage relaxado para 10% (vs 3% produção)
 * - Funções de emergency withdraw e force rebalance
 * - Funções de simulação (view-only)
 * - Debug events detalhados
 * - Aceleração de management fees para testes
 */
contract DeltaNeutralVaultV1Testnet is DeltaNeutralVaultV1 {

    // ============================================
    // CONSTANTES TESTNET (sobrescrevem produção)
    // ============================================

    /// @notice Depósito mínimo reduzido para facilitar testes com faucet
    uint256 public constant MIN_DEPOSIT_TESTNET = 0.0001 ether; // ~$0.20

    /// @notice Timelock reduzido para testes rápidos de fees
    uint256 public constant TIMELOCK_TESTNET = 5 minutes;

    /// @notice Slippage relaxado para testnet (menos falhas)
    uint256 public constant MAX_SLIPPAGE_TESTNET = 1000; // 10%

    /// @notice ChainID do Arbitrum Sepolia
    uint256 public constant ARBITRUM_SEPOLIA_CHAINID = 421614;

    // ============================================
    // EVENTOS DE DEBUG
    // ============================================

    event TestnetEmergencyWithdraw(
        uint256 amount0,
        uint256 amount1,
        address recipient
    );

    event TestnetForceRebalance(
        int24 oldTickLower,
        int24 oldTickUpper,
        int24 newTickLower,
        int24 newTickUpper,
        uint256 priceUsed
    );

    event TestnetManagementFeeAccrued(
        uint256 feeAmount,
        uint256 sharesMinted,
        uint256 simulatedSeconds
    );

    event DebugRebalance(
        int24 oldTickLower,
        int24 oldTickUpper,
        int24 newTickLower,
        int24 newTickUpper,
        int24 currentTick,
        uint256 priceUsed
    );

    event DebugSwap(
        address tokenIn,
        address tokenOut,
        uint256 amountIn,
        uint256 amountOut,
        uint256 slippageBps
    );

    event DebugLiquidity(
        uint128 liquidityBefore,
        uint128 liquidityAfter,
        uint256 amount0,
        uint256 amount1
    );

    // ============================================
    // MODIFIERS
    // ============================================

    /// @notice Garante que função só pode ser chamada em Arbitrum Sepolia
    modifier onlyTestnet() {
        require(
            block.chainid == ARBITRUM_SEPOLIA_CHAINID,
            "TestnetOnly: Must be Arbitrum Sepolia"
        );
        _;
    }

    // ============================================
    // CONSTRUCTOR
    // ============================================

    constructor(
        address _asset,
        address _token0,
        address _token1,
        address _uniswapPool,
        address _positionManager,
        address _swapRouter,
        address _oneInchRouter,
        address _chainlinkPriceFeed,
        address _treasury
    ) DeltaNeutralVaultV1(
        _asset,
        _token0,
        _token1,
        _uniswapPool,
        _positionManager,
        _swapRouter,
        _oneInchRouter,
        _chainlinkPriceFeed,
        _treasury
    ) {
        require(
            block.chainid == ARBITRUM_SEPOLIA_CHAINID,
            "TestnetVault: Deploy only on Arbitrum Sepolia"
        );
    }

    // ============================================
    // SOBRESCRITAS (VALORES TESTNET)
    // ============================================

    /// @notice Retorna depósito mínimo (menor em testnet)
    function getMinDeposit() public pure returns (uint256) {
        return MIN_DEPOSIT_TESTNET;
    }

    /// @notice Retorna timelock duration (menor em testnet)
    function getTimelockDuration() public pure returns (uint256) {
        return TIMELOCK_TESTNET;
    }

    /// @notice Retorna max slippage (maior em testnet para evitar falhas)
    function getMaxSlippage() public pure returns (uint256) {
        return MAX_SLIPPAGE_TESTNET;
    }

    // ============================================
    // FUNÇÕES DE TESTE (APENAS TESTNET)
    // ============================================

    /**
     * @notice Emergency withdraw ALL - extrai TUDO do vault
     * @dev ⚠️ APENAS TESTNET - Use para recuperar fundos após testes
     * @dev Withdraw da posição Uniswap + transfer de todos os tokens
     */
    function testnet_emergencyWithdrawAll() external onlyOwner onlyTestnet {
        // 1. Exit da posição Uniswap se existir
        if (tokenId != 0) {
            // Get current liquidity
            (
                ,
                ,
                ,
                ,
                ,
                ,
                ,
                uint128 liquidity,
                ,
                ,
                ,
            ) = positionManager.positions(tokenId);

            if (liquidity > 0) {
                // Decrease liquidity (slippage ilimitado para testes)
                positionManager.decreaseLiquidity(
                    INonfungiblePositionManager.DecreaseLiquidityParams({
                        tokenId: tokenId,
                        liquidity: liquidity,
                        amount0Min: 0,
                        amount1Min: 0,
                        deadline: block.timestamp
                    })
                );

                // Collect tokens
                positionManager.collect(
                    INonfungiblePositionManager.CollectParams({
                        tokenId: tokenId,
                        recipient: address(this),
                        amount0Max: type(uint128).max,
                        amount1Max: type(uint128).max
                    })
                );
            }

            // Burn NFT
            positionManager.burn(tokenId);
            tokenId = 0;
        }

        // 2. Transfer todos os tokens para owner
        uint256 balance0 = IERC20(token0).balanceOf(address(this));
        uint256 balance1 = IERC20(token1).balanceOf(address(this));

        if (balance0 > 0) {
            IERC20(token0).safeTransfer(owner(), balance0);
        }
        if (balance1 > 0) {
            IERC20(token1).safeTransfer(owner(), balance1);
        }

        emit TestnetEmergencyWithdraw(balance0, balance1, owner());
    }

    /**
     * @notice Force rebalance SEM validações - útil para testar ranges específicos
     * @dev ⚠️ APENAS TESTNET - Permite rebalance manual sem checks
     * @param targetPrice Preço alvo para calcular range (em USD com 8 decimals)
     * @param newTickLower Novo tick lower (deve ser múltiplo de tickSpacing)
     * @param newTickUpper Novo tick upper (deve ser múltiplo de tickSpacing)
     */
    function testnet_forceRebalance(
        uint256 targetPrice,
        int24 newTickLower,
        int24 newTickUpper
    ) external onlyOwner onlyTestnet {
        // Guardar ticks antigos para evento
        int24 oldTickLower = tickLower;
        int24 oldTickUpper = tickUpper;

        // 1. Exit da posição atual (se existir)
        if (tokenId != 0) {
            // Get current liquidity
            (
                ,
                ,
                ,
                ,
                ,
                ,
                ,
                uint128 liquidity,
                ,
                ,
                ,
            ) = positionManager.positions(tokenId);

            if (liquidity > 0) {
                // Decrease liquidity com slippage ilimitado
                positionManager.decreaseLiquidity(
                    INonfungiblePositionManager.DecreaseLiquidityParams({
                        tokenId: tokenId,
                        liquidity: liquidity,
                        amount0Min: 0,
                        amount1Min: 0,
                        deadline: block.timestamp
                    })
                );

                // Collect
                positionManager.collect(
                    INonfungiblePositionManager.CollectParams({
                        tokenId: tokenId,
                        recipient: address(this),
                        amount0Max: type(uint128).max,
                        amount1Max: type(uint128).max
                    })
                );
            }

            // Burn old position
            positionManager.burn(tokenId);
        }

        // 2. Atualizar range
        tickLower = newTickLower;
        tickUpper = newTickUpper;

        // 3. Criar nova posição com range customizado
        uint256 balance0 = IERC20(token0).balanceOf(address(this));
        uint256 balance1 = IERC20(token1).balanceOf(address(this));

        require(balance0 > 0 || balance1 > 0, "No tokens to reenter");

        // Approve tokens
        if (balance0 > 0) {
            IERC20(token0).safeApprove(address(positionManager), balance0);
        }
        if (balance1 > 0) {
            IERC20(token1).safeApprove(address(positionManager), balance1);
        }

        // Mint new position
        (uint256 newTokenId, , , ) = positionManager.mint(
            INonfungiblePositionManager.MintParams({
                token0: token0,
                token1: token1,
                fee: uniswapPool.fee(),
                tickLower: newTickLower,
                tickUpper: newTickUpper,
                amount0Desired: balance0,
                amount1Desired: balance1,
                amount0Min: 0, // Slippage ilimitado para testes
                amount1Min: 0,
                recipient: address(this),
                deadline: block.timestamp
            })
        );

        tokenId = newTokenId;

        emit TestnetForceRebalance(
            oldTickLower,
            oldTickUpper,
            newTickLower,
            newTickUpper,
            targetPrice
        );
    }

    /**
     * @notice Simula rebalance SEM executar (view-only - não gasta gas!)
     * @dev Útil para testar parâmetros antes de executar rebalance real
     * @param targetPrice Preço alvo em USD (8 decimals)
     * @return suggestedTickLower Tick lower sugerido
     * @return suggestedTickUpper Tick upper sugerido
     * @return estimatedAmount0 Quantidade estimada de token0 necessária
     * @return estimatedAmount1 Quantidade estimada de token1 necessária
     * @return needsRebalance Se posição atual precisa de rebalance
     */
    function testnet_simulateRebalance(
        uint256 targetPrice
    ) external view onlyTestnet returns (
        int24 suggestedTickLower,
        int24 suggestedTickUpper,
        uint256 estimatedAmount0,
        uint256 estimatedAmount1,
        bool needsRebalance
    ) {
        // Calcular tick baseado no preço
        // targetPrice está em USD com 8 decimals
        // Precisamos converter para sqrtPriceX96

        // Simplificação: usar range de ±10% (~200 ticks)
        int24 tickAtPrice = _estimateTickFromPrice(targetPrice);

        // Range sugerido
        int24 tickSpacing = uniswapPool.tickSpacing();
        suggestedTickLower = ((tickAtPrice - 200) / tickSpacing) * tickSpacing;
        suggestedTickUpper = ((tickAtPrice + 200) / tickSpacing) * tickSpacing;

        // Estimar distribuição de tokens (50/50 simplificado)
        uint256 totalValue = totalAssets();
        estimatedAmount0 = totalValue / 2;
        estimatedAmount1 = totalValue / 2;

        // Verificar se precisa rebalance
        (uint160 sqrtPriceX96, int24 currentTick, , , , , ) = uniswapPool.slot0();
        needsRebalance = currentTick < tickLower || currentTick > tickUpper;

        return (
            suggestedTickLower,
            suggestedTickUpper,
            estimatedAmount0,
            estimatedAmount1,
            needsRebalance
        );
    }

    /**
     * @notice Acelera accrual de management fee (simula tempo passando)
     * @dev ⚠️ APENAS TESTNET - Use para testar accrual de fees sem esperar
     * @param secondsToAccrue Quantidade de segundos para simular
     */
    function testnet_accrueManagementFee(
        uint256 secondsToAccrue
    ) external onlyOwner onlyTestnet {
        // Simular que tempo passou
        uint256 simulatedTimestamp = lastManagementFeeTimestamp + secondsToAccrue;

        uint256 totalAssetValue = totalAssets();
        uint256 timeElapsed = simulatedTimestamp - lastManagementFeeTimestamp;

        // Calcular fee: (totalAssets * feeBps * timeElapsed) / (10000 * 365 days)
        uint256 feeAmount = (totalAssetValue * managementFeeBps * timeElapsed)
                            / (10000 * 365 days);

        if (feeAmount > 0) {
            // Mint shares para treasury
            uint256 sharesToMint = convertToShares(feeAmount);
            _mint(treasury, sharesToMint);

            // Atualizar timestamp
            lastManagementFeeTimestamp = simulatedTimestamp;

            emit TestnetManagementFeeAccrued(feeAmount, sharesToMint, secondsToAccrue);
        }
    }

    /**
     * @notice Get informações detalhadas da posição (debug)
     * @dev View-only - útil para debugging
     */
    function testnet_getPositionInfo() external view onlyTestnet returns (
        uint256 _tokenId,
        int24 _tickLower,
        int24 _tickUpper,
        int24 _currentTick,
        uint128 _liquidity,
        uint256 _balance0,
        uint256 _balance1,
        bool _inRange
    ) {
        _tokenId = tokenId;
        _tickLower = tickLower;
        _tickUpper = tickUpper;
        _balance0 = IERC20(token0).balanceOf(address(this));
        _balance1 = IERC20(token1).balanceOf(address(this));

        if (tokenId != 0) {
            (
                ,
                ,
                ,
                ,
                ,
                ,
                ,
                uint128 liq,
                ,
                ,
                ,
            ) = positionManager.positions(tokenId);
            _liquidity = liq;
        }

        (, int24 tick, , , , , ) = uniswapPool.slot0();
        _currentTick = tick;
        _inRange = tick >= tickLower && tick <= tickUpper;

        return (
            _tokenId,
            _tickLower,
            _tickUpper,
            _currentTick,
            _liquidity,
            _balance0,
            _balance1,
            _inRange
        );
    }

    /**
     * @notice Zera high water mark (útil para resetar testes de performance fee)
     */
    function testnet_resetHighWaterMark() external onlyOwner onlyTestnet {
        highWaterMark = 0;
    }

    // ============================================
    // HELPERS INTERNOS
    // ============================================

    /**
     * @notice Estima tick baseado em preço USD (simplificado)
     * @dev Não é exato - apenas para simulação
     */
    function _estimateTickFromPrice(uint256 priceUSD) internal pure returns (int24) {
        // Simplificação grosseira: assumir que cada tick = ~0.01% de variação
        // log(1.0001) ≈ 0.0001
        // Para preço de $95,000:
        // tick ≈ log(price) / log(1.0001)

        // Aproximação linear para testes
        // Assumindo preço base de $1000 = tick 0
        int256 tickEstimate = int256(priceUSD / 100);

        return int24(tickEstimate);
    }
}
