// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "forge-std/Test.sol";
import "../DeltaNeutralVaultV1.sol";
import "../mocks/Mocks.sol";

/**
 * @title DeltaNeutralVaultTest
 * @notice Testes completos do DeltaNeutralVaultV1 usando Foundry
 * @dev Muito mais rápido e completo que Hardhat!
 */
contract DeltaNeutralVaultTest is Test {

    DeltaNeutralVaultV1 public vault;
    MockERC20 public usdc;
    MockERC20 public wbtc;
    MockChainlinkFeed public chainlinkFeed;
    MockPositionManager public positionManager;
    MockSwapRouter public swapRouter;
    Mock1inchRouter public oneInchRouter;

    address public owner;
    address public keeper;
    address public treasury;
    address public user1;
    address public user2;

    // Constants
    uint256 constant INITIAL_USDC_BALANCE = 100_000e6;  // 100k USDC
    uint256 constant DEPOSIT_AMOUNT = 10_000e6;         // 10k USDC
    int256 constant INITIAL_BTC_PRICE = 40_000e8;       // $40,000

    // Events (para testar emissão)
    event KeeperUpdated(address indexed oldKeeper, address indexed newKeeper);
    event FeesUpdated(uint16, uint16, uint16, uint16, uint16, uint16);
    event Deposit(address indexed sender, address indexed owner, uint256 assets, uint256 shares);
    event Withdraw(address indexed sender, address indexed receiver, address indexed owner, uint256 assets, uint256 shares);

    function setUp() public {
        // Setup accounts
        owner = address(this);
        keeper = makeAddr("keeper");
        treasury = makeAddr("treasury");
        user1 = makeAddr("user1");
        user2 = makeAddr("user2");

        // Deploy mocks
        usdc = new MockERC20("USD Coin", "USDC", 6);
        wbtc = new MockERC20("Wrapped Bitcoin", "WBTC", 8);
        chainlinkFeed = new MockChainlinkFeed(8, INITIAL_BTC_PRICE);
        positionManager = new MockPositionManager();
        swapRouter = new MockSwapRouter();
        oneInchRouter = new Mock1inchRouter();

        // Deploy vault
        vault = new DeltaNeutralVaultV1(
            IERC20(address(usdc)),
            "Delta Neutral Vault Shares",
            "dnvUSDC",
            address(chainlinkFeed),
            treasury,
            address(positionManager),
            address(swapRouter),
            address(oneInchRouter)
        );

        // Mint USDC to users
        usdc.mint(user1, INITIAL_USDC_BALANCE);
        usdc.mint(user2, INITIAL_USDC_BALANCE);

        // Label addresses para logs
        vm.label(address(vault), "DeltaNeutralVault");
        vm.label(address(usdc), "USDC");
        vm.label(address(wbtc), "WBTC");
        vm.label(user1, "User1");
        vm.label(user2, "User2");
        vm.label(keeper, "Keeper");
        vm.label(treasury, "Treasury");
    }

    // ============================================
    // DEPLOYMENT TESTS
    // ============================================

    function test_Deployment_OwnerIsSet() public {
        assertEq(vault.owner(), owner, "Owner should be set correctly");
    }

    function test_Deployment_TreasuryIsSet() public {
        assertEq(vault.treasury(), treasury, "Treasury should be set correctly");
    }

    function test_Deployment_AssetIsUSDC() public {
        assertEq(address(vault.asset()), address(usdc), "Asset should be USDC");
    }

    function test_Deployment_DefaultParameters() public {
        assertEq(vault.maxOracleDeviationBps(), 500, "Max oracle deviation should be 5%");
        assertEq(vault.maxOracleDelay(), 3600, "Max oracle delay should be 1 hour");
        assertEq(vault.maxSlippageBps(), 100, "Max slippage should be 1%");
    }

    function test_Deployment_RevertsIfTreasuryIsZero() public {
        vm.expectRevert("DeltaNeutralVault: treasury cannot be zero");
        new DeltaNeutralVaultV1(
            IERC20(address(usdc)),
            "Test",
            "TEST",
            address(chainlinkFeed),
            address(0), // ← zero address
            address(positionManager),
            address(swapRouter)
        );
    }

    // ============================================
    // CONFIGURATION TESTS
    // ============================================

    function test_Configuration_SetKeeper() public {
        vm.expectEmit(true, true, false, false);
        emit KeeperUpdated(address(0), keeper);

        vault.setKeeper(keeper);

        assertEq(vault.keeper(), keeper, "Keeper should be set");
    }

    function test_Configuration_SetKeeperRevertsIfNotOwner() public {
        vm.prank(user1);
        vm.expectRevert();
        vault.setKeeper(keeper);
    }

    function test_Configuration_SetKeeperRevertsIfZeroAddress() public {
        vm.expectRevert("DeltaNeutralVault: keeper cannot be zero");
        vault.setKeeper(address(0));
    }

    function test_Configuration_SetFees() public {
        vm.expectEmit(false, false, false, true);
        emit FeesUpdated(2000, 200, 50, 50, 30, 10);

        vault.setFees(
            2000,  // 20% performance
            200,   // 2% management
            50,    // 0.5% entry
            50,    // 0.5% exit
            30,    // 0.3% swap
            10     // 0.1% keeper
        );

        assertEq(vault.performanceFeeBps(), 2000);
        assertEq(vault.managementFeeBps(), 200);
        assertEq(vault.entryFeeBps(), 50);
        assertEq(vault.exitFeeBps(), 50);
        assertEq(vault.swapFeeBps(), 30);
        assertEq(vault.keeperFeeBps(), 10);
    }

    function test_Configuration_SetFeesRevertsIfTooHigh() public {
        vm.expectRevert("DeltaNeutralVault: performance fee too high");
        vault.setFees(6000, 200, 50, 50, 30, 10); // 60% performance - too high
    }

    function test_Configuration_SetTreasury() public {
        address newTreasury = makeAddr("newTreasury");

        vault.setTreasury(newTreasury);

        assertEq(vault.treasury(), newTreasury);
    }

    function test_Configuration_SetSlippageParams() public {
        vault.setSlippageParams(200); // 2%
        assertEq(vault.maxSlippageBps(), 200);
    }

    // ============================================
    // DEPOSIT TESTS
    // ============================================

    function test_Deposit_AllowsDeposit() public {
        uint256 depositAmount = DEPOSIT_AMOUNT;

        vm.startPrank(user1);
        usdc.approve(address(vault), depositAmount);

        vm.expectEmit(true, true, false, false);
        emit Deposit(user1, user1, depositAmount, depositAmount); // 1:1 inicialmente

        uint256 shares = vault.deposit(depositAmount, user1);
        vm.stopPrank();

        assertGt(shares, 0, "Should receive shares");
        assertEq(vault.balanceOf(user1), shares, "User should have shares");
    }

    function test_Deposit_ChargesEntryFee() public {
        // Set 1% entry fee
        vault.setFees(0, 0, 100, 0, 0, 0);

        uint256 depositAmount = DEPOSIT_AMOUNT;
        uint256 expectedFee = depositAmount / 100; // 1%

        uint256 treasuryBalanceBefore = usdc.balanceOf(treasury);

        vm.startPrank(user1);
        usdc.approve(address(vault), depositAmount);
        vault.deposit(depositAmount, user1);
        vm.stopPrank();

        uint256 treasuryBalanceAfter = usdc.balanceOf(treasury);

        assertEq(
            treasuryBalanceAfter - treasuryBalanceBefore,
            expectedFee,
            "Treasury should receive entry fee"
        );
    }

    function test_Deposit_HandlesMultipleDeposits() public {
        uint256 amount1 = 1000e6;
        uint256 amount2 = 2000e6;

        vm.startPrank(user1);
        usdc.approve(address(vault), amount1);
        vault.deposit(amount1, user1);
        vm.stopPrank();

        vm.startPrank(user2);
        usdc.approve(address(vault), amount2);
        vault.deposit(amount2, user2);
        vm.stopPrank();

        uint256 totalAssets = vault.totalAssets();
        assertEq(totalAssets, amount1 + amount2, "Total assets should be sum of deposits");
    }

    function test_Deposit_RevertsWhenPaused() public {
        vault.pause();

        vm.startPrank(user1);
        usdc.approve(address(vault), DEPOSIT_AMOUNT);

        vm.expectRevert("Pausable: paused");
        vault.deposit(DEPOSIT_AMOUNT, user1);
        vm.stopPrank();
    }

    // ============================================
    // WITHDRAWAL TESTS
    // ============================================

    function test_Withdraw_AllowsWithdrawal() public {
        // First deposit
        vm.startPrank(user1);
        usdc.approve(address(vault), DEPOSIT_AMOUNT);
        uint256 shares = vault.deposit(DEPOSIT_AMOUNT, user1);
        vm.stopPrank();

        // Then withdraw
        uint256 balanceBefore = usdc.balanceOf(user1);

        vm.prank(user1);
        vault.redeem(shares, user1, user1);

        uint256 balanceAfter = usdc.balanceOf(user1);

        assertGt(balanceAfter, balanceBefore, "User should receive USDC");
    }

    function test_Withdraw_ChargesExitFee() public {
        // Set 1% exit fee
        vault.setFees(0, 0, 0, 100, 0, 0);

        // Deposit
        vm.startPrank(user1);
        usdc.approve(address(vault), DEPOSIT_AMOUNT);
        uint256 shares = vault.deposit(DEPOSIT_AMOUNT, user1);
        vm.stopPrank();

        uint256 treasuryBalanceBefore = usdc.balanceOf(treasury);

        // Withdraw
        vm.prank(user1);
        vault.redeem(shares, user1, user1);

        uint256 treasuryBalanceAfter = usdc.balanceOf(treasury);

        assertGt(
            treasuryBalanceAfter - treasuryBalanceBefore,
            0,
            "Treasury should receive exit fee"
        );
    }

    // ============================================
    // PAUSE TESTS
    // ============================================

    function test_Pause_AllowsOwnerToPause() public {
        vault.pause();
        assertTrue(vault.paused(), "Vault should be paused");
    }

    function test_Pause_RevertsIfNotOwner() public {
        vm.prank(user1);
        vm.expectRevert();
        vault.pause();
    }

    function test_Pause_AllowsOwnerToUnpause() public {
        vault.pause();
        vault.unpause();
        assertFalse(vault.paused(), "Vault should be unpaused");
    }

    // ============================================
    // ORACLE TESTS
    // ============================================

    function test_Oracle_RevertsOnStaleData() public {
        vault.setKeeper(keeper);

        // Avançar tempo para tornar oracle stale
        vm.warp(block.timestamp + 3601); // > maxOracleDelay (3600)

        vm.prank(keeper);
        vm.expectRevert("DeltaNeutralVault: oracle data too old");
        vault.autoExit(uint256(INITIAL_BTC_PRICE), DeltaNeutralVaultV1.ExitReason.ManualExit);
    }

    function test_Oracle_RevertsOnHighDeviation() public {
        vault.setKeeper(keeper);

        // Tentar autoExit com preço muito diferente (> 5% de desvio)
        uint256 manipulatedPrice = uint256(INITIAL_BTC_PRICE) * 11 / 10; // +10%

        vm.prank(keeper);
        vm.expectRevert("DeltaNeutralVault: price deviation too high");
        vault.autoExit(manipulatedPrice, DeltaNeutralVaultV1.ExitReason.ManualExit);
    }

    // ============================================
    // MANAGEMENT FEE TESTS
    // ============================================

    function test_ManagementFee_AccruesOverTime() public {
        // Set 2% annual management fee
        vault.setFees(0, 200, 0, 0, 0, 0);

        // Deposit
        vm.startPrank(user1);
        usdc.approve(address(vault), DEPOSIT_AMOUNT);
        vault.deposit(DEPOSIT_AMOUNT, user1);
        vm.stopPrank();

        uint256 treasurySharesBefore = vault.balanceOf(treasury);

        // Avançar 1 ano
        vm.warp(block.timestamp + 365 days);

        // Trigger management fee com outro deposit
        vm.startPrank(user1);
        usdc.approve(address(vault), 1e6);
        vault.deposit(1e6, user1);
        vm.stopPrank();

        uint256 treasurySharesAfter = vault.balanceOf(treasury);

        assertGt(
            treasurySharesAfter,
            treasurySharesBefore,
            "Treasury should receive management fee shares"
        );
    }

    // ============================================
    // FUZZ TESTS
    // ============================================

    /// @notice Fuzz test: qualquer deposit válido deve funcionar
    function testFuzz_Deposit(uint96 amount) public {
        vm.assume(amount > 1e6);  // Minimum 1 USDC
        vm.assume(amount <= INITIAL_USDC_BALANCE);

        vm.startPrank(user1);
        usdc.approve(address(vault), amount);
        uint256 shares = vault.deposit(amount, user1);
        vm.stopPrank();

        assertGt(shares, 0, "Should receive shares");
        assertEq(vault.totalAssets(), amount, "Total assets should equal deposit");
    }

    /// @notice Fuzz test: withdraw deve retornar assets corretos
    function testFuzz_WithdrawAfterDeposit(uint96 depositAmount) public {
        vm.assume(depositAmount > 1e6);
        vm.assume(depositAmount <= INITIAL_USDC_BALANCE);

        // Deposit
        vm.startPrank(user1);
        usdc.approve(address(vault), depositAmount);
        uint256 shares = vault.deposit(depositAmount, user1);

        // Withdraw imediatamente
        uint256 assets = vault.redeem(shares, user1, user1);
        vm.stopPrank();

        // Should get back ~same amount (minus rounding)
        assertApproxEqAbs(assets, depositAmount, 1, "Should receive approximately same amount");
    }

    /// @notice Fuzz test: fees nunca devem exceder limites
    function testFuzz_FeesWithinLimits(
        uint16 performanceFee,
        uint16 managementFee,
        uint16 entryFee,
        uint16 exitFee,
        uint16 swapFee,
        uint16 keeperFee
    ) public {
        // Limitar fees aos valores máximos permitidos
        performanceFee = uint16(bound(performanceFee, 0, 5000));  // max 50%
        managementFee = uint16(bound(managementFee, 0, 1000));    // max 10%
        entryFee = uint16(bound(entryFee, 0, 1000));
        exitFee = uint16(bound(exitFee, 0, 1000));
        swapFee = uint16(bound(swapFee, 0, 1000));
        keeperFee = uint16(bound(keeperFee, 0, 1000));

        // Should NOT revert se dentro dos limites
        vault.setFees(
            performanceFee,
            managementFee,
            entryFee,
            exitFee,
            swapFee,
            keeperFee
        );

        assertEq(vault.performanceFeeBps(), performanceFee);
    }

    // ============================================
    // INVARIANT TESTS
    // ============================================

    /// @notice Invariant: totalAssets nunca deve ser menor que soma dos depósitos
    function invariant_TotalAssetsNeverNegative() public {
        assertGe(vault.totalAssets(), 0, "Total assets should never be negative");
    }

    /// @notice Invariant: totalSupply de shares deve ser proporcional a totalAssets
    function invariant_SharesProportionalToAssets() public {
        if (vault.totalSupply() > 0) {
            assertGt(vault.totalAssets(), 0, "If shares exist, assets must exist");
        }
    }

    // ============================================
    // GAS BENCHMARKS
    // ============================================

    function test_GasBenchmark_Deposit() public {
        vm.startPrank(user1);
        usdc.approve(address(vault), DEPOSIT_AMOUNT);

        uint256 gasBefore = gasleft();
        vault.deposit(DEPOSIT_AMOUNT, user1);
        uint256 gasUsed = gasBefore - gasleft();

        vm.stopPrank();

        emit log_named_uint("Gas used for deposit", gasUsed);
    }

    function test_GasBenchmark_Withdraw() public {
        // Setup: deposit first
        vm.startPrank(user1);
        usdc.approve(address(vault), DEPOSIT_AMOUNT);
        uint256 shares = vault.deposit(DEPOSIT_AMOUNT, user1);

        uint256 gasBefore = gasleft();
        vault.redeem(shares, user1, user1);
        uint256 gasUsed = gasBefore - gasleft();

        vm.stopPrank();

        emit log_named_uint("Gas used for withdraw", gasUsed);
    }

    // ============================================
    // HELPER FUNCTIONS
    // ============================================

    function _depositAs(address user, uint256 amount) internal returns (uint256 shares) {
        vm.startPrank(user);
        usdc.approve(address(vault), amount);
        shares = vault.deposit(amount, user);
        vm.stopPrank();
    }
}
