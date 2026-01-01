/**
 * Validador de Dual-Oracle
 *
 * Valida consistência entre múltiplos oracles e detecta possíveis ataques
 */
class DualOracleValidator {
    constructor(maxDeviationBps = 500) {
        this.maxDeviationBps = maxDeviationBps; // 500 = 5% padrão
        console.log(`✅ Validator: max deviation ${this.maxDeviationBps / 100}%`);
    }

    /**
     * Validar consistência entre 2 oracles
     * @param {number} price1 - Preço do primeiro oracle
     * @param {number} price2 - Preço do segundo oracle
     * @param {string} source1 - Nome do primeiro oracle
     * @param {string} source2 - Nome do segundo oracle
     * @returns {Object} { isValid, deviation, deviationPercent, message }
     */
    validate(price1, price2, source1 = 'Oracle1', source2 = 'Oracle2') {
        if (!price1 || !price2 || price1 <= 0 || price2 <= 0) {
            return {
                isValid: false,
                deviation: 0,
                deviationPercent: '0%',
                message: 'Preços inválidos'
            };
        }

        // Calcular desvio em basis points
        const deviation = Math.abs(price1 - price2) * 10000 / Math.min(price1, price2);
        const isValid = deviation < this.maxDeviationBps;

        const message = isValid
            ? `✅ ${source1} vs ${source2}: consistentes`
            : `⚠️  ${source1} vs ${source2}: divergindo ${(deviation / 100).toFixed(2)}%`;

        return {
            isValid,
            deviation: parseFloat(deviation.toFixed(2)),
            deviationPercent: (deviation / 100).toFixed(2) + '%',
            message
        };
    }

    /**
     * Validar múltiplos oracles (3+)
     * @param {Array} prices - Array de { price, source }
     * @returns {Object} { allValid, validations, consensus }
     */
    validateMultiple(prices) {
        if (!prices || prices.length < 2) {
            throw new Error('validateMultiple: necessário pelo menos 2 preços');
        }

        const validations = [];
        let allValid = true;

        // Validar cada par
        for (let i = 0; i < prices.length - 1; i++) {
            for (let j = i + 1; j < prices.length; j++) {
                const validation = this.validate(
                    prices[i].price,
                    prices[j].price,
                    prices[i].source,
                    prices[j].source
                );

                validations.push(validation);

                if (!validation.isValid) {
                    allValid = false;
                }
            }
        }

        // Calcular preço de consenso (mediana)
        const sortedPrices = prices.map(p => p.price).sort((a, b) => a - b);
        const median = sortedPrices[Math.floor(sortedPrices.length / 2)];

        return {
            allValid,
            validations,
            consensus: median,
            prices: sortedPrices
        };
    }

    /**
     * Calcular média ponderada de múltiplos oracles
     * @param {Array} prices - Array de { price, weight }
     * @returns {number}
     */
    weightedAverage(prices) {
        if (!prices || prices.length === 0) {
            throw new Error('weightedAverage: array vazio');
        }

        const totalWeight = prices.reduce((sum, p) => sum + (p.weight || 1), 0);
        const weightedSum = prices.reduce((sum, p) => sum + (p.price * (p.weight || 1)), 0);

        return weightedSum / totalWeight;
    }

    /**
     * Detectar possível ataque de manipulação de preço
     * @param {number} pythPrice - Preço do Pyth
     * @param {number} chainlinkPrice - Preço do Chainlink
     * @param {number} spotPrice - Preço spot (ex: Uniswap)
     * @returns {Object} { attackDetected, type, details }
     */
    detectAttack(pythPrice, chainlinkPrice, spotPrice) {
        // Se os oracles concordam (~1%) mas spot diverge muito (>10%)
        const oraclesValidation = this.validate(pythPrice, chainlinkPrice, 'Pyth', 'Chainlink');

        const spotVsPyth = Math.abs(spotPrice - pythPrice) * 10000 / pythPrice;
        const spotVsChainlink = Math.abs(spotPrice - chainlinkPrice) * 10000 / chainlinkPrice;

        // Caso 1: Flash Loan Attack
        // Oracles concordam, mas pool diverge MUITO
        if (oraclesValidation.isValid &&
            spotVsPyth > 1000 &&
            spotVsChainlink > 1000) {

            return {
                attackDetected: true,
                type: 'FLASH_LOAN_ATTACK',
                details: {
                    pythPrice,
                    chainlinkPrice,
                    spotPrice,
                    oracleDeviation: oraclesValidation.deviationPercent,
                    spotDeviation: (spotVsPyth / 100).toFixed(2) + '%',
                    message: '🚨 POSSÍVEL FLASH LOAN ATTACK! Oracles concordam mas pool diverge muito.'
                }
            };
        }

        // Caso 2: Oracle Manipulation
        // Oracles divergem entre si
        if (!oraclesValidation.isValid) {
            return {
                attackDetected: true,
                type: 'ORACLE_MANIPULATION',
                details: {
                    pythPrice,
                    chainlinkPrice,
                    spotPrice,
                    deviation: oraclesValidation.deviationPercent,
                    message: '⚠️  ORACLES DIVERGINDO! Possível manipulação ou falha.'
                }
            };
        }

        // Nenhum ataque detectado
        return {
            attackDetected: false,
            type: null,
            details: null
        };
    }

    /**
     * Calcular confiança do preço (0-100%)
     * @param {Array} prices - Array de { price, source }
     * @returns {number} Score de confiança (0-100)
     */
    calculateConfidence(prices) {
        if (!prices || prices.length < 2) {
            return 0;
        }

        // Calcular desvio padrão
        const avg = prices.reduce((sum, p) => sum + p.price, 0) / prices.length;
        const variance = prices.reduce((sum, p) => sum + Math.pow(p.price - avg, 2), 0) / prices.length;
        const stdDev = Math.sqrt(variance);

        // Quanto menor o desvio padrão, maior a confiança
        const deviationPercent = (stdDev / avg) * 100;

        if (deviationPercent < 1) return 100;      // Excelente
        if (deviationPercent < 2) return 90;       // Muito bom
        if (deviationPercent < 5) return 75;       // Bom
        if (deviationPercent < 10) return 50;      // Médio
        return 25;                                  // Baixo
    }

    /**
     * Formatar relatório de validação
     * @param {Object} validation - Resultado de validate()
     * @returns {string}
     */
    formatReport(validation) {
        const emoji = validation.isValid ? '✅' : '❌';
        return `${emoji} ${validation.message} (dev: ${validation.deviationPercent})`;
    }
}

module.exports = DualOracleValidator;
