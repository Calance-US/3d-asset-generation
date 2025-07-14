# Add Gold Standards Flow

This document describes the sequence of interactions when an administrator uploads and processes gold standard educational content in the 3D Educational Visualization Platform.

## Overview

The add gold standards flow allows administrators to upload high-quality educational HTML files, process them into snippets, generate embeddings, and store them in the vector database (Qdrant) for use in retrieval-augmented generation (RAG). All admin endpoints require Keycloak authentication (JWT) or system user in dev/migration mode.

## Sequence Diagram

```mermaid
sequenceDiagram
    participant A as Admin
    participant F as Frontend (Admin.jsx)
    participant B as Backend API
    participant FS as File System
    participant PS as Processing Service
    participant ES as Embedding Service
    participant VS as Vector Store (Qdrant)
    participant DB as Database
    participant LLM as AI Provider (OpenAI/Gemini/Ollama)

    Note over A,LLM: Admin initiates gold standard upload
    A->>F: Navigate to Admin Dashboard
    A->>F: Select "Upload Gold Standards" section
    A->>F: Choose HTML file(s) to upload
    A->>F: Set upload parameters
    F->>F: Validate file type (HTML)
    F->>F: Check file size limits
    F->>F: Prepare upload form data
    F->>F: Set upload status to "uploading"
    F->>B: POST /gold-standards/upload (with JWT)
    B->>FS: Save uploaded file temporarily
    B->>B: Create upload status record
    B->>B: Parse HTML content, extract educational content
    B->>PS: Extract snippets from HTML
    PS->>PS: Identify snippet types (lighting, material, animation, narration, ui_controls, renderer_settings, camera_setup, full_scene, etc.)
    PS->>PS: Generate snippet metadata (see below)
    B->>LLM: Enhance snippet metadata (optional)
    LLM->>B: Return enhanced metadata
    B->>ES: Generate embeddings for each snippet
    ES->>VS: Add embeddings to Qdrant
    VS->>VS: Store vectors with faiss_ids
    B->>DB: Save snippet metadata
    B->>DB: Update upload status to "completed"
    B->>F: Return upload response
    F->>F: Update upload status, display results
    F->>A: Display upload summary
```

## Key Components

### Frontend (Admin.jsx)
- **File Upload**: Handles HTML file selection and upload
- **Progress Tracking**: Shows upload and processing progress
- **Result Display**: Shows processing results and snippet details
- **Error Handling**: Displays validation and processing errors

### Backend API (/gold-standards/upload)
- **File Processing**: Parses and validates HTML content
- **Snippet Extraction**: Identifies and extracts different snippet types
- **AI Enhancement**: Uses AI to improve metadata quality
- **Embedding Generation**: Creates vector embeddings for similarity search
- **Database Storage**: Saves metadata and links to vector store (Qdrant)
- **Authentication**: Requires Keycloak JWT (unless in dev bypass mode)

### Processing Service
- **HTML Parsing**: Extracts educational content from HTML
- **Snippet Classification**: Identifies different types of code snippets
- **Metadata Generation**: Creates comprehensive metadata for each snippet
- **Quality Validation**: Ensures snippets meet educational standards

### Embedding Service
- **Text Preparation**: Creates embedding text from metadata
- **Vector Generation**: Converts text to high-dimensional vectors
- **Normalization**: Ensures consistent embedding format

### Vector Store (Qdrant)
- **Vector Storage**: Stores embeddings with unique IDs
- **Indexing**: Creates searchable index for similarity queries
- **ID Management**: Links vector IDs to database records

## Snippet Metadata Structure

Each snippet includes:
```json
{
  "id": "...",
  "summary": "...",
  "snippet_type": "ui_controls",
  "key_concepts": "...",
  "learning_objectives": "...",
  "education_level": "High School",
  "topic": "...",
  "html_snippet": "...",
  "embedding_text": "...",
  "faiss_id": 123,
  "created_at": "...",
  "updated_at": "..."
}
```

## Database Schema

### SnippetMetadata Table
```sql
CREATE TABLE snippet_metadata (
    id VARCHAR PRIMARY KEY,
    summary TEXT,
    snippet_type VARCHAR,
    key_concepts TEXT,
    learning_objectives TEXT,
    education_level VARCHAR,
    topic VARCHAR,
    html_snippet TEXT,
    embedding_text TEXT,
    faiss_id INTEGER UNIQUE,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

### GoldStandardUploadStatus Table
```sql
CREATE TABLE gold_standard_upload_status (
    id VARCHAR PRIMARY KEY,
    filename VARCHAR,
    subject VARCHAR,
    education_level VARCHAR,
    topic VARCHAR,
    status VARCHAR,
    total_snippets INTEGER,
    successful_snippets INTEGER,
    failed_snippets INTEGER,
    processing_time FLOAT,
    result JSON,
    created_at TIMESTAMP
);
```

## Validation Rules

### HTML Content Validation
- **Valid HTML**: Must be well-formed HTML
- **Three.js Components**: Must contain Three.js scene elements
- **Educational Content**: Must have educational value
- **Interactive Elements**: Should include interactive features

### Snippet Quality Validation
- **Required Fields**: summary, snippet_type, key_concepts
- **Content Length**: Minimum content requirements
- **Educational Value**: Must have clear learning objectives
- **Code Quality**: Valid JavaScript/HTML code

### Embedding Validation
- **Text Quality**: Embedding text must be meaningful
- **Vector Generation**: Must generate valid vectors
- **Storage Success**: Must be stored in vector database (Qdrant)

## Error Handling

- **File Validation**: Invalid file types or corrupted content
- **HTML Parsing**: Malformed HTML structure
- **Snippet Extraction**: Failed snippet identification
- **AI Enhancement**: AI provider errors or timeouts
- **Embedding Generation**: Vector generation failures
- **Database Errors**: Storage or constraint violations
- **Vector Store Errors**: Qdrant connection or storage issues

## Performance Considerations

- **Batch Processing**: Process multiple snippets efficiently
- **Parallel Processing**: Concurrent embedding generation
- **Memory Management**: Handle large HTML files
- **Database Optimization**: Efficient metadata storage
- **Vector Indexing**: Fast similarity search setup

## Benefits

1. **Quality Assurance**: Ensures high-quality educational content
2. **Automated Processing**: Streamlines content ingestion
3. **AI Enhancement**: Improves metadata quality automatically
4. **Vector Search**: Enables fast similarity-based retrieval
5. **Educational Standards**: Maintains consistent educational quality
6. **Scalability**: Handles large volumes of educational content
7. **Audit Trail**: Complete tracking of processing results 