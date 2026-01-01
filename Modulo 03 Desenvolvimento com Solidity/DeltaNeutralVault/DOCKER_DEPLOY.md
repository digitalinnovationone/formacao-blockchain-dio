# 🐳 Deploy DeltaNeutralVault via Docker

Guia completo para fazer deploy do DeltaNeutralVaultV1 usando Docker na sua VPS.

---

## 🎯 Por Que Docker?

✅ **Isolamento**: Ambiente consistente independente do SO
✅ **Portabilidade**: Roda em qualquer VPS com Docker
✅ **Sem dependências**: Não precisa instalar Node.js, npm, etc
✅ **Reproduzível**: Mesma build sempre
✅ **Limpeza fácil**: `docker-compose down` remove tudo

---

## 📋 Pré-requisitos na VPS

### 1. Instalar Docker

```bash
# Instalar Docker (Ubuntu/Debian)
curl -fsSL https://get.docker.com | sh

# Adicionar usuário ao grupo docker (evita sudo)
sudo usermod -aG docker $USER

# Relogar ou executar:
newgrp docker

# Verificar
docker --version
```

### 2. Instalar Docker Compose

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install docker-compose -y

# Verificar
docker-compose --version
```

---

## ⚙️ Configuração

### 1. Clonar Repositório na VPS

```bash
# SSH na VPS
ssh usuario@sua-vps-ip

# Clonar
git clone https://github.com/SEU_USUARIO/formacao-blockchain-dio.git
cd "formacao-blockchain-dio/Modulo 03 Desenvolvimento com Solidity/DeltaNeutralVault"
```

### 2. Configurar .env

```bash
# Copiar exemplo
cp .env.example .env

# Editar com sua private key
nano .env
```

**Adicione sua PRIVATE_KEY:**
```env
# SEM o prefixo 0x!
PRIVATE_KEY=sua_private_key_aqui_sem_0x

# RPC Arbitrum Sepolia
ARBITRUM_SEPOLIA_RPC_URL=https://sepolia-rollup.arbitrum.io/rpc
```

Salvar: `Ctrl+O` → Enter → `Ctrl+X`

---

## 🚀 Deploy (3 Métodos)

### **Método 1: Script Automatizado (Recomendado)**

```bash
# Executar script completo
./docker-deploy.sh
```

**O que faz:**
1. ✅ Verifica .env
2. ✅ Verifica Docker instalado
3. ✅ Builda imagem
4. ✅ Compila contratos
5. ✅ Faz deploy no Arbitrum Sepolia
6. ✅ Mostra endereço do vault

---

### **Método 2: Passo a Passo Manual**

```bash
# 1. Build da imagem
docker-compose build

# 2. Compilar contratos
docker-compose run --rm vault-deployer npx hardhat compile

# 3. Deploy
docker-compose run --rm vault-deployer npx hardhat run scripts/deploy.js --network arbitrumSepolia

# 4. (Opcional) Verificar contrato
docker-compose run --rm vault-deployer npx hardhat verify --network arbitrumSepolia VAULT_ADDRESS ...
```

---

### **Método 3: Interativo (Console)**

```bash
# Entrar no container
docker-compose run --rm vault-deployer bash

# Dentro do container:
npx hardhat compile
npx hardhat run scripts/deploy.js --network arbitrumSepolia

# Ou usar console interativo:
npx hardhat console --network arbitrumSepolia
> const vault = await ethers.getContractAt('DeltaNeutralVaultV1', 'VAULT_ADDRESS');
> await vault.owner()

# Sair
exit
```

---

## 🧪 Testes via Docker

### Rodar Testes Foundry

```bash
# Se tiver Foundry instalado no container
docker-compose run --rm vault-deployer forge test -vvv
```

### Rodar Testes Hardhat

```bash
docker-compose run --rm vault-deployer npx hardhat test
```

---

## 🔍 Comandos Úteis

### Verificar Logs

```bash
# Ver logs do container
docker-compose logs -f vault-deployer
```

### Console Hardhat

```bash
# Abrir console interativo
docker-compose run --rm vault-deployer npx hardhat console --network arbitrumSepolia
```

### Limpar Tudo

```bash
# Parar e remover containers
docker-compose down

# Remover volumes também
docker-compose down -v

# Remover imagem
docker rmi deltaneutralvault_vault-deployer
```

### Rebuild (após mudanças no código)

```bash
# Rebuild sem cache
docker-compose build --no-cache

# Ou forçar recreação
docker-compose up --build --force-recreate
```

---

## 📊 Estrutura de Arquivos Docker

```
DeltaNeutralVault/
├── Dockerfile              # Imagem base Node.js + deps
├── docker-compose.yml      # Orquestração
├── .dockerignore          # Arquivos ignorados na build
├── docker-deploy.sh       # Script automatizado
├── DOCKER_DEPLOY.md       # Este guia
└── .env                   # Configurações (NÃO commitar!)
```

---

## 💡 Dicas e Truques

### 1. Verificar Saldo Antes do Deploy

```bash
docker-compose run --rm vault-deployer npx hardhat console --network arbitrumSepolia

