# 🚀 Quick Start - Deploy Rápido

## ⚠️ LEIA PRIMEIRO

**ETAPA 1 (atual)**: Estrutura base - Funções LP são STUBS
**ETAPA 2 (futura)**: Integração completa com Uniswap v3

### O que funciona agora:
✅ Deposit/Withdraw USDC
✅ Fees (entry, exit, management)
✅ Oracle Chainlink

### O que NÃO funciona:
❌ Abrir/fechar posições LP
❌ Swaps automáticos
❌ Delta-neutral hedge completo

---

## 🏃 Deploy em 5 Passos

### 1️⃣ Instalar Dependências

```bash
cd "Modulo 03 Desenvolvimento com Solidity/DeltaNeutralVault"
npm install
```

### 2️⃣ Configurar Variáveis de Ambiente

```bash
cp .env.example .env
# Edite o .env com seus valores
```

**Arquivo `.env`:**
```bash
PRIVATE_KEY=0xsua_chave_privada_aqui
AIRBITHON_RPC_URL=https://rpc.airbithon.network
AIRBITHON_CHAIN_ID=123456  # Ajuste conforme a rede
```

### 3️⃣ Compilar

```bash
npm run compile
```

**Deve compilar sem erros!**

### 4️⃣ Ajustar Endereços no Script

Edite `scripts/deploy.js` (linhas 11-12):

```javascript
const USDC_ADDRESS = "0x..."; // Endereço do USDC na sua rede
const CHAINLINK_FEED = "0x..."; // Price feed WBTC/USD
```

### 5️⃣ Fazer Deploy

```bash
# Para Airbithon
npm run deploy:airbithon

# OU para Sepolia (testnet)
npm run deploy:sepolia
```

---

## 📋 Endereços Necessários

Você precisa descobrir/fornecer:

| Item | Descrição | Onde encontrar |
|------|-----------|----------------|
| **USDC** | Token USDC na rede | Docs da Airbithon |
| **Chainlink Feed** | Price feed WBTC/USD | [Chainlink Docs](https://docs.chain.link/data-feeds) |
| **Pool Uniswap v3** | Pool WBTC/USDC | [Uniswap](https://app.uniswap.org/pools) |

---

## 🎯 Depois do Deploy

### Configurar Pool (obrigatório para Etapa 2)

```javascript
// No console do Hardhat ou via script
const vault = await ethers.getContractAt(
  "DeltaNeutralVaultV1",
  "0xSeuVaultAddress"
);

// Definir endereço da pool
await vault.setUniswapPool("0xPoolWBTC_USDC");

// Definir range (exemplo: full range)
await vault.setRange(-887220, 887220);
```

### Testar Deposit (Etapa 1 funciona!)

```javascript
const usdc = await ethers.getContractAt("IERC20", USDC_ADDRESS);

// Aprovar
await usdc.approve(vaultAddress, ethers.parseUnits("100", 6));

// Depositar
await vault.deposit(ethers.parseUnits("100", 6), yourAddress);

// Ver shares
const shares = await vault.balanceOf(yourAddress);
console.log("Shares:", ethers.formatUnits(shares, 18));
```

---

## 🔍 Verificar Deploy

Após o deploy, você verá:

```
✅ DeltaNeutralVaultV1 deployed to: 0x1234...
✅ Keeper definido: 0xabc...
✅ Fees configuradas
🎉 DEPLOY COMPLETO!
```

Os endereços ficam salvos em: `deployment.json`

---

## ❓ Troubleshooting

### Erro: "Cannot find module 'dotenv'"
```bash
npm install dotenv
```

### Erro: "Cannot find module '@openzeppelin/contracts'"
```bash
npm install
```

### Erro: "insufficient funds"
```bash
# Adicione fundos na sua carteira
# Para testnet, use um faucet
```

### Erro na compilação
```bash
npm run clean
npm run compile
```

---

## 📦 Estrutura de Arquivos

```
DeltaNeutralVault/
├── DeltaNeutralVaultV1.sol    ← Contrato principal
├── scripts/
│   └── deploy.js              ← Script de deploy
├── .env                       ← Suas variáveis (crie isto!)
├── .env.example               ← Exemplo de .env
├── hardhat.config.js          ← Configuração Hardhat
├── package.json               ← Dependências
├── DEPLOY.md                  ← Guia completo de deploy
└── QUICKSTART.md              ← Este arquivo
```

---

## 🎯 Próximos Passos

1. ✅ Deploy na devnet (Etapa 1)
2. ⏳ Implementar Etapa 2 (integração Uniswap v3 real)
3. ⏳ Criar keeper off-chain
4. ⏳ Testes completos
5. ⏳ Auditoria de segurança

---

## 💡 Quer Funcionalidade Completa?

A **Etapa 2** implementará:
- ✅ Integração real com Uniswap v3 (mint/burn posições)
- ✅ Swaps via Uniswap Router
- ✅ Cálculo de liquidez e ranges
- ✅ Delta-neutral hedge completo
- ✅ Keeper automatizado

**Avise se quer que eu implemente a Etapa 2!**

---

## 📞 Suporte

Problemas? Verifique:
1. [DEPLOY.md](./DEPLOY.md) - Guia completo
2. [README.md](./README.md) - Documentação da arquitetura
3. [SETUP.md](./SETUP.md) - Instalação e compilação

---

**Status**: Etapa 1 completa ✅
**Próximo**: Etapa 2 (integração Uniswap v3) ⏳
