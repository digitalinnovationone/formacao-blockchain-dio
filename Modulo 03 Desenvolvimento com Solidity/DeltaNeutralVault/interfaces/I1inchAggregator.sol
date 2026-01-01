// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title I1inchAggregator
 * @notice Interface para 1inch Aggregation Router v5
 * @dev Documentação: https://docs.1inch.io/docs/aggregation-protocol/smart-contract/AggregationRouterV5
 */
interface I1inchAggregator {

    struct SwapDescription {
        address srcToken;
        address dstToken;
        address payable srcReceiver;
        address payable dstReceiver;
        uint256 amount;
        uint256 minReturnAmount;
        uint256 flags;
    }

    /**
     * @notice Executa swap otimizado via 1inch
     * @param executor Executor address (from 1inch API)
     * @param desc Descrição do swap
     * @param permit Permit data (se aplicável)
     * @param data Calldata do swap (from 1inch API)
     * @return returnAmount Quantidade recebida
     * @return spentAmount Quantidade gasta
     */
    function swap(
        address executor,
        SwapDescription calldata desc,
        bytes calldata permit,
        bytes calldata data
    ) external payable returns (uint256 returnAmount, uint256 spentAmount);

    /**
     * @notice Versão simplificada do swap
     * @param caller Caller address
     * @param desc Descrição do swap
     * @param data Calldata do swap
     * @return returnAmount Quantidade recebida
     * @return spentAmount Quantidade gasta
     */
    function unoswap(
        address caller,
        SwapDescription calldata desc,
        bytes calldata data
    ) external payable returns (uint256 returnAmount, uint256 spentAmount);
}
