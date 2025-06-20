import uvicorn
from app.api.api import api_router
from app.auth.keycloak_client import get_keycloak_client
from app.config.logging_config import logger
from app.config.settings import get_settings
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


@app.get("/health")
async def health_check():
    """Health check endpoint that returns system configuration and status."""
    settings = get_settings()

    health_data = {
        "status": "healthy",
        "environment": settings.ENVIRONMENT,
        "vector_store_dimension": settings.VECTOR_STORE_DIMENSION,
        "vector_store_collection_name": settings.VECTOR_STORE_COLLECTION_NAME,
        "database_echo": settings.DATABASE_ECHO,
        "database_pool_recycle": settings.DATABASE_POOL_RECYCLE,
        "ollama_base_url": settings.OLLAMA_BASE_URL,
        "ollama_model": settings.OLLAMA_MODEL,
        "gemini_model": settings.GEMINI_MODEL,
        "openai_model": settings.OPENAI_MODEL,
        "temperature": settings.TEMPERATURE,
        "stream": settings.STREAM,
        "similar_vis_limit": settings.SIMILAR_VIS_LIMIT,
        "enable_comprehensive_validation": settings.ENABLE_COMPREHENSIVE_VALIDATION,
        "enable_runtime_validation": settings.ENABLE_RUNTIME_VALIDATION,
        "validation_timeout_html": settings.VALIDATION_TIMEOUT_HTML,
        "validation_timeout_scientific": settings.VALIDATION_TIMEOUT_SCIENTIFIC,
        "validation_timeout_realism": settings.VALIDATION_TIMEOUT_REALISM,
        "validation_timeout_runtime": settings.VALIDATION_TIMEOUT_RUNTIME,
        "quality_score_threshold": settings.QUALITY_SCORE_THRESHOLD,
        "enable_quality_filtering": settings.ENABLE_QUALITY_FILTERING,
        "enable_feedback_loop": settings.ENABLE_FEEDBACK_LOOP,
        "context_filter_min_quality": settings.CONTEXT_FILTER_MIN_QUALITY,
        "context_filter_max_items": settings.CONTEXT_FILTER_MAX_ITEMS,
        "context_filter_ensure_diversity": settings.CONTEXT_FILTER_ENSURE_DIVERSITY,
        "max_llm_retry": settings.MAX_LLM_RETRY,
        "enable_error_fixing": settings.ENABLE_ERROR_FIXING,
        "save_all_validation_errors": settings.SAVE_ALL_VALIDATION_ERRORS,
        "error_fixing_template_path": settings.ERROR_FIXING_TEMPLATE_PATH,
        "auth_enabled": settings.AUTH_ENABLED,
        "auth_bypass_development": settings.AUTH_BYPASS_DEVELOPMENT,
        "keycloak_server_url": settings.KEYCLOAK_SERVER_URL,
        "keycloak_realm": settings.KEYCLOAK_REALM,
        "keycloak_client_id": settings.KEYCLOAK_CLIENT_ID,
    }

    # Only include database URL in development environment
    if settings.ENVIRONMENT == "development":
        health_data["database_url"] = settings.DATABASE_URL

    return health_data


@app.on_event("startup")
async def startup_event():
    try:
        # Test database connection
        db = next(get_db())
        prompts = get_prompts(db)
        logger.info(
            "Database connection successful",
            extra={"action": "init_database", "prompt_count": len(prompts)},
        )

        # Test authentication service connection if enabled
        settings = get_settings()
        if settings.AUTH_ENABLED:
            try:
                keycloak_client = get_keycloak_client()
                auth_healthy = keycloak_client.health_check()
                if auth_healthy:
                    logger.info(
                        "Authentication service connection successful",
                        extra={
                            "action": "init_auth",
                            "keycloak_server": settings.KEYCLOAK_SERVER_URL,
                        },
                    )
                else:
                    logger.warning(
                        "Authentication service connection failed",
                        extra={
                            "action": "init_auth",
                            "keycloak_server": settings.KEYCLOAK_SERVER_URL,
                        },
                    )
            except Exception as auth_error:
                logger.warning(
                    "Authentication service initialization failed",
                    extra={
                        "action": "init_auth",
                        "error": str(auth_error),
                        "error_type": type(auth_error).__name__,
                        "keycloak_server": settings.KEYCLOAK_SERVER_URL,
                    },
                )
        else:
            logger.info(
                "Authentication is disabled",
                extra={"action": "init_auth", "auth_enabled": False},
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
