from app.config.settings import settings
import json
from app.schemas.schemas import EnhancedConfigSchema

def build_gold_standard_prompt(html_content: str) -> str:
    """Builds a prompt for gold standard analysis using the provided HTML content."""
    schema_json = json.dumps(EnhancedConfigSchema.model_json_schema(), indent=2)
    prompt = settings.GOLD_STANDARD_ANALYSIS_PROMPT.format(
        json_schema=schema_json,
        html_content=html_content
    )
    return prompt 