# No console:
> const [deployer] = await ethers.getSigners();
> console.log("Address:", deployer.address);
> const balance = await ethers.provider.getBalance(deployer.address);
> console.log("Balance:", ethers.formatEther(balance), "ETH");
```

### 2. Deploy em Outra Rede

Edite `docker-compose.yml` ou passe variável:

```bash
docker-compose run --rm vault-deployer npx hardhat run scripts/deploy.js --network sepolia
```

### 3. Usar Alchemy RPC (Melhor Performance)

No `.env`:
```env
ALCHEMY_API_KEY=seu_api_key
ARBITRUM_SEPOLIA_RPC_URL=https://arb-sepolia.g.alchemy.com/v2/SEU_API_KEY
```

### 4. Persistir Dados Entre Rebuilds

Os volumes estão configurados em `docker-compose.yml`:
```yaml
volumes:
  - artifacts:/app/artifacts   # Mantém compilações
  - cache:/app/cache           # Mantém cache
```

---

## ❌ Troubleshooting

### Erro: "Cannot find module"

```bash
# Rebuild completo
docker-compose down -v
docker-compose build --no-cache
```

### Erro: "EACCES: permission denied"

```bash
# Dar permissões corretas
sudo chown -R $USER:$USER .
```

### Erro: "insufficient funds"

```bash
# Pegar mais ETH no faucet
# https://www.alchemy.com/faucets/arbitrum-sepolia

# Ou verificar saldo:
docker-compose run --rm vault-deployer npx hardhat console --network arbitrumSepolia
```

### Container não inicia

```bash
# Ver logs detalhados
docker-compose logs vault-deployer

# Verificar se .env existe
ls -la .env

# Testar build manual
docker build -t test-vault .
```

### Deploy muito lento

```bash
# Usar Alchemy RPC (mais rápido que público)
# Configure ALCHEMY_API_KEY no .env
```

---

## 🔐 Segurança

### ⚠️ Importante:

1. **NUNCA** commite `.env` no git
2. `.env` está no `.gitignore` ✅
3. Use `.env.example` como template
4. Na VPS, proteja `.env`:
   ```bash
   chmod 600 .env
   ```

### Verificar .gitignore

```bash
# .env deve estar ignorado
cat .gitignore | grep .env
```

---

## 📈 Custos (Arbitrum Sepolia)

| Operação | Gas | Custo ETH | Via Docker? |
|----------|-----|-----------|-------------|
| Build imagem | - | Grátis | ✅ |
| Deploy vault | ~3M | ~0.001 | ✅ |
| setKeeper | ~50K | ~0.00002 | ✅ |
| Total | - | ~0.002 ETH | ✅ |

**Vantagem Docker**: Mesmo custo, mas muito mais fácil!

---

## 🎯 Workflow Completo

```bash
# 1. Na VPS
ssh user@vps-ip

# 2. Primeira vez (setup)
git clone ...
cd DeltaNeutralVault
cp .env.example .env
nano .env  # Adicionar PRIVATE_KEY

# 3. Pegar ETH
# https://www.alchemy.com/faucets/arbitrum-sepolia

# 4. Deploy
./docker-deploy.sh

# 5. Verificar
# https://sepolia.arbiscan.io/address/VAULT_ADDRESS

# 6. Limpar (opcional)
docker-compose down
```

---

## 🔄 CI/CD com Docker (Avançado)

### GitHub Actions

```yaml
# .github/workflows/deploy.yml
name: Deploy Vault

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Build
        run: docker-compose build
      - name: Deploy
        env:
          PRIVATE_KEY: ${{ secrets.PRIVATE_KEY }}
        run: docker-compose run vault-deployer npx hardhat run scripts/deploy.js --network arbitrumSepolia
```

---

## 📚 Recursos

- **Docker Docs**: https://docs.docker.com
- **Hardhat Docker**: https://hardhat.org/hardhat-runner/docs/guides/docker
- **Arbitrum Faucet**: https://www.alchemy.com/faucets/arbitrum-sepolia
- **Arbiscan Explorer**: https://sepolia.arbiscan.io

---

## ✅ Checklist de Deploy

```
[ ] Docker instalado na VPS
[ ] Docker Compose instalado
[ ] Repositório clonado
[ ] .env configurado com PRIVATE_KEY
[ ] ETH obtido no faucet (min 0.002 ETH)
[ ] docker-deploy.sh executável (chmod +x)
[ ] Build da imagem OK (docker-compose build)
[ ] Deploy executado com sucesso
[ ] Endereço do vault salvo
[ ] Verificado no Arbiscan
```

---

**🎉 Pronto! Seu vault será deployado via Docker de forma profissional e reproduzível!**

## 🚀 Deploy Rápido (TL;DR)

```bash
# Setup
cp .env.example .env
nano .env  # Adicionar PRIVATE_KEY

# Deploy
./docker-deploy.sh

# Done! ✅
```
