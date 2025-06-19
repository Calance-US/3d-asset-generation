# Show Retrieved Results Flow

This document describes the sequence of interactions when a user views retrieved similar visualizations in the 3D Educational Visualization Platform.

## Overview

The show retrieved results flow is a development/testing feature that allows users to see what similar visualizations the RAG system would retrieve for a given prompt, helping to understand and debug the retrieval-augmented generation process.

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
    Note right of F: Button only visible in NODE_ENV === 'development'
    
    Note over F: Frontend validation
    F->>F: Validate prompt is not empty
    F->>F: Set loading state to true
    F->>F: Set error state to null
    
    Note over F: Prepare retrieval request
    F->>F: Build request payload
    Note right of F: Payload includes:<br/>- topic, provider, subject<br/>- config (if available)<br/>- renderer settings<br/>- Three.js configuration
    
    Note over F,B: Send retrieval request
    F->>B: POST /rag/retrieve-similar
    Note right of F: Request: {<br/>  topic, provider, subject,<br/>  config: {components, materials,<br/>  lights, renderer, ...}<br/>}
    
    Note over B: Backend processing
    B->>B: Extract embedding input
    Note right of B: Uses config if available,<br/>otherwise uses topic
    
    B->>ES: Generate embedding from input
    ES->>ES: Create embedding vector
    ES->>B: Return embedding
    
    B->>VS: Query similar visualizations
    VS->>VS: Search Qdrant vector store
    Note right of VS: Search parameters:<br/>- query_vector: embedding<br/>- limit: top_k (default 5)<br/>- collection: VECTOR_STORE_COLLECTION
    
    VS->>VS: Get search results with scores
    VS->>VS: Extract Qdrant IDs and scores
    
    VS->>DB: Fetch metadata for retrieved IDs
    DB->>DB: Query SnippetMetadata table
    Note right of DB: Filter by faiss_id IN (retrieved_ids)
    
    DB->>VS: Return snippet metadata
    VS->>VS: Map faiss_id to metadata
    VS->>VS: Combine metadata with similarity scores
    
    VS->>B: Return similar visualizations
    Note right of VS: Response format:<br/>[{<br/>  metadata: {...},<br/>  similarity: 0.85<br/>}, ...]
    
    Note over B: Process and format results
    B->>B: Extract metadata and scores
    B->>B: Format for response
    Note right of B: Each result includes:<br/>- metadata: snippet details<br/>- score: similarity score
    
    B->>F: Return RetrieveSimilarResponse
    Note right of B: Response: {<br/>  results: [<br/>    {metadata: {...}, score: 0.85},<br/>    {metadata: {...}, score: 0.72},<br/>    ...<br/>  ]<br/>}
    
    Note over F: Process response
    F->>F: Check if results exist
    F->>F: Log results to console
    F->>F: Show alert to user
    F->>F: Set loading state to false
    
    Note over U: User sees results
    F->>U: Display alert: "Check the console for retrieved results"
    Note right of F: Results logged to browser console:<br/>- Retrieved Results: [...]<br/>- Each result shows:<br/>  * metadata (id, summary, snippet_type, etc.)<br/>  * similarity score<br/>  * educational content
    
    Note over U: User can inspect results
    U->>F: Open browser console
    U->>F: View detailed retrieval results
    Note right of U: Can see:<br/>- Similarity scores<br/>- Snippet types<br/>- Educational content<br/>- Code snippets<br/>- Metadata details
```

## Key Components

### Frontend (Generator.jsx)
- **handleRetrieveSimilar()**: Main retrieval function
- **Development Mode Check**: Only shows button in development environment
- **Console Logging**: Logs detailed results to browser console
- **User Feedback**: Shows alert to direct user to console

### Backend API (/rag/retrieve-similar)
- **Embedding Generation**: Creates vector from user input
- **Vector Search**: Queries Qdrant for similar items
- **Metadata Retrieval**: Fetches complete metadata from database
- **Score Mapping**: Combines similarity scores with metadata
- **Response Formatting**: Returns structured response with scores

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
    },
    {
      "metadata": {
        "id": "17897bf9-9830-4cda-927c-04389aebbf61",
        "summary": "HUD panel toggle button to show or hide controls panel",
        "snippet_type": "ui_controls",
        "key_concepts": "Electric charge, Coulomb's law, Electric field",
        "education_level": "High School",
        "html_snippet": "const hudToggleButton = ...",
        "created_at": "2025-06-18T10:08:14.874884Z",
        "faiss_id": 27
      },
      "score": 0.72
    }
  ]
}
```

## Development Features

### Console Output
The function logs detailed information to the browser console:

```javascript
console.log("Retrieved Results:", data.results);
```

Each result shows:
- **Metadata**: Complete snippet information
- **Score**: Similarity score (0.0 to 1.0)
- **Snippet Type**: Category of the snippet
- **Educational Content**: Key concepts and learning objectives
- **Code Snippets**: HTML/JavaScript code (truncated)

### Development-Only Access
- **Environment Check**: `process.env.NODE_ENV === 'development'`
- **Button Visibility**: Only shows in development mode
- **Debug Information**: Provides detailed debugging data

## Use Cases

1. **RAG Debugging**: Understand what examples the system retrieves
2. **Quality Assessment**: Evaluate similarity search performance
3. **Content Analysis**: Review educational content in vector store
4. **System Tuning**: Optimize embedding and retrieval parameters
5. **Development Testing**: Verify RAG functionality during development

## Error Handling

- **Empty Prompt**: Frontend prevents retrieval of empty prompts
- **Vector Store Errors**: Backend handles Qdrant connection issues
- **Database Errors**: Graceful handling of metadata retrieval failures
- **Network Issues**: Frontend shows user-friendly error messages
- **Invalid Responses**: Validation of response structure

## Performance Considerations

- **Search Limits**: Configurable `top_k` parameter (default: 5)
- **Vector Search**: Fast similarity search in Qdrant
- **Metadata Caching**: Efficient database queries
- **Response Size**: Limited to prevent large payloads
- **Async Processing**: Non-blocking retrieval operations

## Benefits

1. **Development Transparency**: See exactly what RAG retrieves
2. **Quality Assurance**: Verify retrieval relevance and quality
3. **System Understanding**: Understand how embeddings work
4. **Debugging Support**: Identify issues in retrieval process
5. **Performance Monitoring**: Track similarity search effectiveness
6. **Content Validation**: Ensure educational content quality 