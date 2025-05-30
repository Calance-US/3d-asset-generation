import os
import re
import logging
from typing import Literal, Optional, Dict, Any, List
import aiohttp
from openai import AsyncOpenAI
import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
from pathlib import Path
from dotenv import load_dotenv
import openai
import json
from datetime import datetime
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

from app.services.prompt_selector import PromptSelector
from app.services.model_repository import ModelRepository
from app.services.scene_generator import SceneGenerator
from app.config.settings import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI()

# Enable CORS for all origins (adjust for production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
prompt_selector = PromptSelector()
model_repository = ModelRepository()
scene_generator = SceneGenerator()

# Initialize OpenAI client if API key is available
if settings.OPENAI_API_KEY:
    client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
else:
    client = None
    logger.warning("OpenAI API key not found. OpenAI provider will not be available.")

# Initialize Google Gemini client if API key is available
if settings.GOOGLE_API_KEY:
    genai.configure(api_key=settings.GOOGLE_API_KEY)
    gemini_model = genai.GenerativeModel(settings.GEMINI_MODEL)
else:
    gemini_model = None
    logger.warning("Google API key not found. Gemini provider will not be available.")

# Request schema
class GenerateRequest(BaseModel):
    topic: str
    subject: str = "physics"  # Default to physics
    provider: str = "ollama"  # Default to Ollama
    modelType: Optional[str] = "generated"
    selectedModel: Optional[str] = None

# Shared system prompt for all providers
SYSTEM_PROMPT = """You are a code generation assistant that converts natural language descriptions of educational interactive 3D scenes into standalone embeddable HTML files.

Your goal is to create 3D visualizations that help students quickly and intuitively understand core scientific or engineering concepts.

You must:

* Use only HTML, CSS, and JavaScript (ES6).
* Use browser-compatible Three.js modules via CDN imports using full URLs from [esm.sh](https://esm.sh), which rewrites internal imports for browser compatibility.
* Always import Three.js and its extensions (like OrbitControls) using esm.sh with versioned paths, for example:
  * import * as THREE from 'https://esm.sh/three@0.155.0';
  * import { OrbitControls } from 'https://esm.sh/three@0.155.0/examples/jsm/controls/OrbitControls';

You must ensure that:
* The scene is educational, scientifically accurate, and clearly demonstrates the user-provided concept.
* Each component must be clearly identifiable and photorealistic.
* Include labels or visual cues (arrows, color changes, flows, toggles) that help explain what's happening.
* Animate key behaviors (e.g., current flow, wave motion, collisions).
* Structure the layout for maximum visual clarity, avoiding clutter.
* The scene must be interactive and fully 3D (rotate, zoom, pan via OrbitControls).
* The output must be a single complete valid HTML file and fully runnable inside an <iframe> and nothing else. Do not include explanations, tags like <think>, or commentary — only the HTML.

Now, given the following user prompt, return only a complete embeddable HTML document that implements it:
"""

# History models
class HistoryEntry(BaseModel):
    id: str
    prompt: str
    provider: str
    html: str
    timestamp: str

class HistoryResponse(BaseModel):
    entries: List[HistoryEntry]

# Initialize history storage
HISTORY_FILE = Path(__file__).parent / "app" / "data" / "history.json"
HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)

def load_history() -> List[Dict]:
    if HISTORY_FILE.exists():
        with open(HISTORY_FILE, 'r') as f:
            return json.load(f)
    return []

def save_history(entry: Dict):
    history = load_history()
    # Add new entry
    history.append(entry)
    # Keep only the 10 most recent entries
    history = history[-10:]
    with open(HISTORY_FILE, 'w') as f:
        json.dump(history, f, indent=2)

