# ====================
# config.py
# ====================
import os
from pydantic import BaseSettings

class Settings(BaseSettings):
	# API Configuration
	API_KEY: str = os.getenv("API_KEY", "your-secret-api-key")
	REQUIRE_AUTH: bool = os.getenv("REQUIRE_AUTH", "true").lower() == "true"
	DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
	
	# Typesense Configuration
	TYPESENSE_HOST: str = os.getenv("TYPESENSE_HOST", "localhost")
	TYPESENSE_PORT: int = int(os.getenv("TYPESENSE_PORT", "8108"))
	TYPESENSE_PROTOCOL: str = os.getenv("TYPESENSE_PROTOCOL", "http")
	TYPESENSE_API_KEY: str = os.getenv("TYPESENSE_API_KEY", "xyz")
	TYPESENSE_COLLECTION: str = os.getenv("TYPESENSE_COLLECTION", "snippets")
	
	# Embedding Configuration
	EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "intfloat/e5-small-v2")
	EMBEDDING_DIMENSION: int = int(os.getenv("EMBEDDING_DIMENSION", "384"))
	USE_OPENAI_EMBEDDINGS: bool = os.getenv("USE_OPENAI_EMBEDDINGS", "false").lower() == "true"
	OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
	
	# Cache Configuration
	ENABLE_EMBEDDING_CACHE: bool = os.getenv("ENABLE_EMBEDDING_CACHE", "true").lower() == "true"
	CACHE_TTL: int = int(os.getenv("CACHE_TTL", "3600"))  # 1 hour
	
	# Model version for tracking
	MODEL_VERSION: str = "v1.0"

settings = Settings()