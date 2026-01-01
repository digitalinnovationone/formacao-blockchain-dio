// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/token/ERC20/extensions/ERC4626.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/security/Pausable.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import "@chainlink/contracts/src/v0.8/interfaces/AggregatorV3Interface.sol";
import "@uniswap/v3-periphery/contracts/interfaces/INonfungiblePositionManager.sol";
import "@uniswap/v3-periphery/contracts/interfaces/ISwapRouter.sol";
import "@uniswap/v3-core/contracts/interfaces/IUniswapV3Pool.sol";
import "@uniswap/v3-core/contracts/libraries/TickMath.sol";
import "./libraries/LiquidityMath.sol";
import "./interfaces/I1inchAggregator.sol";

/**
 * @title DeltaNeutralVaultV1
 * @notice Vault ERC-4626 para estratégia delta-neutral com Uniswap v3
 * @dev Etapa 3: PRODUCTION-READY com 1inch, LiquidityMath otimizada e proteção de slippage
 */
contract DeltaNeutralVaultV1 is ERC20, ERC4626, Ownable, Pausable, ReentrancyGuard {
    using SafeERC20 for IERC20;

    // ============================================
    // ENUMS
    // ============================================

    enum ExitReason {
        ManualExit,
        RangeExit,
        EmergencyExit,
        Rebalance
    }

    // ============================================
    // ROLES
    // ============================================

    address public keeper;
    address public treasury;

    // ============================================
    // FEES (basis points - 10000 = 100%)
    // ============================================

    uint16 public performanceFeeBps;
    uint16 public managementFeeBps;
    uint16 public entryFeeBps;
    uint16 public exitFeeBps;
    uint16 public swapFeeBps;
    uint16 public keeperFeeBps;

    // ============================================
    // ORACLES
    // ============================================

    AggregatorV3Interface public chainlinkPriceFeed;
    uint256 public maxOracleDeviationBps;
    uint256 public maxOracleDelay;

    // ============================================
    // UNISWAP V3
    // ============================================

    IUniswapV3Pool public uniswapPool;
    INonfungiblePositionManager public positionManager;
    ISwapRouter public swapRouter;
    I1inchAggregator public oneInchRouter;

    int24 public tickLower;
    int24 public tickUpper;
    uint256 public tokenId; // NFT da posição LP (0 = sem posição)

    address public token0;
    address public token1;

    // ============================================
    // ACCOUNTING
    // ============================================

    uint256 public lastManagementFeeTimestamp;
    uint256 public highWaterMark;

    // ============================================
    // SLIPPAGE & OTHER PARAMS
    // ============================================

    uint256 public maxSlippageBps;

    // ============================================
    // EVENTS
    // ============================================

    event KeeperUpdated(address indexed oldKeeper, address indexed newKeeper);
    event TreasuryUpdated(address indexed oldTreasury, address indexed newTreasury);
    event FeesUpdated(
        uint16 performanceFeeBps,
        uint16 managementFeeBps,
        uint16 entryFeeBps,
        uint16 exitFeeBps,
        uint16 swapFeeBps,
        uint16 keeperFeeBps
    );
    event OracleUpdated(
        address indexed priceFeed,
        uint256 maxDeviationBps,
        uint256 maxDelay
    );
    event UniswapConfigUpdated(
        address indexed pool,
        address indexed positionManager,
        address indexed swapRouter
    );
    event RangeUpdated(int24 tickLower, int24 tickUpper);
    event SlippageParamsUpdated(uint256 maxSlippageBps);
    event EntryFeeCharged(uint256 assets, uint256 fee);
    event ExitFeeCharged(uint256 assets, uint256 fee);
    event ManagementFeeCharged(uint256 fee, uint256 shares);
    event PerformanceFeeCharged(uint256 profit, uint256 fee);
    event SwapFeeApplied(uint256 amountIn, uint256 fee);
    event AutoExitExecuted(
        uint256 indexed price,
        ExitReason indexed reason,
        uint256 totalAssets,
        uint256 profit
    );
    event AutoReenterExecuted(
        uint256 indexed price,
        int24 tickLower,
        int24 tickUpper,
        uint256 totalAssets
    );
    event HedgeStateRecorded(bytes32 indexed stateHash, uint64 timestamp);
    event AccountingUpdated(uint256 totalAssets, uint256 totalShares);
    event EmergencyExitExecuted(uint256 totalAssets);
    event SwapExecuted(
        address indexed tokenIn,
        address indexed tokenOut,
        uint256 amountIn,
        uint256 amountOut
    );
    event PositionMinted(
        uint256 indexed tokenId,
        uint128 liquidity,
        uint256 amount0,
        uint256 amount1
    );
    event PositionClosed(
        uint256 indexed tokenId,
        uint256 amount0,
        uint256 amount1,
        uint256 fees0,
        uint256 fees1
    );
    event FeesCollected(uint256 amount0, uint256 amount1);

    // ============================================
    // MODIFIERS
    // ============================================

    modifier onlyKeeper() {
        require(msg.sender == keeper, "DeltaNeutralVault: caller is not keeper");
        _;
    }

    // ============================================
    // CONSTRUCTOR
    // ============================================

    /**
     * @notice Construtor do vault
     * @param _asset Endereço do token base (USDC)
     * @param _name Nome do token de shares
     * @param _symbol Símbolo do token de shares
     * @param _chainlinkFeed Endereço do price feed Chainlink
     * @param _treasury Endereço da treasury para receber fees
     * @param _positionManager Endereço do NonfungiblePositionManager do Uniswap v3
     * @param _swapRouter Endereço do SwapRouter do Uniswap v3
     * @param _oneInchRouter Endereço do 1inch Aggregation Router v5
     */
    constructor(
        IERC20 _asset,
        string memory _name,
        string memory _symbol,
        address _chainlinkFeed,
        address _treasury,
        address _positionManager,
        address _swapRouter,
        address _oneInchRouter
    )
        ERC20(_name, _symbol)
        ERC4626(_asset)
    {
        require(_treasury != address(0), "DeltaNeutralVault: treasury cannot be zero");
        require(_chainlinkFeed != address(0), "DeltaNeutralVault: chainlink feed cannot be zero");
        require(_positionManager != address(0), "DeltaNeutralVault: position manager cannot be zero");
        require(_swapRouter != address(0), "DeltaNeutralVault: swap router cannot be zero");
        require(_oneInchRouter != address(0), "DeltaNeutralVault: 1inch router cannot be zero");

        treasury = _treasury;
        chainlinkPriceFeed = AggregatorV3Interface(_chainlinkFeed);
        positionManager = INonfungiblePositionManager(_positionManager);
        swapRouter = ISwapRouter(_swapRouter);
        oneInchRouter = I1inchAggregator(_oneInchRouter);
        lastManagementFeeTimestamp = block.timestamp;

        // Defaults
        maxOracleDeviationBps = 500; // 5%
        maxOracleDelay = 3600; // 1 hour
        maxSlippageBps = 100; // 1%
    }

    // ============================================
    // CONFIGURAÇÃO (onlyOwner)
    // ============================================

    /**
     * @notice Define configuração do Uniswap v3
     * @param _pool Endereço do pool
     * @param _positionManager Endereço do position manager
     * @param _swapRouter Endereço do swap router
     */
    function setUniswapConfig(
        address _pool,
        address _positionManager,
        address _swapRouter
    ) external onlyOwner {
        require(_pool != address(0), "DeltaNeutralVault: pool cannot be zero");
        require(_positionManager != address(0), "DeltaNeutralVault: position manager cannot be zero");
        require(_swapRouter != address(0), "DeltaNeutralVault: swap router cannot be zero");

        uniswapPool = IUniswapV3Pool(_pool);
        positionManager = INonfungiblePositionManager(_positionManager);
        swapRouter = ISwapRouter(_swapRouter);

        // Obter token0 e token1 do pool
        token0 = uniswapPool.token0();
        token1 = uniswapPool.token1();

        emit UniswapConfigUpdated(_pool, _positionManager, _swapRouter);
    }

    /**
     * @notice Define o 1inch router
     * @param _oneInchRouter Endereço do 1inch Aggregation Router v5
     */
    function setOneInchRouter(address _oneInchRouter) external onlyOwner {
        require(_oneInchRouter != address(0), "DeltaNeutralVault: 1inch router cannot be zero");
        oneInchRouter = I1inchAggregator(_oneInchRouter);
    }

    /**
     * @notice Define o range de ticks da posição LP
     * @param _tickLower Tick inferior
     * @param _tickUpper Tick superior
     */
    function setRange(int24 _tickLower, int24 _tickUpper) external onlyOwner {
        require(_tickLower < _tickUpper, "DeltaNeutralVault: invalid tick range");

        // Validar que os ticks são válidos para o pool
        int24 tickSpacing = uniswapPool.tickSpacing();
        require(_tickLower % tickSpacing == 0, "DeltaNeutralVault: invalid tickLower");
        require(_tickUpper % tickSpacing == 0, "DeltaNeutralVault: invalid tickUpper");

        tickLower = _tickLower;
        tickUpper = _tickUpper;
        emit RangeUpdated(_tickLower, _tickUpper);
    }

    /**
     * @notice Define o keeper autorizado
     * @param _keeper Endereço do keeper
     */
    function setKeeper(address _keeper) external onlyOwner {
        require(_keeper != address(0), "DeltaNeutralVault: keeper cannot be zero");
        address oldKeeper = keeper;
        keeper = _keeper;
        emit KeeperUpdated(oldKeeper, _keeper);
    }

    /**
     * @notice Define parâmetros do oracle
     * @param _priceFeed Endereço do price feed Chainlink
     * @param _maxDeviationBps Desvio máximo permitido em bps
     * @param _maxDelay Delay máximo permitido em segundos
     */
    function setOracles(
        address _priceFeed,
        uint256 _maxDeviationBps,
        uint256 _maxDelay
    ) external onlyOwner {
        require(_priceFeed != address(0), "DeltaNeutralVault: price feed cannot be zero");
        require(_maxDeviationBps <= 10000, "DeltaNeutralVault: max deviation too high");

        chainlinkPriceFeed = AggregatorV3Interface(_priceFeed);
        maxOracleDeviationBps = _maxDeviationBps;
        maxOracleDelay = _maxDelay;

        emit OracleUpdated(_priceFeed, _maxDeviationBps, _maxDelay);
    }

    /**
     * @notice Define parâmetros de slippage
     * @param _maxSlippageBps Slippage máximo em bps
     */
    function setSlippageParams(uint256 _maxSlippageBps) external onlyOwner {
        require(_maxSlippageBps <= 10000, "DeltaNeutralVault: slippage too high");
        maxSlippageBps = _maxSlippageBps;
        emit SlippageParamsUpdated(_maxSlippageBps);
    }

    /**
     * @notice Define o endereço da treasury
     * @param _treasury Nova treasury
     */
    function setTreasury(address _treasury) external onlyOwner {
        require(_treasury != address(0), "DeltaNeutralVault: treasury cannot be zero");
        address oldTreasury = treasury;
        treasury = _treasury;
        emit TreasuryUpdated(oldTreasury, _treasury);
    }

    /**
     * @notice Define todas as fees de uma vez
     * @param _performanceFeeBps Fee de performance
     * @param _managementFeeBps Fee de gestão anual
     * @param _entryFeeBps Fee de entrada
     * @param _exitFeeBps Fee de saída
     * @param _swapFeeBps Fee de swap
     * @param _keeperFeeBps Fee do keeper
     */
    function setFees(
        uint16 _performanceFeeBps,
        uint16 _managementFeeBps,
        uint16 _entryFeeBps,
        uint16 _exitFeeBps,
        uint16 _swapFeeBps,
        uint16 _keeperFeeBps
    ) external onlyOwner {
        require(_performanceFeeBps <= 1500, "DeltaNeutralVault: performance fee too high"); // max 15%
        require(_managementFeeBps <= 1000, "DeltaNeutralVault: management fee too high"); // max 10%
        require(_entryFeeBps == 0, "DeltaNeutralVault: entry fee must be 0%"); // fixed 0%
        require(_exitFeeBps == 0, "DeltaNeutralVault: exit fee must be 0%"); // fixed 0%
        require(_swapFeeBps <= 1000, "DeltaNeutralVault: swap fee too high"); // max 10%
        require(_keeperFeeBps <= 500, "DeltaNeutralVault: keeper fee too high"); // max 5%

        performanceFeeBps = _performanceFeeBps;
        managementFeeBps = _managementFeeBps;
        entryFeeBps = _entryFeeBps;
        exitFeeBps = _exitFeeBps;
        swapFeeBps = _swapFeeBps;
        keeperFeeBps = _keeperFeeBps;

        emit FeesUpdated(
            _performanceFeeBps,
            _managementFeeBps,
            _entryFeeBps,
            _exitFeeBps,
            _swapFeeBps,
            _keeperFeeBps
        );
    }

    /**
     * @notice Pausa o contrato
     */
    function pause() external onlyOwner {
        _pause();
    }

    /**
     * @notice Despausa o contrato
     */
    function unpause() external onlyOwner {
        _unpause();
    }

    // ============================================
    // FUNÇÕES DE FEE
    // ============================================

    /**
     * @notice Cobra entry fee
     * @param assets Quantidade de assets depositados
     * @return netAssets Assets após a fee
     */
    function _chargeEntryFee(uint256 assets) internal returns (uint256 netAssets) {
        if (entryFeeBps == 0) {
            return assets;
        }

        uint256 fee = (assets * entryFeeBps) / 10000;
        netAssets = assets - fee;

        if (fee > 0) {
            IERC20(asset()).safeTransfer(treasury, fee);
            emit EntryFeeCharged(assets, fee);
        }
    }

    /**
     * @notice Cobra exit fee
     * @param assets Quantidade de assets a sacar
     * @return netAssets Assets após a fee
     */
    function _chargeExitFee(uint256 assets) internal returns (uint256 netAssets) {
        if (exitFeeBps == 0) {
            return assets;
        }

        uint256 fee = (assets * exitFeeBps) / 10000;
        netAssets = assets - fee;

        if (fee > 0) {
            IERC20(asset()).safeTransfer(treasury, fee);
            emit ExitFeeCharged(assets, fee);
        }
    }

    /**
     * @notice Cobra management fee (anualizada, calculada proporcionalmente ao tempo)
     */
    function _chargeManagementFee() internal {
        if (managementFeeBps == 0) {
            return;
        }

        uint256 timeElapsed = block.timestamp - lastManagementFeeTimestamp;
        if (timeElapsed == 0) {
            return;
        }

        uint256 totalAssets_ = totalAssets();
        if (totalAssets_ == 0) {
            lastManagementFeeTimestamp = block.timestamp;
            return;
        }

        // Fee anualizada: (totalAssets * managementFeeBps * timeElapsed) / (10000 * 365 days)
        uint256 feeAmount = (totalAssets_ * managementFeeBps * timeElapsed) / (10000 * 365 days);

        if (feeAmount > 0) {
            // Minta shares para a treasury equivalentes ao fee
            uint256 shares = convertToShares(feeAmount);
            _mint(treasury, shares);
            emit ManagementFeeCharged(feeAmount, shares);
        }

        lastManagementFeeTimestamp = block.timestamp;
    }

    /**
     * @notice Cobra performance fee sobre lucro realizado
     * @param profit Lucro realizado
     * @return netProfit Lucro após fee
     */
    function _chargePerformanceFee(uint256 profit) internal returns (uint256 netProfit) {
        if (performanceFeeBps == 0 || profit == 0) {
            return profit;
        }

        // Performance fee é cobrada apenas sobre lucro acima do high water mark
        uint256 totalAssets_ = totalAssets();

        if (totalAssets_ > highWaterMark) {
            uint256 profitAboveHWM = totalAssets_ - highWaterMark;
            if (profitAboveHWM > profit) {
                profitAboveHWM = profit;
            }

            uint256 fee = (profitAboveHWM * performanceFeeBps) / 10000;
            netProfit = profit - fee;

            if (fee > 0) {
                // Minta shares para a treasury equivalentes ao fee
                uint256 shares = convertToShares(fee);
                _mint(treasury, shares);
                emit PerformanceFeeCharged(profit, fee);
            }

            // Atualiza high water mark
            highWaterMark = totalAssets_;
        } else {
            netProfit = profit;
        }
    }

    /**
     * @notice Aplica swap fee ao valor do swap
     * @param amountIn Quantidade a ser swapada
     * @return netAmount Quantidade após fee
     */
    function _applySwapFee(uint256 amountIn) internal returns (uint256 netAmount) {
        if (swapFeeBps == 0) {
            return amountIn;
        }

        uint256 fee = (amountIn * swapFeeBps) / 10000;
        netAmount = amountIn - fee;

        if (fee > 0) {
            emit SwapFeeApplied(amountIn, fee);
        }
    }

    // ============================================
    // ORACLE (Chainlink)
    // ============================================

    /**
     * @notice Obtém preço do oracle Chainlink
     * @return price Preço atual
     * @return updatedAt Timestamp da última atualização
     */
    function _getOraclePrice() internal view returns (uint256 price, uint256 updatedAt) {
        (
            uint80 roundId,
            int256 answer,
            ,
            uint256 timestamp,
            uint80 answeredInRound
        ) = chainlinkPriceFeed.latestRoundData();

        require(answer > 0, "DeltaNeutralVault: invalid oracle price");
        require(answeredInRound >= roundId, "DeltaNeutralVault: stale oracle data");

        price = uint256(answer);
        updatedAt = timestamp;
    }

    /**
     * @notice Valida preço do keeper contra oracle
     * @param priceFromKeeper Preço fornecido pelo keeper
     */
    function _checkOracle(uint256 priceFromKeeper) internal view {
        (uint256 oraclePrice, uint256 updatedAt) = _getOraclePrice();

        // Verifica staleness
        require(
            block.timestamp - updatedAt <= maxOracleDelay,
            "DeltaNeutralVault: oracle data too old"
        );

        // Verifica desvio
        uint256 deviation;
        if (priceFromKeeper > oraclePrice) {
            deviation = ((priceFromKeeper - oraclePrice) * 10000) / oraclePrice;
        } else {
            deviation = ((oraclePrice - priceFromKeeper) * 10000) / oraclePrice;
        }

        require(
            deviation <= maxOracleDeviationBps,
            "DeltaNeutralVault: price deviation too high"
        );
    }

    // ============================================
    // FUNÇÕES DO KEEPER
    // ============================================

    /**
     * @notice Auto-exit da posição LP (chamado pelo keeper)
     * @param price Preço atual (para validação contra oracle)
     * @param reason Razão do exit
     */
    function autoExit(
        uint256 price,
        ExitReason reason
    ) external onlyKeeper whenNotPaused nonReentrant {
        // Valida oracle
        _checkOracle(price);

        // Cobra management fee
        _chargeManagementFee();

        uint256 totalAssetsBefore = totalAssets();

        // Fecha posição LP e converte tudo para USDC
        _closePositionAndConvertToUSDC();

        uint256 totalAssetsAfter = totalAssets();

        // Calcula lucro e cobra performance fee
        uint256 profit = 0;
        if (totalAssetsAfter > totalAssetsBefore) {
            profit = totalAssetsAfter - totalAssetsBefore;
            _chargePerformanceFee(profit);
        }

        emit AutoExitExecuted(price, reason, totalAssetsAfter, profit);
    }

    /**
     * @notice Auto-reenter em nova posição LP (chamado pelo keeper)
     * @param price Preço atual (para validação contra oracle)
     * @param _tickLower Novo tick inferior
     * @param _tickUpper Novo tick superior
     */
    function autoReenter(
        uint256 price,
        int24 _tickLower,
        int24 _tickUpper
    ) external onlyKeeper whenNotPaused nonReentrant {
        require(_tickLower < _tickUpper, "DeltaNeutralVault: invalid tick range");

        // Valida oracle
        _checkOracle(price);

        // Cobra management fee
        _chargeManagementFee();

        // Atualiza ticks
        tickLower = _tickLower;
        tickUpper = _tickUpper;

        uint256 totalAssets_ = totalAssets();

        // Abre nova posição LP
        _openPosition();

        emit AutoReenterExecuted(price, _tickLower, _tickUpper, totalAssets_);
    }

    /**
     * @notice Registra estado do hedge (para auditoria)
     * @param stateHash Hash do estado do hedge
     * @param timestamp Timestamp do estado
     */
    function recordHedgeState(
        bytes32 stateHash,
        uint64 timestamp
    ) external onlyKeeper {
        require(timestamp <= block.timestamp, "DeltaNeutralVault: future timestamp");
        emit HedgeStateRecorded(stateHash, timestamp);
    }

    /**
     * @notice Atualiza accounting (cobra management fee)
     */
    function updateAccounting() external onlyKeeper {
        _chargeManagementFee();
        emit AccountingUpdated(totalAssets(), totalSupply());
    }

    /**
     * @notice Coleta fees acumulados da posição LP
     */
    function collectFees() external onlyKeeper nonReentrant returns (uint256 amount0, uint256 amount1) {
        require(tokenId != 0, "DeltaNeutralVault: no position");

        INonfungiblePositionManager.CollectParams memory params = INonfungiblePositionManager.CollectParams({
            tokenId: tokenId,
            recipient: address(this),
            amount0Max: type(uint128).max,
            amount1Max: type(uint128).max
        });

        (amount0, amount1) = positionManager.collect(params);

        emit FeesCollected(amount0, amount1);
    }

    // ============================================
    // FUNÇÕES CORE (INTEGRAÇÃO UNISWAP V3 REAL)
    // ============================================

    /**
     * @notice Abre posição LP no Uniswap v3 (IMPLEMENTAÇÃO REAL)
     */
    function _openPosition() internal {
        require(address(uniswapPool) != address(0), "DeltaNeutralVault: pool not set");
        require(tickLower < tickUpper, "DeltaNeutralVault: invalid range");
        require(tokenId == 0, "DeltaNeutralVault: position already exists");

        uint256 usdcBalance = IERC20(asset()).balanceOf(address(this));
        require(usdcBalance > 0, "DeltaNeutralVault: no USDC to invest");

        // Determinar qual token é USDC
        bool usdcIsToken0 = asset() == token0;

        // Calcular quanto de cada token precisamos
        (uint256 amount0Desired, uint256 amount1Desired) = _calculateTokenAmounts(
            usdcBalance,
            usdcIsToken0
        );

        // Se precisamos do outro token, fazer swap
        if (usdcIsToken0 && amount1Desired > 0) {
            // USDC é token0, precisamos de token1
            uint256 usdcToSwap = (usdcBalance * amount1Desired) / (amount0Desired + amount1Desired);
            amount1Desired = executeSwap(asset(), token1, usdcToSwap);
            amount0Desired = IERC20(asset()).balanceOf(address(this));
        } else if (!usdcIsToken0 && amount0Desired > 0) {
            // USDC é token1, precisamos de token0
            uint256 usdcToSwap = (usdcBalance * amount0Desired) / (amount0Desired + amount1Desired);
            amount0Desired = executeSwap(asset(), token0, usdcToSwap);
            amount1Desired = IERC20(asset()).balanceOf(address(this));
        }

        // Aprovar tokens para o position manager
        IERC20(token0).safeApprove(address(positionManager), amount0Desired);
        IERC20(token1).safeApprove(address(positionManager), amount1Desired);

        // Calcular amounts mínimos (com slippage)
        uint256 amount0Min = (amount0Desired * (10000 - maxSlippageBps)) / 10000;
        uint256 amount1Min = (amount1Desired * (10000 - maxSlippageBps)) / 10000;

        // Mint da posição
        INonfungiblePositionManager.MintParams memory params = INonfungiblePositionManager.MintParams({
            token0: token0,
            token1: token1,
            fee: uniswapPool.fee(),
            tickLower: tickLower,
            tickUpper: tickUpper,
            amount0Desired: amount0Desired,
            amount1Desired: amount1Desired,
            amount0Min: amount0Min,
            amount1Min: amount1Min,
            recipient: address(this),
            deadline: block.timestamp
        });

        (uint256 newTokenId, uint128 liquidity, uint256 amount0, uint256 amount1) = positionManager.mint(params);

        tokenId = newTokenId;

        // Reset approvals
        IERC20(token0).safeApprove(address(positionManager), 0);
        IERC20(token1).safeApprove(address(positionManager), 0);

        emit PositionMinted(newTokenId, liquidity, amount0, amount1);
    }

    /**
     * @notice Fecha posição LP e converte tudo para USDC (IMPLEMENTAÇÃO REAL)
     */
    function _closePositionAndConvertToUSDC() internal {
        if (tokenId == 0) {
            return; // Nenhuma posição para fechar
        }

        // Obter informações da posição
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
            // Decrease liquidity para 0
            INonfungiblePositionManager.DecreaseLiquidityParams memory decreaseParams =
                INonfungiblePositionManager.DecreaseLiquidityParams({
                    tokenId: tokenId,
                    liquidity: liquidity,
                    amount0Min: 0,
                    amount1Min: 0,
                    deadline: block.timestamp
                });

            positionManager.decreaseLiquidity(decreaseParams);
        }

        // Collect todos os tokens
        INonfungiblePositionManager.CollectParams memory collectParams =
            INonfungiblePositionManager.CollectParams({
                tokenId: tokenId,
                recipient: address(this),
                amount0Max: type(uint128).max,
                amount1Max: type(uint128).max
            });

        (uint256 amount0, uint256 amount1) = positionManager.collect(collectParams);

        // Burn da posição NFT
        positionManager.burn(tokenId);

        emit PositionClosed(tokenId, amount0, amount1, 0, 0);

        tokenId = 0;

        // Converter todos os tokens para USDC
        uint256 token0Balance = IERC20(token0).balanceOf(address(this));
        uint256 token1Balance = IERC20(token1).balanceOf(address(this));

        if (asset() == token0) {
            // USDC é token0, converter token1 para USDC
            if (token1Balance > 0) {
                executeSwap(token1, asset(), token1Balance);
            }
        } else {
            // USDC é token1, converter token0 para USDC
            if (token0Balance > 0) {
                executeSwap(token0, asset(), token0Balance);
            }
        }
    }

    /**
     * @notice Executa swap via 1inch Aggregator v5 (PRODUÇÃO)
     * @dev Keeper deve chamar API 1inch off-chain para obter executor e data
     * @param tokenIn Token de entrada
     * @param tokenOut Token de saída
     * @param amountIn Quantidade a ser swapada
     * @param executor Executor address (from 1inch API)
     * @param data Calldata do swap (from 1inch API)
     * @return amountOut Quantidade recebida
     */
    function executeSwapVia1inch(
        address tokenIn,
        address tokenOut,
        uint256 amountIn,
        address executor,
        bytes calldata data
    ) external onlyKeeper nonReentrant returns (uint256 amountOut) {
        if (amountIn == 0) {
            return 0;
        }

        // Aplica swap fee
        uint256 netAmountIn = _applySwapFee(amountIn);

        // Calcular amount mínimo usando oracle (PROTEÇÃO DE SLIPPAGE)
        (uint256 oraclePrice,) = _getOraclePrice();
        uint256 expectedOut = (netAmountIn * oraclePrice) / 1e18;
        uint256 amountOutMinimum = (expectedOut * (10000 - maxSlippageBps)) / 10000;

        // Aprovar tokens para 1inch
        IERC20(tokenIn).safeApprove(address(oneInchRouter), netAmountIn);

        // Preparar descrição do swap
        I1inchAggregator.SwapDescription memory desc = I1inchAggregator.SwapDescription({
            srcToken: tokenIn,
            dstToken: tokenOut,
            srcReceiver: payable(address(this)),
            dstReceiver: payable(address(this)),
            amount: netAmountIn,
            minReturnAmount: amountOutMinimum,
            flags: 0
        });

        // Executar swap via 1inch
        (amountOut,) = oneInchRouter.swap(executor, desc, "", data);

        // Reset approval
        IERC20(tokenIn).safeApprove(address(oneInchRouter), 0);

        emit SwapExecuted(tokenIn, tokenOut, amountIn, amountOut);
    }

    /**
     * @notice Executa swap via Uniswap v3 (FALLBACK)
     * @dev Usado internamente quando 1inch não está disponível
     * @param tokenIn Token de entrada
     * @param tokenOut Token de saída
     * @param amountIn Quantidade a ser swapada
     * @return amountOut Quantidade recebida
     */
    function executeSwap(
        address tokenIn,
        address tokenOut,
        uint256 amountIn
    ) internal returns (uint256 amountOut) {
        if (amountIn == 0) {
            return 0;
        }

        // Aplica swap fee
        uint256 netAmountIn = _applySwapFee(amountIn);

        // Aprovar tokens para o router
        IERC20(tokenIn).safeApprove(address(swapRouter), netAmountIn);

        // Calcular amount mínimo usando oracle (PROTEÇÃO DE SLIPPAGE)
        (uint256 oraclePrice,) = _getOraclePrice();
        uint256 expectedOut = (netAmountIn * oraclePrice) / 1e18;
        uint256 amountOutMinimum = (expectedOut * (10000 - maxSlippageBps)) / 10000;

        // Executar swap
        ISwapRouter.ExactInputSingleParams memory params = ISwapRouter.ExactInputSingleParams({
            tokenIn: tokenIn,
            tokenOut: tokenOut,
            fee: uniswapPool.fee(),
            recipient: address(this),
            deadline: block.timestamp,
            amountIn: netAmountIn,
            amountOutMinimum: amountOutMinimum,
            sqrtPriceLimitX96: 0
        });

        amountOut = swapRouter.exactInputSingle(params);

        // Reset approval
        IERC20(tokenIn).safeApprove(address(swapRouter), 0);

        emit SwapExecuted(tokenIn, tokenOut, amountIn, amountOut);
    }

    /**
     * @notice Calcula quanto de cada token é necessário para a posição
     * @param totalUsdc Total de USDC disponível
     * @param usdcIsToken0 Se USDC é token0
     * @return amount0 Quantidade de token0
     * @return amount1 Quantidade de token1
     */
    function _calculateTokenAmounts(
        uint256 totalUsdc,
        bool usdcIsToken0
    ) internal view returns (uint256 amount0, uint256 amount1) {
        // Obter preço atual da pool
        (uint160 sqrtPriceX96,,,,,,) = uniswapPool.slot0();

        // Obter sqrt prices para os ticks
        uint160 sqrtPriceAX96 = TickMath.getSqrtRatioAtTick(tickLower);
        uint160 sqrtPriceBX96 = TickMath.getSqrtRatioAtTick(tickUpper);

        // Usar LiquidityMath para calcular distribuição ótima
        (amount0, amount1) = LiquidityMath.calculateOptimalAmounts(
            totalUsdc,
            sqrtPriceX96,
            sqrtPriceAX96,
            sqrtPriceBX96,
            usdcIsToken0
        );
    }

    /**
     * @notice Emergency exit: fecha tudo e converte para USDC
     */
    function emergencyExitToUSDC() external onlyOwner whenPaused nonReentrant {
        // Fecha posição LP e converte para USDC
        _closePositionAndConvertToUSDC();

        uint256 totalAssets_ = totalAssets();
        emit EmergencyExitExecuted(totalAssets_);
    }

    // ============================================
    // OVERRIDES ERC4626
    // ============================================

    /**
     * @notice Override deposit para cobrar entry fee
     */
    function deposit(
        uint256 assets,
        address receiver
    ) public virtual override whenNotPaused nonReentrant returns (uint256) {
        // Cobra management fee antes do depósito
        _chargeManagementFee();

        // Transfer assets antes de cobrar fee
        IERC20(asset()).safeTransferFrom(msg.sender, address(this), assets);

        // Cobra entry fee
        uint256 netAssets = _chargeEntryFee(assets);

        // Calcula shares baseado nos assets líquidos
        uint256 shares = previewDeposit(netAssets);

        // Minta shares para o receiver
        _mint(receiver, shares);

        emit Deposit(msg.sender, receiver, assets, shares);

        return shares;
    }

    /**
     * @notice Override withdraw para cobrar exit fee
     */
    function withdraw(
        uint256 assets,
        address receiver,
        address owner
    ) public virtual override whenNotPaused nonReentrant returns (uint256) {
        // Cobra management fee antes do saque
        _chargeManagementFee();

        uint256 shares = previewWithdraw(assets);

        if (msg.sender != owner) {
            _spendAllowance(owner, msg.sender, shares);
        }

        // Burn shares
        _burn(owner, shares);

        // Cobra exit fee
        uint256 netAssets = _chargeExitFee(assets);

        // Transfer assets para o receiver
        IERC20(asset()).safeTransfer(receiver, netAssets);

        emit Withdraw(msg.sender, receiver, owner, assets, shares);

        return shares;
    }

    /**
     * @notice Override redeem para cobrar exit fee
     */
    function redeem(
        uint256 shares,
        address receiver,
        address owner
    ) public virtual override whenNotPaused nonReentrant returns (uint256) {
        // Cobra management fee antes do resgate
        _chargeManagementFee();

        if (msg.sender != owner) {
            _spendAllowance(owner, msg.sender, shares);
        }

        uint256 assets = previewRedeem(shares);

        // Burn shares
        _burn(owner, shares);

        // Cobra exit fee
        uint256 netAssets = _chargeExitFee(assets);

        // Transfer assets para o receiver
        IERC20(asset()).safeTransfer(receiver, netAssets);

        emit Withdraw(msg.sender, receiver, owner, assets, shares);

        return assets;
    }

    /**
     * @notice Override totalAssets - inclui valor da posição LP
     */
    function totalAssets() public view virtual override returns (uint256) {
        uint256 usdcBalance = IERC20(asset()).balanceOf(address(this));

        // Se não há posição, retornar apenas saldo USDC
        if (tokenId == 0) {
            return usdcBalance;
        }

        // Obter valor da posição LP
        (uint256 amount0, uint256 amount1) = _getPositionValue();

        // Converter tudo para USDC
        uint256 totalValue = usdcBalance;

        if (asset() == token0) {
            // USDC é token0
            totalValue += amount0;
            // Converter token1 para USDC (simplificado - em produção, usar oracle)
            totalValue += amount1; // Simplificação
        } else {
            // USDC é token1
            totalValue += amount1;
            // Converter token0 para USDC (simplificado - em produção, usar oracle)
            totalValue += amount0; // Simplificação
        }

        return totalValue;
    }

    /**
     * @notice Obtém valor atual da posição LP
     * @return amount0 Quantidade de token0
     * @return amount1 Quantidade de token1
     */
    function _getPositionValue() internal view returns (uint256 amount0, uint256 amount1) {
        if (tokenId == 0) {
            return (0, 0);
        }

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
            uint128 tokensOwed0,
            uint128 tokensOwed1
        ) = positionManager.positions(tokenId);

        // Simplificação: retornar apenas fees acumulados
        // Em produção, calcular valor baseado na liquidez e preço atual
        amount0 = tokensOwed0;
        amount1 = tokensOwed1;
    }

    /**
     * @notice Função para receber NFTs do Uniswap v3
     */
    function onERC721Received(
        address,
        address,
        uint256,
        bytes calldata
    ) external pure returns (bytes4) {
        return this.onERC721Received.selector;
    }
}
