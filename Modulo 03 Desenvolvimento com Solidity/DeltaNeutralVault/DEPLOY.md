# Guia de Deploy - DeltaNeutralVaultV1 na Devnet

## ⚠️ IMPORTANTE - Leia Antes de Fazer Deploy

### Status Atual da Implementação

**ETAPA 1 (Atual)**: ⚠️ Parcialmente Funcional
- ✅ Estrutura base compilável
- ✅ Sistema de fees
- ✅ Oracle Chainlink
- ❌ **Integração Uniswap v3 são STUBS (não funcionam)**
- ❌ **NÃO cria pools automaticamente**
- ❌ **NÃO abre/fecha posições LP reais**

**ETAPA 2 (Necessária)**: Implementação completa
- Integração real com Uniswap v3
- Swaps via 1inch
- Keeper off-chain

### O que você pode testar AGORA (Etapa 1):

✅ Deploy do contrato
✅ Deposit/Withdraw de USDC (sem LP)
✅ Cobrança de entry/exit fees
✅ Validação de oracles
✅ Permissões (owner/keeper)

❌ Abrir posições LP
❌ Hedge delta-neutral
❌ Swaps automáticos

---

## 📡 Configuração da Rede

### Opção 1: Airbithon Devnet

Primeiro, precisamos dos **endereços dos contratos** na rede Airbithon:

```javascript
// Endereços necessários (você precisa descobrir/fornecer):
USDC_ADDRESS = "0x..." // Token USDC na Airbithon
WBTC_ADDRESS = "0x..." // Token WBTC na Airbithon
CHAINLINK_FEED = "0x..." // Price Feed WBTC/USD na Airbithon
UNISWAP_V3_FACTORY = "0x..." // Factory do Uniswap v3 na Airbithon
UNISWAP_V3_POSITION_MANAGER = "0x..." // NonfungiblePositionManager
TREASURY_ADDRESS = "0x..." // Sua carteira para receber fees
```

### Opção 2: Testnet Pública (Sepolia)

Se a Airbithon não tiver esses contratos, use Sepolia:

```javascript
// Sepolia (testnet Ethereum)
USDC_ADDRESS = "0x1c7D4B196Cb0C7B01d743Fbc6116a902379C7238"
WBTC_ADDRESS = "0x29f2D40B0605204364af54EC677bD022dA425d03"
CHAINLINK_FEED = "0x1b44F3514812d835EB1BDB0acB33d3fA3351Ee43" // BTC/USD
UNISWAP_V3_FACTORY = "0x0227628f3F023bb0B980b67D528571c95c6DaC1c"
UNISWAP_V3_POSITION_MANAGER = "0x1238536071E1c677A632429e3655c799b22cDA52"
```

---

## 🛠️ Passo 1: Configurar Hardhat

### 1.1 Atualizar hardhat.config.js

Crie um arquivo `.env` primeiro:

```bash
# .env
PRIVATE_KEY=sua_private_key_aqui
AIRBITHON_RPC_URL=https://rpc.airbithon.network # (exemplo)
ETHERSCAN_API_KEY=opcional_para_verificacao
```

Depois atualize o `hardhat.config.js`:

```javascript
require("@nomicfoundation/hardhat-toolbox");
require("dotenv").config();

module.exports = {
  solidity: {
    version: "0.8.20",
    settings: {
      optimizer: {
        enabled: true,
        runs: 200
      }
    }
  },
  networks: {
    hardhat: {
      forking: {
        enabled: false
      }
    },
    airbithon: {
      url: process.env.AIRBITHON_RPC_URL || "https://rpc.airbithon.network",
      accounts: [process.env.PRIVATE_KEY],
      chainId: 123456 // Substitua pelo chainId correto da Airbithon
    },
    sepolia: {
      url: `https://eth-sepolia.g.alchemy.com/v2/${process.env.ALCHEMY_API_KEY}`,
      accounts: [process.env.PRIVATE_KEY],
      chainId: 11155111
    }
  },
  paths: {
    sources: "./",
    tests: "./test",
    cache: "./cache",
    artifacts: "./artifacts"
  }
};
```

### 1.2 Instalar dotenv

```bash
cd "Modulo 03 Desenvolvimento com Solidity/DeltaNeutralVault"
npm install dotenv
```

---

## 📝 Passo 2: Criar Script de Deploy

Crie o diretório e arquivo:

```bash
mkdir -p scripts
```

Arquivo: `scripts/deploy.js`

```javascript
const hre = require("hardhat");

