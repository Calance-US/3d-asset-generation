# 3D Concept Visualizer

A web application that generates interactive 3D visualizations of scientific concepts using AI.

## Features

1. Generate 3D visualizations from natural language descriptions
2. Support for multiple AI providers (OpenAI, Ollama, Gemini)
3. Interactive 3D scenes with rotation, zoom, and pan controls
4. History tracking of generated visualizations
5. Download visualizations as standalone HTML files
6. Use the history panel to manage past generations

---

## Local Development Setup (Makefile-Driven)

### Prerequisites

Before running `make up`, ensure you have the following installed:

- **Docker** (for Postgres, Keycloak, Qdrant, pgAdmin)
- **Node.js** (v18+ recommended, for frontend)
- **uv** (Python package manager, [install guide](https://docs.astral.sh/uv/getting-started/installation/))
- **GNU Make** (standard on Linux/macOS)
- **.env file**: Copy the example env files and edit as needed:
  ```bash
  cp backend/.env.example backend/.env
  # Edit backend/.env and set your secrets

  cp frontend/.env.example frontend/.env
  # Edit frontend/.env and set your secrets
  ```

> **Note:** No need to install Postgres, Qdrant, or Keycloak manually—these are managed by Docker Compose.

### Quick Start (One Command)

```bash
make up
```

This will:
- Start all infrastructure (Postgres, Keycloak, Qdrant, pgAdmin) via Docker Compose
- Wait for Keycloak to be ready and set up realms/users/clients
- Run Alembic migrations to set up the database schema
- Start the backend (FastAPI), frontend (React), and docs (MkDocs) servers
- Print all service URLs for quick access

### What Each Makefile Target Does

- **make up**: Full local stack (infra, backend, frontend, docs)
- **make infra**: Only start external services (Postgres, Keycloak, Qdrant, pgAdmin), set up Keycloak, and run DB migrations
- **make backend**: Create backend venv if needed, install dependencies, and run FastAPI server
- **make frontend**: Install frontend dependencies and run React dev server
- **make docs**: Create docs venv if needed, install dependencies, and serve documentation
- **make reset-db**: DANGER! Wipes all Postgres data and re-initializes databases and schema
- **make down**: Stop all services and kill app servers
- **make logs**: Show logs for all Docker services
- **make clean**: Remove all containers, volumes, and build artifacts

### Service URLs
- **Backend API:** http://localhost:8000
- **Frontend:** http://localhost:3000
- **Docs:** http://localhost:8002
- **Keycloak:** http://localhost:28080
- **pgAdmin:** http://localhost:5051
- **Qdrant:** http://localhost:6333

---

## Environment Variables

- Copy `.env.example` to `.env` in the `backend/` directory and fill in required values (API keys, database URL, etc):
  ```bash
  cp backend/.env.example backend/.env
  # Edit backend/.env and set your secrets
  ```
- Most local development will work out-of-the-box with the provided Docker Compose setup.

---

## Project Structure
```
.
├── backend
│   ├── alembic.ini
│   ├── app
│   │   ├── api
│   │   │   ├── api.py
│   │   │   └── endpoints
│   │   │       ├── admin.py
│   │   │       ├── async_visualizations.py
│   │   │       ├── auth.py
│   │   │       ├── gold_standards.py
│   │   │       ├── history.py
│   │   │       ├── local_models.py
│   │   │       ├── models.py
│   │   │       ├── prompt.py
│   │   │       ├── rag.py
│   │   │       └── visualizations.py
│   │   ├── auth
│   │   │   ├── dependencies.py
│   │   │   ├── jwt_utils.py
│   │   │   └── keycloak_client.py
│   │   ├── config
│   │   │   ├── logging_config.py
│   │   │   └── settings.py
│   │   ├── data
│   │   │   ├── costs.json
│   │   │   └── history.json
│   │   ├── database
│   │   │   ├── database.py
│   │   │   └── db_config.py
│   │   ├── models.py
│   │   ├── prompts
│   │   │   ├── biology
│   │   │   │   ├── generic.txt
│   │   │   │   └── human_heart.txt
│   │   │   ├── cbse_chemistry_boyle_gas_law.prompt.txt
│   │   │   ├── cbse_chemistry_titration_setup.prompt.txt
│   │   │   ├── cbse_physics_ohms_law_v2.prompt.txt
│   │   │   ├── cbse_physics_ohms_law.prompt.txt
│   │   │   ├── cbse_physics_pulley_system.prompt.txt
│   │   │   ├── chemistry
│   │   │   │   ├── atomic_structure.txt
│   │   │   │   ├── boyles_law.txt
│   │   │   │   ├── chemical_bonding.txt
│   │   │   │   ├── generic.txt
│   │   │   │   └── thermodynamics.txt
│   │   │   ├── embeddings
│   │   │   │   └── topics.npy
│   │   │   ├── enhanced_template.prompt.txt
│   │   │   ├── error_fixing_template.prompt.txt
│   │   │   ├── physics
│   │   │   │   ├── generic.txt
│   │   │   │   ├── ohms_law.txt
│   │   │   │   └── oscillations_shm.txt
│   │   │   ├── template.json
│   │   │   ├── template.prompt.txt
│   │   │   ├── template.prompt.txt.zip
│   │   │   └── template.sample.json
│   │   ├── schemas
│   │   │   ├── schemas.py
│   │   │   └── visualization.py
│   │   ├── services
│   │   │   ├── db_task_manager.py
│   │   │   ├── error_fixing
│   │   │   │   ├── enhanced_error_fixing_service.py
│   │   │   │   ├── error_fixing_service.py
│   │   │   │   └── validation_error_service.py
│   │   │   ├── local_model_service.py
│   │   │   ├── metadata_service.py
│   │   │   ├── model_repository.py
│   │   │   ├── prompt_generator.py
│   │   │   ├── prompt_selector.py
│   │   │   ├── quality_enhancement
│   │   │   │   ├── quality_analyzer.py
│   │   │   │   ├── quality_enhancement_service.py
│   │   │   │   └── types.py
│   │   │   ├── rag
│   │   │   │   ├── embedding_service.py
│   │   │   │   ├── metadata_service.py
│   │   │   │   ├── rag_service.py
│   │   │   │   └── vector_store.py
│   │   │   └── validation
│   │   │       ├── browser_tester.py
│   │   │       ├── context_filter.py
│   │   │       ├── enhanced_realism_validator.py
│   │   │       ├── enhanced_scientific_validator.py
│   │   │       ├── feedback_loop.py
│   │   │       ├── html_validator.py
│   │   │       ├── performance_validator.py
│   │   │       ├── quality_scorer.py
│   │   │       ├── realism_validator.py
│   │   │       ├── rendering_validator.py
│   │   │       ├── runtime_validator.py
│   │   │       ├── scientific_validator.py
│   │   │       ├── simple_orchestrator.py
│   │   │       ├── threejs_validator.py
│   │   │       └── validation_orchestrator.py
│   │   └── utils
│   │       ├── coerce_utils.py
│   │       ├── datetime_utils.py
│   │       ├── embedding_utils.py
│   │       ├── html_utils.py
│   │       ├── llm_utils.py
│   │       ├── prompt_utils.py
│   │       └── snippet_utils.py
│   ├── main.py
│   ├── migrations
│   │   ├── env.py
│   │   ├── README
│   │   ├── script.py.mako
│   │   └── versions
│   │       └── 2025_07_09_133110_create_all_models.py
│   ├── pyproject.toml
│   ├── sql
│   │   └── init-multi-db.sh
│   ├── uv.lock
├── docker-compose.yml
├── docs
│   ├── docs
│   │   ├── add-gold-standards-flow.md
│   │   ├── enhance-prompt-flow.md
│   │   ├── generate-visualization-flow.md
│   │   ├── index.md
│   │   ├── README.md
│   │   └── show-retrieved-results-flow.md
│   ├── javascripts
│   │   └── mathjax.js
│   ├── main.py
│   ├── mkdocs.yml
│   ├── pyproject.toml
│   ├── README-DOCS.md
│   ├── serve-docs.sh
│   ├── stylesheets
│   │   └── extra.css
│   └── uv.lock
├── frontend
│   ├── index.html
│   ├── package-lock.json
│   ├── package.json
│   ├── postcss.config.js
│   ├── public
│   │   ├── favicon.ico
│   │   ├── index.html
│   │   ├── logo192.png
│   │   ├── logo512.png
│   │   ├── manifest.json
│   │   └── silent-check-sso.html
│   ├── src
│   │   ├── App.jsx
│   │   ├── components
│   │   │   ├── admin
│   │   │   │   ├── ValidationMetrics.jsx
│   │   │   │   └── VectorStoreDashboard.jsx
│   │   │   ├── Admin.jsx
│   │   │   ├── auth
│   │   │   │   ├── AuthLoading.jsx
│   │   │   │   ├── LoginPage.jsx
│   │   │   │   ├── ProtectedRoute.jsx
│   │   │   │   └── UserMenu.jsx
│   │   │   ├── Generator.jsx
│   │   │   ├── PromptConfig.jsx
│   │   │   └── validation
│   │   │       └── ValidationStatus.jsx
│   │   ├── contexts
│   │   │   └── AuthContext.js
│   │   ├── index.css
│   │   ├── index.js
│   │   ├── lib
│   │   │   ├── api.js
│   │   │   ├── keycloak.js
│   │   │   └── utils.js
│   │   └── pages
│   │       └── AdminPage.jsx
│   ├── tailwind.config.js
│   └── vite.config.js
├── keycloak
│   ├── README.md
│   ├── realm-export.json
│   ├── setup-guide.md
│   └── themes
├── Makefile
├── openapi.json
├── pyrightconfig.json
├── README.md
├── scripts
│   ├── setup-keycloak-realm.sh
│   ├── start-keycloak.sh
│   └── stop-keycloak.sh
├── sequence-diagrams.md
```

---

## Troubleshooting

- **401 Unauthorized on admin endpoints:**
  - Log in via the frontend as an admin user (see Keycloak test users in setup output)
  - Ensure your frontend is configured to use the correct Keycloak realm/client
- **Port conflicts:**
  - Make sure nothing else is running on ports 3000, 8000, 8002, 28080, 5051, or 6333
- **Database issues:**
  - Use `make reset-db` to wipe and re-initialize all Postgres data (DANGER: destroys all data)

---

## License

MIT License

---

## Optional: Code Quality Analysis with SonarQube

You can optionally run static code analysis and code coverage checks using SonarQube. This is recommended for contributors who want to check code quality and test coverage locally before submitting changes.

### **Step 1: Run SonarQube Server (Docker)**

```bash
docker run -d --name sonarqube \
  -p 9000:9000 \
  -e SONAR_ES_BOOTSTRAP_CHECKS_DISABLE=true \
  sonarqube:community
```
- Access the UI at: http://localhost:9000 (default login: `admin` / `admin`)

### **Step 2: Install SonarScanner CLI**

- [Download SonarScanner CLI](https://docs.sonarsource.com/sonarqube/latest/analyzing-source-code/scanners/sonarscanner/)
- Or, on Mac with Homebrew:
  ```bash
  brew install sonar-scanner
  ```

### **Step 3: Configure Project**

- The repo includes a `sonar-project.example.properties` file in the backend directory. Rename to `sonar-project.properties` and edit as needed for your environment.

### **Step 4: Run SonarScanner**

```bash
sonar-scanner
```

### **Step 7: View Results**

- Go to http://localhost:9000 and find your project.
- Review code smells, bugs, dead code, and coverage.

---

**Note:** SonarQube integration is optional and not required for local development or PRs, but is recommended for code quality best practices.