import time
import asyncio
import logging
from typing import List, Dict, Optional
from sentence_transformers import SentenceTransformer
import openai
from config import settings

logger = logging.getLogger(__name__)

class EmbeddingService:
	def __init__(self):
		self.model = None
		self.cache: Dict[str, List[float]] = {}
		self.model_version = settings.MODEL_VERSION
		self.is_initialized = False

	async def initialize(self):
		"""Initialize the embedding model"""
		try:
			if settings.USE_OPENAI_EMBEDDINGS:
				openai.api_key = settings.OPENAI_API_KEY
				logger.info("Using OpenAI embeddings")
			else:
				logger.info(f"Loading embedding model: {settings.EMBEDDING_MODEL}")
				# Load model in thread pool to avoid blocking
				loop = asyncio.get_event_loop()
				self.model = await loop.run_in_executor(
					None, 
					SentenceTransformer, 
					settings.EMBEDDING_MODEL
				)
				logger.info("Embedding model loaded successfully")
			
			self.is_initialized = True
		except Exception as e:
			logger.error(f"Failed to initialize embedding service: {e}")
			raise

	def is_ready(self) -> bool:
		"""Check if service is ready"""
		return self.is_initialized

	async def get_embedding(self, text: str) -> List[float]:
		"""Generate embedding for text"""
		if not self.is_initialized:
			raise Exception("Embedding service not initialized")

		# Check cache first
		if settings.ENABLE_EMBEDDING_CACHE and text in self.cache:
			logger.debug("Embedding cache hit")
			return self.cache[text]

		start_time = time.time()
		
		try:
			if settings.USE_OPENAI_EMBEDDINGS:
				embedding = await self._get_openai_embedding(text)
			else:
				embedding = await self._get_local_embedding(text)
			
			# Cache the result
			if settings.ENABLE_EMBEDDING_CACHE:
				self.cache[text] = embedding
				# Simple cache size management
				if len(self.cache) > 1000:
					# Remove oldest half of cache
					items = list(self.cache.items())
					self.cache = dict(items[500:])

			processing_time = (time.time() - start_time) * 1000
			logger.info(f"Generated embedding in {processing_time:.2f}ms")
			
			return embedding
			
		except Exception as e:
			logger.error(f"Failed to generate embedding: {e}")
			raise

	async def _get_local_embedding(self, text: str) -> List[float]:
		"""Generate embedding using local model"""
		loop = asyncio.get_event_loop()
		embedding = await loop.run_in_executor(
			None,
			self.model.encode,
			text
		)
		return embedding.tolist()

	async def _get_openai_embedding(self, text: str) -> List[float]:
		"""Generate embedding using OpenAI API"""
		response = await openai.Embedding.acreate(
			input=text,
			model="text-embedding-ada-002"
		)
		return response['data'][0]['embedding']

	def get_cache_stats(self) -> Dict[str, int]:
		"""Get cache statistics"""
		return {
			"cache_size": len(self.cache),
			"cache_enabled": settings.ENABLE_EMBEDDING_CACHE
		}