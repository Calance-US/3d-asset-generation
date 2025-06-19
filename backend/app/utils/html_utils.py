import json
import logging

import aiohttp
import google.generativeai as genai
from bs4 import BeautifulSoup
from fastapi import HTTPException
from google.generativeai.types import HarmBlockThreshold, HarmCategory
from openai import AsyncOpenAI

from app.config.settings import settings
from app.schemas.schemas import EnhancedPromptResponse, HtmlAnalysisRequest
from app.utils.prompt_utils import build_gold_standard_prompt
from app.utils.snippet_utils import normalize_snippet_types

logger = logging.getLogger(__name__)


def parse_html_content(text: str) -> str:
    """
    Parse and extract HTML content from the generated text.

    Args:
        text: The generated text that may contain HTML

    Returns:
        str: The extracted HTML content or empty string if not found
    """
    try:
        # Remove any markdown code block markers
        text = text.replace("```html", "").replace("```", "")

        # Find the first <!DOCTYPE html> or <html> tag
        html_start = text.find("<!DOCTYPE html>")
        if html_start == -1:
            html_start = text.find("<html>")

        if html_start == -1:
            logger.error(
                "No HTML content found in the response",
                extra={"action": "validate_html", "response_length": len(text)},
            )
            return ""

        # Find the last </html> tag
        html_end = text.rfind("</html>")
        if html_end == -1:
            logger.error(
                "No closing HTML tag found in the response",
                extra={"action": "validate_html", "content_length": len(text)},
            )
            return ""

        # Extract the HTML content
        html_content = text[html_start : html_end + 7]  # +7 for </html>

        # Validate that it's proper HTML
        if not html_content.strip().startswith(("<!DOCTYPE html>", "<html")):
            logger.error(
                "Invalid HTML content in the response",
                extra={"action": "validate_html", "error": "No valid HTML tag found"},
            )
            return ""

        try:
            BeautifulSoup(html_content, "html.parser")
        except Exception as e:
            logger.error(
                "Invalid HTML content",
                extra={"action": "validate_html", "error": str(e)},
            )
            return ""

        return html_content

    except Exception as e:
        logger.error(f"Error parsing HTML content: {str(e)}")
        return ""


async def analyze_html(request: HtmlAnalysisRequest):
    """Analyze HTML content and extract configuration and topic."""
    try:
        # Create a prompt for the LLM to analyze the HTML
        analysis_prompt = build_gold_standard_prompt(request.html)

        # Initialize OpenAI client if API key is available
        if settings.OPENAI_API_KEY:
            client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        else:
            client = None
            logging.warning("OpenAI API key not found")

        # Initialize Google Gemini client if API key is available
        if settings.GOOGLE_API_KEY:
            genai.configure(api_key=settings.GOOGLE_API_KEY)
            gemini_model = genai.GenerativeModel(settings.GEMINI_MODEL)
        else:
            gemini_model = None
            logging.warning("Google API key not found")

        generated_text = None

        if request.provider == "openai":
            if not client:
                raise HTTPException(
                    status_code=400, detail="OpenAI API key not configured"
                )

            response = await client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[{"role": "user", "content": analysis_prompt}],
                temperature=0.7,
            )

            generated_text = response.choices[0].message.content

        elif request.provider == "ollama":
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{settings.OLLAMA_BASE_URL}/api/generate",
                    json={
                        "model": settings.OLLAMA_MODEL,
                        "prompt": analysis_prompt,
                        "stream": False,
                    },
                ) as response:
                    if response.status != 200:
                        raise HTTPException(
                            status_code=500, detail="Failed to generate with Ollama"
                        )

                    result = await response.json()
                    generated_text = result.get("response", "")

        elif request.provider == "gemini":
            if not gemini_model:
                raise HTTPException(
                    status_code=400, detail="Google API key not configured"
                )

            response = gemini_model.generate_content(
                analysis_prompt,
                safety_settings={
                    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
                },
            )

            generated_text = response.text

        else:
            raise HTTPException(status_code=400, detail="Invalid provider specified")

        if not generated_text:
            raise HTTPException(status_code=500, detail="No response from LLM")

        # Log the raw LLM response
        logging.info(
            "Raw LLM response:",
            extra={
                "action": "analyze_html",
                "provider": request.provider,
                "response": generated_text,
            },
        )

        # Clean the response to ensure it's valid JSON
        try:
            # Remove any markdown code block markers
            cleaned_text = (
                generated_text.replace("```json", "").replace("```", "").strip()
            )
            # Try to find the first { and last }
            start_idx = cleaned_text.find("{")
            end_idx = cleaned_text.rfind("}") + 1
            if start_idx >= 0 and end_idx > start_idx:
                cleaned_text = cleaned_text[start_idx:end_idx]

            # Log the cleaned response
            logging.info(
                "Cleaned LLM response:",
                extra={
                    "action": "analyze_html",
                    "provider": request.provider,
                    "response": cleaned_text,
                },
            )

            # Validate JSON structure
            enhanced_config = json.loads(cleaned_text)
            # Normalize snippet types before any validation
            if "snippets" in enhanced_config:
                enhanced_config["snippets"] = normalize_snippet_types(
                    enhanced_config["snippets"]
                )

            # Log the parsed configuration
            logging.info(
                "Parsed configuration:",
                extra={
                    "action": "analyze_html",
                    "provider": request.provider,
                    "config": json.dumps(enhanced_config, indent=2),
                },
            )

            # Validate required fields
            required_fields = [
                "topic_name",
                "key_concepts",
                "education_level",
                "learning_objectives",
                "interactive_features",
                "components",
                "materials",
                "lights",
                "interactive_description",
                "animated_elements",
                "intro_narration_texts",
                "supporting_narration_texts",
                "scene_description",
                "snippets",
            ]
            missing_fields = [
                field for field in required_fields if field not in enhanced_config
            ]
            if missing_fields:
                raise ValueError(
                    f"Missing required fields: {', '.join(missing_fields)}"
                )

            # Validate snippets structure
            if not enhanced_config.get("snippets"):
                raise ValueError("Response must include at least one snippet")

            for snippet in enhanced_config.get("snippets", []):
                snippet_fields = [
                    "snippet_type",
                    "summary",
                    "embedding_text",
                    "html_snippet",
                ]
                missing_snippet_fields = [
                    field for field in snippet_fields if field not in snippet
                ]
                if missing_snippet_fields:
                    raise ValueError(
                        f"Missing required snippet fields: {', '.join(missing_snippet_fields)}"
                    )

                # No need to raise error for invalid snippet_type, as normalization guarantees validity

            # Clamp light intensity values to 1.0 before schema validation
            if "lights" in enhanced_config:
                for light in enhanced_config["lights"]:
                    if "intensity" in light and isinstance(
                        light["intensity"], (int, float)
                    ):
                        if light["intensity"] > 1.0:
                            light["intensity"] = 1.0

            return EnhancedPromptResponse(**enhanced_config)

        except json.JSONDecodeError as e:
            logging.error(f"Failed to parse LLM response as JSON: {str(e)}")
            logging.error(f"Raw response: {generated_text}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to parse LLM response as JSON: {str(e)}",
            )

    except Exception as e:
        logging.error(
            "Error analyzing HTML",
            extra={
                "action": "analyze_html",
                "error": str(e),
                "error_type": type(e).__name__,
            },
        )
        raise HTTPException(status_code=500, detail=str(e))
