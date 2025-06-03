#!/bin/bash

# Setup script for the embedding service

set -e

echo "Setting up Embedding + RAG Service..."

# Create necessary directories
mkdir -p logs
mkdir -p data

# Copy environment file if it doesn't exist
if [ ! -f .env ]; then
	cp .env.example .env
	echo "Created .env file from template. Please update the values."
fi

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Download embedding model (optional - will be downloaded on first use)
echo "Pre-downloading embedding model..."
python -c "
from sentence_transformers import SentenceTransformer
import os
model_name = os.getenv('EMBEDDING_MODEL', 'intfloat/e5-small-v2')
print(f'Downloading {model_name}...')
SentenceTransformer(model_name)
print('Model downloaded successfully!')
"

echo "Setup completed!"
echo "To start the service:"
echo "  1. Update .env with your configuration"
echo "  2. Run: uvicorn main:app --host 0.0.0.0 --port 8000"
echo "  3. Or use Docker: docker-compose up --build"