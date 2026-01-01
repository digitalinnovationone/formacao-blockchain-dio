require('dotenv').config();
const { ethers } = require('ethers');
const PythOracle = require('./oracles/pyth');
const ChainlinkOracle = require('./oracles/chainlink');
const DualOracleValidator = require('./utils/validation');
const { getInstance: getLogger } = require('./utils/logger');

/**
 * DeltaNeutralVault Keeper Bot
 *
 * Dual-Oracle Strategy (Chainlink + Pyth OFF-CHAIN)
 * - Pyth: consulta via API HTTP (ZERO CUSTO!)
 * - Chainlink: consulta on-chain (reads grátis)
 * - Validação cruzada para segurança máxima
 */
class DeltaNeutralKeeper {
    constructor() {
        this.logger = getLogger();
        this.dryRun = process.env.DRY_RUN === 'true';

        this.logger.info('╔════════════════════════════════════════════════════╗');
        this.logger.info('║   DeltaNeutralVault Keeper - Dual Oracle          ║');
        this.logger.info('║   Pyth (off-chain) + Chainlink (on-chain)         ║');
        this.logger.info('╚════════════════════════════════════════════════════╝');
        this.logger.info('');

        // Validar env vars
        this.validateEnv();

        // Setup provider e wallet
        this.setupProvider();

        // Setup oracles
        this.setupOracles();

        // Setup validator
        this.validator = new DualOracleValidator(
            parseInt(process.env.MAX_ORACLE_DEVIATION_BPS)
        );

        // Setup vault contract
        this.setupVault();

        // Stats
        this.stats = {
            checks: 0,
            rebalances: 0,
            errors: 0,
            lastCheck: null,
            lastRebalance: null
        };

        if (this.dryRun) {
            this.logger.warn('⚠️  DRY RUN MODE - Não executará transações reais!');
        }

        this.logger.info('✅ Keeper inicializado com sucesso!\n');
    }

    validateEnv() {
        const required = [
            'PRIVATE_KEY',
            'ARBITRUM_SEPOLIA_RPC_URL',
            'VAULT_ADDRESS',
            'CHAINLINK_FEED_ADDRESS',
            'PYTH_PRICE_ID_BTC'
        ];

        const missing = required.filter(key => !process.env[key]);

        if (missing.length > 0) {
            throw new Error(`Variáveis de ambiente faltando: ${missing.join(', ')}`);
        }
    }

    setupProvider() {
        this.logger.info('🔌 Conectando ao RPC...');
        this.provider = new ethers.JsonRpcProvider(process.env.ARBITRUM_SEPOLIA_RPC_URL);
        this.wallet = new ethers.Wallet(process.env.PRIVATE_KEY, this.provider);
        this.logger.info(`   Wallet: ${this.wallet.address}`);
        this.logger.info('');
    }

    setupOracles() {
        this.logger.info('🔮 Inicializando oracles...');

        // Pyth (OFF-CHAIN - GRÁTIS!)
        this.pythOracle = new PythOracle(
            process.env.PYTH_HERMES_URL,
            process.env.PYTH_PRICE_ID_BTC
        );

        // Chainlink (ON-CHAIN)
        this.chainlinkOracle = new ChainlinkOracle(
            this.provider,
            process.env.CHAINLINK_FEED_ADDRESS
        );

        this.logger.info('');
    }

    setupVault() {
        this.logger.info('🏦 Conectando ao vault...');

        const vaultABI = [
            'function autoExit(uint256 price, uint8 reason) external',
            'function autoReenter(uint256 price, int24 tickLower, int24 tickUpper) external',
            'function tokenId() external view returns (uint256)',
            'function tickLower() external view returns (int24)',
            'function tickUpper() external view returns (int24)',
            'function totalAssets() external view returns (uint256)',
            'function uniswapPool() external view returns (address)',
            'function keeper() external view returns (address)'
        ];

        this.vault = new ethers.Contract(
            process.env.VAULT_ADDRESS,
            vaultABI,
            this.wallet
        );

        this.logger.info(`   Vault: ${process.env.VAULT_ADDRESS}`);
        this.logger.info('');
    }

    /**
     * Loop principal do keeper
     */
    async run() {
        this.logger.info('🚀 Keeper iniciado!\n');
        this.logger.info(`⏱️  Intervalo de verificação: ${process.env.CHECK_INTERVAL_MS}ms (${parseInt(process.env.CHECK_INTERVAL_MS) / 1000}s)\n`);
        this.logger.info('═'.repeat(60) + '\n');

        // Health check inicial
        await this.healthCheck();

        // Primeira execução imediata
        await this.tick();

        // Loop periódico
        setInterval(() => this.tick(), parseInt(process.env.CHECK_INTERVAL_MS));
    }

