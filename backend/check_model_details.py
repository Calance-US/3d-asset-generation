import openai
from app.config.settings import settings
from app.config.logging_config import logger
from app.services.model_repository import ModelRepository

# Set the API key from settings
openai.api_key = settings.OPENAI_API_KEY

# Get model details
model = openai.models.retrieve("gpt-4.1-mini")
logger.info("Model details: %s", model.model_dump()) 