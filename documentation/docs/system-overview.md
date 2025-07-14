# 3D Educational Visualization Platform - Documentation

This directory contains comprehensive documentation for the 3D Educational Visualization Platform, including detailed sequence diagrams and flow documentation.

## Overview

The 3D Educational Visualization Platform is a sophisticated system that combines AI-powered generation with retrieval-augmented generation (RAG) to create interactive 3D educational visualizations. The platform supports multiple AI providers, vector-based similarity search, and comprehensive educational content management.

## Documentation Structure

### Core Flows

1. **[Enhance Prompt Flow](./enhance-prompt-flow.md)**
      - Documents the process of enhancing basic user prompts with AI-generated educational content
      - Shows how the system automatically generates detailed configurations
      - Covers AI provider integration and response processing

2. **[Generate Visualization Flow](./generate-visualization-flow.md)**
      - The core functionality for creating 3D visualizations
      - Details the RAG (Retrieval-Augmented Generation) process
      - Covers AI generation, validation, and database persistence

3. **[Show Retrieved Results Flow](./show-retrieved-results-flow.md)**
      - Development/testing feature for debugging RAG functionality
      - Shows how similar visualizations are retrieved and displayed
      - Covers vector search and similarity scoring

4. **[Add Gold Standards Flow](./add-gold-standards-flow.md)**
      - Administrative process for uploading high-quality educational content
      - Details the snippet extraction and embedding generation process
      - Covers AI enhancement and vector store integration

## System Architecture

### Key Components

- **Frontend**: React-based UI with Material-UI and Tailwind CSS
- **Backend**: FastAPI with async/await support
- **Vector Store**: Qdrant for similarity search
- **Database**: PostgreSQL with Alembic migrations
- **AI Providers**: OpenAI, Google Gemini, Ollama support
- **Embedding Service**: Sentence Transformers for embedding generation

### Technology Stack

- **Backend**: Python 3.11+, FastAPI, SQLAlchemy, Pydantic V2
- **Frontend**: React, Material-UI, Tailwind CSS
- **Database**: PostgreSQL with vector extensions
- **Vector Store**: Qdrant
- **AI/ML**: Sentence Transformers, OpenAI API, Google Gemini API
- **Package Management**: uv (Astral)

## Sequence Diagrams

All sequence diagrams are written in Mermaid format and can be rendered in:
- GitHub (native support)
- GitLab (native support)
- VS Code (with Mermaid extension)
- Online Mermaid editor
- Documentation generators

### Diagram Conventions

- **Participants**: Clear naming with abbreviations
- **Notes**: Detailed explanations of complex steps
- **Data Flow**: Shows request/response formats
- **Error Handling**: Includes error paths and recovery
- **Timing**: Shows async operations and parallel processing

## Key Features Documented

### 1. AI-Powered Enhancement
- Automatic prompt enhancement with educational content
- Multi-provider AI support (OpenAI, Gemini, Ollama)
- Structured configuration generation

### 2. Retrieval-Augmented Generation (RAG)
- Vector-based similarity search
- Context injection from similar examples
- Quality improvement through example learning

### 3. Educational Content Management
- Gold standard content upload and processing
- Snippet extraction and classification
- Metadata generation and AI enhancement

### 4. Vector Search and Embeddings
- Sentence Transformers for embedding generation
- Qdrant vector store for similarity search
- Fast retrieval with similarity scoring

### 5. Database and Persistence
- Comprehensive history tracking
- Prompt and visualization storage
- Metadata management with relationships

## Development Workflow

### 1. Content Creation
1. Upload gold standard HTML files
2. Process into educational snippets
3. Generate embeddings and store in vector database
4. Validate quality and educational value

### 2. User Interaction
1. User enters basic topic description
2. Optionally enhance prompt with AI
3. Generate visualization with RAG context
4. Display interactive 3D scene

### 3. Quality Assurance
1. Development tools for debugging RAG
2. Similarity search testing
3. Content validation and enhancement
4. Performance monitoring

## API Endpoints

### Core Endpoints
- `POST /prompt/enhance-prompt` - Enhance user prompts
- `POST /visualizations/generate` - Generate 3D visualizations
- `POST /rag/retrieve-similar` - Retrieve similar visualizations (dev)
- `POST /gold-standards/upload` - Upload educational content

### Supporting Endpoints
- `GET /visualizations/` - List visualizations
- `POST /visualizations/save` - Save to library
- `GET /history/` - View generation history
- `GET /admin/stats` - System statistics

## Database Schema

### Core Tables
- **prompts**: Educational prompt storage
- **history**: Generation history and results
- **snippet_metadata**: Educational content snippets
- **visualizations**: Saved visualization library
- **gold_standard_upload_status**: Upload processing status

### Relationships
- Prompts → History (one-to-many)
- SnippetMetadata → Vector Store (via faiss_id)
- Visualizations → Tags (many-to-many)

## Configuration

### Environment Variables
- `OPENAI_API_KEY` - OpenAI API access
- `GOOGLE_API_KEY` - Google Gemini API access
- `OLLAMA_BASE_URL` - Local Ollama instance
- `VECTOR_STORE_COLLECTION_NAME` - Qdrant collection
- `SIMILAR_VIS_LIMIT` - RAG retrieval limit

### Settings
- AI provider selection
- Vector store configuration
- Database connection settings
- Logging and monitoring

## Error Handling

### Frontend Error Handling
- Network request failures
- Validation errors
- User input validation
- Loading state management

### Backend Error Handling
- AI provider failures
- Database constraint violations
- Vector store connection issues
- File processing errors

## Performance Considerations

### Optimization Strategies
- Async processing for AI requests
- Vector search optimization
- Database query optimization
- Frontend state management
- Caching strategies

### Monitoring
- Generation time tracking
- Similarity search performance
- AI provider response times
- Database query performance

## Security Considerations

### API Security
- Input validation and sanitization
- Rate limiting
- Error message sanitization
- Authentication (future enhancement)

### Data Security
- Secure file upload handling
- Database connection security
- API key management
- Content validation

## Future Enhancements

### Planned Features
- User authentication and authorization
- Advanced content management
- Real-time collaboration
- Mobile application support
- Advanced analytics and reporting

### Technical Improvements
- Microservices architecture
- Advanced caching strategies
- Real-time notifications
- Advanced vector search features
- Multi-language support

## Contributing

When contributing to the documentation:

1. **Update Sequence Diagrams**: Modify Mermaid diagrams to reflect code changes
2. **Add New Flows**: Document new features with sequence diagrams
3. **Update API Documentation**: Keep endpoint documentation current
4. **Review Accuracy**: Ensure documentation matches implementation

## Support

For questions about the documentation or system architecture:

1. Review the sequence diagrams for specific flows
2. Check the API documentation for endpoint details
3. Refer to the database schema for data relationships
4. Contact the development team for technical support

---

*This documentation is maintained alongside the codebase and should be updated when features are added or modified.* 