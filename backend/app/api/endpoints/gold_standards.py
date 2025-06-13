from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any
from pydantic import BaseModel
from app.rag.rag_service import get_rag_service
from app.rag.vector_store import get_vector_store
from app.config.settings import settings
from app.schemas.schemas import EnhancedPromptResponse
from openai import AsyncOpenAI
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
import aiohttp
import json
import logging

router = APIRouter()

class GoldStandardCreate(BaseModel):
    html: str
    config: Dict[str, Any]
    metadata: Dict[str, Any] = None

class GoldStandardResponse(BaseModel):
    id: int
    metadata: Dict[str, Any]
    distance: float = None
    html: str = None

class HtmlAnalysisRequest(BaseModel):
    html: str
    provider: str = "openai"  # Default to OpenAI

@router.post("/", response_model=GoldStandardResponse)
async def create_gold_standard(
    gold_standard: GoldStandardCreate,
    rag_service = Depends(get_rag_service)
):
    """Add a new gold standard visualization to the vector store."""
    try:
        logging.info("Creating new gold standard", extra={
            "action": "create_gold_standard",
            "has_config": bool(gold_standard.config),
            "has_metadata": bool(gold_standard.metadata)
        })

        # Add to vector store
        rag_service.add_gold_standard(
            html=gold_standard.html,
            config=gold_standard.config,
            metadata=gold_standard.metadata or {}
        )

        # Get the index of the newly added entry
        vector_store = get_vector_store()
        new_index = len(vector_store.metadata) - 1

        logging.info("Successfully added gold standard to vector store", extra={
            "action": "create_gold_standard",
            "index": new_index
        })

        return GoldStandardResponse(
            id=new_index,
            metadata=gold_standard.metadata or {}
        )

    except Exception as e:
        logging.error("Error creating gold standard", extra={
            "action": "create_gold_standard",
            "error": str(e),
            "error_type": type(e).__name__
        })
        raise HTTPException(
            status_code=500,
            detail=f"Error creating gold standard: {str(e)}"
        )

