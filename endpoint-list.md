# Frontend API Endpoints

This document lists all API endpoints used by the frontend application and their UI locations.

## Base Configuration
- **Base URL**: `process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000'`
- **API Prefix**: `/api/v1`

## Admin Endpoints (`/admin/*`)

| Endpoint | Method | UI Location | Description |
|----------|--------|-------------|-------------|
| `/admin/tasks` | GET | Admin panel - Tasks tab | Fetch list of background tasks |
| `/admin/tasks/{taskId}` | GET | Admin panel - Task details modal | Get specific task details |
| `/admin/validation-metrics` | GET | Admin panel - Validation metrics tab | Get validation performance metrics |
| `/admin/vector-store-stats` | GET | Admin panel - Vector store dashboard | Get vector database statistics |
| `/admin/vector-store-vectors` | GET | Admin panel - Vector store dashboard | Get paginated vector entries |

## Gold Standards Endpoints (`/gold-standards/*`)

| Endpoint | Method | UI Location | Description |
|----------|--------|-------------|-------------|
| `/gold-standards/` | GET | Admin panel - Gold standards tab | Fetch gold standards list |
| `/gold-standards/` | POST | Admin panel - Multi-file upload | Upload multiple gold standard files |
| `/gold-standards/{id}` | PUT | Admin panel - Edit gold standard dialog | Update specific gold standard |
| `/gold-standards/{index}` | DELETE | Admin panel - Delete button | Delete gold standard by index |
| `/gold-standards/status/{upload_id}` | GET | Admin panel - Upload progress | Check batch upload status |

## History Endpoints (`/history/*`)

| Endpoint | Method | UI Location | Description |
|----------|--------|-------------|-------------|
| `/history` | GET | Generator - History sidebar | Get visualization history entries |
| `/history/{id}/html` | GET | Generator - Load from history | Get HTML content for entry |
| `/history/{entryId}` | DELETE | Generator - Delete history button | Delete specific history entry |

## Prompt Endpoints (`/prompt/*`)

| Endpoint | Method | UI Location | Description |
|----------|--------|-------------|-------------|
| `/prompt` | GET | Admin panel - Prompts section | Load available prompt templates |
| `/prompt/enhance-prompt` | POST | Generator - Enhance prompt button | AI-powered prompt enhancement |

## Visualization Endpoints (`/visualizations/*`)

| Endpoint | Method | UI Location | Description |
|----------|--------|-------------|-------------|
| `/visualizations/generate` | POST | Generator - Regenerate button | Generate visualization synchronously |
| `/visualizations/save` | POST | Generator - Save visualization button | Save visualization with metadata |

## Async Visualization Endpoints (`/async-visualizations/*`)

| Endpoint | Method | UI Location | Description |
|----------|--------|-------------|-------------|
| `/async-visualizations/generate-async` | POST | Generator - Generate button | Start async visualization generation |
| `/async-visualizations/status/{taskId}` | GET | Generator - Progress polling | Check async task status |
| `/async-visualizations/result/{taskId}` | GET | Generator - Task completion | Get completed task result |
| `/async-visualizations/cancel/{taskId}` | DELETE | Generator - Cancel button | Cancel running async task |

## RAG Endpoints (`/rag/*`)

| Endpoint | Method | UI Location | Description |
|----------|--------|-------------|-------------|
| `/rag/retrieve-similar` | POST | Generator - Retrieve similar button | Find similar content using RAG |

## Summary by HTTP Method

### GET Requests (Data Fetching)
- **9 endpoints** - Used for loading data, checking status, and retrieving content
- Primary locations: Admin panels, history sidebar, task monitoring

### POST Requests (Creation/Processing)
- **5 endpoints** - Used for generating content, uploading files, and processing
- Primary locations: Generator buttons, admin upload forms

### PUT Requests (Updates)
- **1 endpoint** - Used for updating existing gold standards
- Primary location: Admin edit dialogs

### DELETE Requests (Deletion)
- **3 endpoints** - Used for removing content and canceling tasks
- Primary locations: Delete buttons, cancel operations

## Component Usage

| Component | Endpoints Used | Purpose |
|-----------|----------------|---------|
| `Admin.jsx` | 8 admin + gold-standards endpoints | Administrative interface |
| `Generator.jsx` | 9 core generation endpoints | Main visualization interface |
| `VectorStoreDashboard.jsx` | 2 vector store endpoints | Vector database management |
| `ValidationMetrics.jsx` | 1 validation endpoint | Performance monitoring |

## Request Libraries
- **fetch()** - Primary HTTP client (18 endpoints)
- **axios** - Used in vector store dashboard (2 endpoints)