async def generate_with_ollama(topic: str, subject: str) -> str:
    """Generate visualization using Ollama."""
    try:
        # Get the appropriate prompt using select_prompt and get_prompt_content
        selected_subject, filename = prompt_selector.select_prompt(topic, subject)
        prompt_content = prompt_selector.get_prompt_content(selected_subject, filename, topic)
        logger.info(f"Using prompt for topic: {topic}, subject: {subject}, file: {filename}")
        
        async with aiohttp.ClientSession() as session:
            logger.info(f"Generating with Ollama model: {settings.OLLAMA_MODEL}")
            async with session.post(
                f"{settings.OLLAMA_BASE_URL}/api/generate",
                json={
                    "model": settings.OLLAMA_MODEL,
                    "prompt": f"{SYSTEM_PROMPT}\n\n{prompt_content}",
                    "stream": settings.STREAM
                }
            ) as response:
                if response.status != 200:
                    raise HTTPException(status_code=500, detail="Failed to generate with Ollama")
                
                result = await response.json()
                generated_text = result.get("response", "")
                
                # Parse the HTML content from the response
                html_content = parse_html_content(generated_text)
                if not html_content:
                    raise HTTPException(status_code=500, detail="Failed to generate valid HTML content")
                
                return html_content
    except Exception as e:
        logger.error(f"Error generating with Ollama: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

async def generate_with_gemini(topic: str, subject: str) -> str:
    """Generate visualization using Google Gemini."""
    try:
        if not gemini_model:
            raise HTTPException(status_code=400, detail="Google API key not configured")
        
        # Get the appropriate prompt using select_prompt and get_prompt_content
        selected_subject, filename = prompt_selector.select_prompt(topic, subject)
        prompt_content = prompt_selector.get_prompt_content(selected_subject, filename, topic)
        logger.info(f"Using prompt for topic: {topic}, subject: {subject}, file: {filename}")
        
        # Generate using Gemini
        logger.info(f"Generating with Gemini model: {settings.GEMINI_MODEL}")
        try:
            response = gemini_model.generate_content(
                f"{SYSTEM_PROMPT}\n\n{prompt_content}",
                safety_settings={
                    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
                }
            )
            
            if not response or not response.text:
                raise HTTPException(status_code=500, detail="Empty response from Gemini API")
            
            generated_text = response.text
            logger.info("Received response from Gemini")
            
        except Exception as api_error:
            logger.error(f"Gemini API error: {str(api_error)}")
            raise HTTPException(
                status_code=500,
                detail=f"Error from Gemini API: {str(api_error)}. Please check if the model name '{settings.GEMINI_MODEL}' is correct and available."
            )
        
        # Parse the HTML content
        html_content = parse_html_content(generated_text)
        if not html_content:
            logger.error("Failed to parse HTML content from Gemini response")
            raise HTTPException(status_code=500, detail="Failed to generate valid HTML content")
        
        return html_content
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating with Gemini: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

def parse_html_content(text: str) -> Optional[str]:
    """Parse HTML content from the generated text."""
    try:
        logger.info("Starting HTML content parsing")
        
        # Remove markdown code block syntax if present
        if text.startswith('```html'):
            logger.info("Found markdown code block, removing syntax")
            text = text.replace('```html\n', '').replace('\n```', '')
        elif text.startswith('```'):
            logger.info("Found generic markdown code block, removing syntax")
            text = text.replace('```\n', '').replace('\n```', '')
        
        # Clean up any leading/trailing whitespace
        text = text.strip()
        
        # Try to find HTML content with more flexible patterns
        html_patterns = [
            r'<html[^>]*>[\s\S]*?<\/html>',  # Standard HTML tags
            r'<!DOCTYPE\s+html[^>]*>[\s\S]*?<\/html>',  # With DOCTYPE
            r'<html[^>]*>[\s\S]*?<\/html>',  # Case insensitive
        ]
        
        for pattern in html_patterns:
            html_match = re.search(pattern, text, re.IGNORECASE)
            if html_match:
                logger.info(f"Found HTML content using pattern: {pattern}")
                return html_match.group(0)
        
        # If no HTML found, try to wrap the content in HTML tags
        if '<!DOCTYPE' not in text and '<html' not in text:
            logger.info("No HTML tags found, attempting to wrap content")
            # Check if the content contains any HTML-like content
            if '<' in text and '>' in text:
                logger.info("Content contains HTML-like tags, wrapping in full HTML structure")
                wrapped_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>3D Visualization</title>
</head>
<body>
{text}
</body>
</html>"""
                logger.info("Content wrapped in HTML tags")
                return wrapped_html
            else:
                logger.error("Content does not contain any HTML-like tags")
                return None
        
        logger.error("No valid HTML content found in the response")
        return None
    except Exception as e:
        logger.error(f"Error parsing HTML content: {str(e)}")
        return None

# Main endpoint
@app.post("/generate")
async def generate_visualization(request: GenerateRequest):
    """Generate a 3D visualization based on the topic."""
    try:
        if request.provider == "openai":
            if not client:
                raise HTTPException(status_code=400, detail="OpenAI API key not configured")
            
            # Get the appropriate prompt using select_prompt and get_prompt_content
            selected_subject, filename = prompt_selector.select_prompt(request.topic, request.subject)
            prompt_content = prompt_selector.get_prompt_content(selected_subject, filename, request.topic)
            logger.info(f"Using prompt for topic: {request.topic}, subject: {request.subject}, file: {filename}")
            
            # Generate using OpenAI
            logger.info(f"Generating with OpenAI model: {settings.OPENAI_MODEL}")
            response = client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt_content}
                ],
                temperature=settings.TEMPERATURE,
                max_tokens=settings.MAX_TOKENS
            )
            
            generated_text = response.choices[0].message.content
            logger.info("Received response from OpenAI")
            
            # Parse the HTML content
            html_content = parse_html_content(generated_text)
            if not html_content:
                logger.error("Failed to parse HTML content from OpenAI response")
                raise HTTPException(status_code=500, detail="Failed to generate valid HTML content")
            
            # Save to history
            history_entry = {
                "id": str(datetime.now().timestamp()),
                "prompt": request.topic,  # Save just the user's prompt
                "provider": request.provider,
                "html": html_content,
                "timestamp": datetime.now().isoformat()
            }
            save_history(history_entry)
            
            return {"html": html_content}
            
        elif request.provider == "ollama":
            html_content = await generate_with_ollama(request.topic, request.subject)
            
            # Save to history
            history_entry = {
                "id": str(datetime.now().timestamp()),
                "prompt": request.topic,  # Save just the user's prompt
                "provider": request.provider,
                "html": html_content,
                "timestamp": datetime.now().isoformat()
            }
            save_history(history_entry)
            
            return {"html": html_content}
            
        elif request.provider == "gemini":
            html_content = await generate_with_gemini(request.topic, request.subject)
            
            # Save to history
            history_entry = {
                "id": str(datetime.now().timestamp()),
                "prompt": request.topic,  # Save just the user's prompt
                "provider": request.provider,
                "html": html_content,
                "timestamp": datetime.now().isoformat()
            }
            save_history(history_entry)
            
            return {"html": html_content}
            
        else:
            raise HTTPException(status_code=400, detail="Invalid provider specified")
            
    except Exception as e:
        logger.error(f"Error generating visualization: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/models/{subject}")
async def get_available_models(subject: str):
    try:
        models = await model_repository.get_available_models(subject)
        return {"models": models}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/history", response_model=HistoryResponse)
async def get_history():
    """Get the history of generated visualizations."""
    try:
        history = load_history()
        # Sort history by timestamp in descending order (latest first)
        history.sort(key=lambda x: x["timestamp"], reverse=True)
        return {"entries": history}
    except Exception as e:
        logger.error(f"Error getting history: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/history/{entry_id}")
async def get_history_entry(entry_id: str):
    """Get a specific history entry by ID."""
    try:
        history = load_history()
        entry = next((e for e in history if e["id"] == entry_id), None)
        if not entry:
            raise HTTPException(status_code=404, detail="History entry not found")
        return entry
    except Exception as e:
        logger.error(f"Error getting history entry: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

def delete_history_entry(entry_id: str):
    """Delete a specific history entry by ID."""
    history = load_history()
    # Filter out the entry with the matching ID
    history = [entry for entry in history if entry["id"] != entry_id]
    with open(HISTORY_FILE, 'w') as f:
        json.dump(history, f, indent=2)

@app.delete("/history/{entry_id}")
async def delete_history_entry_endpoint(entry_id: str):
    """Delete a specific history entry by ID."""
    try:
        delete_history_entry(entry_id)
        return {"message": "History entry deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting history entry: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.on_event("shutdown")
async def shutdown_event():
    await model_repository.close()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
