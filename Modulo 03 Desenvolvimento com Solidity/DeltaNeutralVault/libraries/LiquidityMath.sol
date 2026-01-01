// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@uniswap/v3-core/contracts/libraries/TickMath.sol";
import "@uniswap/v3-core/contracts/libraries/FullMath.sol";
import "@uniswap/v3-core/contracts/libraries/FixedPoint96.sol";

/**
 * @title LiquidityMath
 * @notice Biblioteca para cálculos de liquidez no Uniswap v3
 * @dev Baseado nas bibliotecas oficiais do Uniswap v3
 */
library LiquidityMath {

    /**
     * @notice Calcula a quantidade de token0 e token1 necessários para uma quantidade de liquidez
     * @param sqrtRatioX96 Preço atual da pool (sqrt(price) * 2^96)
     * @param sqrtRatioAX96 Sqrt price no tick inferior
     * @param sqrtRatioBX96 Sqrt price no tick superior
     * @param liquidity Quantidade de liquidez desejada
     * @return amount0 Quantidade de token0
     * @return amount1 Quantidade de token1
     */
    function getAmountsForLiquidity(
        uint160 sqrtRatioX96,
        uint160 sqrtRatioAX96,
        uint160 sqrtRatioBX96,
        uint128 liquidity
    ) internal pure returns (uint256 amount0, uint256 amount1) {
        if (sqrtRatioAX96 > sqrtRatioBX96) {
            (sqrtRatioAX96, sqrtRatioBX96) = (sqrtRatioBX96, sqrtRatioAX96);
        }

        if (sqrtRatioX96 <= sqrtRatioAX96) {
            // Preço atual está abaixo do range - apenas token0
            amount0 = getAmount0ForLiquidity(sqrtRatioAX96, sqrtRatioBX96, liquidity);
        } else if (sqrtRatioX96 < sqrtRatioBX96) {
            // Preço atual está dentro do range - ambos os tokens
            amount0 = getAmount0ForLiquidity(sqrtRatioX96, sqrtRatioBX96, liquidity);
            amount1 = getAmount1ForLiquidity(sqrtRatioAX96, sqrtRatioX96, liquidity);
        } else {
            // Preço atual está acima do range - apenas token1
            amount1 = getAmount1ForLiquidity(sqrtRatioAX96, sqrtRatioBX96, liquidity);
        }
    }

    /**
     * @notice Calcula quantidade de liquidez para amounts de token0 e token1
     * @param sqrtRatioX96 Preço atual da pool
     * @param sqrtRatioAX96 Sqrt price no tick inferior
     * @param sqrtRatioBX96 Sqrt price no tick superior
     * @param amount0 Quantidade disponível de token0
     * @param amount1 Quantidade disponível de token1
     * @return liquidity Liquidez resultante
     */
    function getLiquidityForAmounts(
        uint160 sqrtRatioX96,
        uint160 sqrtRatioAX96,
        uint160 sqrtRatioBX96,
        uint256 amount0,
        uint256 amount1
    ) internal pure returns (uint128 liquidity) {
        if (sqrtRatioAX96 > sqrtRatioBX96) {
            (sqrtRatioAX96, sqrtRatioBX96) = (sqrtRatioBX96, sqrtRatioAX96);
        }

        if (sqrtRatioX96 <= sqrtRatioAX96) {
            liquidity = getLiquidityForAmount0(sqrtRatioAX96, sqrtRatioBX96, amount0);
        } else if (sqrtRatioX96 < sqrtRatioBX96) {
            uint128 liquidity0 = getLiquidityForAmount0(sqrtRatioX96, sqrtRatioBX96, amount0);
            uint128 liquidity1 = getLiquidityForAmount1(sqrtRatioAX96, sqrtRatioX96, amount1);
            liquidity = liquidity0 < liquidity1 ? liquidity0 : liquidity1;
        } else {
            liquidity = getLiquidityForAmount1(sqrtRatioAX96, sqrtRatioBX96, amount1);
        }
    }

    /**
     * @notice Calcula quantidade de token0 para uma quantidade de liquidez
     */
    function getAmount0ForLiquidity(
        uint160 sqrtRatioAX96,
        uint160 sqrtRatioBX96,
        uint128 liquidity
    ) internal pure returns (uint256 amount0) {
        if (sqrtRatioAX96 > sqrtRatioBX96) {
            (sqrtRatioAX96, sqrtRatioBX96) = (sqrtRatioBX96, sqrtRatioAX96);
        }

        return FullMath.mulDiv(
            uint256(liquidity) << FixedPoint96.RESOLUTION,
            sqrtRatioBX96 - sqrtRatioAX96,
            sqrtRatioBX96
        ) / sqrtRatioAX96;
    }

    /**
     * @notice Calcula quantidade de token1 para uma quantidade de liquidez
     */
    function getAmount1ForLiquidity(
        uint160 sqrtRatioAX96,
        uint160 sqrtRatioBX96,
        uint128 liquidity
    ) internal pure returns (uint256 amount1) {
        if (sqrtRatioAX96 > sqrtRatioBX96) {
            (sqrtRatioAX96, sqrtRatioBX96) = (sqrtRatioBX96, sqrtRatioAX96);
        }

        return FullMath.mulDiv(liquidity, sqrtRatioBX96 - sqrtRatioAX96, FixedPoint96.Q96);
    }

    /**
     * @notice Calcula liquidez para uma quantidade de token0
     */
    function getLiquidityForAmount0(
        uint160 sqrtRatioAX96,
        uint160 sqrtRatioBX96,
        uint256 amount0
    ) internal pure returns (uint128 liquidity) {
        if (sqrtRatioAX96 > sqrtRatioBX96) {
            (sqrtRatioAX96, sqrtRatioBX96) = (sqrtRatioBX96, sqrtRatioAX96);
        }

        uint256 intermediate = FullMath.mulDiv(sqrtRatioAX96, sqrtRatioBX96, FixedPoint96.Q96);
        return uint128(FullMath.mulDiv(amount0, intermediate, sqrtRatioBX96 - sqrtRatioAX96));
    }

    /**
     * @notice Calcula liquidez para uma quantidade de token1
     */
    function getLiquidityForAmount1(
        uint160 sqrtRatioAX96,
        uint160 sqrtRatioBX96,
        uint256 amount1
    ) internal pure returns (uint128 liquidity) {
        if (sqrtRatioAX96 > sqrtRatioBX96) {
            (sqrtRatioAX96, sqrtRatioBX96) = (sqrtRatioBX96, sqrtRatioAX96);
        }

        return uint128(FullMath.mulDiv(amount1, FixedPoint96.Q96, sqrtRatioBX96 - sqrtRatioAX96));
    }

    /**
     * @notice Calcula distribuição ótima de tokens para range específico
     * @param totalAmount Total de USDC disponível
     * @param sqrtPriceX96 Preço atual
     * @param sqrtPriceAX96 Preço no tick inferior
     * @param sqrtPriceBX96 Preço no tick superior
     * @param token0IsUSDC Se token0 é USDC
     * @return amount0 Quantidade de token0
     * @return amount1 Quantidade de token1
     */
    function calculateOptimalAmounts(
        uint256 totalAmount,
        uint160 sqrtPriceX96,
        uint160 sqrtPriceAX96,
        uint160 sqrtPriceBX96,
        bool token0IsUSDC
    ) internal pure returns (uint256 amount0, uint256 amount1) {
        // Assegurar ordem correta
        if (sqrtPriceAX96 > sqrtPriceBX96) {
            (sqrtPriceAX96, sqrtPriceBX96) = (sqrtPriceBX96, sqrtPriceAX96);
        }

        // Calcular ratio baseado na posição do preço no range
        if (sqrtPriceX96 <= sqrtPriceAX96) {
            // Preço abaixo do range - 100% token0
            if (token0IsUSDC) {
                amount0 = totalAmount;
                amount1 = 0;
            } else {
                amount0 = 0;
                amount1 = totalAmount;
            }
        } else if (sqrtPriceX96 >= sqrtPriceBX96) {
            // Preço acima do range - 100% token1
            if (token0IsUSDC) {
                amount0 = 0;
                amount1 = totalAmount;
            } else {
                amount0 = totalAmount;
                amount1 = 0;
            }
        } else {
            // Preço dentro do range - calcular proporção
            // Fórmula: ratio = (sqrtPrice - sqrtPriceA) / (sqrtPriceB - sqrtPriceA)
            uint256 numerator = uint256(sqrtPriceX96 - sqrtPriceAX96);
            uint256 denominator = uint256(sqrtPriceBX96 - sqrtPriceAX96);
            uint256 ratio = (numerator * 10000) / denominator; // ratio em bps

            if (token0IsUSDC) {
                // Maior o preço, menos token0 (USDC) precisamos
                amount0 = (totalAmount * (10000 - ratio)) / 10000;
                amount1 = totalAmount - amount0;
            } else {
                // Maior o preço, mais token1 (USDC) precisamos
                amount1 = (totalAmount * ratio) / 10000;
                amount0 = totalAmount - amount1;
            }
        }
    }
}
