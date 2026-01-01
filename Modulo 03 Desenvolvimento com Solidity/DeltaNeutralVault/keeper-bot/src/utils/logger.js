const winston = require('winston');
const path = require('path');

/**
 * Sistema de Logging do Keeper
 */
class Logger {
    constructor() {
        const logLevel = process.env.LOG_LEVEL || 'info';
        const logToFile = process.env.LOG_TO_FILE === 'true';

        // Formato customizado
        const customFormat = winston.format.combine(
            winston.format.timestamp({ format: 'YYYY-MM-DD HH:mm:ss' }),
            winston.format.errors({ stack: true }),
            winston.format.printf(({ level, message, timestamp, stack }) => {
                const emoji = this.getLevelEmoji(level);
                if (stack) {
                    return `${timestamp} ${emoji} [${level.toUpperCase()}]: ${message}\n${stack}`;
                }
                return `${timestamp} ${emoji} [${level.toUpperCase()}]: ${message}`;
            })
        );

        // Transports
        const transports = [
            new winston.transports.Console({
                format: winston.format.combine(
                    winston.format.colorize(),
                    customFormat
                )
            })
        ];

        // Adicionar arquivo se configurado
        if (logToFile) {
            transports.push(
                new winston.transports.File({
                    filename: path.join(__dirname, '../../logs/error.log'),
                    level: 'error',
                    format: customFormat
                }),
                new winston.transports.File({
                    filename: path.join(__dirname, '../../logs/combined.log'),
                    format: customFormat
                })
            );
        }

        this.logger = winston.createLogger({
            level: logLevel,
            transports: transports
        });

        this.logger.info(`Logger inicializado (level: ${logLevel})`);
    }

    getLevelEmoji(level) {
        const emojis = {
            error: '❌',
            warn: '⚠️ ',
            info: 'ℹ️ ',
            debug: '🐛'
        };
        return emojis[level] || '📝';
    }

    info(message) {
        this.logger.info(message);
    }

    warn(message) {
        this.logger.warn(message);
    }

    error(message, error = null) {
        if (error) {
            this.logger.error(`${message}: ${error.message}`, { stack: error.stack });
        } else {
            this.logger.error(message);
        }
    }

    debug(message) {
        this.logger.debug(message);
    }

    /**
     * Log de preços com formatação especial
     */
    logPrices(prices) {
        const lines = prices.map(p => `   ${p.source}: $${p.price.toFixed(2)}`);
        this.info('📊 Preços dos Oracles:\n' + lines.join('\n'));
    }

    /**
     * Log de transação
     */
    logTransaction(txHash, action) {
        this.info(`📝 ${action} - TX: ${txHash}`);
    }

    /**
     * Log de alerta crítico
     */
    alert(message) {
        this.logger.error(`🚨 ALERTA: ${message}`);
    }
}

// Singleton
let instance = null;

module.exports = {
    getInstance: () => {
        if (!instance) {
            instance = new Logger();
        }
        return instance;
    }
};
