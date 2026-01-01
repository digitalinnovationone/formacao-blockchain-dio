# 🤖 DeltaNeutralVault Keeper Bot

Bot off-chain automatizado para gerenciar rebalanceamento do vault usando **Dual-Oracle Strategy** (Pyth + Chainlink).

---

## 🎯 Estratégia

### Dual-Oracle (ZERO CUSTO!)

```
┌─────────────┐
│ Pyth Oracle │  ← OFF-CHAIN (HTTP API - GRÁTIS!)
└──────┬──────┘
       │
       ├──────→ Validação Cruzada → Média Ponderada
       │
┌──────┴──────┐
│  Chainlink  │  ← ON-CHAIN (reads grátis)
└─────────────┘
```

**Por que Dual-Oracle?**
- ✅ **Pyth**: Preços de alta frequência via API HTTP (ZERO custo!)
- ✅ **Chainlink**: Validação on-chain para segurança
- ✅ **Proteção**: Flash loan attack detection
- ✅ **Confiança**: Score de confidence baseado em divergência

---

## 📦 Instalação

### Pré-requisitos

- Node.js 18+
- npm ou yarn
- Vault deployado no Arbitrum Sepolia
- Private key com saldo mínimo (0.001 ETH para gas)

### Setup

```bash
# 1. Entrar no diretório do keeper
cd keeper-bot

# 2. Instalar dependências
npm install

# 3. Configurar ambiente
cp .env.example .env
nano .env
```

---

## ⚙️ Configuração

### Arquivo .env

```env
# =====================================================
# KEEPER BOT - Configuração
# =====================================================

# Private Key (sem 0x)
PRIVATE_KEY=sua_private_key_aqui

# RPC URL
ARBITRUM_SEPOLIA_RPC_URL=https://sepolia-rollup.arbitrum.io/rpc

# Vault deployado
VAULT_ADDRESS=0x...endereço_do_seu_vault

# Oracles
CHAINLINK_FEED_ADDRESS=0x56a43EB56Da12C0dc1D972ACb089c06a5dEF8e69
PYTH_HERMES_URL=https://hermes.pyth.network
PYTH_PRICE_ID_BTC=0xe62df6c8b4a85fe1a67db44dc12de5db330f7ac66b72dc658afedf0f4a415b43

# Intervalo de verificação (ms)
CHECK_INTERVAL_MS=60000  # 1 minuto

# Desvio máximo aceito entre oracles (bps)
MAX_ORACLE_DEVIATION_BPS=500  # 5%

# Gas máximo (gwei)
MAX_GAS_PRICE_GWEI=50

# Modo dry run (true = simulação, false = real)
DRY_RUN=false
```

---

## 🚀 Executar

### Modo Dry Run (Simulação)

```bash
# Testar sem executar transações reais
DRY_RUN=true npm start
```

**Output esperado:**
```
╔════════════════════════════════════════════════════╗
║   DeltaNeutralVault Keeper - Dual Oracle          ║
║   Pyth (off-chain) + Chainlink (on-chain)         ║
╚════════════════════════════════════════════════════╝

⚠️  DRY RUN MODE - Não executará transações reais!

🏥 Health Check...
✅ Wallet é keeper autorizado
💰 Saldo: 0.0500 ETH
✅ Pyth Oracle: saudável
✅ Chainlink Oracle: saudável

🚀 Keeper iniciado!
⏱️  Intervalo de verificação: 60000ms (60s)
```

### Modo Produção (Real)

```bash
# ⚠️ CUIDADO: Executará transações reais!
DRY_RUN=false npm start

# Ou simplesmente:
npm start
```

---

## 📊 Como Funciona

### Fluxo de Verificação (a cada 60s)

```
1. 📊 Consultar Oracles
   ├─ Pyth (off-chain via HTTP)  ← GRÁTIS!
   └─ Chainlink (on-chain read)  ← GRÁTIS!

2. ✅ Validar Consistência
   ├─ Calcular desvio entre oracles
   ├─ Verificar se < 5% (MAX_ORACLE_DEVIATION_BPS)
   └─ Se > 5%: PULAR (segurança)

3. 💰 Calcular Preço Médio
   └─ Média ponderada 50/50

4. 🎯 Calcular Confidence Score
   └─ 100% - (desvio × 2)

5. 🔍 Verificar Necessidade de Rebalanceamento
   ├─ Obter tick atual
   ├─ Comparar com range [tickLower, tickUpper]
   └─ Se fora do range: REBALANCEAR

6. 🔄 Executar Rebalanceamento (se necessário)
   ├─ Verificar gas price (< MAX_GAS_PRICE_GWEI)
   ├─ Executar autoExit(avgPrice, REBALANCE)
   └─ TODO: autoReenter com novo range otimizado
```

---

## 🛡️ Segurança