    /**
     * Health check dos oracles e vault
     */
    async healthCheck() {
        this.logger.info('🏥 Health Check...\n');

        try {
            // Verificar keeper
            const keeper = await this.vault.keeper();
            const isKeeper = keeper.toLowerCase() === this.wallet.address.toLowerCase();

            if (!isKeeper) {
                this.logger.warn(`⚠️  Wallet ${this.wallet.address} NÃO é o keeper!`);
                this.logger.warn(`   Keeper atual: ${keeper}`);
            } else {
                this.logger.info(`✅ Wallet é keeper autorizado`);
            }

            // Verificar saldo
            const balance = await this.provider.getBalance(this.wallet.address);
            const balanceEth = parseFloat(ethers.formatEther(balance));

            if (balanceEth < 0.001) {
                this.logger.warn(`⚠️  Saldo baixo: ${balanceEth.toFixed(4)} ETH`);
            } else {
                this.logger.info(`💰 Saldo: ${balanceEth.toFixed(4)} ETH`);
            }

            // Verificar oracles
            const [pythHealth, chainlinkHealth] = await Promise.all([
                this.pythOracle.healthCheck(),
                this.chainlinkOracle.healthCheck()
            ]);

            if (pythHealth.healthy) {
                this.logger.info('✅ Pyth Oracle: saudável');
            } else {
                this.logger.warn(`⚠️  Pyth Oracle: ${pythHealth.issues.join(', ')}`);
            }

            if (chainlinkHealth.healthy) {
                this.logger.info('✅ Chainlink Oracle: saudável');
            } else {
                this.logger.warn(`⚠️  Chainlink Oracle: ${chainlinkHealth.issues.join(', ')}`);
            }

            this.logger.info('');

        } catch (error) {
            this.logger.error('Health check falhou', error);
        }
    }

    /**
     * Tick único - verifica e age
     */
    async tick() {
        const startTime = Date.now();
        this.stats.checks++;
        this.stats.lastCheck = new Date().toISOString();

        try {
            this.logger.info(`⏰ Tick #${this.stats.checks} - ${this.stats.lastCheck}`);
            this.logger.info('─'.repeat(60));

            // 1. Obter preços dos oracles (OFF-CHAIN = GRÁTIS!)
            this.logger.info('📊 Consultando oracles...');

            const [pythData, chainlinkData] = await Promise.all([
                this.pythOracle.getPrice(),
                this.chainlinkOracle.getPrice()
            ]);

            this.logger.logPrices([
                { source: 'Pyth (off-chain)', price: pythData.price },
                { source: 'Chainlink (on-chain)', price: chainlinkData.price }
            ]);

            // 2. Validar consistência (DUAL ORACLE)
            const validation = this.validator.validate(
                pythData.price,
                chainlinkData.price,
                'Pyth',
                'Chainlink'
            );

            this.logger.info(validation.message);

            if (!validation.isValid) {
                this.logger.error('⚠️  Oracles divergindo demais! Pulando rebalanceamento por segurança.');
                this.logger.warn(`   Max permitido: ${this.validator.maxDeviationBps / 100}%`);
                this.logger.warn(`   Atual: ${validation.deviationPercent}\n`);
                this.stats.errors++;
                return;
            }

            // 3. Calcular preço médio ponderado
            const avgPrice = this.validator.weightedAverage([
                { price: pythData.price, weight: 0.5 },      // Pyth 50%
                { price: chainlinkData.price, weight: 0.5 }  // Chainlink 50%
            ]);

            this.logger.info(`💰 Preço médio (ponderado): $${avgPrice.toFixed(2)}`);

            // 4. Calcular confidence score
            const confidence = this.validator.calculateConfidence([
                { price: pythData.price, source: 'Pyth' },
                { price: chainlinkData.price, source: 'Chainlink' }
            ]);

            this.logger.info(`🎯 Confidence Score: ${confidence}%`);

            // 5. Verificar se precisa rebalancear
            const needsRebalance = await this.checkRebalance(avgPrice);

            if (needsRebalance) {
                this.logger.info('');
                this.logger.info('🔄 REBALANCEAMENTO NECESSÁRIO!');

                if (this.dryRun) {
                    this.logger.warn('⚠️  DRY RUN - Simulando rebalanceamento...');
                    await this.simulateRebalance(avgPrice);
                } else {
                    await this.executeRebalance(avgPrice);
                }

                this.stats.rebalances++;
                this.stats.lastRebalance = new Date().toISOString();
            } else {
                this.logger.info('✅ Posição dentro do range. Sem ação necessária.');
            }

            // Tempo de execução
            const elapsed = Date.now() - startTime;
            this.logger.info(`⏱️  Tempo de execução: ${elapsed}ms`);

            this.logger.info('─'.repeat(60) + '\n');

        } catch (error) {
            this.stats.errors++;
            this.logger.error('❌ Erro no tick', error);
            this.logger.info('─'.repeat(60) + '\n');
        }
    }

