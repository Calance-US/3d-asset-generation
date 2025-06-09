import openai
from app.config.settings import settings
from app.config.logging_config import logger
from app.services.model_repository import ModelRepository

# Set the API key from settings
openai.api_key = settings.OPENAI_API_KEY

# List all models
response = openai.models.list()
for model in response.model_dump()["data"]:
    logger.info("Model ID: %s", model["id"]) 