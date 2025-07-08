"""
LLM Generation Utilities

This module provides utilities for generating content using different LLM providers
to avoid circular imports between services.
"""

import logging
from typing import Optional

from app.config.settings import settings
from google.generativeai.types import HarmBlockThreshold, HarmCategory
from openai import AsyncOpenAI

logger = logging.getLogger(__name__)

# Initialize OpenAI client
client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY) if settings.OPENAI_API_KEY else None


async def generate_with_provider(prompt: str, provider: str) -> Optional[str]:
    """
    Generate content using the specified provider.
    
    Args:
        prompt: The prompt to send to the LLM
        provider: The provider to use (openai, gemini, ollama)
        
    Returns:
        Generated content or None if generation failed
    """
    try:
        if provider == "openai":
            if not client:
                logger.error("OpenAI API key not configured")
                return None
                
            response = await client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=settings.TEMPERATURE,
                stream=settings.STREAM,
            )
            return response.choices[0].message.content
            
        elif provider == "gemini":
            import google.generativeai as genai
            
            genai.configure(api_key=settings.GOOGLE_API_KEY)
            model = genai.GenerativeModel(
                settings.GEMINI_MODEL,
                safety_settings={
                    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
                },
            )
            
            response = model.generate_content(prompt)
            return response.text
            
        elif provider == "ollama":
            import aiohttp
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{settings.OLLAMA_BASE_URL}/api/generate",
                    json={
                        "model": settings.OLLAMA_MODEL,
                        "prompt": prompt,
                        "stream": False,
                    },
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result.get("response", "")
                    else:
                        logger.error(f"Ollama API error: {response.status}")
                        return None
        else:
            logger.error(f"Unknown provider: {provider}")
            return None
            
    except Exception as e:
        logger.error(f"Error generating content with {provider}: {e}")
        return None 