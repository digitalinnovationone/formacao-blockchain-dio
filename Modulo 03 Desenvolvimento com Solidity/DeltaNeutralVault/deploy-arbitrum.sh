#!/bin/bash

# =====================================================
# Script de Deploy Automatizado - Arbitrum Sepolia
# =====================================================

set -e  # Parar em caso de erro

echo "🚀 Iniciando deploy no Arbitrum Sepolia..."
echo ""

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# =====================================================
# 1. Verificar arquivo .env
# =====================================================

if [ ! -f .env ]; then
    echo -e "${RED}❌ Arquivo .env não encontrado!${NC}"
    echo ""
    echo "Criando .env a partir de .env.example..."
    cp .env.example .env
    echo -e "${YELLOW}⚠️  Por favor, edite o arquivo .env com sua PRIVATE_KEY${NC}"
    echo "   nano .env"
    exit 1
fi

# Verificar se PRIVATE_KEY está configurada
if grep -q "sua_private_key" .env; then
    echo -e "${RED}❌ PRIVATE_KEY não configurada no .env!${NC}"
    echo ""
    echo "Edite o arquivo .env e adicione sua private key:"
    echo "   nano .env"
    exit 1
fi

echo -e "${GREEN}✅ Arquivo .env encontrado${NC}"
echo ""

# =====================================================
# 2. Carregar variáveis do .env
# =====================================================

source .env

# =====================================================
# 3. Verificar Node.js e npm
# =====================================================

if ! command -v node &> /dev/null; then
    echo -e "${RED}❌ Node.js não instalado!${NC}"
    echo "Instale com: sudo apt install nodejs npm"
    exit 1
fi

echo -e "${GREEN}✅ Node.js $(node --version)${NC}"
echo ""

# =====================================================
# 4. Instalar dependências
# =====================================================

echo "📦 Instalando dependências..."
npm install --silent
echo -e "${GREEN}✅ Dependências instaladas${NC}"
echo ""

# =====================================================
# 5. Compilar contratos
# =====================================================

echo "🔨 Compilando contratos..."
npx hardhat compile
echo -e "${GREEN}✅ Compilação concluída${NC}"
echo ""

# =====================================================
# 6. Verificar saldo
# =====================================================

echo "💰 Verificando saldo na Arbitrum Sepolia..."
echo ""

# Extrair endereço da private key (usando hardhat console)
BALANCE_CHECK=$(npx hardhat run --network arbitrumSepolia - <<EOF
async function main() {
    const [deployer] = await ethers.getSigners();
    const balance = await ethers.provider.getBalance(deployer.address);
    console.log("Deployer:", deployer.address);
    console.log("Balance:", ethers.formatEther(balance), "ETH");

    if (balance === 0n) {
        console.log("\n⚠️  SALDO ZERO! Pegue ETH no faucet:");
        console.log("   https://www.alchemy.com/faucets/arbitrum-sepolia");
        process.exit(1);
    }
}
main();
EOF
)

echo "$BALANCE_CHECK"
echo ""

# =====================================================
# 7. Confirmação do usuário
# =====================================================

echo -e "${YELLOW}⚠️  Você está prestes a fazer deploy no Arbitrum Sepolia!${NC}"
echo ""
read -p "Deseja continuar? (s/n) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[SsYy]$ ]]; then
    echo "Deploy cancelado."
    exit 0
fi

echo ""

# =====================================================
# 8. Deploy
# =====================================================

echo "🚀 Iniciando deploy..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

npx hardhat run scripts/deploy.js --network arbitrumSepolia

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# =====================================================
# 9. Sucesso
# =====================================================

echo -e "${GREEN}✅ Deploy concluído com sucesso!${NC}"
echo ""
echo "📋 Próximos passos:"
echo "   1. Verifique no Arbiscan: https://sepolia.arbiscan.io"
echo "   2. Configure o pool Uniswap: vault.setUniswapConfig()"
echo "   3. Defina o range: vault.setRange(tickLower, tickUpper)"
echo ""
echo -e "${GREEN}🎉 Vault pronto para uso!${NC}"
