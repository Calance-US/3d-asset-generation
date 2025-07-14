# Documentation Index

Welcome to the 3D Educational Visualization Platform documentation. This index provides quick navigation to all available documentation.

## 📋 Quick Start

- **[System Overview](./system-overview.md)** - Comprehensive overview and system architecture


## 🔄 Core Flows

### 1. Enhance Prompt Flow
**File**: `enhance-prompt-flow.md`  
**Purpose**: AI-powered prompt enhancement with educational content  
**Key Features**:
- Automatic configuration generation (all config fields: components, materials, lights, narration, renderer, etc.)
- Multi-AI provider support
- Educational content injection
- Structured response processing

### 2. Generate Visualization Flow
**File**: `generate-visualization-flow.md`  
**Purpose**: Core 3D visualization generation with async task management and RAG  
**Key Features**:
- Async task creation, polling, cancellation, and result retrieval
- Retrieval-augmented generation
- Vector similarity search
- AI provider integration
- Database persistence (full config structure)
- HTML validation

### 3. Show Retrieved Results Flow
**File**: `show-retrieved-results-flow.md`  
**Purpose**: Development tool for RAG debugging  
**Key Features**:
- Vector search testing
- Similarity score display
- Console-based debugging
- Development-only access

### 4. Add Gold Standards Flow
**File**: `add-gold-standards-flow.md`  
**Purpose**: Administrative content management  
**Key Features**:
- HTML file upload and processing
- Snippet extraction and classification
- AI metadata enhancement
- Vector embedding generation

## 🏗️ System Architecture

### Technology Stack
- **Backend**: FastAPI (async), SQLAlchemy, Pydantic V2
- **Frontend**: React, Material-UI, Tailwind CSS
- **Database**: PostgreSQL with vector extensions
- **Vector Store**: Qdrant
- **AI Providers**: OpenAI, Google Gemini, Ollama
- **Package Manager**: uv (Astral)
- **Authentication**: Keycloak (OIDC), system user fallback for dev/migrations

### Key Components
- **Async Task Manager**: Handles async generation, polling, cancellation
- **RAG Service**: Retrieval-augmented generation
- **Vector Store**: Qdrant similarity search
- **Embedding Service**: Sentence Transformers
- **Prompt Generator**: AI prompt creation
- **Admin Dashboard**: Content management
- **System User/Seeding**: Automated DB seeding for system and test users

## 📈 Sequence Diagrams

All flows include detailed Mermaid sequence diagrams showing:

- **Participant Interactions**: Clear actor definitions
- **Data Flow**: Request/response formats
- **Error Handling**: Error paths and recovery
- **Async Operations**: Parallel processing, task polling
- **External Dependencies**: AI providers, databases, Keycloak

## 🛠️ Development Tools

### Debugging Features
- **RAG Testing**: Show retrieved results
- **Console Logging**: Detailed debugging output
- **Similarity Scoring**: Vector search validation
- **Content Validation**: Educational quality checks

### Admin Features
- **Content Upload**: Gold standard processing
- **System Statistics**: Performance monitoring
- **Vector Store Management**: Embedding administration
- **Quality Assurance**: Content validation

## 📚 API Reference

<a href="http://localhost:8000/docs" target="_blank">🚀 <b>Swagger UI</b></a>


### Core Endpoints
```
POST /prompt/enhance-prompt     - Enhance user prompts
POST /async-visualizations/generate-async   - Generate 3D visualizations (async)
GET  /async-visualizations/status/{task_id} - Poll task status
GET  /async-visualizations/result/{task_id} - Get result HTML
POST /rag/retrieve-similar      - Retrieve similar (dev)
POST /gold-standards/upload     - Upload educational content
```

### Supporting Endpoints
```
GET  /visualizations/           - List visualizations
POST /visualizations/save       - Save to library
GET  /history/                  - View generation history (full config)
GET  /admin/stats               - System statistics
```

## 🗄️ Database Schema

### Core Tables
- **prompts**: Educational prompt storage
- **history**: Generation history and results (full config: components, materials, lights, narration, etc.)
- **snippet_metadata**: Educational content snippets
- **visualizations**: Saved visualization library
- **gold_standard_upload_status**: Upload processing status
- **users**: Keycloak and system users (seeded)

## ⚙️ Configuration

### Environment Variables
```bash
OPENAI_API_KEY=your_openai_key
GOOGLE_API_KEY=your_google_key
OLLAMA_BASE_URL=http://localhost:11434
VECTOR_STORE_COLLECTION_NAME=educational_snippets
SIMILAR_VIS_LIMIT=10
AUTH_ENABLED=true
AUTH_BYPASS_DEVELOPMENT=false
```

## 🚀 Getting Started

### 1. Setup Environment
```bash
# Backend setup
cd backend
uv sync
uv run uvicorn main:app --reload

# Frontend setup
cd frontend
npm install
npm start
```

### 2. Upload Gold Standards
1. Navigate to Admin Dashboard
2. Upload HTML educational files
3. Process into snippets and embeddings
4. Validate quality and content

### 3. Generate Visualizations
1. Enter topic description
2. Optionally enhance with AI
3. Generate 3D visualization (async)
4. Interact with educational content

## 🔍 Troubleshooting

### Common Issues
- **Score Always Null**: Check vector store configuration
- **RAG Not Working**: Verify embeddings and similarity search
- **AI Provider Errors**: Check API keys and configuration
- **Database Issues**: Verify migrations and connections
- **System User Not Found**: Ensure DB seeding script ran after Keycloak setup

### Debug Tools
- **Show Retrieved Results**: Test RAG functionality
- **Console Logging**: Detailed error information
- **Admin Statistics**: System performance metrics
- **Vector Store Dashboard**: Embedding management

## 📊 Performance

### Optimization Strategies
- Async AI processing
- Vector search optimization
- Database query optimization
- Frontend state management
- Caching strategies

### Monitoring
- Generation time tracking
- Similarity search performance
- AI provider response times
- Database query performance

## 🔒 Security

### Current Security
- Input validation and sanitization
- Secure file upload handling
- API key management
- Content validation
- Keycloak authentication

### Future Enhancements
- Rate limiting
- Advanced authorization
- Audit logging

## 🤝 Contributing

### Documentation Updates
1. Update sequence diagrams for code changes
2. Add new flows for new features
3. Keep API documentation current
4. Review accuracy with implementation

### Code Contributions
1. Follow project conventions
2. Update documentation
3. Add tests for new features
4. Review existing flows

## 📞 Support

### Documentation Help
- Review sequence diagrams for specific flows
- Check API documentation for endpoint details
- Refer to database schema for relationships
- Contact development team for technical support

### Development Support
- GitHub Issues for bug reports
- Pull Requests for contributions
- Code reviews for quality assurance
- Team discussions for architecture decisions

---

**Last Updated**: July 2025  
**Version**: 1.1.0  
**Maintainer**: Calance Development Team 