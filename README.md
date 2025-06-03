# Embedding + RAG Service

A production-ready FastAPI microservice for embedding generation and vector search with Typesense integration.

## Features

- 🚀 **FastAPI** with async support
- 🔍 **Hybrid Search** (text + vector similarity)
- 🤖 **Local Embeddings** (Hugging Face) or OpenAI API
- 📊 **Typesense Integration** for vector storage
- 🔒 **API Key Authentication**
- 📈 **Performance Monitoring**
- 🐳 **Docker Ready**
- 📚 **Auto-generated API docs**

## Quick Start

### 1. Setup Environment

```bash
# Clone and setup
git clone <your-repo>
cd embedding-rag-service

# Copy environment file
cp .env.example .env

# Edit .env with your configuration
nano .env
```

### 2. Install Dependencies

```bash
# Using pip
pip install -r requirements.txt

# Or using Docker
docker-compose up --build
```

### 3. Run the Service

```bash
# Development
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Production
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

### 4. Test the Service

```bash
# Run test suite
python scripts/test_service.py

# Check health
curl http://localhost:8000/health
```

## API Endpoints

### Core Endpoints

- `POST /api/v1/embed-snippet` - Generate embeddings
- `POST /api/v1/index-snippet` - Index single snippet
- `POST /api/v1/batch-index` - Batch index snippets
- `POST /api/v1/search-snippets` - Search snippets
- `GET /health` - Health check

### API Documentation

Visit `http://localhost:8000/docs` for interactive API documentation.

## Usage Examples

### Generate Embedding

```python
import requests

response = requests.post(
	"http://localhost:8000/api/v1/embed-snippet",
	headers={"Authorization": "Bearer your-api-key"},
	json={"text": "Machine learning algorithms"}
)
print(response.json())
```

### Index a Snippet

```python
snippet_data = {
	"snippet": {
		"id": "ml-101",
		"title": "Machine Learning Basics",
		"description": "Introduction to ML concepts",
		"created_on": "2024-01-01T00:00:00",
		"snippet_type": "tutorial",
		"published": True,
		"product_category_ids": [1, 2]
	}
}

response = requests.post(
	"http://localhost:8000/api/v1/index-snippet",
	headers={"Authorization": "Bearer your-api-key"},
	json=snippet_data
)
```

### Search Snippets

```python
search_data = {
	"query": "machine learning",
	"limit": 10,
	"published_only": True
}

# Text search
response = requests.post(
	"http://localhost:8000/api/v1/search-snippets?search_type=text",
	headers={"Authorization": "Bearer your-api-key"},
	json=search_data
)

# Vector search
response = requests.post(
	"http://localhost:8000/api/v1/search-snippets?search_type=vector",
	headers={"Authorization": "Bearer your-api-key"},
	json=search_data
)

# Hybrid search (default)
response = requests.post(
	"http://localhost:8000/api/v1/search-snippets?search_type=hybrid",
	headers={"Authorization": "Bearer your-api-key"},
	json=search_data
)
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `API_KEY` | API authentication key | `your-secret-api-key` |
| `TYPESENSE_HOST` | Typesense server host | `localhost` |
| `TYPESENSE_API_KEY` | Typesense API key | `xyz` |
| `EMBEDDING_MODEL` | Hugging Face model name | `intfloat/e5-small-v2` |
| `USE_OPENAI_EMBEDDINGS` | Use OpenAI instead of local | `false` |
| `ENABLE_EMBEDDING_CACHE` | Cache embeddings | `true` |

### Typesense Setup

Ensure your Typesense instance is running and accessible. The service will automatically create the required collection schema.

## Deployment

### Docker Deployment

```bash
# Build and run
docker-compose up --build -d

# Check logs
docker-compose logs -f embedding-service
```

### AWS EC2 Deployment

```bash
# On your EC2 instance
git clone <your-repo>
cd embedding-rag-service

# Setup environment
cp .env.example .env
# Edit .env with your Typesense configuration

# Run with Docker
docker-compose up -d

# Or run directly
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 2
```

### Production Considerations

- Use a reverse proxy (nginx) for SSL termination
- Set up log rotation
- Monitor memory usage (embedding models can be large)
- Consider using Redis for distributed caching
- Set up health check monitoring

## Migration from Legacy System

Use the migration script to move existing snippets:

```bash
# Prepare your snippets in JSON format
python scripts/migrate_existing_snippets.py
```

## Monitoring

### Health Monitoring

```bash
# One-time health check
python monitoring/health_check.py

# Continuous monitoring
python monitoring/health_check.py --continuous
```

### Performance Metrics

- Embedding generation time
- Search response time
- Cache hit rates
- Typesense connection status

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   FastAPI App   │    │  Embedding      │    │   Typesense     │
│                 │    │  Service        │    │   Vector DB     │
│ • Authentication│────│• Local Model    │────│• Collection     │
│ • API Routes    │    │• OpenAI API     │    │• Vector Search  │
│ • Validation    │    │• Caching        │    │• Text Search    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT License - see LICENSE file for details.