# 🧪 DeltaNeutralVault - Guia Completo TESTNET

> **Arbitrum Sepolia - Chain ID 421614**

Este guia explica como usar a versão **TESTNET** do DeltaNeutralVault, otimizada para desenvolvimento e testes.

---

## 📋 Índice

1. [Diferenças Testnet vs Produção](#diferenças-testnet-vs-produção)
2. [Pré-requisitos](#pré-requisitos)
3. [Setup Rápido](#setup-rápido)
4. [Deploy do Contrato](#deploy-do-contrato)
5. [Funções de Teste](#funções-de-teste)
6. [Keeper Bot - Testnet](#keeper-bot---testnet)
7. [Cenários de Teste](#cenários-de-teste)
8. [Troubleshooting](#troubleshooting)
9. [Recursos Úteis](#recursos-úteis)

---

## 🔄 Diferenças Testnet vs Produção

### **DeltaNeutralVaultV1Testnet.sol**

| Feature | Produção | **Testnet** | Benefício |
|---------|----------|-------------|-----------|
| MIN_DEPOSIT | 0.01 ETH | **0.0001 ETH** | Testar com menos fundos |
| TIMELOCK_DURATION | 2 days | **5 minutes** | Testes rápidos de fees |
| MAX_SLIPPAGE | 3% | **10%** | Menos falhas em testes |
| Funções de Teste | ❌ Não | **✅ 6 funções** | Debug e recovery |
| Debug Events | Mínimo | **Detalhados** | Debugging facilitado |
| Chain Restriction | Qualquer | **Apenas Sepolia** | Segurança |

### **Keeper Bot - Testnet**

| Configuração | Produção | **Testnet** |
|--------------|----------|-------------|
| CHECK_INTERVAL | 60s | **30s** |
| ORACLE_DEVIATION | 5% | **10%** |
| LOG_LEVEL | info | **debug** |
| DRY_RUN default | false | **true** |
| GAS_PRICE_MAX | 50 gwei | **100 gwei** |

---

## ✅ Pré-requisitos

### **1. Software**

```bash
# Node.js 18+
node --version  # v18.0.0+

# npm ou yarn
npm --version

# Git
git --version
```

### **2. Wallet com Fundos Testnet**

**Opção A: Criar nova wallet (recomendado)**

```bash
# Gerar nova private key APENAS para testes
npx hardhat console
> const wallet = ethers.Wallet.createRandom()
> console.log("Address:", wallet.address)
> console.log("Private Key:", wallet.privateKey)
```

**Opção B: Usar wallet existente**

⚠️ **ATENÇÃO:** Use apenas wallet de TESTE! Nunca private key com fundos reais!

### **3. ETH no Arbitrum Sepolia**

**Faucets disponíveis:**

1. **Alchemy** (0.1 ETH/dia):
   ```
   https://www.alchemy.com/faucets/arbitrum-sepolia
   ```

2. **QuickNode**:
   ```
   https://faucet.quicknode.com/arbitrum/sepolia
   ```

3. **Triangle** (via Sepolia ETH):
   ```
   https://faucet.triangleplatform.com/arbitrum/sepolia
   ```

**Mínimo necessário:** 0.01 ETH (para deploy + testes)

### **4. Adicionar Arbitrum Sepolia no Rabby/MetaMask**

```
Network Name: Arbitrum Sepolia
RPC URL: https://sepolia-rollup.arbitrum.io/rpc
Chain ID: 421614
Currency Symbol: ETH
Block Explorer: https://sepolia.arbiscan.io
```

---

## 🚀 Setup Rápido

### **1. Clone do Repositório**

```bash
git clone -b claude/delta-neutral-vault-v1-01BnQkDPrYZRztpwvLpkQdRH \
  https://github.com/Leandrosmoreira/formacao-blockchain-dio.git

cd formacao-blockchain-dio
cd "Modulo 03 Desenvolvimento com Solidity/DeltaNeutralVault"
```

### **2. Instalar Dependências**

```bash
# Instalar dependências do contrato
npm install

# Instalar dependências do keeper
cd keeper-bot
npm install
cd ..
```

### **3. Configurar .env**

```bash
# Copiar template
cp .env.example .env

# Editar
nano .env
```

**Configuração mínima:**

```env
PRIVATE_KEY=sua_private_key_testnet_sem_0x
ARBISCAN_API_KEY=sua_api_key  # Opcional, para verificação
```

### **4. Compilar Contratos**

```bash
npx hardhat compile
```

Deve exibir:
```
✅ Compiled 50 Solidity files successfully
```

---

## 📦 Deploy do Contrato

### **Método 1: Script Automático (Recomendado)**

```bash
npx hardhat run scripts/deploy-testnet.js --network arbitrumSepolia
```

**Output esperado:**

```
╔═══════════════════════════════════════════════════════╗
║   DeltaNeutralVault TESTNET Deploy                   ║
║   Arbitrum Sepolia - Chain ID 421614                 ║
╚═══════════════════════════════════════════════════════╝

📡 Network: arbitrum-sepolia
🆔 Chain ID: 421614
👤 Deployer: 0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb
💰 Saldo: 0.0500 ETH

📦 Deploying DeltaNeutralVaultV1Testnet...
⏳ Aguardando deploy...
✅ Vault deployed: 0xA1B2C3D4E5F6...

⚙️  Configurando fees...
✅ Fees configuradas

🤖 Configurando keeper...
✅ Keeper configurado: 0x742d35Cc...

╔═══════════════════════════════════════════════════════╗
║   ✅ DEPLOY TESTNET COMPLETO!                        ║
╚═══════════════════════════════════════════════════════╝

📝 Salve estas informações:
────────────────────────────────────────────────────────
Vault Address: 0xA1B2C3D4E5F6...
Network: Arbitrum Sepolia (421614)
Deployer: 0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb
────────────────────────────────────────────────────────
```

**💾 Salve o endereço do Vault!** Você vai precisar para o keeper bot.

### **Método 2: Hardhat Console (Manual)**

```bash
npx hardhat console --network arbitrumSepolia
```

```javascript
// Dentro do console
const DeltaNeutralVaultTestnet = await ethers.getContractFactory("DeltaNeutralVaultV1Testnet");

const vault = await DeltaNeutralVaultTestnet.deploy(
  "0x980B62Da83eFf3D4576C647993b0c1D7faf17c73", // WETH
  "0x980B62Da83eFf3D4576C647993b0c1D7faf17c73", // token0
  "0x75faf114eafb1BDbe2F0316DF893fd58CE46AA4d", // token1
  "0x0000000000000000000000000000000000000000", // pool (TODO)
  "0xC36442b4a4522E871399CD717aBDD847Ab11FE88", // positionManager
  "0x101F443B4d1b059569D643917553c771E1b9663E", // swapRouter
  "0x101F443B4d1b059569D643917553c771E1b9663E", // 1inch
  "0x56a43EB56Da12C0dc1D972ACb089c06a5dEF8e69", // chainlink
  "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"  // treasury
);

await vault.waitForDeployment();
console.log("Vault:", await vault.getAddress());
```

---

## 🧪 Funções de Teste

A versão testnet inclui **6 funções exclusivas** para facilitar desenvolvimento:

### **1. testnet_emergencyWithdrawAll()**

**Propósito:** Extrair TUDO do vault (recovery após testes)

```javascript
// Via console
const vault = await ethers.getContractAt(
  "DeltaNeutralVaultV1Testnet",
  "0xVAULT_ADDRESS"
);

await vault.testnet_emergencyWithdrawAll();
```

**O que faz:**
- ✅ Withdraw da posição Uniswap
- ✅ Burn do NFT
- ✅ Transfer todos os tokens para owner
- ✅ Slippage ilimitado (para garantir sucesso)

**Quando usar:**
- Resetar vault após testes
- Recuperar fundos antes de re-deploy
- Situações de emergência

---

### **2. testnet_forceRebalance()**

**Propósito:** Rebalancear SEM validações (testar ranges específicos)

```javascript
await vault.testnet_forceRebalance(
  95000_00000000,  // targetPrice: $95,000 (8 decimals)
  254400,          // newTickLower (múltiplo de tickSpacing)
  255600           // newTickUpper
);
```

**Parâmetros:**
- `targetPrice`: Preço alvo em USD (8 decimals)
- `newTickLower`: Tick inferior do novo range
- `newTickUpper`: Tick superior do novo range

**O que faz:**
- ✅ Exit da posição atual (slippage ilimitado)
- ✅ Atualiza tickLower/tickUpper
- ✅ Cria nova posição com range customizado
- ✅ Emite evento DebugRebalance

**Quando usar:**
- Testar ranges específicos
- Rebalancear manualmente
- Debugging de liquidez

---

### **3. testnet_simulateRebalance()** (view-only)

**Propósito:** Simular rebalance SEM executar (não gasta gas!)

```javascript
const result = await vault.testnet_simulateRebalance(
  95000_00000000  // targetPrice: $95,000
);

console.log("Suggested Range:");
console.log("  tickLower:", result.suggestedTickLower);
console.log("  tickUpper:", result.suggestedTickUpper);
console.log("  amount0:", ethers.formatEther(result.estimatedAmount0));
console.log("  amount1:", ethers.formatEther(result.estimatedAmount1));
console.log("  needsRebalance:", result.needsRebalance);
```

**Retorna:**
- `suggestedTickLower`: Range sugerido (tick inferior)
- `suggestedTickUpper`: Range sugerido (tick superior)
- `estimatedAmount0`: Quantidade estimada de token0
- `estimatedAmount1`: Quantidade estimada de token1
- `needsRebalance`: Se posição atual precisa rebalance

**Quando usar:**
- Testar parâmetros antes de executar
- Ver sugestões de range
- Debugging sem gastar gas

---

### **4. testnet_accrueManagementFee()**

**Propósito:** Acelerar accrual de management fee (simular tempo)

```javascript
// Simular 30 dias passando
await vault.testnet_accrueManagementFee(30 * 24 * 60 * 60);

// Simular 1 ano
await vault.testnet_accrueManagementFee(365 * 24 * 60 * 60);
```

**Parâmetro:**
- `secondsToAccrue`: Quantidade de segundos para simular

**O que faz:**
- ✅ Calcula management fee como se tempo tivesse passado
- ✅ Mint shares para treasury
- ✅ Atualiza lastManagementFeeTimestamp

**Quando usar:**
- Testar accrual de fees sem esperar
- Simular cenários de longo prazo
- Validar cálculos de fees

---

### **5. testnet_getPositionInfo()** (view-only)

**Propósito:** Ver informações detalhadas da posição (debugging)

```javascript
const info = await vault.testnet_getPositionInfo();

console.log("Position Info:");
console.log("  tokenId:", info._tokenId);
console.log("  tickLower:", info._tickLower);
console.log("  tickUpper:", info._tickUpper);
console.log("  currentTick:", info._currentTick);
console.log("  liquidity:", info._liquidity);
console.log("  balance0:", ethers.formatEther(info._balance0));
console.log("  balance1:", ethers.formatEther(info._balance1));
console.log("  inRange:", info._inRange);
```

**Quando usar:**
- Debugging de posição
- Verificar se está in-range
- Ver saldos e liquidez

---

### **6. testnet_resetHighWaterMark()**

**Propósito:** Zerar high water mark (resetar performance fee)

```javascript
await vault.testnet_resetHighWaterMark();
```

**O que faz:**
- ✅ Reseta highWaterMark para 0
- ✅ Permite testar performance fee novamente

**Quando usar:**
- Resetar testes de performance fee
- Começar novo ciclo de testes

---

## 🤖 Keeper Bot - Testnet

### **1. Configurar Keeper**

```bash
cd keeper-bot

# Copiar config de testnet
cp .env.testnet .env

# Editar
nano .env
```

**Edite estas linhas:**

```env
PRIVATE_KEY=sua_private_key_sem_0x
VAULT_ADDRESS=0x...endereço_do_vault_deployado
```

### **2. Testar em Dry Run (Recomendado)**

```bash
# Modo simulação (não executa transações reais)
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
💰 Saldo: 0.0050 ETH
✅ Pyth Oracle: saudável
✅ Chainlink Oracle: saudável

🚀 Keeper iniciado!
⏱️  Intervalo de verificação: 30000ms (30s)

⏰ Tick #1 - 2025-01-15T10:00:00.000Z
────────────────────────────────────────────────────────
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
✅ Posição dentro do range. Sem ação necessária.
```

### **3. Rodar em Produção**

⚠️ **Apenas após testar em DRY_RUN!**

```bash
DRY_RUN=false npm start
```

### **4. Docker (Opcional)**

```bash
# Usar docker-compose testnet
docker compose -f docker-compose.testnet.yml up -d

# Ver logs
docker compose -f docker-compose.testnet.yml logs -f

# Parar
docker compose -f docker-compose.testnet.yml down
```

---

## 📊 Cenários de Teste

### **Cenário 1: Deploy e Primeiro Depósito**

```bash
# 1. Deploy do vault
npx hardhat run scripts/deploy-testnet.js --network arbitrumSepolia

# 2. Aprovar WETH
npx hardhat console --network arbitrumSepolia
```

```javascript
// No console
const weth = await ethers.getContractAt(
  "IERC20",
  "0x980B62Da83eFf3D4576C647993b0c1D7faf17c73"
);

const vault = await ethers.getContractAt(
  "DeltaNeutralVaultV1Testnet",
  "0xVAULT_ADDRESS"
);

// Aprovar 0.001 ETH
await weth.approve(vault.target, ethers.parseEther("0.001"));

// Depositar
await vault.deposit(
  ethers.parseEther("0.001"),
  await vault.signer.getAddress()
);

console.log("Shares recebidas:", await vault.balanceOf(await vault.signer.getAddress()));
```

---

### **Cenário 2: Testar Rebalance Manual**

```javascript
// 1. Ver posição atual
const info = await vault.testnet_getPositionInfo();
console.log("Current tick:", info._currentTick);
console.log("Range:", info._tickLower, "-", info._tickUpper);
console.log("In range:", info._inRange);

// 2. Simular novo rebalance
const sim = await vault.testnet_simulateRebalance(95000_00000000);
console.log("Suggested range:", sim.suggestedTickLower, "-", sim.suggestedTickUpper);

// 3. Executar force rebalance
await vault.testnet_forceRebalance(
  95000_00000000,
  sim.suggestedTickLower,
  sim.suggestedTickUpper
);

// 4. Verificar nova posição
const newInfo = await vault.testnet_getPositionInfo();
console.log("New tick range:", newInfo._tickLower, "-", newInfo._tickUpper);
```

---

### **Cenário 3: Testar Management Fee**

```javascript
// 1. Ver shares atuais do treasury
const treasury = await vault.treasury();
const sharesBefore = await vault.balanceOf(treasury);
console.log("Treasury shares antes:", ethers.formatEther(sharesBefore));

// 2. Simular 30 dias passando
await vault.testnet_accrueManagementFee(30 * 24 * 60 * 60);

// 3. Ver novas shares
const sharesAfter = await vault.balanceOf(treasury);
console.log("Treasury shares depois:", ethers.formatEther(sharesAfter));
console.log("Diferença:", ethers.formatEther(sharesAfter - sharesBefore));
```

---

### **Cenário 4: Testar Keeper Bot**

```bash
# 1. Configurar keeper
cd keeper-bot
cp .env.testnet .env
nano .env  # Adicionar VAULT_ADDRESS

# 2. Testar em dry run
DRY_RUN=true npm start

# Deixar rodar por 5 minutos e observar:
# - Consultas aos oracles a cada 30s
# - Validação de consenso
# - Verificação de range
# - Logs detalhados
```

---

### **Cenário 5: Recovery Completo**

```javascript
// Extrair TUDO do vault (resetar testes)
await vault.testnet_emergencyWithdrawAll();

// Verificar saldos
const token0 = await ethers.getContractAt("IERC20", await vault.token0());
const token1 = await ethers.getContractAt("IERC20", await vault.token1());

console.log("Balance token0:", await token0.balanceOf(await vault.signer.getAddress()));
console.log("Balance token1:", await token1.balanceOf(await vault.signer.getAddress()));
```

---

## 🐛 Troubleshooting

### **Erro: "TestnetOnly: Must be Arbitrum Sepolia"**

**Causa:** Tentando usar funções de testnet em outra network

**Solução:**
```bash
# Verificar network
npx hardhat console --network arbitrumSepolia
> (await ethers.provider.getNetwork()).chainId
# Deve retornar: 421614n
```

---

### **Erro: "Insufficient balance"**

**Causa:** Sem ETH suficiente para gas

**Solução:**
```bash
# Pegar mais ETH
# https://www.alchemy.com/faucets/arbitrum-sepolia
```

---

### **Erro: "Oracles divergindo demais"**

**Causa:** Alta volatilidade ou problema em oracle

**Solução:**
```javascript
// Aumentar desvio permitido (temporariamente)
// No keeper-bot/.env:
MAX_ORACLE_DEVIATION_BPS=1500  # 15%
```

---

### **Keeper não rebalanceia**

**Checklist:**
1. ✅ Wallet é keeper? `await vault.keeper()`
2. ✅ Posição fora do range? `await vault.testnet_getPositionInfo()`
3. ✅ DRY_RUN=false? Verificar .env
4. ✅ Gas suficiente? Ver logs do keeper

---

## 📚 Recursos Úteis

### **Explorers & Faucets**

| Recurso | URL |
|---------|-----|
| Arbiscan Sepolia | https://sepolia.arbiscan.io |
| Alchemy Faucet | https://www.alchemy.com/faucets/arbitrum-sepolia |
| QuickNode Faucet | https://faucet.quicknode.com/arbitrum/sepolia |

### **Oracles**

| Oracle | Feed | Address |
|--------|------|---------|
| Chainlink BTC/USD | Sepolia | `0x56a43EB56Da12C0dc1D972ACb089c06a5dEF8e69` |
| Pyth BTC/USD | Off-chain | API: https://hermes.pyth.network |

### **Uniswap v3**

| Contrato | Address |
|----------|---------|
| NonfungiblePositionManager | `0xC36442b4a4522E871399CD717aBDD847Ab11FE88` |
| SwapRouter | `0x101F443B4d1b059569D643917553c771E1b9663E` |

### **Tokens Testnet**

| Token | Address |
|-------|---------|
| WETH | `0x980B62Da83eFf3D4576C647993b0c1D7faf17c73` |
| USDC | `0x75faf114eafb1BDbe2F0316DF893fd58CE46AA4d` |

---

## 🎯 Checklist de Testes

Antes de ir para produção, teste:

- [ ] Deploy do contrato testnet
- [ ] Deposit mínimo (0.0001 ETH)
- [ ] Withdraw parcial
- [ ] Withdraw total
- [ ] Configurar fees (esperar 5 min timelock)
- [ ] testnet_forceRebalance()
- [ ] testnet_simulateRebalance()
- [ ] testnet_accrueManagementFee()
- [ ] testnet_emergencyWithdrawAll()
- [ ] Keeper bot em DRY_RUN
- [ ] Keeper bot em modo real
- [ ] Verificar logs do keeper
- [ ] Testar com oracles divergindo
- [ ] Testar sem gas suficiente
- [ ] Recovery completo

---

## ⚠️ Avisos Importantes

1. **NUNCA** use private key com fundos reais em testnet
2. **SEMPRE** teste em DRY_RUN primeiro
3. **NUNCA** deploy versão testnet em mainnet
4. **SEMPRE** salve endereços após deploy
5. **LEMBRE-SE:** Funções testnet_ só funcionam em Arbitrum Sepolia

---

## 🆘 Suporte

**Problemas?**

1. Consulte [Troubleshooting](#troubleshooting)
2. Verifique logs: `keeper-bot/logs/combined.log`
3. Teste funções individualmente no console
4. Verifique saldo e network

---

**🎉 Pronto para testar! Boa sorte! 🚀**
