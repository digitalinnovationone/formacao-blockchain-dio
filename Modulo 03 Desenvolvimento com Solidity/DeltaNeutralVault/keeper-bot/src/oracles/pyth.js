const axios = require('axios');

/**
 * Pyth Oracle - Consulta OFF-CHAIN via Hermes API (ZERO CUSTO!)
 *
 * Documentação: https://docs.pyth.network/price-feeds
 */
class PythOracle {
    constructor(hermesUrl, priceId) {
        this.hermesUrl = hermesUrl || process.env.PYTH_HERMES_URL;
        this.priceId = priceId || process.env.PYTH_PRICE_ID_BTC;

        if (!this.hermesUrl || !this.priceId) {
            throw new Error('Pyth: hermesUrl e priceId são obrigatórios');
        }

        console.log('✅ Pyth Oracle inicializado (OFF-CHAIN)');
        console.log(`   URL: ${this.hermesUrl}`);
        console.log(`   Price ID: ${this.priceId.substring(0, 10)}...`);
    }

    /**
     * Obter preço BTC/USD do Pyth via Hermes API
     * @returns {Promise<Object>} { price, confidence, timestamp, expo, source }
     */
    async getPrice() {
        try {
            const url = `${this.hermesUrl}/api/latest_price_feeds?ids[]=${this.priceId}`;

            const response = await axios.get(url, {
                timeout: 5000 // 5 segundos timeout
            });

            if (!response.data || response.data.length === 0) {
                throw new Error('Pyth: resposta vazia da API');
            }

            const priceData = response.data[0];

            if (!priceData || !priceData.price) {
                throw new Error('Pyth: dados de preço inválidos');
            }

            const price = priceData.price;

            // Converter para formato legível (considerando expoente)
            // Exemplo: price.price = 4234550000000, price.expo = -8
            // Resultado: 42345.50000000
            const priceFloat = parseFloat(price.price) * Math.pow(10, price.expo);
            const confidenceFloat = parseFloat(price.conf) * Math.pow(10, price.expo);

            // Validações
            if (priceFloat <= 0) {
                throw new Error('Pyth: preço inválido (<=0)');
            }

            if (confidenceFloat > priceFloat * 0.05) {
                console.warn('⚠️  Pyth: confidence interval alto (>5% do preço)');
            }

            return {
                price: priceFloat,
                confidence: confidenceFloat,
                timestamp: price.publish_time,
                expo: price.expo,
                source: 'Pyth (off-chain)',
                raw: price // Dados brutos para debug
            };

        } catch (error) {
            if (error.code === 'ECONNABORTED') {
                throw new Error('Pyth: timeout ao consultar API');
            }

            if (error.response) {
                throw new Error(`Pyth: HTTP ${error.response.status} - ${error.response.statusText}`);
            }

            throw new Error(`Pyth: ${error.message}`);
        }
    }

    /**
     * Verificar se preço está atualizado (< 1 minuto)
     * @returns {Promise<boolean>}
     */
    async isPriceFresh() {
        try {
            const data = await this.getPrice();
            const ageSeconds = Date.now() / 1000 - data.timestamp;
            return ageSeconds < 60; // Menos de 1 minuto = fresco
        } catch (error) {
            console.error('Pyth: erro ao verificar freshness:', error.message);
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
            if (ageSeconds > 60) {
                issues.push(`Dados antigos (${ageSeconds.toFixed(0)}s)`);
            }

            // Verificar confidence
            const confidencePercent = (data.confidence / data.price) * 100;
            if (confidencePercent > 5) {
                issues.push(`Confidence alto (${confidencePercent.toFixed(2)}%)`);
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
}

module.exports = PythOracle;
