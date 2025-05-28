import os
import re
from typing import Literal

import openai
import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Initialize FastAPI app
app = FastAPI()

# Enable CORS for all origins (adjust for production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request schema
class PromptRequest(BaseModel):
    prompt: str
    model: Literal["openai", "anthropic", "ollama"]


# Load API keys from environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

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
* Include labels or visual cues (arrows, color changes, flows, toggles) that help explain what’s happening.
* Animate key behaviors (e.g., current flow, wave motion, collisions).
* Structure the layout for maximum visual clarity, avoiding clutter.
* The scene must be interactive and fully 3D (rotate, zoom, pan via OrbitControls).
* The output must be a single complete valid HTML file and fully runnable inside an <iframe> and nothing else. Do not include explanations, tags like <think>, or commentary — only the HTML.

Now, given the following user prompt, return only a complete embeddable HTML document that implements it:
"""


# Main endpoint
@app.post("/generate")
async def generate_scene(req: PromptRequest):
    try:
        if req.model == "openai":
            if not OPENAI_API_KEY:
                raise HTTPException(
                    status_code=500, detail="OpenAI API key not configured"
                )
            openai.api_key = OPENAI_API_KEY
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": req.prompt},
                ],
                temperature=0.3,
            )
            html = response["choices"][0]["message"]["content"]

        elif req.model == "anthropic":
            if not ANTHROPIC_API_KEY:
                raise HTTPException(
                    status_code=500, detail="Anthropic API key not configured"
                )
            response = requests.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": ANTHROPIC_API_KEY,
                    "anthropic-version": "2023-06-01",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "claude-3-sonnet-20240229",
                    "system": SYSTEM_PROMPT,
                    "messages": [{"role": "user", "content": req.prompt}],
                    "max_tokens": 4096,
                    "temperature": 0.3,
                },
            )
            data = response.json()
            html = data["content"][0]["text"]

        elif req.model == "ollama":
            response = requests.post(
                "http://localhost:11434/api/chat",
                json={
                    "model": "deepseek-r1:latest",
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": req.prompt},
                    ],
                    "stream": False,
                },
            )
            data = response.json()
            cleaned_html = data["message"]["content"].strip()

            # Extract only the content between <html>...</html> (non-greedy)
            match = re.search(
                r"<html.*?>.*?</html>", cleaned_html, re.DOTALL | re.IGNORECASE
            )
            if match:
                html = match.group(0).strip()
            else:
                return {"error": "No valid <html>...</html> block found in response."}

        else:
            raise HTTPException(status_code=400, detail="Unsupported model selected.")

        return {"html": html}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
