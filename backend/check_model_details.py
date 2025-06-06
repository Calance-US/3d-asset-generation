import openai
from app.config.settings import settings

# Set the API key from settings
openai.api_key = settings.OPENAI_API_KEY

# Get model details
model = openai.models.retrieve("gpt-4.1-mini")
print(model.model_dump()) 