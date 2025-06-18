def normalize_snippet_types(snippets):
    """Ensure all snippets are dicts and snippet_type is valid, else set to 'miscellaneous'."""
    from app.schemas.schemas import SnippetType
    allowed_types = {e.value for e in SnippetType}
    normalized = []
    for snippet in snippets:
        # Convert to dict if it's a Pydantic model
        if hasattr(snippet, 'model_dump'):
            snippet = snippet.model_dump(mode='python', by_alias=True)
        # Map invalid snippet_type to 'miscellaneous'
        if 'snippet_type' in snippet and snippet['snippet_type'] not in allowed_types:
            snippet['snippet_type'] = 'miscellaneous'
        normalized.append(snippet)
    return normalized 