async function main() {
  console.log("🚀 Iniciando deploy do DeltaNeutralVaultV1...\n");

  // ========================================
  // CONFIGURAÇÃO - AJUSTE ESTES ENDEREÇOS
  // ========================================

  const USDC_ADDRESS = "0x1c7D4B196Cb0C7B01d743Fbc6116a902379C7238"; // Sepolia USDC
  const CHAINLINK_FEED = "0x1b44F3514812d835EB1BDB0acB33d3fA3351Ee43"; // BTC/USD Sepolia
  const TREASURY_ADDRESS = "0xYourTreasuryAddress"; // ⚠️ ALTERE AQUI

  const VAULT_NAME = "Delta Neutral Vault Shares";
  const VAULT_SYMBOL = "dnvUSDC";

  // ========================================
  // DEPLOY
  // ========================================

  const DeltaNeutralVaultV1 = await hre.ethers.getContractFactory("DeltaNeutralVaultV1");

  console.log("📦 Fazendo deploy do contrato...");
  const vault = await DeltaNeutralVaultV1.deploy(
    USDC_ADDRESS,
    VAULT_NAME,
    VAULT_SYMBOL,
    CHAINLINK_FEED,
    TREASURY_ADDRESS
  );

  await vault.waitForDeployment();
  const vaultAddress = await vault.getAddress();

  console.log("✅ DeltaNeutralVaultV1 deployed to:", vaultAddress);
  console.log("\n📋 Informações do Deploy:");
  console.log("- Asset (USDC):", USDC_ADDRESS);
  console.log("- Chainlink Feed:", CHAINLINK_FEED);
  console.log("- Treasury:", TREASURY_ADDRESS);
  console.log("- Nome:", VAULT_NAME);
  console.log("- Símbolo:", VAULT_SYMBOL);

  // ========================================
  // CONFIGURAÇÃO INICIAL
  // ========================================

  console.log("\n⚙️ Configurando vault...");

  // Definir keeper (por enquanto, o deployer)
  const [deployer] = await hre.ethers.getSigners();
  await vault.setKeeper(deployer.address);
  console.log("✅ Keeper definido:", deployer.address);

  // Definir fees (valores conservadores)
  await vault.setFees(
    2000, // 20% performance fee
    200,  // 2% management fee
    50,   // 0.5% entry fee
    50,   // 0.5% exit fee
    30,   // 0.3% swap fee
    10    // 0.1% keeper fee
  );
  console.log("✅ Fees configuradas");

  // ⚠️ ATENÇÃO: Estas configurações são para Etapa 1 (sem Uniswap)
  // Na Etapa 2, você precisará configurar:
  // - setUniswapPool(poolAddress)
  // - setRange(tickLower, tickUpper)

  console.log("\n🎉 Deploy completo!");
  console.log("\n⚠️ LEMBRE-SE:");
  console.log("- Este é o contrato da Etapa 1 (funções LP são stubs)");
  console.log("- Para funcionalidade completa, implemente a Etapa 2");
  console.log("- Configure o pool Uniswap v3 depois com setUniswapPool()");

  console.log("\n📝 Próximos passos:");
  console.log("1. Criar pool WBTC/USDC no Uniswap v3 (se não existir)");
  console.log("2. Chamar setUniswapPool(poolAddress)");
  console.log("3. Chamar setRange(tickLower, tickUpper)");
  console.log("4. Implementar Etapa 2 para integração real");
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });
```

---

## 🏊 Passo 3: Como Criar uma Pool Uniswap v3 (SEPARADO)

### ⚠️ IMPORTANTE: O vault NÃO cria a pool!

A pool WBTC/USDC precisa **existir antes** no Uniswap v3. Existem 2 opções:

### Opção A: Usar Pool Existente

Verifique se já existe uma pool WBTC/USDC na rede:
- Acesse https://app.uniswap.org/pools
- Conecte na rede Airbithon/Sepolia
- Procure por WBTC/USDC

Se existir, pegue o endereço da pool e pule para o Passo 4.

### Opção B: Criar Nova Pool (Script Separado)

Crie `scripts/create-pool.js`:

```javascript
const hre = require("hardhat");

