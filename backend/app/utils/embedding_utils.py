"""Utilities for creating and managing embeddings."""

def create_embedding_text(
    llm_embedding_text: str,
    snippet_type: str,
    topic: str = "",
    concepts: str = "",
    summary: str = ""
) -> str:
    """Create a rich context for embedding that combines LLM's semantic description with additional context.
    
    Args:
        llm_embedding_text: The LLM's semantic description of the snippet
        snippet_type: Type of the snippet (e.g., lighting, material)
        topic: Topic name from the config
        concepts: Key concepts from the config
        summary: Summary of the snippet
        
    Returns:
        A rich context string combining all the information
    """
    # Create a rich context that combines:
    # 1. The LLM's semantic description (primary)
    # 2. Additional context for better matching
    rich_context = f"""
    {llm_embedding_text}
    
    Additional Context:
    Type: {snippet_type}
    Topic: {topic}
    Concepts: {concepts}
    Summary: {summary}
    """
    return rich_context.strip()

COMMON_EMBEDDING_FIELDS = [
    "topic_name",
    "key_concepts",
    "education_level",
    "learning_objectives",
    "interactive_features",
    "scene_description",
    "components",
    "materials",
    "lights",
    "interactive_description",
    "animated_elements",
    "intro_narration_texts",
    "supporting_narration_texts"
]

def build_embedding_text_from_config(config: dict) -> str:
    """
    Build a deterministic embedding text from only the common fields between PromptConfig and EnhancedPromptResponse.
    Args:
        config: dict-like object (from PromptConfig or EnhancedPromptResponse)
    Returns:
        str: JSON string of only the common fields, sorted by key.
    """
    import json
    filtered = {k: config[k] for k in COMMON_EMBEDDING_FIELDS if k in config}
    return json.dumps(filtered, sort_keys=True, ensure_ascii=False) 