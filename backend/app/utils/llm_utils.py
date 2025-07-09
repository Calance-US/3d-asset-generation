"""
LLM Generation Utilities

This module provides utilities for generating content using different LLM providers
to avoid circular imports between services.
"""

import logging
from typing import Optional, List, Dict

from app.config.settings import settings
from google.generativeai.types import HarmBlockThreshold, HarmCategory
from openai import AsyncOpenAI

logger = logging.getLogger(__name__)

# Initialize OpenAI client
client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY) if settings.OPENAI_API_KEY else None


async def generate_with_provider(prompt: str, provider: str, messages: Optional[List[Dict[str, str]]] = None) -> Optional[str]:
    """
    Generate content using the specified provider.
    
    Args:
        prompt: The prompt to send to the LLM
        provider: The provider to use (openai, gemini, ollama)
        messages: Optional list of chat messages (role/content) for chat-based LLMs
    Returns:
        Generated content or None if generation failed
    """
    try:
        if provider == "openai":
            if not client:
                logger.error("OpenAI API key not configured")
                return None
            # Use messages if provided, else fallback to prompt
            chat_messages = messages if messages else [{"role": "user", "content": prompt}]
            response = await client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=chat_messages,
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
            
            # Gemini supports chat history as a list of messages
            if messages:
                response = model.generate_content(messages)
            else:
                response = model.generate_content(prompt)
            return response.text
            
        elif provider == "ollama":
            import aiohttp
            
            # Ollama does not support structured chat, so prepend chat context to prompt
            chat_prompt = prompt
            if messages:
                chat_context = ""
                for msg in messages:
                    chat_context += f"{msg['role'].upper()}: {msg['content']}\n"
                chat_prompt = f"Previous conversation:\n{chat_context}\n\n{prompt}"
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{settings.OLLAMA_BASE_URL}/api/generate",
                    json={
                        "model": settings.OLLAMA_MODEL,
                        "prompt": chat_prompt,
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