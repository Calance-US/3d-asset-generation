from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from app.config.settings import settings
from app.database.database import get_db, get_prompts
from app.config.logging_config import logger
from app.api.api import api_router
from app.services.rag.vector_store import get_vector_store

# Initialize FastAPI app
app = FastAPI()

# Enable CORS for all origins (adjust for production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the API router
app.include_router(api_router, prefix="/api/v1")

@app.on_event("startup")
async def startup_event():
    """Run migrations only if RUN_MIGRATIONS setting is enabled."""
    try:
        db = next(get_db())
        prompts = get_prompts(db)
        logger.info("Database connection successful", extra={
            "action": "init_database",
            "prompt_count": len(prompts)
        })
        if settings.RUN_MIGRATIONS:
            logger.info("Running database migrations...", extra={
                "action": "run_migrations"
            })
            # migrate_from_json()
            # run_migration()  # Run the new migration
            pass
        else:
            logger.info("Skipping database migrations. Set RUN_MIGRATIONS=1 to run migrations.", extra={
                "action": "skip_migrations"
            })
        vector_store = get_vector_store()
        try:
            vector_store.load(settings.VECTOR_STORE_PATH)
            logger.info("Vector store loaded successfully", extra={
                "action": "init_vector_store",
                "path": settings.VECTOR_STORE_PATH,
                "num_vectors": vector_store.faiss_index.ntotal if vector_store.faiss_index else 0
            })
        except FileNotFoundError:
            logger.info("No existing vector store found, starting fresh", extra={
                "action": "init_vector_store",
                "path": settings.VECTOR_STORE_PATH
            })
        except Exception as e:
            logger.error("Error loading vector store", extra={
                "action": "init_vector_store",
                "error": str(e)
            })
    except Exception as e:
        logger.error("Error during startup", extra={
            "action": "startup",
            "error": str(e),
            "error_type": type(e).__name__
        })
        raise

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