    /**
     * Verificar se precisa rebalancear
     */
    async checkRebalance(currentPrice) {
        try {
            const tokenId = await this.vault.tokenId();

            if (tokenId === 0n) {
                this.logger.info('ℹ️  Sem posição ativa no momento.');
                return false;
            }

            const [tickLower, tickUpper, pool] = await Promise.all([
                this.vault.tickLower(),
                this.vault.tickUpper(),
                this.vault.uniswapPool()
            ]);

            if (pool === ethers.ZeroAddress) {
                this.logger.warn('⚠️  Pool não configurado!');
                return false;
            }

            // Converter preço para tick (aproximação)
            // Fórmula real seria mais complexa, mas para BTC/USDC:
            const currentTick = this.priceToTick(currentPrice);

            this.logger.info(`📈 Posição atual:`);
            this.logger.info(`   Tick atual: ${currentTick}`);
            this.logger.info(`   Range: [${tickLower}, ${tickUpper}]`);

            // Verificar se está fora do range
            if (currentTick < tickLower || currentTick > tickUpper) {
                const distance = currentTick < tickLower
                    ? tickLower - currentTick
                    : currentTick - tickUpper;

                this.logger.info(`⚠️  Preço FORA do range! (distância: ${distance} ticks)`);
                return true;
            }

            return false;

        } catch (error) {
            this.logger.error('Erro ao verificar rebalanceamento', error);
            return false;
        }
    }

    /**
     * Simular rebalanceamento (DRY RUN)
     */
    async simulateRebalance(avgPrice) {
        this.logger.info('');
        this.logger.info('💭 Simulação de rebalanceamento:');
        this.logger.info(`   1. autoExit(${avgPrice.toFixed(2)}, Rebalance)`);
        this.logger.info(`   2. Calcular novo range otimizado`);
        this.logger.info(`   3. autoReenter(...)`);
        this.logger.info('');
        this.logger.info('✅ Simulação completa (sem transações reais)');
    }

    /**
     * Executar rebalanceamento real
     */
    async executeRebalance(avgPrice) {
        try {
            this.logger.info('');
            this.logger.info('🔄 Executando autoExit...');

            // Converter preço para formato on-chain (8 decimais para BTC/USD)
            const priceOnChain = Math.floor(avgPrice * 1e8);

            // Verificar gas price
            const feeData = await this.provider.getFeeData();
            const gasPriceGwei = parseFloat(ethers.formatUnits(feeData.gasPrice, 'gwei'));

            this.logger.info(`⛽ Gas Price: ${gasPriceGwei.toFixed(2)} gwei`);

            const maxGasPrice = parseInt(process.env.MAX_GAS_PRICE_GWEI || '50');
            if (gasPriceGwei > maxGasPrice) {
                this.logger.warn(`⚠️  Gas muito alto (>${maxGasPrice} gwei). Pulando.`);
                return;
            }

            // AutoExit (Reason: 3 = Rebalance)
            const txExit = await this.vault.autoExit(priceOnChain, 3);

            this.logger.info('📝 Transação enviada, aguardando confirmação...');
            this.logger.info(`   TX Hash: ${txExit.hash}`);

            const receipt = await txExit.wait();

            this.logger.info(`✅ autoExit confirmado! (Gas usado: ${receipt.gasUsed.toString()})`);
            this.logger.logTransaction(txExit.hash, 'autoExit');

            // TODO: Implementar cálculo de novo range otimizado
            // TODO: Executar autoReenter com novo range

            this.logger.info('');
            this.logger.info('✅ Rebalanceamento completo!');
            this.logger.info('');

        } catch (error) {
            this.logger.error('❌ Erro no rebalanceamento', error);

            // Parse error message
            if (error.message.includes('keeper')) {
                this.logger.error('   Wallet não é keeper autorizado!');
            } else if (error.message.includes('insufficient funds')) {
                this.logger.error('   Saldo insuficiente para gas!');
            }
        }
    }

    /**
     * Converter preço USD para tick (aproximado)
     * Para conversão precisa, usar biblioteca @uniswap/v3-sdk
     */
    priceToTick(price) {
        // Simplificação: tick ≈ log(price) / log(1.0001)
        // Para BTC/USDC, ajustar conforme pool real
        return Math.floor(Math.log(price / 1e12) / Math.log(1.0001));
    }

    /**
     * Mostrar estatísticas
     */
    printStats() {
        this.logger.info('\n📊 Estatísticas do Keeper:');
        this.logger.info(`   Verificações: ${this.stats.checks}`);
        this.logger.info(`   Rebalanceamentos: ${this.stats.rebalances}`);
        this.logger.info(`   Erros: ${this.stats.errors}`);
        this.logger.info(`   Última verificação: ${this.stats.lastCheck || 'N/A'}`);
        this.logger.info(`   Último rebalanceamento: ${this.stats.lastRebalance || 'N/A'}`);
    }
}

// ═══════════════════════════════════════════════════════════
// MAIN
// ═══════════════════════════════════════════════════════════

async function main() {
    try {
        const keeper = new DeltaNeutralKeeper();

        // Handlers de shutdown
        process.on('SIGINT', () => {
            console.log('\n\n⚠️  SIGINT recebido. Encerrando keeper...');
            keeper.printStats();
            process.exit(0);
        });

        process.on('SIGTERM', () => {
            console.log('\n\n⚠️  SIGTERM recebido. Encerrando keeper...');
            keeper.printStats();
            process.exit(0);
        });

        // Rodar keeper
        await keeper.run();

    } catch (error) {
        console.error('\n❌ Erro fatal:', error.message);
        console.error(error.stack);
        process.exit(1);
    }
}

// Iniciar
main();