async function main() {
  console.log("🏊 Criando pool Uniswap v3 WBTC/USDC...\n");

  // Endereços (ajuste conforme sua rede)
  const WBTC = "0x29f2D40B0605204364af54EC677bD022dA425d03"; // Sepolia
  const USDC = "0x1c7D4B196Cb0C7B01d743Fbc6116a902379C7238"; // Sepolia
  const FACTORY = "0x0227628f3F023bb0B980b67D528571c95c6DaC1c"; // Sepolia

  const FEE_TIER = 3000; // 0.3% (padrão para WBTC/USDC)

  // Definir preço inicial (sqrtPriceX96)
  // Exemplo: 1 WBTC = 40,000 USDC
  // sqrtPriceX96 = sqrt(40000) * 2^96 ≈ 1.58...e+79
  const INITIAL_SQRT_PRICE = "1584563250285286751870944"; // Ajuste conforme necessário

  const factory = await hre.ethers.getContractAt(
    "IUniswapV3Factory",
    FACTORY
  );

  // Criar pool
  console.log("Criando pool...");
  const tx = await factory.createPool(WBTC, USDC, FEE_TIER);
  await tx.wait();

  const poolAddress = await factory.getPool(WBTC, USDC, FEE_TIER);
  console.log("✅ Pool criada:", poolAddress);

  // Inicializar preço
  const pool = await hre.ethers.getContractAt("IUniswapV3Pool", poolAddress);
  const initTx = await pool.initialize(INITIAL_SQRT_PRICE);
  await initTx.wait();

  console.log("✅ Pool inicializada com preço:", INITIAL_SQRT_PRICE);
  console.log("\n🎉 Pool criada com sucesso!");
  console.log("Endereço da pool:", poolAddress);
}

main().catch(console.error);
```

**Nota**: Você também pode criar a pool diretamente pela interface do Uniswap.

---

## 🚀 Passo 4: Fazer o Deploy

### 4.1 Compilar

```bash
cd "Modulo 03 Desenvolvimento com Solidity/DeltaNeutralVault"
npm install
npx hardhat compile
```

### 4.2 Fazer Deploy

```bash
# Para Airbithon
npx hardhat run scripts/deploy.js --network airbithon

# OU para Sepolia (testnet)
npx hardhat run scripts/deploy.js --network sepolia
```

### 4.3 Anotar o Endereço

Copie o endereço do contrato deployado. Você vai precisar dele.

---

## ⚙️ Passo 5: Configurar Pool (Depois do Deploy)

Depois do deploy, configure o pool:

```javascript
// No console do Hardhat ou via script
const vault = await ethers.getContractAt(
  "DeltaNeutralVaultV1",
  "0xSeuVaultAddress"
);

// Configurar pool
await vault.setUniswapPool("0xPoolWBTC_USDC_Address");

// Configurar range (exemplo: -887220 a 887220 = full range)
await vault.setRange(-887220, 887220);

