#!/bin/bash
set -e
echo "============================================================"
echo "  Media Web 6 AI - Building for Render"
echo "============================================================"
echo "📦 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
echo "📁 Creating directories..."
mkdir -p data audio_files flask_sessions static
echo "✅ Build complete!"
EOF
