import openai
from app.config.settings import settings

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
print(response.choices[0].message.content) 