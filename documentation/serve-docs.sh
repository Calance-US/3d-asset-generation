#!/bin/bash

echo "🚀 Starting MkDocs documentation server..."
echo "📚 Documentation will be available at: http://127.0.0.1:8001"
echo "🔧 Press Ctrl+C to stop the server"
echo ""

# Start MkDocs server
uv run mkdocs serve --dev-addr=127.0.0.1:8001
