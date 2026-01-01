#!/bin/bash

# =====================================================
# Script Completo de Setup VPS + Deploy
# =====================================================
# Executar APENAS na VPS após clonar repositório
# =====================================================

set -e

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${BLUE}"
echo "╔════════════════════════════════════════════════════╗"
echo "║     DeltaNeutralVault - Setup Completo VPS        ║"
echo "║            Automatização Total                     ║"
echo "╚════════════════════════════════════════════════════╝"
echo -e "${NC}"
echo ""

# =====================================================
# VERIFICAR SE ESTÁ NA VPS
# =====================================================

echo -e "${CYAN}📍 Verificando ambiente...${NC}"
echo ""

if [ ! -f "DeltaNeutralVaultV1.sol" ]; then
    echo -e "${RED}❌ Erro: Execute este script no diretório DeltaNeutralVault!${NC}"
    echo ""
    echo "Navegue até o diretório correto:"
    echo "  cd ~/formacao-blockchain-dio/Modulo\ 03\ Desenvolvimento\ com\ Solidity/DeltaNeutralVault"
    echo ""
    exit 1
fi

echo -e "${GREEN}✅ Diretório correto${NC}"
echo ""

# =====================================================
# PARTE 1: INSTALAR DEPENDÊNCIAS
# =====================================================

echo -e "${MAGENTA}╔════════════════════════════════════════════════════╗${NC}"
echo -e "${MAGENTA}║ PARTE 1: Instalando Dependências                  ║${NC}"
echo -e "${MAGENTA}╚════════════════════════════════════════════════════╝${NC}"
echo ""

# Verificar se é root
if [ "$EUID" -ne 0 ] && ! groups | grep -q docker; then
    echo -e "${YELLOW}⚠️  Este script precisa de permissões sudo${NC}"
    echo "Você pode:"
    echo "  1. Executar como root: sudo bash setup-vps.sh"
    echo "  2. Ou adicionar seu usuário ao grupo docker primeiro"
    echo ""
fi

# Verificar Docker
if ! command -v docker &> /dev/null; then
    echo -e "${YELLOW}📦 Docker não encontrado. Instalando...${NC}"

    # Atualizar sistema
    echo "   Atualizando sistema..."
    sudo apt update -qq

    # Instalar Docker
    echo "   Instalando Docker..."
    curl -fsSL https://get.docker.com | sudo sh

    # Adicionar usuário ao grupo docker
    sudo usermod -aG docker $USER

    echo -e "${GREEN}✅ Docker instalado${NC}"
else
    echo -e "${GREEN}✅ Docker já instalado: $(docker --version)${NC}"
fi
echo ""

# Verificar Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo -e "${YELLOW}📦 Docker Compose não encontrado. Instalando...${NC}"
    sudo apt install docker-compose -y -qq
    echo -e "${GREEN}✅ Docker Compose instalado${NC}"
else
    echo -e "${GREEN}✅ Docker Compose já instalado: $(docker-compose --version)${NC}"
fi
echo ""

# =====================================================
# PARTE 2: CONFIGURAR .env
# =====================================================

echo -e "${MAGENTA}╔════════════════════════════════════════════════════╗${NC}"
echo -e "${MAGENTA}║ PARTE 2: Configurando Ambiente                    ║${NC}"
echo -e "${MAGENTA}╚════════════════════════════════════════════════════╝${NC}"
echo ""

if [ -f .env ]; then
    echo -e "${YELLOW}⚠️  Arquivo .env já existe!${NC}"
    echo ""
    read -p "Deseja reconfigurar? (s/n) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[SsYy]$ ]]; then
        rm .env
    else
        echo "Mantendo .env existente..."
    fi
fi

if [ ! -f .env ]; then
    echo -e "${CYAN}📝 Criando arquivo .env...${NC}"
    echo ""

    # Pedir private key
    echo -e "${YELLOW}Digite sua PRIVATE KEY (sem o prefixo 0x):${NC}"
    read -s PRIVATE_KEY
    echo ""

    # Validar private key
    if [ -z "$PRIVATE_KEY" ]; then
        echo -e "${RED}❌ Erro: Private key não pode ser vazia!${NC}"
        exit 1
    fi

    # Remover 0x se presente
    PRIVATE_KEY="${PRIVATE_KEY#0x}"

    # Criar .env
    cat > .env << EOF
# =====================================================
# CONFIGURAÇÃO PARA DEPLOY - Arbitrum Sepolia
# =====================================================

# Private Key (configurada automaticamente)
PRIVATE_KEY=$PRIVATE_KEY

# Arbitrum Sepolia RPC
ARBITRUM_SEPOLIA_RPC_URL=https://sepolia-rollup.arbitrum.io/rpc

# Opcional: APIs externas
ALCHEMY_API_KEY=
ARBISCAN_API_KEY=
EOF

    # Proteger .env
    chmod 600 .env

    echo -e "${GREEN}✅ Arquivo .env criado e protegido${NC}"
else
    echo -e "${GREEN}✅ Usando .env existente${NC}"
fi
echo ""

# =====================================================
# PARTE 3: VERIFICAR SALDO
# =====================================================

echo -e "${MAGENTA}╔════════════════════════════════════════════════════╗${NC}"
echo -e "${MAGENTA}║ PARTE 3: Verificando Saldo                        ║${NC}"
echo -e "${MAGENTA}╚════════════════════════════════════════════════════╝${NC}"
echo ""

echo -e "${CYAN}💰 Extraindo endereço da carteira...${NC}"
echo ""

# Carregar .env
source .env