@router.post("/analyze", response_model=EnhancedPromptResponse)
async def analyze_html(request: HtmlAnalysisRequest):
    """Analyze HTML content and extract configuration and topic."""
    try:
        # Create a prompt for the LLM to analyze the HTML
        analysis_prompt = f"""Given the following HTML visualization, analyze it and generate a detailed configuration. Return the response as a JSON object with the following structure.
        IMPORTANT: Keep all text fields concise (max 200 characters) to avoid truncation.
        {{
            "topic_name": "A short, concise name for the topic (max 20 chars)",
            "key_concepts": "Comma separated main concepts to be visualized (max 200 chars)",
            "education_level": "choose between Elementary, Middle School, High School or College",
            "learning_objectives": "What students will learn (max 200 chars)",
            "interactive_features": "What users can interact with in the scene (max 200 chars)",
            "scene_description": "A detailed description of the 3D scene with realistic details(max 1000 chars)",
            "components": [
                {{
                    "component_name": "Name of a 3D component required in the 3D scene (max 50 chars)",
                    "component_description": "Description of what this component represents in the 3D scene (max 100 chars)"
                }}
            ],
            "materials": [
                {{
                    "material_name": "Name of the material (based on the components)",
                    "material_type": "Type of material (choose between MeshStandardMaterial, MeshPhysicalMaterial, MeshPhongMaterial)",
                    "color": "#RRGGBB",
                    "metalness": 0.5,
                    "roughness": 0.5,
                    "emissive": "#RRGGBB",
                    "emissiveIntensity": 0.5
                }}
            ],
            "lights": [
                {{
                    "light_type": "Type of light (max 50 chars)",
                    "light_class": "THREE.LightClass [choose between DirectionalLight, AmbientLight, HemisphereLight]",
                    "light_color": "#RRGGBB",
                    "intensity": 0.5
                }}
            ],
            "interactive_description": "How users can interact with the visualization (max 200 chars)",
            "animated_elements": "What components should be animated and how (max 200 chars)",
            "intro_narration_texts": [
                "Concise introductory narration texts about the topic to be played at the start (each max 500 chars)"
            ],
            "supporting_narration_texts": [
                "Short texts to be played during user interactions explaining controls or feedback (each max 100 chars)"
            ]
        }}

        HTML Content:
        {request.html}

        IMPORTANT:
        1. Return ONLY the JSON object, no other text or explanation.
        2. Keep all text fields concise to avoid truncation.
        3. Ensure all JSON fields are properly closed.
        4. Do not include any markdown formatting.
        5. Analyze the HTML to identify the 3D components, materials, and lighting setup.
        6. Extract the educational content and learning objectives from the visualization.
        """

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
                raise HTTPException(status_code=400, detail="OpenAI API key not configured")

            response = await client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "user", "content": analysis_prompt}
                ],
                temperature=0.7
            )

            generated_text = response.choices[0].message.content

        elif request.provider == "ollama":
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{settings.OLLAMA_BASE_URL}/api/generate",
                    json={
                        "model": settings.OLLAMA_MODEL,
                        "prompt": analysis_prompt,
                        "stream": False
                    }
                ) as response:
                    if response.status != 200:
                        raise HTTPException(status_code=500, detail="Failed to generate with Ollama")

                    result = await response.json()
                    generated_text = result.get("response", "")

        elif request.provider == "gemini":
            if not gemini_model:
                raise HTTPException(status_code=400, detail="Google API key not configured")

            response = gemini_model.generate_content(
                analysis_prompt,
                safety_settings={
                    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
                }
            )

            generated_text = response.text

        else:
            raise HTTPException(status_code=400, detail="Invalid provider specified")

        if not generated_text:
            raise HTTPException(status_code=500, detail="No response from LLM")

        # Clean the response to ensure it's valid JSON
        try:
            # Remove any markdown code block markers
            cleaned_text = generated_text.replace("```json", "").replace("```", "").strip()
            # Try to find the first { and last }
            start_idx = cleaned_text.find("{")
            end_idx = cleaned_text.rfind("}") + 1
            if start_idx >= 0 and end_idx > start_idx:
                cleaned_text = cleaned_text[start_idx:end_idx]

            # Validate JSON structure
            enhanced_config = json.loads(cleaned_text)
            
            # Validate required fields
            required_fields = [
                "topic_name", "key_concepts", "education_level", "learning_objectives",
                "interactive_features", "components", "materials", "lights",
                "interactive_description", "animated_elements", "intro_narration_texts", 
                "supporting_narration_texts", "scene_description"
            ]
            missing_fields = [field for field in required_fields if field not in enhanced_config]
            if missing_fields:
                raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")

            return EnhancedPromptResponse(**enhanced_config)

        except json.JSONDecodeError as e:
            logging.error(f"Failed to parse LLM response as JSON: {str(e)}")
            logging.error(f"Raw response: {generated_text}")
            raise HTTPException(status_code=500, detail=f"Failed to parse LLM response as JSON: {str(e)}")

    except Exception as e:
        logging.error("Error analyzing HTML", extra={
            "action": "analyze_html",
            "error": str(e),
            "error_type": type(e).__name__
        })
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/search", response_model=List[GoldStandardResponse])
async def search_gold_standards(
    query: str,
    top_k: int = 2,
    rag_service = Depends(get_rag_service)
):
    """Search for similar gold standard visualizations."""
    try:
        results = rag_service.get_similar_visualizations(query, top_k=top_k)
        return [
            GoldStandardResponse(
                id=i,
                metadata=result['metadata'],
                distance=result['distance']
            )
            for i, result in enumerate(results)
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/", response_model=List[GoldStandardResponse])
async def list_gold_standards(
    rag_service = Depends(get_rag_service)
):
    """List all gold standard visualizations."""
    try:
        vector_store = get_vector_store()
        return [
            GoldStandardResponse(
                id=i,
                metadata=metadata,
                html=metadata.get('html', '')
            )
            for i, metadata in enumerate(vector_store.metadata)
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{index}")
async def delete_gold_standard(
    index: int,
    rag_service = Depends(get_rag_service)
):
    """Delete a gold standard visualization from the vector store."""
    try:
        vector_store = get_vector_store()
        success = vector_store.delete_visualization(index)
        
        if success:
            # Save the updated vector store
            vector_store.save(settings.VECTOR_STORE_PATH)
            
            logging.info("Successfully deleted gold standard", extra={
                "action": "delete_gold_standard",
                "index": index
            })
            
            return {"message": f"Successfully deleted gold standard at index {index}"}
        else:
            raise HTTPException(
                status_code=404,
                detail=f"Gold standard at index {index} not found"
            )
            
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        logging.error("Error deleting gold standard", extra={
            "action": "delete_gold_standard",
            "error": str(e),
            "error_type": type(e).__name__,
            "index": index
        })
        raise HTTPException(
            status_code=500,
            detail=f"Error deleting gold standard: {str(e)}"
        ) 