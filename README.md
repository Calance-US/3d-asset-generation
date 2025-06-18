# 3D Concept Visualizer

A web application that generates interactive 3D visualizations of scientific concepts using AI.

## Features

1. Generate 3D visualizations from natural language descriptions
2. Support for multiple AI providers (OpenAI, Ollama, Gemini)
3. Interactive 3D scenes with rotation, zoom, and pan controls
4. History tracking of generated visualizations
5. Download visualizations as standalone HTML files
6. Use the history panel to manage past generations

## Development

### External Services & Environment Setup

- **.env file:**
  - Copy `.env.example` to `.env` in the `backend/` directory and fill in required values (API keys, database URL, etc).
  - Example:
    ```bash
    cp backend/.env.example backend/.env
    # Edit backend/.env and set your secrets
    ```
- **Database:**
  - By default, uses SQLite (`app.db`).
  - To use Postgres or another DB, set `DATABASE_URL` in `.env` (e.g., `postgresql://user:pass@localhost:5432/dbname`).
  - For Postgres (Docker):
    ```bash
    docker run --name pg-3dwebapp -e POSTGRES_PASSWORD=yourpassword -e POSTGRES_DB=3dwebapp -p 5432:5432 -d postgres:15
    # Then set DATABASE_URL=postgresql://postgres:yourpassword@localhost:5432/3dwebapp in .env
    ```
- **Redis:**
  - Required for caching/session (default: `redis://localhost:6379`).
  - Run with Docker:
    ```bash
    docker run --name redis-3dwebapp -p 6379:6379 -d redis:7
    ```
  - Or install locally: https://redis.io/download
- **Qdrant (optional, for production-scale vector search):**
  - Run with Docker:
    ```bash
    docker run -p 6333:6333 -p 6334:6334 qdrant/qdrant
    ```
  - Set the following in your `.env`:
    ```
    QDRANT_URL=http://localhost:6333
    QDRANT_COLLECTION=visualizations
    ```
  - See https://qdrant.tech/documentation/ for more options.
- **AI Provider Keys:**
  - Set your OpenAI, Google, Ollama, and Gemini API keys/URLs in `.env` as needed.

### Project Structure
```
.
├── backend
│   ├── alembic.ini
│   ├── app
│   │   ├── api
│   │   │   ├── api.py
│   │   │   └── endpoints
│   │   │       ├── admin.py
│   │   │       ├── gold_standards.py
│   │   │       ├── history.py
│   │   │       ├── models.py
│   │   │       ├── prompt.py
│   │   │       ├── rag.py
│   │   │       └── visualizations.py
│   │   ├── config
│   │   │   ├── logging_config.py
│   │   │   └── settings.py
│   │   ├── database
│   │   │   ├── database.py
│   │   │   └── db_config.py
│   │   ├── models.py
│   │   ├── prompts
│   │   │   └── template.prompt.txt
│   │   ├── schemas
│   │   │   ├── schemas.py
│   │   │   └── visualization.py
│   │   ├── services
│   │   │   ├── metadata_service.py
│   │   │   ├── model_repository.py
│   │   │   ├── prompt_generator.py
│   │   │   ├── prompt_selector.py
│   │   │   └── rag
│   │   │       ├── embedding_service.py
│   │   │       ├── metadata_service.py
│   │   │       ├── rag_service.py
│   │   │       └── vector_store.py
│   │   └── utils
│   │       ├── coerce_utils.py
│   │       ├── datetime_utils.py
│   │       ├── embedding_utils.py
│   │       ├── html_utils.py
│   │       ├── prompt_utils.py
│   │       └── snippet_utils.py
│   ├── main.py
│   ├── migrations
│   │   ├── env.py
│   │   ├── README
│   │   ├── script.py.mako
│   │   └── versions
│   │       ├── 2024_03_19_0001_create_snippet_metadata_table.py
│   │       ├── 2025_06_16_1023-e7c7d9ac9c85_add_gold_standard_upload_status_table.py
│   │       ├── 2025_06_16_1047-b264deffc916_add_result_column_to_gold_standard_.py
│   │       ├── 2025_06_16_1050_recreate_gold_standard_upload_status.py
│   │       ├── 2025_06_17_0001_create_faiss_id_metadata_link.py
│   │       ├── 2025_06_18_0001_autoincrement_prompt_id.py
│   │       ├── 2025_06_18_0100_prompts_id_identity.py
│   │       ├── 2025_06_18_0200_visualizations_id_identity.py
│   │       ├── 74c94aab2a18_initial_migration.py
│   │       ├── add_string_id_to_history.py
│   │       └── add_visualization_tags.py
│   ├── pyproject.toml
│   └── uv.lock
├── FILE_STRUCTURE.md
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
│   │   └── manifest.json
│   ├── src
│   │   ├── App.jsx
│   │   ├── components
│   │   │   ├── admin
│   │   │   │   └── VectorStoreDashboard.jsx
│   │   │   ├── Admin.jsx
│   │   │   ├── Generator.jsx
│   │   │   └── PromptConfig.jsx
│   │   ├── index.css
│   │   ├── index.js
│   │   ├── lib
│   │   │   └── utils.js
│   │   └── pages
│   │       └── AdminPage.jsx
│   ├── tailwind.config.js
│   └── vite.config.js
├── pyrightconfig.json
└── README.md
```

### Running the Application

1. Start the backend server:
```bash
cd backend
uv run uvicorn main:app --reload
```

2. Start the frontend development server:
```bash
cd frontend
npm install
npm start
```

3. Open http://localhost:3000 in your browser

### Adding New Features
1. Frontend components are in `frontend/src/components/`
2. Backend API endpoints are in `backend/main.py`
3. Add new dependencies to `package.json` or `requirements.txt`

## License

MIT License 