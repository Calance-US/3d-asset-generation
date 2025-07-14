# Show Retrieved Results Flow

This document describes the sequence of interactions when a user views retrieved similar visualizations in the 3D Educational Visualization Platform.

## Overview

The show retrieved results flow is a development/testing feature that allows users to see what similar visualizations the RAG system would retrieve for a given prompt, helping to understand and debug the retrieval-augmented generation process. The retrieval always uses the full config structure (components, materials, lights, renderer, etc) if available. Endpoint requires Keycloak JWT (unless in dev bypass mode).

## Sequence Diagram

```mermaid
sequenceDiagram
    participant U as User
    participant F as Frontend (Generator.jsx)
    participant B as Backend API
    participant VS as Vector Store (Qdrant)
    participant ES as Embedding Service
    participant DB as Database

    Note over U,DB: User initiates retrieval test (Development mode only)
    U->>F: Enter topic prompt
    U->>F: Click "Show Retrieval Results" button
    F->>F: Validate prompt is not empty
    F->>F: Set loading state to true
    F->>F: Set error state to null
    F->>F: Build request payload (full config)
    F->>B: POST /rag/retrieve-similar (with JWT)
    B->>ES: Generate embedding from input
    ES->>B: Return embedding
    B->>VS: Query similar visualizations
    VS->>VS: Search Qdrant vector store
    VS->>DB: Fetch metadata for retrieved IDs
    DB->>VS: Return snippet metadata
    VS->>B: Return similar visualizations with scores
    B->>F: Return RetrieveSimilarResponse
    F->>F: Log results to console, show alert
    F->>U: Display alert: "Check the console for retrieved results"
```

## Key Components

### Frontend (Generator.jsx)
- **handleRetrieveSimilar()**: Main retrieval function
- **Development Mode Check**: Only shows button in development environment
- **Console Logging**: Logs detailed results to browser console
- **User Feedback**: Shows alert to direct user to console
- **Config Structure**: Always sends full config (components, materials, lights, renderer, etc) if available

### Backend API (/rag/retrieve-similar)
- **Embedding Generation**: Creates vector from user input (topic/config)
- **Vector Search**: Queries Qdrant for similar items
- **Metadata Retrieval**: Fetches complete metadata from database
- **Score Mapping**: Combines similarity scores with metadata
- **Response Formatting**: Returns structured response with scores
- **Authentication**: Requires Keycloak JWT (unless in dev bypass mode)

### Vector Store (Qdrant)
- **Similarity Search**: Performs vector similarity search
- **Score Calculation**: Provides cosine similarity scores
- **ID Mapping**: Maps vector IDs to database records

### Database (SnippetMetadata)
- **Metadata Storage**: Stores educational content and snippets
- **ID Linking**: Links Qdrant IDs to metadata records
- **Content Retrieval**: Provides complete snippet information

## Request/Response Format

### Request
```json
{
  "topic": "Ohm's Law electric circuit",
  "provider": "openai",
  "subject": "physics",
  "config": {
    "components": [...],
    "materials": [...],
    "lights": [...],
    "renderer": {...}
  }
}
```

### Response
```json
{
  "results": [
    {
      "metadata": {
        "id": "b6a2beff-ff1a-4278-bb59-400564e6a04a",
        "summary": "Mouse drag controls for moving positive and negative charge spheres",
        "snippet_type": "ui_controls",
        "key_concepts": "Electric charge, Coulomb's law, Electric field",
        "education_level": "High School",
        "html_snippet": "function onMouseDown(event) {...}",
        "created_at": "2025-06-18T10:08:14.809083Z",
        "faiss_id": 18
      },
      "score": 0.85
    }
  ]
}
```

## Development Features

- **Console Output**: Logs detailed information to the browser console
- **Development-Only Access**: Only available in development mode
- **Config Structure**: Always uses full config if available

## Error Handling
- **Empty Prompt**: Frontend prevents retrieval of empty prompts
- **Vector Store Errors**: Backend handles Qdrant connection issues
- **Database Errors**: Graceful handling of metadata retrieval failures
- **Network Issues**: Frontend shows user-friendly error messages
- **Invalid Responses**: Validation of response structure

## Benefits
1. **Development Transparency**: See exactly what RAG retrieves
2. **Quality Assurance**: Verify retrieval relevance and quality
3. **System Understanding**: Understand how embeddings work
4. **Debugging Support**: Identify issues in retrieval process
5. **Performance Monitoring**: Track similarity search effectiveness
6. **Content Validation**: Ensure educational content quality 