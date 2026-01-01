# =====================================================
# Dockerfile para Deploy DeltaNeutralVault
# =====================================================

FROM node:18-alpine

# Instalar dependências do sistema
RUN apk add --no-cache \
    git \
    python3 \
    make \
    g++ \
    bash

# Criar diretório de trabalho
WORKDIR /app

# Copiar package files
COPY package*.json ./

# Instalar dependências
RUN npm install --production=false

# Copiar código do projeto
COPY . .

# Compilar contratos
RUN npx hardhat compile

# Expor porta (se necessário para API)
EXPOSE 8545

# Comando padrão
CMD ["bash"]