console.log("✅ Pool configurada!");
```

---

## 🧪 Passo 6: Testar (Limitado - Etapa 1)

### O que você PODE testar:

```javascript
const usdc = await ethers.getContractAt("IERC20", USDC_ADDRESS);
const vault = await ethers.getContractAt("DeltaNeutralVaultV1", vaultAddress);

// 1. Aprovar USDC para o vault
await usdc.approve(vaultAddress, ethers.parseUnits("1000", 6)); // 1000 USDC

// 2. Depositar (vai cobrar entry fee)
await vault.deposit(ethers.parseUnits("1000", 6), deployerAddress);

// 3. Ver saldo de shares
const shares = await vault.balanceOf(deployerAddress);
console.log("Shares recebidas:", ethers.formatUnits(shares, 18));

// 4. Resgatar (vai cobrar exit fee)
await vault.redeem(shares, deployerAddress, deployerAddress);
```

### O que NÃO vai funcionar ainda:

❌ `autoExit()` - Fecha posição LP (stub vazio)
❌ `autoReenter()` - Abre posição LP (stub vazio)
❌ Swaps - executeSwap é placeholder

---

## 📊 Endereços que Você Precisa

Para fazer o deploy completo na **Airbithon**, você precisa descobrir:

| Item | Descrição | Como Encontrar |
|------|-----------|----------------|
| USDC | Token USDC na rede | Documentação da Airbithon |
| WBTC | Token WBTC na rede | Documentação da Airbithon |
| Chainlink Feed | Price feed WBTC/USD | https://docs.chain.link/data-feeds |
| Uniswap v3 Factory | Factory do Uniswap v3 | Documentação da Airbithon |
| Position Manager | NFT Position Manager | Documentação da Airbithon |

### Se a Airbithon não tiver Uniswap v3:

Você terá que:
1. Fazer fork do Uniswap v3 e fazer deploy você mesmo, OU
2. Usar uma testnet pública (Sepolia, Arbitrum Sepolia, etc.)

---

## 📝 Resumo: Deploy Mínimo (Etapa 1)

```bash
# 1. Instalar dependências
npm install

# 2. Configurar .env
echo "PRIVATE_KEY=0x..." >> .env
echo "AIRBITHON_RPC_URL=https://..." >> .env

# 3. Compilar
npx hardhat compile

# 4. Fazer deploy
npx hardhat run scripts/deploy.js --network airbithon

# 5. Configurar pool (depois)
# via script ou console do Hardhat
```

---

## ❓ Perguntas Frequentes

### 1. "Posso testar tudo agora?"

**NÃO**. Na Etapa 1, você pode testar apenas:
- Deposit/Withdraw básico
- Cobrança de fees
- Validação de oracles

As funções de LP (autoExit, autoReenter) são stubs vazios.

### 2. "O contrato cria a pool automaticamente?"

**NÃO**. A pool Uniswap v3 WBTC/USDC precisa:
1. Já existir na rede, OU
2. Ser criada separadamente (via Uniswap ou script)

### 3. "Quando vou ter funcionalidade completa?"

Na **Etapa 2**, que implementará:
- Integração real com Uniswap v3
- Abrir/fechar posições LP
- Swaps via 1inch
- Keeper automatizado

### 4. "Onde coloco os valores WBTC/USDC?"

Você **NÃO coloca** WBTC/USDC diretamente no vault.

Fluxo correto:
1. Usuário deposita **USDC** no vault
2. Vault usa o USDC para criar posição LP na pool WBTC/USDC
3. Vault gerencia a posição automaticamente

---

## 🎯 Próximos Passos

Quer que eu implemente a **Etapa 2** agora para ter funcionalidade completa?

Isso incluirá:
- ✅ Integração real com Uniswap v3 (mint/burn de posições)
- ✅ Cálculo de liquidez e distribuição de tokens
- ✅ Swaps via Uniswap v3 Router
- ✅ Collect de fees da pool
- ✅ Funções completas de autoExit/autoReenter

**Me avise se quer que eu continue com a Etapa 2!**
