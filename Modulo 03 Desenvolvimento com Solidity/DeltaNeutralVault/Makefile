# =====================================================
# Makefile - DeltaNeutralVault Docker
# =====================================================

.PHONY: help build deploy test console clean verify

# Cores
GREEN := \033[0;32m
YELLOW := \033[1;33m
NC := \033[0m

help: ## Mostra ajuda
	@echo "$(GREEN)DeltaNeutralVault - Comandos Docker$(NC)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(YELLOW)%-15s$(NC) %s\n", $$1, $$2}'
	@echo ""

build: ## Build da imagem Docker
	@echo "$(GREEN)📦 Building Docker image...$(NC)"
	docker-compose build --no-cache

deploy: ## Deploy no Arbitrum Sepolia
	@echo "$(GREEN)🚀 Deploying to Arbitrum Sepolia...$(NC)"
	docker-compose run --rm vault-deployer npx hardhat run scripts/deploy.js --network arbitrumSepolia

compile: ## Compilar contratos
	@echo "$(GREEN)🔨 Compiling contracts...$(NC)"
	docker-compose run --rm vault-deployer npx hardhat compile

test: ## Rodar testes
	@echo "$(GREEN)🧪 Running tests...$(NC)"
	docker-compose run --rm vault-deployer npx hardhat test

console: ## Abrir console Hardhat (Arbitrum Sepolia)
	@echo "$(GREEN)💻 Opening Hardhat console...$(NC)"
	docker-compose run --rm vault-deployer npx hardhat console --network arbitrumSepolia

shell: ## Abrir shell no container
	@echo "$(GREEN)🐚 Opening shell...$(NC)"
	docker-compose run --rm vault-deployer bash

clean: ## Limpar containers e volumes
	@echo "$(YELLOW)🧹 Cleaning up...$(NC)"
	docker-compose down -v
	rm -rf artifacts/ cache/

rebuild: clean build ## Rebuild completo (limpa + build)

verify: ## Verificar contrato no Arbiscan (VAULT_ADDRESS=0x...)
	@echo "$(GREEN)🔍 Verifying contract...$(NC)"
	@if [ -z "$(VAULT_ADDRESS)" ]; then \
		echo "$(YELLOW)⚠️  Use: make verify VAULT_ADDRESS=0x...$(NC)"; \
		exit 1; \
	fi
	docker-compose run --rm vault-deployer npx hardhat verify --network arbitrumSepolia $(VAULT_ADDRESS)

logs: ## Ver logs do container
	docker-compose logs -f vault-deployer

status: ## Ver status dos containers
	docker-compose ps

# Comandos combinados
quick-deploy: build deploy ## Build + Deploy

# Default
.DEFAULT_GOAL := help
