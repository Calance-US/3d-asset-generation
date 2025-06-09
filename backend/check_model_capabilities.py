import openai
from app.config.settings import settings
from app.config.logging_config import logger
from app.services.model_repository import ModelRepository

# Set the API key from settings
openai.api_key = settings.OPENAI_API_KEY

# Test model capabilities
response = openai.chat.completions.create(
    model="gpt-4.1-mini",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "What is your maximum token limit?"}
    ],
    max_tokens=100
)
logger.info("Model response: %s", response.choices[0].message.content) 