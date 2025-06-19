# Generate Visualization Flow

This document describes the sequence of interactions when a user generates a 3D visualization in the 3D Educational Visualization Platform.

## Overview

The generate visualization flow is the core functionality that takes a user's prompt (enhanced or basic) and creates an interactive 3D educational visualization using AI-powered generation and retrieval-augmented generation (RAG).

## Sequence Diagram

```mermaid
sequenceDiagram
    participant U as User
    participant F as Frontend (Generator.jsx)
    participant B as Backend API
    participant VS as Vector Store (Qdrant)
    participant ES as Embedding Service
    participant PG as Prompt Generator
    participant LLM as AI Provider (OpenAI/Gemini/Ollama)
    participant DB as Database
    participant H as History Service

    Note over U,H: User initiates visualization generation
    U->>F: Click "Generate Scene" button
    
    Note over F: Frontend validation and preparation
    F->>F: Validate prompt is not empty
    F->>F: Set loading state to true
    F->>F: Prepare request payload
    Note right of F: Payload includes:<br/>- topic, provider, subject<br/>- config (if enhanced)<br/>- renderer settings<br/>- Three.js URLs
    
    Note over F,B: Send generation request
    F->>B: POST /visualizations/generate
    Note right of F: Request: {<br/>  topic, provider, subject,<br/>  config: {components, materials,<br/>  lights, renderer, ...}<br/>}
    
    Note over B: Backend processing starts
    B->>B: Start timing generation
    B->>B: Log generation start
    
    Note over B: RAG - Retrieve similar visualizations
    B->>ES: Generate embedding from config/topic
    ES->>ES: Create embedding vector
    ES->>VS: Query similar visualizations
    VS->>VS: Search Qdrant vector store
    VS->>DB: Fetch metadata for similar items
    DB->>VS: Return snippet metadata
    VS->>B: Return similar visualizations with scores
    
    Note over B: Filter and build context
    B->>B: Filter to 1 example per snippet_type
    B->>B: Build context blocks from similar examples
    Note right of B: Context includes:<br/>- Summary of each example<br/>- Code snippets (truncated)<br/>- Educational content
    
    Note over B: Generate prompt with context
    B->>PG: Generate prompt with RAG context
    PG->>PG: Combine context + user config
    Note right of PG: Final prompt includes:<br/>- Gold standard examples<br/>- User's specific requirements<br/>- Educational objectives
    
    Note over B,LLM: AI generation
    B->>LLM: Send enhanced prompt
    Note right of B: Provider-specific requests:<br/>- OpenAI: Chat completion<br/>- Gemini: Generate content<br/>- Ollama: Generate API
    
    LLM->>B: Return generated HTML content
    Note right of LLM: Response includes:<br/>- Complete Three.js scene<br/>- Interactive elements<br/>- Educational content<br/>- Styling and animations
    
    Note over B: Validate and parse response
    B->>B: Parse HTML content
    B->>B: Validate HTML structure
    B->>B: Check for closing tags
    B->>B: Validate with BeautifulSoup
    
    Note over B: Save to database
    B->>DB: Create prompt entry
    Note right of B: Prompt includes:<br/>- topic, subject, content<br/>- key_concepts, education_level<br/>- learning_objectives
    
    B->>DB: Create history entry
    Note right of B: History includes:<br/>- prompt_id, user_query<br/>- response (HTML), provider<br/>- components, materials, lights<br/>- generation_time
    
    Note over B: Calculate timing
    B->>B: Calculate generation_time
    B->>B: Log completion
    
    Note over B,F: Return response
    B->>F: Return HTMLResponse
    Note right of B: Response: {html: "complete HTML content"}
    
    Note over F: Update frontend
    F->>F: Set HTML content
    F->>F: Set loading state to false
    F->>F: Display visualization in iframe
    
    Note over U: User sees generated visualization
    F->>U: Show 3D visualization
    Note right of F: Features:<br/>- Interactive 3D scene<br/>- Educational content<br/>- Controls and animations<br/>- Responsive design
    
    Note over U: User can interact with visualization
    U->>F: Interact with 3D scene
    U->>F: View educational content
    U->>F: Use interactive features
```

## Key Components

### Frontend (Generator.jsx)
- **handleGenerate()**: Main generation function
- **State Management**: Manages `loading`, `html`, and `error` states
- **Request Preparation**: Builds complete request payload with all settings
- **Response Handling**: Displays generated HTML in iframe

### Backend API (/visualizations/generate)
- **RAG Integration**: Retrieves similar visualizations for context
- **Prompt Generation**: Creates comprehensive prompts with examples
- **AI Provider Management**: Handles different AI providers (OpenAI, Gemini, Ollama)
- **Response Validation**: Ensures generated HTML is valid and complete
- **Database Persistence**: Saves prompts and history entries

### Vector Store (Qdrant)
- **Similarity Search**: Finds relevant visualizations based on embedding
- **Metadata Retrieval**: Fetches educational content and code snippets
- **Score Calculation**: Provides similarity scores for ranking

### AI Provider Integration
- **OpenAI**: Uses GPT-4 with chat completion API
- **Gemini**: Uses Google's Gemini with content generation
- **Ollama**: Uses local Ollama with generate API

## RAG (Retrieval-Augmented Generation) Process

1. **Embedding Generation**: Convert user request to vector
2. **Similarity Search**: Find relevant examples in vector store
3. **Context Building**: Create context blocks from similar examples
4. **Prompt Enhancement**: Inject context into generation prompt
5. **Quality Improvement**: Use examples to guide AI generation

## Database Schema

### Prompts Table
```sql
CREATE TABLE prompts (
    id INTEGER PRIMARY KEY,
    topic VARCHAR,
    subject VARCHAR,
    content TEXT,
    key_concepts JSON,
    education_level VARCHAR,
    learning_objectives TEXT,
    interactive_features JSON,
    created_at TIMESTAMP
);
```

### History Table
```sql
CREATE TABLE history (
    id VARCHAR PRIMARY KEY,
    prompt_id INTEGER,
    user_query TEXT,
    response TEXT,
    provider VARCHAR,
    components JSON,
    materials JSON,
    lights JSON,
    render_settings JSON,
    generation_time FLOAT,
    created_at TIMESTAMP
);
```

## Error Handling

- **Empty Prompt**: Frontend prevents generation of empty prompts
- **AI Provider Errors**: Backend handles API failures with specific error messages
- **Invalid HTML**: Backend validates HTML structure and content
- **Network Issues**: Frontend shows user-friendly error messages
- **Database Errors**: Backend handles persistence failures gracefully

## Performance Considerations

- **Generation Time**: Tracked and logged for optimization
- **Context Truncation**: Code snippets limited to 1000 characters
- **Similarity Limits**: Configurable limit for similar visualizations
- **Caching**: Vector store provides fast similarity search
- **Async Processing**: Non-blocking generation with proper state management

## Benefits

1. **Educational Quality**: RAG ensures high-quality educational content
2. **Interactive Features**: Automatically includes relevant interactive elements
3. **Consistent Styling**: Professional 3D rendering with educational focus
4. **History Tracking**: Complete audit trail of generations
5. **Multi-Provider Support**: Flexible AI provider integration
6. **Error Resilience**: Robust error handling and validation 