# 🚀 Guia Completo - Deploy na VPS com Docker

## Passo a Passo do Zero até o Deploy

---

## 📋 PRÉ-REQUISITOS

Você precisa ter:
- ✅ Acesso SSH à VPS
- ✅ VPS com Ubuntu/Debian (recomendado)
- ✅ Sua private key da carteira
- ✅ Conta no GitHub (para clonar o repositório)

---

## 🔧 PARTE 1: PREPARAR A VPS

### Passo 1.1: Conectar na VPS via SSH

```bash
# Do seu computador local, conecte na VPS:
ssh root@SEU_IP_DA_VPS
# ou
ssh usuario@SEU_IP_DA_VPS

# Exemplo:
# ssh root@192.168.1.100
```

**Se pedir senha, digite a senha da VPS.**

---

### Passo 1.2: Atualizar Sistema

```bash
# Atualizar pacotes
sudo apt update && sudo apt upgrade -y
```

---

### Passo 1.3: Instalar Git

```bash
# Instalar git
sudo apt install git -y

# Verificar instalação
git --version
# Deve mostrar: git version 2.x.x
```

---

### Passo 1.4: Instalar Docker

```bash
# Instalar Docker (um comando só)
curl -fsSL https://get.docker.com | sh

# Adicionar seu usuário ao grupo docker (para não precisar de sudo)
sudo usermod -aG docker $USER

# Aplicar as mudanças de grupo
newgrp docker

# Verificar instalação
docker --version
# Deve mostrar: Docker version 24.x.x
```

---

### Passo 1.5: Instalar Docker Compose

```bash
# Instalar Docker Compose
sudo apt install docker-compose -y

# Verificar instalação
docker-compose --version
# Deve mostrar: docker-compose version 1.29.x
```

---

## 📦 PARTE 2: CLONAR REPOSITÓRIO

### Passo 2.1: Ir para o Diretório Home

```bash
# Voltar para home
cd ~

# Ver onde você está
pwd
# Deve mostrar: /home/usuario ou /root
```

---

### Passo 2.2: Clonar Repositório do GitHub

```bash
# Clonar repositório
git clone https://github.com/Leandrosmoreira/formacao-blockchain-dio.git

# Entrar no diretório do vault
cd "formacao-blockchain-dio/Modulo 03 Desenvolvimento com Solidity/DeltaNeutralVault"

# Verificar arquivos
ls -la
```

**Você deve ver:**
```
Dockerfile
docker-compose.yml
docker-deploy.sh
.env.example
hardhat.config.js
DeltaNeutralVaultV1.sol
...
```

---

## ⚙️ PARTE 3: CONFIGURAR AMBIENTE

### Passo 3.1: Criar arquivo .env

```bash
# Copiar exemplo
cp .env.example .env

# Editar arquivo
nano .env
```

---

### Passo 3.2: Configurar .env

**No editor nano, você verá:**

```env
# ⚠️ Private Key da carteira (NUNCA compartilhe!)
# Remova o prefixo 0x se presente
PRIVATE_KEY=sua_private_key_sem_0x

# =====================================================
# ARBITRUM SEPOLIA (RECOMENDADO - L2, Gas Barato)
# =====================================================
ARBITRUM_SEPOLIA_RPC_URL=https://sepolia-rollup.arbitrum.io/rpc
```

**EDITE a linha:**
```env
PRIVATE_KEY=sua_private_key_sem_0x
```

**Substitua por sua private key REAL** (sem o 0x):
```env
PRIVATE_KEY=abc123def456...
```

**⚠️ IMPORTANTE:**
- Remova o `0x` do início se tiver
- Exemplo ERRADO: `PRIVATE_KEY=0xabc123...`
- Exemplo CERTO: `PRIVATE_KEY=abc123...`

---

### Passo 3.3: Salvar e Sair do Nano

```
1. Pressione: Ctrl + O  (para salvar)
2. Pressione: Enter      (confirmar nome)
3. Pressione: Ctrl + X  (para sair)
```

