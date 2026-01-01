#!/bin/bash

# =====================================================
# Script de Deploy via Docker - Arbitrum Sepolia
# =====================================================

set -e

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}╔════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   DeltaNeutralVault - Deploy via Docker       ║${NC}"
echo -e "${BLUE}║   Arbitrum Sepolia Testnet                     ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════╝${NC}"
echo ""

# =====================================================
# 1. Verificar .env
# =====================================================

if [ ! -f .env ]; then
    echo -e "${RED}❌ Arquivo .env não encontrado!${NC}"
    echo ""
    echo "Criando .env a partir de .env.example..."
    cp .env.example .env
    echo -e "${YELLOW}⚠️  Configure sua PRIVATE_KEY no .env:${NC}"
    echo "   nano .env"
    echo ""
    exit 1
fi

# Verificar se PRIVATE_KEY está configurada
if grep -q "sua_private_key" .env; then
    echo -e "${RED}❌ PRIVATE_KEY não configurada!${NC}"
    echo ""
    echo "Edite o arquivo .env:"
    echo "   nano .env"
    echo ""
    exit 1
fi

echo -e "${GREEN}✅ Arquivo .env configurado${NC}"
echo ""

# =====================================================
# 2. Verificar Docker
# =====================================================

if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker não está instalado!${NC}"
    echo ""
    echo "Instale com:"
    echo "   curl -fsSL https://get.docker.com | sh"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ Docker Compose não está instalado!${NC}"
    echo ""
    echo "Instale com:"
    echo "   sudo apt install docker-compose"
    exit 1
fi

echo -e "${GREEN}✅ Docker instalado: $(docker --version)${NC}"
echo -e "${GREEN}✅ Docker Compose: $(docker-compose --version)${NC}"
echo ""

# =====================================================
# 3. Build da imagem Docker
# =====================================================

echo -e "${BLUE}📦 Construindo imagem Docker...${NC}"
docker-compose build --no-cache

echo -e "${GREEN}✅ Imagem construída${NC}"
echo ""

# =====================================================
# 4. Deploy
# =====================================================

echo -e "${YELLOW}⚠️  Iniciando deploy no Arbitrum Sepolia${NC}"
echo ""
read -p "Continuar? (s/n) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[SsYy]$ ]]; then
    echo "Deploy cancelado."
    exit 0
fi

echo ""
echo -e "${BLUE}🚀 Executando deploy...${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Executar deploy dentro do container
docker-compose run --rm vault-deployer npx hardhat run scripts/deploy.js --network arbitrumSepolia

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo -e "${GREEN}✅ Deploy concluído!${NC}"
echo ""
echo -e "${BLUE}📋 Próximos passos:${NC}"
echo "   1. Verifique no Arbiscan: https://sepolia.arbiscan.io"
echo "   2. Configure pool: vault.setUniswapConfig()"
echo "   3. Defina range: vault.setRange(tickLower, tickUpper)"
echo ""
echo -e "${GREEN}🎉 Vault deployado via Docker!${NC}"