### Validação Dual-Oracle

```javascript
// Exemplo de validação
Pyth: $95,000.00
Chainlink: $95,250.00
Desvio: 0.26% ← ✅ OK (< 5%)
Preço médio: $95,125.00
Confidence: 99.48%
```

**Se desvio > 5%:**
```
⚠️  Oracles divergindo demais! Pulando rebalanceamento por segurança.
   Max permitido: 5%
   Atual: 8.5%
```

### Proteção contra Flash Loan Attacks

```javascript
// O validator detecta se:
// - Oracles concordam (< 5% desvio)
// - MAS preço spot no Uniswap difere muito
// → Possível flash loan attack!

attackDetected: true
type: 'FLASH_LOAN_ATTACK'
spotVsOracle: 12.5%  ← Spot muito diferente!
```

---

## 📈 Monitoramento

### Logs

O keeper gera logs detalhados:

```
⏰ Tick #42 - 2025-01-15T10:30:00.000Z
────────────────────────────────────────────────────────────
📊 Consultando oracles...

┌─────────────────────────┬──────────────┐
│ Source                  │ Price (USD)  │
├─────────────────────────┼──────────────┤
│ Pyth (off-chain)        │ $95,123.45   │
│ Chainlink (on-chain)    │ $95,200.00   │
└─────────────────────────┴──────────────┘

✅ Oracles em consenso (desvio: 0.08%)
💰 Preço médio (ponderado): $95,161.73
🎯 Confidence Score: 99.84%

📈 Posição atual:
   Tick atual: 256020
   Range: [255600, 256400]

✅ Posição dentro do range. Sem ação necessária.
⏱️  Tempo de execução: 1234ms
────────────────────────────────────────────────────────────
```

### Estatísticas

Pressione `Ctrl+C` para ver estatísticas:

```
📊 Estatísticas do Keeper:
   Verificações: 142
   Rebalanceamentos: 3
   Erros: 0
   Última verificação: 2025-01-15T10:30:00.000Z
   Último rebalanceamento: 2025-01-15T08:15:22.000Z
```

---

## 🔧 Comandos Úteis

```bash
# Desenvolvimento (auto-restart)
npm run dev

# Produção
npm start

# Verificar sintaxe
npm run lint

# Ver versões
npm list ethers @pythnetwork/pyth-evm-js
```

---

## 🐛 Problemas Comuns

### Erro: "Wallet não é keeper autorizado"

**Solução:**
```javascript
// No console Hardhat ou via Arbiscan:
await vault.setKeeper("SEU_ENDEREÇO");
```

### Erro: "Saldo insuficiente para gas"

**Solução:**
Pegue mais ETH no faucet: https://www.alchemy.com/faucets/arbitrum-sepolia

### Erro: "Oracles divergindo demais"

**Causa:** Alta volatilidade ou problema em um dos oracles

**Solução:**
1. Verificar Pyth: https://pyth.network/price-feeds
2. Verificar Chainlink: https://data.chain.link
3. Aumentar `MAX_ORACLE_DEVIATION_BPS` (com cuidado!)

### Erro: "Cannot connect to RPC"

**Solução:**
1. Verificar `ARBITRUM_SEPOLIA_RPC_URL` no .env
2. Testar outro RPC público:
   ```env
   ARBITRUM_SEPOLIA_RPC_URL=https://arbitrum-sepolia.infura.io/v3/YOUR_KEY
   ```

---

## 📚 Referências

### Oracles

- **Pyth Network**: https://pyth.network
- **Pyth Hermes API**: https://hermes.pyth.network
- **Chainlink BTC/USD**: https://data.chain.link

### Arbitrum Sepolia

- **Explorer**: https://sepolia.arbiscan.io
- **Faucet**: https://www.alchemy.com/faucets/arbitrum-sepolia
- **Chain ID**: 421614

### Documentação

- **Ethers.js v6**: https://docs.ethers.org/v6/
- **Pyth EVM JS**: https://github.com/pyth-network/pyth-crosschain

---

## 🎯 Roadmap

### TODO

- [ ] Implementar cálculo automático de novo range (autoReenter)
- [ ] Adicionar suporte para múltiplos vaults
- [ ] Dashboard web para monitoramento
- [ ] Alertas via Telegram/Discord
- [ ] Integração com serviços como Gelato/Chainlink Automation
- [ ] Métricas de performance (APY, sharpe ratio)

---

## 📄 Licença

MIT

---

## 🆘 Suporte

Se tiver problemas:
1. Verifique os logs do keeper
2. Teste em DRY_RUN mode primeiro
3. Verifique saldo e permissões
4. Consulte a documentação completa em `../VPS_SETUP_COMPLETO.md`

---

**🚀 Keeper rodando 24/7 com ZERO custo de oracle!**