---

### Passo 3.4: Verificar .env

```bash
# Ver conteúdo (CUIDADO: sua private key vai aparecer!)
cat .env

# Verificar permissões (deve mostrar -rw-------)
ls -la .env

# Se permissões estiverem erradas, corrija:
chmod 600 .env
```

---

## 💰 PARTE 4: OBTER ETH DE TESTE

### Passo 4.1: Pegar Endereço da Carteira

Se você não sabe seu endereço, pode extrair da private key:

```bash
# Instalar ethkey (se necessário)
npm install -g ethkey

# Obter endereço da private key
ethkey address --private-key SUA_PRIVATE_KEY
```

**Ou use MetaMask:**
- Importe sua private key no MetaMask
- Copie o endereço

---

### Passo 4.2: Adicionar Arbitrum Sepolia no MetaMask

**Configuração manual:**
```
Network Name: Arbitrum Sepolia
RPC URL: https://sepolia-rollup.arbitrum.io/rpc
Chain ID: 421614
Currency Symbol: ETH
Block Explorer: https://sepolia.arbiscan.io
```

**Ou via Chainlist:**
1. Acesse: https://chainlist.org
2. Busque: "Arbitrum Sepolia"
3. Clique: "Add to MetaMask"

---

### Passo 4.3: Pegar ETH nos Faucets

**Visite estes faucets (em ordem):**

#### 1️⃣ Alchemy (0.1 ETH) - MELHOR
```
https://www.alchemy.com/faucets/arbitrum-sepolia
```
- Criar conta grátis
- Colar seu endereço
- Receber 0.1 ETH

#### 2️⃣ QuickNode (0.05 ETH)
```
https://faucet.quicknode.com/arbitrum/sepolia
```

#### 3️⃣ Chainlink (0.01 ETH)
```
https://faucets.chain.link/arbitrum-sepolia
```

---

### Passo 4.4: Verificar Saldo

```
https://sepolia.arbiscan.io/address/SEU_ENDEREÇO
```

**Você deve ter pelo menos:** 0.002 ETH (suficiente para deploy)

---

## 🐳 PARTE 5: DEPLOY COM DOCKER

### Passo 5.1: Dar Permissão ao Script

```bash
# Voltar para o diretório do vault (se não estiver)
cd ~/formacao-blockchain-dio/Modulo\ 03\ Desenvolvimento\ com\ Solidity/DeltaNeutralVault

# Dar permissão de execução
chmod +x docker-deploy.sh

# Verificar
ls -la docker-deploy.sh
# Deve mostrar: -rwxr-xr-x (com x = executável)
```

---

### Passo 5.2: Executar Deploy Automatizado

```bash
# Executar script completo
./docker-deploy.sh
```

**O que vai acontecer:**

```
🚀 Iniciando deploy no Arbitrum Sepolia...

✅ Arquivo .env configurado

✅ Docker instalado: Docker version 24.0.0
✅ Docker Compose: docker-compose version 1.29.2

📦 Construindo imagem Docker...
[+] Building 45.2s
✅ Imagem construída

⚠️  Iniciando deploy no Arbitrum Sepolia
Continuar? (s/n)
```

**Digite:** `s` (ou `y`) e pressione Enter

---

### Passo 5.3: Aguardar Deploy

O processo vai:
1. ✅ Build da imagem Docker (~2-3min)
2. ✅ Compilar contratos (~30s)
3. ✅ Fazer deploy (~10s)
4. ✅ Configurar vault (~5s)

