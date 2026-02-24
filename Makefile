.PHONY: help setup test lint clean run deploy docker-build docker-run health check-config backup restore secrets monitoring

# Default target
help:
	@echo "OpenClaw Memory Template - Make commands:"
	@echo ""
	@echo "  make setup         - Install dependencies and initialize"
	@echo "  make test          - Run tests"
	@echo "  make lint          - Run linters (black, isort, flake8, mypy)"
	@echo "  make clean         - Clean build artifacts and cache"
	@echo "  make run           - Run memory sync"
	@echo "  make deploy        - Deploy to Git"
	@echo "  make docker-build  - Build Docker image"
	@echo "  make docker-run    - Run Docker container"
	@echo "  make health        - Start health check server"
	@echo "  make check-config  - Check and print configuration"
	@echo "  make test-logging - Test structured logging"
	@echo "  make backup        - Create backup"
	@echo "  make backup-list   - List backups"
	@echo "  make restore       - Restore from backup"
	@echo "  make backup-prune  - Prune old backups"
	@echo "  make backup-auto   - Auto backup (for cron)"
	@echo "  make secrets-*     - Secrets management (get/set/delete/list/rotate)"
	@echo "  make monitoring    - Start Prometheus monitoring server"
	@echo ""

# Setup: Install and initialize
setup:
	@echo "📦 Installing dependencies..."
	pip install -r requirements.txt
	@echo "📝 Initializing workspace..."
	bash .openclaw/scripts/init.sh
	@echo "✅ Setup complete!"

# Run tests
test:
	@echo "🧪 Running tests..."
	pytest tests/ -v --cov=tests --cov-report=term

# Run tests with coverage report
test-ci:
	@echo "🧪 Running tests for CI..."
	pytest tests/ -v --cov=tests --cov-report=xml --cov-report=term

# Run linters
lint:
	@echo "🔍 Running black..."
	black --check --diff . || echo "Run 'black .' to fix"
	@echo "🔍 Running isort..."
	isort --check-only --diff . || echo "Run 'isort .' to fix"
	@echo "🔍 Running flake8..."
	flake8 . --count --max-line-length=100 --show-source --statistics
	@echo "🔍 Running mypy..."
	mypy . --ignore-missing-imports || true

# Format code
format:
	@echo "✨ Formatting code..."
	black .
	isort .

# Clean build artifacts and cache
clean:
	@echo "🧹 Cleaning..."
	rm -rf .pytest_cache
	rm -rf __pycache__
	rm -rf .mypy_cache
	rm -rf .coverage
	rm -rf coverage.xml
	rm -rf htmlcov
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	find . -type d -name ".msam" -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.db" -delete 2>/dev/null || true
	@echo "✅ Clean complete!"

# Run memory sync
run:
	@echo "🔄 Running memory sync..."
	bash .openclaw/scripts/sync.sh

# Create daily log
log:
	@echo "📝 Creating daily log..."
	bash .openclaw/scripts/log.sh

# Check status
status:
	@echo "📊 Checking status..."
	bash .openclaw/scripts/status.sh

# Deploy to Git
deploy:
	@echo "🚀 Deploying to Git..."
	cd memory && git push origin main

# Build Docker image
docker-build:
	@echo "🐳 Building Docker image..."
	docker build -t openclaw-memory-template:latest .

# Run Docker container
docker-run:
	@echo "🐳 Running Docker container..."
	docker run -it --rm \
		-v $(PWD)/memory:/app/memory \
		-v $(PWD)/.openclaw:/app/.openclaw \
		openclaw-memory-template:latest

# Run tests in Docker
docker-test:
	@echo "🐳 Running tests in Docker..."
	docker run -it --rm \
		openclaw-memory-template:latest \
		make test

# Install development dependencies
dev-install:
	@echo "📦 Installing development dependencies..."
	pip install -r requirements.txt
	pip install -r requirements-dev.txt

# Run all checks (test + lint)
check: lint test
	@echo "✅ All checks passed!"

# Initialize research engine
research-init:
	@echo "📚 Initializing research engine..."
	bash scripts/research.sh init

# Run research engine
research-run:
	@echo "📚 Running research engine..."
	bash scripts/research.sh run

# Run research engine status
research-status:
	@echo "📚 Research engine status..."
	bash scripts/research.sh status

# Start health check server
health:
	@echo "🚀 Starting health check server..."
	python health.py

# Check configuration
check-config:
	@echo "📋 Checking configuration..."
	python config.py

# Test logging
test-logging:
	@echo "📝 Testing structured logging..."
	python logging.py

# Create backup
backup:
	@echo "📦 Creating backup..."
	python backup.py backup

# List backups
backup-list:
	@echo "📋 Listing backups..."
	python backup.py list

# Restore backup
restore:
	@echo "📦 Restoring backup..."
	python backup.py restore $(BACKUP_NAME)

# Prune old backups
backup-prune:
	@echo "🧹 Pruning old backups..."
	python backup.py prune --keep 10

# Auto backup (for cron)
backup-auto:
	@echo "📦 Running auto backup..."
	python backup.py auto --interval 24

# Secrets management
secrets-get:
	@echo "🔐 Getting secret..."
	python secrets.py get $(SECRET_NAME)

secrets-set:
	@echo "🔐 Setting secret..."
	python secrets.py set $(SECRET_NAME) "$(SECRET_VALUE)"

secrets-delete:
	@echo "🔐 Deleting secret..."
	python secrets.py delete $(SECRET_NAME)

secrets-list:
	@echo "🔐 Listing secrets..."
	python secrets.py list

secrets-rotate:
	@echo "🔐 Rotating secrets password..."
	python secrets.py rotate

# Monitoring server
monitoring:
	@echo "📊 Starting monitoring server..."
	python monitoring.py
