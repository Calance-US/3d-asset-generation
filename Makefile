# Makefile for unified local dev environment

.PHONY: up down logs ps clean keycloak-setup backend frontend docs infra reset-db seed-keycloak-users

up:
	make infra
	@echo "Starting backend server..."
	make backend &
	@echo "Waiting for backend to be ready..."
	@until curl -sSf http://localhost:8000/health > /dev/null; do \
	  echo "Waiting for backend..."; \
	  sleep 3; \
	done
	@echo "Backend is up! Starting frontend and docs servers..."
	make frontend &
	make docs &
	@echo "---"
	@echo "All services are up!"
	@echo "Backend:     http://localhost:8000"
	@echo "Frontend:    http://localhost:3000"
	@echo "Docs:        http://localhost:8002"
	@echo "Keycloak:    http://localhost:28080"
	@echo "pgAdmin:     http://localhost:5051"
	@echo "Qdrant:      http://localhost:6333"
	@echo "---"


down:
	docker-compose down
	@pkill -f "uvicorn main:app" || true
	@pkill -f "npm start" || true
	@pkill -f "mkdocs serve" || true

logs:
	docker-compose logs -f

ps:
	docker-compose ps

clean:
	docker-compose down -v
	rm -rf postgres_data pgadmin-data qdrant

keycloak-setup:
	@echo "Running Keycloak realm setup script..."
	@cd keycloak && bash ../scripts/setup-keycloak-realm.sh

backend:
	cd backend && (test -d .venv || uv venv .venv) && . .venv/bin/activate && uv pip install -r pyproject.toml && uv run uvicorn main:app --reload

frontend:
	cd frontend && npm install && npm start

docs:
	cd docs && (test -d .venv || uv venv .venv) && . .venv/bin/activate && uv pip install mkdocs mkdocs-material mkdocs-mermaid2-plugin pymdown-extensions && uv run mkdocs serve -a 0.0.0.0:8002

docs-build:
	cd docs && (test -d .venv || uv venv .venv) && . .venv/bin/activate && uv pip install mkdocs mkdocs-material mkdocs-mermaid2-plugin pymdown-extensions && uv run mkdocs build

docker-check:
	@docker info > /dev/null 2>&1 || (echo "ERROR: Docker is not running. Please start Docker Desktop or the Docker daemon." && exit 1)

seed-keycloak-users:
	@echo "Seeding Keycloak test users into Postgres..."
	./scripts/seed_keycloak_users.sh

infra:
	docker-compose up -d
	@echo "External services started: Postgres, Keycloak, Qdrant, pgAdmin."
	@echo "Waiting for Keycloak to be ready..."
	@until curl -sSf http://localhost:28080/ > /dev/null; do \
	  echo "Waiting for Keycloak..."; \
	  sleep 3; \
	done
	@make keycloak-setup
	@echo "Keycloak setup completed."
	@cd backend && (test -d .venv || uv venv .venv) && . .venv/bin/activate && uv pip install -r pyproject.toml && alembic upgrade head
	@echo "Alembic migrations applied."
	@make seed-keycloak-users

reset-db:
	@echo "WARNING: This will delete all Postgres data and recreate the databases!"
	@read -p "Press enter to continue or Ctrl+C to abort..." dummy
	make down
	rm -rf postgres_data
	make infra