**Output esperado:**
```
🚀 Iniciando deploy do DeltaNeutralVaultV1...

📋 Configuração:
- Deployer: 0xSEU_ENDEREÇO
- Network: arbitrumSepolia
- USDC: 0x75faf114eafb1BDbe2F0316DF893fd58CE46AA4d
- Chainlink Feed: 0x56a43EB56Da12C0dc1D972ACb089c06a5dEF8e69
- Position Manager: 0x6b2937Bde17889EDCf8fbD8dE31C3C2a70Bc4d65
- Swap Router: 0x101F443B4d1b059569D643917553c771E1b9663E
- 1inch Router: 0x111111125421cA6dc452d289314280a0f8842A65
- Treasury: 0xSEU_ENDEREÇO

💰 Saldo do deployer: 0.1 ETH

📦 Fazendo deploy do contrato...
⏳ Aguarde...

✅ DeltaNeutralVaultV1 deployed to: 0xVAULT_ADDRESS_AQUI

⚙️ Configurando vault...

✅ Keeper definido: 0xSEU_ENDEREÇO
✅ Fees configuradas:
   ├─ Performance: 20%
   ├─ Management: 2% (anual)
   ├─ Entry: 0.5%
   ├─ Exit: 0.5%
   ├─ Swap: 0.3%
   └─ Keeper: 0.1%

════════════════════════════════════════════════════════════
🎉 DEPLOY COMPLETO!
════════════════════════════════════════════════════════════

📝 Endereço do Contrato:
   0xVAULT_ADDRESS_AQUI
```

---

### Passo 5.4: Salvar Endereço do Vault

**⚠️ MUITO IMPORTANTE:**

Copie o endereço do vault que apareceu:
```
0xVAULT_ADDRESS_AQUI
```

**Guarde em local seguro:**
- Anote em um arquivo .txt
- Ou copie para um documento
- Você vai precisar dele!

---

## ✅ PARTE 6: VERIFICAR DEPLOY

### Passo 6.1: Ver no Explorer

Abra no navegador:
```
https://sepolia.arbiscan.io/address/0xVAULT_ADDRESS_AQUI
```

**Substitua** `0xVAULT_ADDRESS_AQUI` pelo endereço real do seu vault.

**Você deve ver:**
- ✅ Contract (código do contrato)
- ✅ Balance: 0 ETH (normal)
- ✅ Transactions: 1 transaction (o deploy)

---

### Passo 6.2: Verificar via Console (Opcional)

```bash
# Entrar no container
docker-compose run --rm vault-deployer bash

# Dentro do container:
npx hardhat console --network arbitrumSepolia
```

**No console Hardhat:**
```javascript
// Conectar ao vault (SUBSTITUA pelo endereço real!)
const vault = await ethers.getContractAt(
  'DeltaNeutralVaultV1',
  '0xVAULT_ADDRESS_AQUI'
);

// Verificar owner
await vault.owner()
// Deve retornar SEU endereço

// Verificar treasury
await vault.treasury()
// Deve retornar SEU endereço

// Verificar total assets
await vault.totalAssets()
// Deve retornar 0 (vault vazio)

// Sair do console
.exit
```

```bash
# Sair do container
exit
```

---

## 🎯 PARTE 7: PRÓXIMOS PASSOS

### Opção A: Testar Deposit (Simples)

Você pode usar MetaMask + Arbiscan para interagir:

1. Abra: `https://sepolia.arbiscan.io/address/0xVAULT_ADDRESS_AQUI#writeContract`
2. Clique "Connect to Web3"
3. Conecte MetaMask
4. Use função `deposit()` para depositar USDC

---

### Opção B: Configurar Pool Uniswap (Avançado)

Para habilitar funcionalidades completas:

```bash
# Console
docker-compose run --rm vault-deployer npx hardhat console --network arbitrumSepolia
```

```javascript
const vault = await ethers.getContractAt('DeltaNeutralVaultV1', 'VAULT_ADDRESS');

// Configurar pool (exemplo - ajuste endereços!)
await vault.setUniswapConfig(
  'POOL_ADDRESS',
  '0x6b2937Bde17889EDCf8fbD8dE31C3C2a70Bc4d65',  // Position Manager
  '0x101F443B4d1b059569D643917553c771E1b9663E'   // Swap Router
);

// Definir range
await vault.setRange(-887220, 887220);  // Full range
```