# Criar script temporário para extrair endereço
cat > /tmp/get_address.js << 'EOJS'
const ethers = require('ethers');
const wallet = new ethers.Wallet(process.env.PRIVATE_KEY);
console.log(wallet.address);
EOJS

# Verificar se tem Node.js no sistema (para extrair endereço)
if command -v node &> /dev/null; then
    # Instalar ethers temporariamente
    npm install --silent ethers@5 > /dev/null 2>&1
    ADDRESS=$(node /tmp/get_address.js)
    rm /tmp/get_address.js

    echo -e "${GREEN}📍 Seu endereço: ${CYAN}$ADDRESS${NC}"
    echo ""
    echo -e "${YELLOW}⚠️  Verifique seu saldo em:${NC}"
    echo -e "   ${BLUE}https://sepolia.arbiscan.io/address/$ADDRESS${NC}"
    echo ""
    echo -e "${YELLOW}⚠️  Se saldo = 0, pegue ETH nos faucets:${NC}"
    echo "   1. https://www.alchemy.com/faucets/arbitrum-sepolia (0.1 ETH)"
    echo "   2. https://faucet.quicknode.com/arbitrum/sepolia (0.05 ETH)"
    echo "   3. https://faucets.chain.link/arbitrum-sepolia (0.01 ETH)"
    echo ""
else
    echo -e "${YELLOW}⚠️  Node.js não instalado. Extraia o endereço manualmente.${NC}"
    echo ""
fi

echo -e "${YELLOW}Você tem saldo suficiente (min 0.002 ETH)?${NC}"
read -p "Continuar com o deploy? (s/n) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[SsYy]$ ]]; then
    echo -e "${YELLOW}Deploy cancelado.${NC}"
    echo ""
    echo "Pegue ETH nos faucets e execute novamente:"
    echo "  ./setup-vps.sh"
    exit 0
fi

echo ""

# =====================================================
# PARTE 4: BUILD DOCKER
# =====================================================

echo -e "${MAGENTA}╔════════════════════════════════════════════════════╗${NC}"
echo -e "${MAGENTA}║ PARTE 4: Construindo Imagem Docker                ║${NC}"
echo -e "${MAGENTA}╚════════════════════════════════════════════════════╝${NC}"
echo ""

echo -e "${CYAN}📦 Construindo imagem Docker (pode levar 2-3min)...${NC}"
echo ""

docker-compose build --no-cache

echo ""
echo -e "${GREEN}✅ Imagem Docker construída${NC}"
echo ""

# =====================================================
# PARTE 5: DEPLOY
# =====================================================

echo -e "${MAGENTA}╔════════════════════════════════════════════════════╗${NC}"
echo -e "${MAGENTA}║ PARTE 5: Deploy no Arbitrum Sepolia               ║${NC}"
echo -e "${MAGENTA}╚════════════════════════════════════════════════════╝${NC}"
echo ""

echo -e "${YELLOW}🚀 Iniciando deploy...${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Executar deploy
docker-compose run --rm vault-deployer npx hardhat run scripts/deploy.js --network arbitrumSepolia

echo ""
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# =====================================================
# PARTE 6: FINALIZAÇÃO
# =====================================================

echo -e "${MAGENTA}╔════════════════════════════════════════════════════╗${NC}"
echo -e "${MAGENTA}║ 🎉 DEPLOY CONCLUÍDO COM SUCESSO!                  ║${NC}"
echo -e "${MAGENTA}╚════════════════════════════════════════════════════╝${NC}"
echo ""

echo -e "${GREEN}✅ Vault deployado no Arbitrum Sepolia${NC}"
echo ""

echo -e "${CYAN}📋 Próximos passos:${NC}"
echo ""
echo "1. ${YELLOW}Verifique o vault no Arbiscan:${NC}"
echo "   Procure o endereço na saída acima"
echo "   https://sepolia.arbiscan.io/address/VAULT_ADDRESS"
echo ""
echo "2. ${YELLOW}Salve o endereço do vault!${NC}"
echo "   Ele foi mostrado na saída acima"
echo ""
echo "3. ${YELLOW}Comandos úteis:${NC}"
echo "   make console    # Console interativo"
echo "   make test       # Rodar testes"
echo "   make clean      # Limpar containers"
echo ""
echo "4. ${YELLOW}Para interagir:${NC}"
echo "   Use MetaMask + Arbiscan Write Contract"
echo "   Ou use: make console"
echo ""
echo -e "${GREEN}🎉 Parabéns! Seu vault está pronto!${NC}"
echo ""

# Salvar informações
if [ ! -z "$ADDRESS" ]; then
    cat > deployment-info.txt << EOF
╔════════════════════════════════════════════════════╗
║           INFORMAÇÕES DO DEPLOYMENT                ║
╚════════════════════════════════════════════════════╝

Data/Hora: $(date)
Deployer: $ADDRESS
Rede: Arbitrum Sepolia (Chain ID: 421614)
Explorer: https://sepolia.arbiscan.io

IMPORTANTE:
- O endereço do vault foi mostrado na saída acima
- Salve em local seguro!
- Verifique no Arbiscan

Links Úteis:
- Faucet: https://www.alchemy.com/faucets/arbitrum-sepolia
- Explorer: https://sepolia.arbiscan.io
- Seu endereço: https://sepolia.arbiscan.io/address/$ADDRESS
EOF

    echo -e "${CYAN}💾 Informações salvas em: deployment-info.txt${NC}"
    echo ""
fi

echo -e "${BLUE}════════════════════════════════════════════════════${NC}"
