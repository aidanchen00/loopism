#!/bin/bash
echo "🔄 Starting Loopism..."

# Load environment
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
    echo "✅ Loaded .env file"
else
    echo "⚠️  No .env file found. Copy .env.template to .env and add your API keys."
fi

# Check dependencies
python -c "import replicate, weave, streamlit" 2>/dev/null || {
    echo "📦 Installing dependencies..."
    pip install -r requirements.txt
}

# Run the app
echo "🚀 Launching Streamlit UI at http://localhost:8501"
streamlit run app.py --server.port 8501
