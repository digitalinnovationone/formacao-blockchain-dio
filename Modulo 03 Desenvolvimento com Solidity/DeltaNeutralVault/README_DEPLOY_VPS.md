# 🚀 Deploy na VPS - 2 Métodos

---

## ⚡ MÉTODO 1: Script Automatizado (MAIS FÁCIL!)

### Um comando faz tudo:

```bash
# 1. SSH na VPS
ssh root@SEU_IP_VPS

# 2. Clonar repositório
git clone https://github.com/Leandrosmoreira/formacao-blockchain-dio.git
cd "formacao-blockchain-dio/Modulo 03 Desenvolvimento com Solidity/DeltaNeutralVault"

# 3. Executar script mágico ✨
./setup-vps.sh
```

**O script vai:**
- ✅ Instalar Docker automaticamente
- ✅ Instalar Docker Compose
- ✅ Pedir sua private key
- ✅ Criar arquivo .env
- ✅ Build da imagem Docker
- ✅ Deploy no Arbitrum Sepolia
- ✅ Salvar informações em deployment-info.txt

**Tempo total:** ~5 minutos

---

## 📋 MÉTODO 2: Passo a Passo Manual

Para quem quer mais controle, siga o guia completo:

📖 **[VPS_SETUP_COMPLETO.md](VPS_SETUP_COMPLETO.md)**

**Passos:**
1. Preparar VPS (instalar Docker)
2. Clonar repositório
3. Configurar .env manualmente
4. Obter ETH de teste
5. Deploy com Docker
6. Verificar no Arbiscan

---

## 💰 Obter ETH de Teste (OBRIGATÓRIO!)

Antes de fazer deploy, pegue ETH nos faucets:

| Faucet | Quantidade | Link |
|--------|------------|------|
| **Alchemy** ⭐ | 0.1 ETH | https://www.alchemy.com/faucets/arbitrum-sepolia |
| **QuickNode** | 0.05 ETH | https://faucet.quicknode.com/arbitrum/sepolia |
| **Chainlink** | 0.01 ETH | https://faucets.chain.link/arbitrum-sepolia |

**Mínimo necessário:** 0.002 ETH

---

## 🎯 Comparação dos Métodos

| Aspecto | Script Automatizado | Passo a Passo |
|---------|---------------------|---------------|
| **Tempo** | ~5 min | ~15 min |
| **Facilidade** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| **Controle** | Automático | Manual |
| **Para quem?** | Iniciantes | Avançados |
| **Recomendado?** | ✅ SIM | Se quiser aprender |

---

## ✅ Após o Deploy

Seu vault estará deployado em:
```
https://sepolia.arbiscan.io/address/VAULT_ADDRESS
```

### Comandos Úteis:

```bash
# Console interativo
make console

# Rodar testes
make test

# Limpar tudo
make clean

# Ver ajuda
make help
```

---

## 📚 Documentação Completa

- **[VPS_SETUP_COMPLETO.md](VPS_SETUP_COMPLETO.md)** - Guia detalhado (1000+ linhas)
- **[DOCKER_DEPLOY.md](DOCKER_DEPLOY.md)** - Referência Docker
- **[DEPLOY_ARBITRUM_SEPOLIA.md](DEPLOY_ARBITRUM_SEPOLIA.md)** - Sobre Arbitrum

---

## 🆘 Problemas?

### Erro: "insufficient funds"
Pegue mais ETH: https://www.alchemy.com/faucets/arbitrum-sepolia

### Erro: "Docker not found"
Execute: `curl -fsSL https://get.docker.com | sh`

### Erro: ".env not found"
Execute: `cp .env.example .env` e edite com sua private key

### Outros problemas?
Veja seção "Problemas Comuns" em [VPS_SETUP_COMPLETO.md](VPS_SETUP_COMPLETO.md)

---

## 🎉 TL;DR (Resumo Ultrarrápido)

```bash
# Na VPS:
git clone https://github.com/Leandrosmoreira/formacao-blockchain-dio.git
cd "formacao-blockchain-dio/Modulo 03 Desenvolvimento com Solidity/DeltaNeutralVault"
./setup-vps.sh

# Pronto! ✅
```

**Antes:** Pegue ETH em https://www.alchemy.com/faucets/arbitrum-sepolia

---

**🚀 Deploy profissional em 5 minutos!**
