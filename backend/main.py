import uvicorn
from app.api.api import api_router
from app.config.logging_config import logger
from app.database.database import get_db, get_prompts
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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
    try:
        db = next(get_db())
        prompts = get_prompts(db)
        logger.info(
            "Database connection successful",
            extra={"action": "init_database", "prompt_count": len(prompts)},
        )
    except Exception as e:
        logger.error(
            "Error during startup",
            extra={
                "action": "startup",
                "error": str(e),
                "error_type": type(e).__name__,
            },
        )
        raise


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
