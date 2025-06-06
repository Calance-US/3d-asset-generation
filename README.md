# 3D Concept Visualizer

A web application that generates interactive 3D visualizations of scientific concepts using AI.

## Features

1. Generate 3D visualizations from natural language descriptions
2. Support for multiple AI providers (OpenAI, Ollama, Gemini)
3. Interactive 3D scenes with rotation, zoom, and pan controls
4. History tracking of generated visualizations
5. Download visualizations as standalone HTML files
6. Use the history panel to manage past generations

## Development

### Project Structure
```
.
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Generator.jsx
│   │   │   └── Admin.jsx
│   │   └── App.jsx
│   └── package.json
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   └── data/
│   └── requirements.txt
└── README.md
```

### Running the Application

1. Start the backend server:
```bash
cd backend
uvicorn app.main:app --reload
```

2. Start the frontend development server:
```bash
cd frontend
npm install
npm start
```

3. Open http://localhost:3000 in your browser

### Adding New Features
1. Frontend components are in `frontend/src/components/`
2. Backend API endpoints are in `backend/app/main.py`
3. Add new dependencies to `package.json` or `requirements.txt`

## License

MIT License 