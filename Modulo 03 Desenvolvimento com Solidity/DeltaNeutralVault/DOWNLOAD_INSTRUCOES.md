# 📦 Download do DeltaNeutralVault

## Arquivos Essenciais para Deploy na VPS

Execute estes comandos na sua VPS:

```bash
# Criar diretório
mkdir -p ~/DeltaNeutralVault
cd ~/DeltaNeutralVault

# Criar package.json
cat > package.json << 'PKGJSON'
{
  "name": "delta-neutral-vault",
  "version": "1.0.0",
  "devDependencies": {
    "@nomicfoundation/hardhat-toolbox": "^3.0.0",
    "@openzeppelin/contracts": "^4.9.3",
    "@chainlink/contracts": "^0.8.0",
    "@uniswap/v3-core": "^1.0.1",
    "@uniswap/v3-periphery": "^1.4.3",
    "hardhat": "^2.17.0",
    "dotenv": "^16.3.1"
  }
}
PKGJSON

# Criar .env.example
cat > .env.example << 'ENVEX'
PRIVATE_KEY=sua_private_key_sem_0x
ARBITRUM_SEPOLIA_RPC_URL=https://sepolia-rollup.arbitrum.io/rpc
ENVEX

# Criar Dockerfile
cat > Dockerfile << 'DFILE'
FROM node:18-alpine
RUN apk add --no-cache git python3 make g++ bash
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npx hardhat compile
CMD ["bash"]
DFILE

# Criar docker-compose.yml
cat > docker-compose.yml << 'DCFILE'
version: '3.8'
services:
  vault-deployer:
    build: .
    container_name: deltaneutral-vault
    volumes:
      - .:/app
      - node_modules:/app/node_modules
    environment:
      - PRIVATE_KEY=${PRIVATE_KEY}
      - ARBITRUM_SEPOLIA_RPC_URL=${ARBITRUM_SEPOLIA_RPC_URL}
    env_file: .env
    stdin_open: true
    tty: true
volumes:
  node_modules:
DCFILE

echo "✅ Arquivos criados!"
echo ""
echo "PRÓXIMOS PASSOS:"
echo "1. Baixe os arquivos .sol (enviarei separadamente)"
echo "2. Configure .env: cp .env.example .env && nano .env"
echo "3. Execute: docker compose build && docker compose run --rm vault-deployer npx hardhat run scripts/deploy.js --network arbitrumSepolia"
```
