# 🚀 Deploy no Arbitrum Sepolia via VPS

Guia completo para fazer deploy do DeltaNeutralVaultV1 no Arbitrum Sepolia usando sua VPS.

---

## 📋 Pré-requisitos

### 1. Obter ETH de Teste (Arbitrum Sepolia)

**Faucets Recomendados:**

| Faucet | Quantidade | Link |
|--------|------------|------|
| **Alchemy** ⭐ | 0.1 ETH | https://www.alchemy.com/faucets/arbitrum-sepolia |
| **QuickNode** | 0.05 ETH | https://faucet.quicknode.com/arbitrum/sepolia |
| **Chainlink** | 0.01 ETH | https://faucets.chain.link/arbitrum-sepolia |

**Passos:**
1. Acesse o faucet (recomendado: Alchemy)
2. Cole seu endereço de carteira
3. Aguarde 10-30 segundos
4. Verifique no explorer: https://sepolia.arbiscan.io

---

## ⚙️ Configuração

### 1. Criar arquivo .env

```bash
cd "/home/user/formacao-blockchain-dio/Modulo 03 Desenvolvimento com Solidity/DeltaNeutralVault"

# Copiar exemplo
cp .env.example .env

# Editar com sua private key
nano .env
```

**Conteúdo do .env:**
```env
# Sua private key (SEM o prefixo 0x)
PRIVATE_KEY=sua_private_key_aqui

# RPC Arbitrum Sepolia (público - grátis)
ARBITRUM_SEPOLIA_RPC_URL=https://sepolia-rollup.arbitrum.io/rpc

# Opcional: Alchemy (melhor performance)
# ALCHEMY_API_KEY=seu_api_key
# ARBITRUM_SEPOLIA_RPC_URL=https://arb-sepolia.g.alchemy.com/v2/YOUR_KEY
```

**⚠️ IMPORTANTE:** Nunca commite o arquivo `.env` no git!

---

### 2. Instalar Dependências

```bash
npm install
```

---

### 3. Compilar Contratos

```bash
npx hardhat compile
```

**Output esperado:**
```
Compiled 50 Solidity files successfully
```

---

## 🚀 Deploy

### Método 1: Hardhat (Recomendado)

```bash
npx hardhat run scripts/deploy.js --network arbitrumSepolia
```

**Output esperado:**
```
🚀 Iniciando deploy do DeltaNeutralVaultV1...

📋 Configuração:
- Deployer: 0x...
- Network: arbitrumSepolia
- USDC: 0x...
- Chainlink Feed: 0x...
...

✅ DeltaNeutralVaultV1 deployed to: 0x...
```

---

### Método 2: Foundry (Se instalado)

```bash
# Verificar se Foundry está instalado
forge --version

# Deploy
forge script script/Deploy.s.sol:DeployScript \
  --rpc-url $ARBITRUM_SEPOLIA_RPC_URL \
  --broadcast \
  --verify
```

---

## 📊 Endereços de Contratos - Arbitrum Sepolia

```javascript
// Tokens
USDC: "0x75faf114eafb1BDbe2F0316DF893fd58CE46AA4d"  // Arbitrum Sepolia USDC
WETH: "0x980B62Da83eFf3D4576C647993b0c1D7faf17c73"  // Wrapped ETH

// Chainlink Price Feeds
BTC/USD: "0x56a43EB56Da12C0dc1D972ACb089c06a5dEF8e69"
ETH/USD: "0xd30e2101a97dcbAeBCBC04F14C3f624E67A35165"

// Uniswap v3
Position Manager: "0x6b2937Bde17889EDCf8fbD8dE31C3C2a70Bc4d65"
Swap Router: "0x101F443B4d1b059569D643917553c771E1b9663E"

// 1inch
1inch Router v5: "0x111111125421cA6dc452d289314280a0f8842A65"
```

**⚠️ NOTA:** Estes endereços podem mudar. Sempre verifique a documentação oficial.

---

## 🔍 Verificar Deploy

### 1. No Arbiscan

```
https://sepolia.arbiscan.io/address/SEU_VAULT_ADDRESS
```

### 2. Via Hardhat

```bash
npx hardhat verify --network arbitrumSepolia SEU_VAULT_ADDRESS \
  "USDC_ADDRESS" \
  "Delta Neutral Vault Shares" \
  "dnvUSDC" \
  "CHAINLINK_FEED" \
  "TREASURY_ADDRESS" \
  "POSITION_MANAGER" \
  "SWAP_ROUTER" \
  "ONEINCH_ROUTER"
```

---

## 🧪 Testar o Vault

```bash
# Abrir console Hardhat
npx hardhat console --network arbitrumSepolia
```

```javascript
// No console:
const vault = await ethers.getContractAt(
  'DeltaNeutralVaultV1',
  'SEU_VAULT_ADDRESS'
);

// Verificar configuração
console.log('Owner:', await vault.owner());
console.log('Treasury:', await vault.treasury());
console.log('Total Assets:', await vault.totalAssets());
```

---

## 📈 Custos Estimados (Arbitrum Sepolia)

| Operação | Gas | Custo Estimado (ETH) |
|----------|-----|----------------------|
| Deploy Vault | ~3M gas | ~0.001 ETH |
| setKeeper() | ~50K gas | ~0.00002 ETH |
| setFees() | ~100K gas | ~0.00003 ETH |
| deposit() | ~200K gas | ~0.00006 ETH |

**Total para deploy completo:** ~0.002 ETH

---

## ❌ Troubleshooting

### Erro: "insufficient funds"
```bash
# Verificar saldo
npx hardhat console --network arbitrumSepolia
> (await ethers.provider.getBalance('SEU_ENDEREÇO')).toString()

# Se saldo = 0, pegue mais ETH no faucet
```

### Erro: "nonce too high"
```bash
# Resetar nonce
npx hardhat clean
rm -rf cache artifacts
```

### Erro: "network timeout"
```bash
# Usar RPC alternativo no .env
ARBITRUM_SEPOLIA_RPC_URL=https://arb-sepolia.g.alchemy.com/v2/YOUR_KEY
```

---

## 🎯 Próximos Passos Após Deploy

1. **Configurar Pool Uniswap:**
```javascript
await vault.setUniswapConfig(
  POOL_ADDRESS,
  POSITION_MANAGER,
  SWAP_ROUTER
);
```

2. **Definir Range:**
```javascript
await vault.setRange(tickLower, tickUpper);
```

3. **Testar Deposit:**
```javascript
// Aprovar USDC
await usdc.approve(vaultAddress, amount);

// Depositar
await vault.deposit(amount, yourAddress);
```

---

## 🔗 Links Úteis

- **Arbitrum Sepolia Explorer:** https://sepolia.arbiscan.io
- **Chainlink Feeds:** https://docs.chain.link/data-feeds/price-feeds/addresses?network=arbitrum&page=1#arbitrum-sepolia
- **Uniswap Info:** https://app.uniswap.org
- **1inch API Docs:** https://docs.1inch.io

---

## 💡 Dicas

- ✅ Use Alchemy RPC para melhor performance
- ✅ Sempre teste no console antes de usar na interface
- ✅ Guarde o endereço do vault em local seguro
- ✅ Verifique o contrato no Arbiscan após deploy
- ⚠️ NUNCA compartilhe sua PRIVATE_KEY!

---

**🎉 Pronto! Seu vault está deployado no Arbitrum Sepolia!**
