# ⚡ DeltaNeutralVault - Guia Foundry (Testnet)

> **Usando Foundry ao invés de Hardhat**

Este guia mostra como usar **Foundry** para deploy e testes do DeltaNeutralVault no Arbitrum Sepolia.

---

## 📋 Índice

1. [Por que Foundry?](#por-que-foundry)
2. [Instalação](#instalação)
3. [Setup Rápido](#setup-rápido)
4. [Compilar Contratos](#compilar-contratos)
5. [Deploy Testnet](#deploy-testnet)
6. [Testar Funções](#testar-funções)
7. [Comandos Úteis](#comandos-úteis)
8. [Hardhat vs Foundry](#hardhat-vs-foundry)

---

## ⚡ Por que Foundry?

| Feature | Hardhat | **Foundry** |
|---------|---------|-------------|
| Linguagem | JavaScript | **Solidity** ✅ |
| Velocidade | ~30s compile | **~3s compile** 🚀 |
| Testes | JS (Mocha) | **Solidity (Fuzzing)** ✅ |
| Gas reports | Básico | **Detalhado** 📊 |
| Scripts | JavaScript | **Solidity** ✅ |
| Debugging | console.log | **Traces + Debug** 🔍 |

**Foundry = Mais rápido, mais nativo Solidity!**

---

## 📦 Instalação

### **1. Instalar Foundry**

```bash
# Instalar foundryup
curl -L https://foundry.paradigm.xyz | bash

# Instalar forge, cast, anvil
foundryup

# Verificar instalação
forge --version
cast --version
```

### **2. Instalar Dependências**

```bash
cd "Modulo 03 Desenvolvimento com Solidity/DeltaNeutralVault"

# Instalar deps (OpenZeppelin, Chainlink, Uniswap)
forge install
```

---

## 🚀 Setup Rápido

### **1. Configurar .env**

```bash
cp .env.example .env
nano .env
```

```env
# Private Key (sem 0x)
PRIVATE_KEY=sua_private_key_testnet_sem_0x

# RPC URL - Arbitrum Sepolia
ARBITRUM_SEPOLIA_RPC_URL=https://sepolia-rollup.arbitrum.io/rpc

# Arbiscan API (opcional, para verificação)
ARBISCAN_API_KEY=sua_api_key_arbiscan
```

### **2. Carregar .env**

```bash
source .env

# Ou use direnv (recomendado)
echo "dotenv" > .envrc
direnv allow
```

---

## 🔨 Compilar Contratos

```bash
# Compilar todos os contratos
forge build

# Compilar com otimização
forge build --optimize --optimizer-runs 200

# Ver tamanho dos contratos
forge build --sizes
```

**Output esperado:**

```
[⠢] Compiling...
[⠆] Compiling 50 files with 0.8.20
[⠰] Solc 0.8.20 finished in 2.95s
Compiler run successful!
```

**Muito mais rápido que Hardhat! 🚀**

---

## 🎯 Deploy Testnet

### **Método 1: Deploy com Broadcast (Real)**

```bash
# Deploy no Arbitrum Sepolia
forge script script/DeployTestnet.s.sol:DeployTestnetScript \
  --rpc-url arbitrum_sepolia \
  --broadcast \
  --verify \
  -vvvv
```

**O que acontece:**
1. ✅ Valida Chain ID (deve ser 421614)
2. ✅ Verifica saldo do deployer
3. ✅ Deploy DeltaNeutralVaultV1Testnet
4. ✅ Configura fees
5. ✅ Configura keeper
6. ✅ Verifica contrato no Arbiscan (se --verify)
7. ✅ Salva deployment info em JSON

**Output esperado:**

```
========================================================
   DeltaNeutralVault TESTNET Deploy - Foundry
   Arbitrum Sepolia - Chain ID 421614
========================================================

Chain ID: 421614
Deployer: 0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb
Balance: 0.0500 ETH
Treasury: 0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb

Deploying DeltaNeutralVaultV1Testnet...
--------------------------------------------------------
Vault deployed: 0xA1B2C3D4E5F6789...

Configurando fees...
Fees configuradas:
  - Performance: 10%
  - Management: 5%
  - Entry: 0%
  - Exit: 0%
  - Swap: 5%
  - Keeper: 3%

Configurando keeper...
Keeper configurado: 0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb

========================================================
   DEPLOY TESTNET COMPLETO!
========================================================

Vault Address: 0xA1B2C3D4E5F6789...
Network: Arbitrum Sepolia (421614)
Deployer: 0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb

Deployment info salvo em: deployments/testnet-foundry-1705324800.json
```

**💾 Salve o endereço do Vault!**

---

### **Método 2: Dry Run (Simulação)**

```bash
# Simular deploy SEM executar (zero custo!)
forge script script/DeployTestnet.s.sol:DeployTestnetScript \
  --rpc-url arbitrum_sepolia \
  -vvvv
```

**Benefício:** Ver o que vai acontecer antes de gastar gas!

---

### **Método 3: Deploy com RPC Público (sem .env)**

```bash
# Usar RPC público direto
forge script script/DeployTestnet.s.sol:DeployTestnetScript \
  --rpc-url https://sepolia-rollup.arbitrum.io/rpc \
  --private-key $PRIVATE_KEY \
  --broadcast \
  -vvvv
```

---

## 🧪 Testar Funções

### **1. Chamar Funções View (sem gas)**

```bash
# Ver posição atual
cast call 0xVAULT_ADDRESS \
  "testnet_getPositionInfo()(uint256,int24,int24,int24,uint128,uint256,uint256,bool)" \
  --rpc-url arbitrum_sepolia

# Simular rebalance
cast call 0xVAULT_ADDRESS \
  "testnet_simulateRebalance(uint256)(int24,int24,uint256,uint256,bool)" \
  9500000000000 \
  --rpc-url arbitrum_sepolia
```

---

### **2. Executar Transações**

```bash
# Emergency withdraw (extrai tudo)
cast send 0xVAULT_ADDRESS \
  "testnet_emergencyWithdrawAll()" \
  --rpc-url arbitrum_sepolia \
  --private-key $PRIVATE_KEY

# Force rebalance
cast send 0xVAULT_ADDRESS \
  "testnet_forceRebalance(uint256,int24,int24)" \
  9500000000000 254400 255600 \
  --rpc-url arbitrum_sepolia \
  --private-key $PRIVATE_KEY

# Acelerar management fee (simular 30 dias)
cast send 0xVAULT_ADDRESS \
  "testnet_accrueManagementFee(uint256)" \
  2592000 \
  --rpc-url arbitrum_sepolia \
  --private-key $PRIVATE_KEY
```

---

### **3. Ver Eventos**

```bash
# Ver todos os eventos do vault
cast logs --from-block 0 \
  --address 0xVAULT_ADDRESS \
  --rpc-url arbitrum_sepolia

# Ver evento específico (TestnetForceRebalance)
cast logs --from-block 0 \
  --address 0xVAULT_ADDRESS \
  --events "TestnetForceRebalance(int24,int24,int24,int24,uint256)" \
  --rpc-url arbitrum_sepolia
```

---

### **4. Deposit de Teste**

```bash
# 1. Aprovar WETH
cast send 0x980B62Da83eFf3D4576C647993b0c1D7faf17c73 \
  "approve(address,uint256)" \
  0xVAULT_ADDRESS \
  1000000000000000 \
  --rpc-url arbitrum_sepolia \
  --private-key $PRIVATE_KEY

# 2. Depositar 0.001 ETH
cast send 0xVAULT_ADDRESS \
  "deposit(uint256,address)" \
  1000000000000000 \
  0xYOUR_ADDRESS \
  --rpc-url arbitrum_sepolia \
  --private-key $PRIVATE_KEY

# 3. Ver shares recebidas
cast call 0xVAULT_ADDRESS \
  "balanceOf(address)(uint256)" \
  0xYOUR_ADDRESS \
  --rpc-url arbitrum_sepolia
```

---

## 🛠️ Comandos Úteis

### **Build & Compile**

```bash
# Compilar
forge build

# Compilar só um arquivo
forge build --force src/DeltaNeutralVaultV1Testnet.sol

# Ver tamanho
forge build --sizes

# Limpar cache
forge clean
```

---

### **Testes**

```bash
# Rodar testes
forge test

# Testes com verbosity
forge test -vvvv

# Testar contrato específico
forge test --match-contract VaultTest

# Testar função específica
forge test --match-test testDeposit

# Gas report
forge test --gas-report

# Coverage
forge coverage
```

---

### **Verificação no Arbiscan**

```bash
# Verificar contrato
forge verify-contract \
  0xVAULT_ADDRESS \
  src/DeltaNeutralVaultV1Testnet.sol:DeltaNeutralVaultV1Testnet \
  --chain arbitrum-sepolia \
  --etherscan-api-key $ARBISCAN_API_KEY \
  --constructor-args $(cast abi-encode "constructor(address,address,address,address,address,address,address,address,address)" \
    0x980B62Da83eFf3D4576C647993b0c1D7faf17c73 \
    0x980B62Da83eFf3D4576C647993b0c1D7faf17c73 \
    0x75faf114eafb1BDbe2F0316DF893fd58CE46AA4d \
    0x0000000000000000000000000000000000000000 \
    0xC36442b4a4522E871399CD717aBDD847Ab11FE88 \
    0x101F443B4d1b059569D643917553c771E1b9663E \
    0x101F443B4d1b059569D643917553c771E1b9663E \
    0x56a43EB56Da12C0dc1D972ACb089c06a5dEF8e69 \
    0xYOUR_TREASURY)
```

**Ou usar --verify no deploy:**

```bash
forge script script/DeployTestnet.s.sol:DeployTestnetScript \
  --rpc-url arbitrum_sepolia \
  --broadcast \
  --verify \
  -vvvv
```

---

### **Debugging**

```bash
# Debug de transação
forge debug \
  --rpc-url arbitrum_sepolia \
  0xTRANSACTION_HASH

# Trace de transação
cast run \
  0xTRANSACTION_HASH \
  --rpc-url arbitrum_sepolia \
  --debug
```

---

### **Gas Estimation**

```bash
# Estimar gas para função
cast estimate \
  0xVAULT_ADDRESS \
  "testnet_forceRebalance(uint256,int24,int24)" \
  9500000000000 254400 255600 \
  --rpc-url arbitrum_sepolia

# Ver gas price atual
cast gas-price --rpc-url arbitrum_sepolia

# Ver base fee
cast basefee --rpc-url arbitrum_sepolia
```

---

### **Storage Inspection**

```bash
# Ver storage slot
cast storage 0xVAULT_ADDRESS 0 --rpc-url arbitrum_sepolia

# Ver todas as variáveis
cast storage 0xVAULT_ADDRESS --rpc-url arbitrum_sepolia
```

---

### **Utils**

```bash
# Converter endereço para uint256
cast --to-uint256 0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb

# Converter hex para dec
cast --to-dec 0x1234

# Converter dec para hex
cast --to-hex 4660

# Hash keccak256
cast keccak "Transfer(address,address,uint256)"

# ABI encode
cast abi-encode "transfer(address,uint256)" 0x... 1000000

# ABI decode
cast abi-decode "transfer(address,uint256)" 0x...
```

---

## ⚖️ Hardhat vs Foundry

### **Equivalências de Comandos**

| Tarefa | Hardhat | **Foundry** |
|--------|---------|-------------|
| Compilar | `npx hardhat compile` | `forge build` |
| Deploy | `npx hardhat run scripts/deploy.js --network arbitrumSepolia` | `forge script script/Deploy.s.sol --rpc-url arbitrum_sepolia --broadcast` |
| Testar | `npx hardhat test` | `forge test` |
| Console | `npx hardhat console --network arbitrumSepolia` | `cast call/send` |
| Verificar | `npx hardhat verify` | `forge verify-contract` |
| Gas report | `REPORT_GAS=true npx hardhat test` | `forge test --gas-report` |
| Flatten | `npx hardhat flatten` | `forge flatten` |

---

### **Quando usar cada um?**

**Use Foundry quando:**
- ✅ Quer velocidade máxima
- ✅ Prefere escrever testes em Solidity
- ✅ Precisa de fuzzing/invariant testing
- ✅ Quer gas reports detalhados
- ✅ Debugging avançado (traces)

**Use Hardhat quando:**
- ✅ Time já conhece JavaScript
- ✅ Precisa de plugins específicos do Hardhat
- ✅ Integração com frontend em JS
- ✅ Testes complexos com mocks em JS

---

## 📚 Arquivos do Projeto

```
DeltaNeutralVault/
├── foundry.toml                        # Config Foundry ✅
├── script/
│   ├── Deploy.s.sol                    # Deploy produção (Foundry)
│   └── DeployTestnet.s.sol            # Deploy testnet (Foundry) ⭐ NOVO
├── scripts/
│   ├── deploy.js                       # Deploy (Hardhat)
│   └── deploy-testnet.js              # Deploy testnet (Hardhat)
├── src/  ou  ./
│   ├── DeltaNeutralVaultV1.sol        # Contrato principal
│   └── DeltaNeutralVaultV1Testnet.sol # Versão testnet ⭐
├── test/
│   └── (testes Foundry aqui)
├── hardhat.config.js                   # Config Hardhat
└── package.json                        # Deps Node.js (keeper bot)
```

**Você pode usar AMBOS! Foundry para desenvolvimento, Hardhat para keeper bot em Node.js**

---

## 🎯 Workflow Recomendado

### **1. Desenvolvimento (Foundry)**

```bash
# Compilar
forge build

# Testar
forge test -vvv

# Deploy testnet
forge script script/DeployTestnet.s.sol \
  --rpc-url arbitrum_sepolia \
  --broadcast \
  --verify
```

### **2. Keeper Bot (Node.js/Hardhat)**

```bash
cd keeper-bot

# Configurar
cp .env.testnet .env
nano .env  # Adicionar VAULT_ADDRESS

# Rodar
DRY_RUN=true npm start
```

**Best of both worlds! 🚀**

---

## 🆘 Troubleshooting

### **Erro: "Failed to get EIP-1559 fees"**

**Solução:** Arbitrum Sepolia usa legacy transactions:

```bash
# Adicionar --legacy
forge script script/DeployTestnet.s.sol \
  --rpc-url arbitrum_sepolia \
  --broadcast \
  --legacy
```

---

### **Erro: "Compiler version mismatch"**

```bash
# Instalar versão correta do solc
foundryup --version nightly

# Ou especificar no foundry.toml
solc_version = "0.8.20"
```

---

### **Erro: "Library not found"**

```bash
# Reinstalar dependências
rm -rf lib/
forge install OpenZeppelin/openzeppelin-contracts@v5.0.0
forge install Uniswap/v3-core
forge install Uniswap/v3-periphery
forge install smartcontractkit/chainlink
```

---

## 📖 Documentação Oficial

- **Foundry Book**: https://book.getfoundry.sh
- **Forge Reference**: https://book.getfoundry.sh/reference/forge/
- **Cast Reference**: https://book.getfoundry.sh/reference/cast/
- **Cheatcodes**: https://book.getfoundry.sh/cheatcodes/

---

## ✅ Checklist de Deploy

- [ ] Foundry instalado (`forge --version`)
- [ ] .env configurado (PRIVATE_KEY, RPC_URL)
- [ ] Compilar: `forge build`
- [ ] Dry run: `forge script script/DeployTestnet.s.sol --rpc-url arbitrum_sepolia`
- [ ] Deploy real: adicionar `--broadcast`
- [ ] Verificar: adicionar `--verify`
- [ ] Salvar endereço do vault
- [ ] Configurar keeper bot
- [ ] Testar funções: `cast call ...`

---

**⚡ Foundry = Velocidade + Poder! Compile em 3s, não 30s! 🚀**