---

## 🧹 PARTE 8: COMANDOS ÚTEIS

### Limpar Tudo

```bash
# Parar containers
docker-compose down

# Limpar volumes também
docker-compose down -v

# Limpar imagens
docker system prune -a
```

---

### Rebuild (após mudanças no código)

```bash
# Pull novas mudanças do git
git pull origin main

# Rebuild
docker-compose build --no-cache

# Deploy novamente
./docker-deploy.sh
```

---

### Ver Logs

```bash
# Ver logs do último deploy
docker-compose logs vault-deployer
```

---

### Usar Makefile (Atalhos)

```bash
# Ver comandos disponíveis
make help

# Deploy rápido
make quick-deploy

# Console
make console

# Compilar
make compile
```

---

## ❌ PROBLEMAS COMUNS

### Erro: "insufficient funds"

**Solução:**
```bash
# Pegar mais ETH no faucet
https://www.alchemy.com/faucets/arbitrum-sepolia

# Verificar saldo
https://sepolia.arbiscan.io/address/SEU_ENDEREÇO
```

---

### Erro: "Cannot find module"

**Solução:**
```bash
# Rebuild completo
docker-compose down -v
docker-compose build --no-cache
```

---

### Erro: ".env not found"

**Solução:**
```bash
# Verificar se .env existe
ls -la .env

# Se não existir, criar:
cp .env.example .env
nano .env
```

---

### Erro: "permission denied"

**Solução:**
```bash
# Dar permissões
chmod +x docker-deploy.sh

# Ou rodar com bash
bash docker-deploy.sh
```

---

## 📋 CHECKLIST COMPLETO

```
PREPARAÇÃO VPS:
[ ] SSH conectado na VPS
[ ] Sistema atualizado (apt update && apt upgrade)
[ ] Git instalado
[ ] Docker instalado
[ ] Docker Compose instalado

REPOSITÓRIO:
[ ] Repositório clonado
[ ] Navegado até DeltaNeutralVault
[ ] .env criado (cp .env.example .env)
[ ] PRIVATE_KEY configurada no .env
[ ] Permissões .env corretas (chmod 600)

ETH DE TESTE:
[ ] Endereço da carteira identificado
[ ] Arbitrum Sepolia adicionado no MetaMask
[ ] ETH obtido no faucet Alchemy (min 0.002 ETH)
[ ] Saldo verificado no Arbiscan

DEPLOY:
[ ] docker-deploy.sh executável (chmod +x)
[ ] Deploy executado com sucesso
[ ] Endereço do vault salvo
[ ] Vault verificado no Arbiscan

PÓS-DEPLOY:
[ ] Console testado
[ ] Funções básicas verificadas
[ ] Documentação lida
```

---

## 🎉 PARABÉNS!

Se você chegou até aqui, seu vault está deployado e funcionando! 🚀

### 📊 Arquivos Criados na Blockchain:

- ✅ **DeltaNeutralVaultV1**: Contrato principal
- ✅ **Endereço**: 0xVAULT_ADDRESS_AQUI
- ✅ **Rede**: Arbitrum Sepolia
- ✅ **Explorer**: https://sepolia.arbiscan.io

### 🔗 Links Úteis:

- **Arbiscan**: https://sepolia.arbiscan.io
- **Faucet**: https://www.alchemy.com/faucets/arbitrum-sepolia
- **Documentação Completa**: Ver DOCKER_DEPLOY.md

---

## 📞 SUPORTE

Se tiver problemas:
1. Verifique o checklist acima
2. Veja seção "Problemas Comuns"
3. Verifique logs: `docker-compose logs`
4. Leia DOCKER_DEPLOY.md para detalhes

---

**🎯 Vault deployado com sucesso! Agora você pode:**
- Depositar USDC
- Configurar estratégias
- Monitorar performance
- Escalar para produção

**Bom trabalho! 🚀**
