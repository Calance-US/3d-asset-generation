import openai
from app.config.settings import settings

# Set the API key from settings
openai.api_key = settings.OPENAI_API_KEY

# List all models
response = openai.models.list()
for model in response.model_dump()["data"]:
    print(model["id"]) 