import os
import logging
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from routes.embedding_routes import router as embedding_router
from routes.search_routes import router as search_router
from routes.chat_routes import router as chat_router
from services.embedding import EmbeddingService
from services.typesense_service import TypesenseService
from config import settings

# Configure logging
logging.basicConfig(
	level=logging.INFO,
	format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global services
embedding_service = None
typesense_service = None

@asynccontextmanager
async def lifespan(app: FastAPI):
	"""Initialize services on startup"""
	global embedding_service, typesense_service

	logger.info("Initializing services...")
	embedding_service = EmbeddingService()
	typesense_service = TypesenseService()

	# Initialize embedding model
	await embedding_service.initialize()

	# Test Typesense connection
	if not await typesense_service.health_check():
		logger.error("Failed to connect to Typesense")
		raise Exception("Typesense connection failed")

	logger.info("Services initialized successfully")
	yield

	logger.info("Shutting down services...")

# FastAPI app
app = FastAPI(
	title="Embedding + RAG Service",
	description="Microservice for embedding generation and vector search with Typesense",
	version="1.0.0",
	lifespan=lifespan
)

# CORS middleware
app.add_middleware(
	CORSMiddleware,
	allow_origins=["*"],
	allow_credentials=True,
	allow_methods=["*"],
	allow_headers=["*"],
)

# Security
security = HTTPBearer()

async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
	"""Verify API token"""
	if credentials.credentials != settings.API_KEY:
		raise HTTPException(
			status_code=status.HTTP_401_UNAUTHORIZED,
			detail="Invalid authentication credentials",
			headers={"WWW-Authenticate": "Bearer"},
		)
	return credentials

# Dependency to get services
def get_embedding_service():
	return embedding_service

def get_typesense_service():
	return typesense_service

# Include routers
app.include_router(
	embedding_router,
	prefix="/api/v1",
	dependencies=[Depends(verify_token)] if settings.REQUIRE_AUTH else []
)
app.include_router(
	search_router,
	prefix="/api/v1",
	dependencies=[Depends(verify_token)] if settings.REQUIRE_AUTH else []
)

app.include_router(
	chat_router,
	prefix="/api/v1",
	dependencies=[Depends(verify_token)] if settings.REQUIRE_AUTH else []
)

@app.get("/health")
async def health_check():
	"""Health check endpoint"""
	try:
		ts_health = await typesense_service.health_check() if typesense_service else False
		embedding_health = embedding_service.is_ready() if embedding_service else False

		return {
			"status": "healthy" if ts_health and embedding_health else "unhealthy",
			"services": {
				"typesense": "up" if ts_health else "down",
				"embedding": "ready" if embedding_health else "not_ready"
			}
		}
	except Exception as e:
		logger.error(f"Health check failed: {e}")
		return {"status": "unhealthy", "error": str(e)}

if __name__ == "__main__":
	import uvicorn
	uvicorn.run(
		"main:app",
		host="0.0.0.0",
		port=8000,
		reload=settings.DEBUG
	)