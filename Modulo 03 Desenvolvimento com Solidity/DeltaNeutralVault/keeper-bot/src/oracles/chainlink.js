const { ethers } = require('ethers');

/**
 * Chainlink Oracle - Consulta ON-CHAIN
 *
 * Documentação: https://docs.chain.link/data-feeds
 */
class ChainlinkOracle {
    constructor(provider, feedAddress) {
        if (!provider) {
            throw new Error('Chainlink: provider é obrigatório');
        }

        if (!feedAddress || !ethers.isAddress(feedAddress)) {
            throw new Error('Chainlink: feedAddress inválido');
        }

        this.provider = provider;
        this.feedAddress = feedAddress;

        // ABI mínimo do Chainlink Aggregator
        const abi = [
            'function latestRoundData() external view returns (uint80 roundId, int256 answer, uint256 startedAt, uint256 updatedAt, uint80 answeredInRound)',
            'function decimals() external view returns (uint8)'
        ];

        this.feed = new ethers.Contract(feedAddress, abi, provider);

        console.log('✅ Chainlink Oracle inicializado (ON-CHAIN)');
        console.log(`   Feed: ${feedAddress}`);
    }

    /**
     * Obter preço BTC/USD do Chainlink
     * @returns {Promise<Object>} { price, timestamp, roundId, source }
     */
    async getPrice() {
        try {
            // Buscar dados mais recentes
            const [roundId, answer, , updatedAt, answeredInRound] =
                await this.feed.latestRoundData();

            // Validações de segurança
            if (answer <= 0n) {
                throw new Error('Chainlink: preço inválido (<=0)');
            }

            if (answeredInRound < roundId) {
                throw new Error('Chainlink: dados stale (answeredInRound < roundId)');
            }

            // Obter decimais (BTC/USD geralmente tem 8 decimais)
            const decimals = await this.feed.decimals();

            // Converter para float
            const priceFloat = parseFloat(ethers.formatUnits(answer, decimals));

            // Verificar staleness (dados muito antigos)
            const ageSeconds = Date.now() / 1000 - parseInt(updatedAt.toString());
            if (ageSeconds > 3600) {
                console.warn(`⚠️  Chainlink: dados antigos (${ageSeconds.toFixed(0)}s)`);
            }

            return {
                price: priceFloat,
                timestamp: parseInt(updatedAt.toString()),
                roundId: parseInt(roundId.toString()),
                source: 'Chainlink (on-chain)',
                decimals: decimals,
                raw: {
                    answer: answer.toString(),
                    roundId: roundId.toString(),
                    answeredInRound: answeredInRound.toString()
                }
            };

        } catch (error) {
            if (error.code === 'CALL_EXCEPTION') {
                throw new Error('Chainlink: falha ao chamar contrato (rede offline?)');
            }

            throw new Error(`Chainlink: ${error.message}`);
        }
    }

    /**
     * Verificar se preço está atualizado (< 1 hora)
     * @returns {Promise<boolean>}
     */
    async isPriceFresh() {
        try {
            const data = await this.getPrice();
            const ageSeconds = Date.now() / 1000 - data.timestamp;
            return ageSeconds < 3600; // Menos de 1 hora
        } catch (error) {
            console.error('Chainlink: erro ao verificar freshness:', error.message);
            return false;
        }
    }

    /**
     * Obter idade do preço em segundos
     * @returns {Promise<number>}
     */
    async getPriceAge() {
        const data = await this.getPrice();
        return Date.now() / 1000 - data.timestamp;
    }

    /**
     * Verificar saúde do oracle
     * @returns {Promise<Object>} { healthy, issues }
     */
    async healthCheck() {
        const issues = [];

        try {
            const data = await this.getPrice();

            // Verificar idade
            const ageSeconds = Date.now() / 1000 - data.timestamp;
            if (ageSeconds > 3600) {
                issues.push(`Dados antigos (${ageSeconds.toFixed(0)}s)`);
            }

            // Verificar round
            if (!data.roundId || data.roundId === 0) {
                issues.push('Round ID inválido');
            }

            return {
                healthy: issues.length === 0,
                issues: issues,
                data: data
            };

        } catch (error) {
            return {
                healthy: false,
                issues: [error.message],
                data: null
            };
        }
    }

    /**
     * Obter descrição do feed
     * @returns {Promise<string>}
     */
    async getDescription() {
        try {
            const abiWithDesc = ['function description() external view returns (string)'];
            const feedWithDesc = new ethers.Contract(this.feedAddress, abiWithDesc, this.provider);
            return await feedWithDesc.description();
        } catch (error) {
            return 'Unknown Feed';
        }
    }
}

module.exports = ChainlinkOracle;
