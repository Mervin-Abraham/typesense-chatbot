import time
import asyncio
import logging
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from typing import List
from models.schemas import (
	EmbedRequest, EmbedResponse, IndexRequest, IndexResponse,
	BatchIndexRequest, BatchIndexResponse, SnippetWithEmbedding
)
from services.embedding import EmbeddingService
from services.typesense_service import TypesenseService
from main import get_embedding_service, get_typesense_service
from config import settings

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/embed-snippet", response_model=EmbedResponse)
async def embed_snippet(
	request: EmbedRequest,
	embedding_service: EmbeddingService = Depends(get_embedding_service)
):
	"""Generate embedding for text"""
	start_time = time.time()

	try:
		embedding = await embedding_service.get_embedding(request.text)
		processing_time = (time.time() - start_time) * 1000

		return EmbedResponse(
			embedding=embedding,
			model_version=embedding_service.model_version,
			processing_time_ms=processing_time
		)
	except Exception as e:
		logger.error(f"Embedding generation failed: {e}")
		raise HTTPException(status_code=500, detail=str(e))

@router.post("/index-snippet", response_model=IndexResponse)
async def index_snippet(
	request: IndexRequest,
	embedding_service: EmbeddingService = Depends(get_embedding_service),
	typesense_service: TypesenseService = Depends(get_typesense_service)
):
	"""Index a single snippet with embedding"""
	start_time = time.time()

	try:
		# Generate embedding for title + description
		text_to_embed = f"{request.snippet.title} {request.snippet.description}"
		embedding = await embedding_service.get_embedding(text_to_embed)

		# Create snippet with embedding
		snippet_with_embedding = SnippetWithEmbedding(
			**request.snippet.dict(),
			embedding=embedding,
			model_version=settings.MODEL_VERSION
		)

		# Index to Typesense
		success = await typesense_service.upsert_snippet(snippet_with_embedding)

		processing_time = (time.time() - start_time) * 1000

		return IndexResponse(
			success=success,
			snippet_id=request.snippet.id,
			message="Successfully indexed" if success else "Failed to index",
			processing_time_ms=processing_time
		)

	except Exception as e:
		logger.error(f"Indexing failed for snippet {request.snippet.id}: {e}")
		raise HTTPException(status_code=500, detail=str(e))

async def process_batch_indexing(
	snippets: List,
	embedding_service: EmbeddingService,
	typesense_service: TypesenseService,
	batch_size: int = 10
):
	"""Background task for batch indexing"""
	successful = 0
	failed = 0
	errors = []

	# Process in batches
	for i in range(0, len(snippets), batch_size):
		batch = snippets[i:i + batch_size]

		# Process batch concurrently
		tasks = []
		for snippet in batch:
			task = process_single_snippet(snippet, embedding_service, typesense_service)
			tasks.append(task)

		results = await asyncio.gather(*tasks, return_exceptions=True)

		for result in results:
			if isinstance(result, Exception):
				failed += 1
				errors.append(str(result))
			elif result:
				successful += 1
			else:
				failed += 1
				errors.append("Unknown indexing error")

	logger.info(f"Batch indexing completed: {successful} successful, {failed} failed")

async def process_single_snippet(snippet, embedding_service, typesense_service):
	"""Process a single snippet for indexing"""
	try:
		text_to_embed = f"{snippet.title} {snippet.description}"
		embedding = await embedding_service.get_embedding(text_to_embed)

		snippet_with_embedding = SnippetWithEmbedding(
			**snippet.dict(),
			embedding=embedding,
			model_version=settings.MODEL_VERSION
		)

		return await typesense_service.upsert_snippet(snippet_with_embedding)
	except Exception as e:
		logger.error(f"Failed to process snippet {snippet.id}: {e}")
		raise

@router.post("/batch-index", response_model=BatchIndexResponse)
async def batch_index_snippets(
	request: BatchIndexRequest,
	background_tasks: BackgroundTasks,
	embedding_service: EmbeddingService = Depends(get_embedding_service),
	typesense_service: TypesenseService = Depends(get_typesense_service)
):
	"""Batch index multiple snippets"""
	start_time = time.time()

	try:
		# For small batches, process immediately
		if len(request.snippets) <= 5:
			successful = 0
			failed = 0
			errors = []

			for snippet in request.snippets:
				try:
					text_to_embed = f"{snippet.title} {snippet.description}"
					embedding = await embedding_service.get_embedding(text_to_embed)

					snippet_with_embedding = SnippetWithEmbedding(
						**snippet.dict(),
						embedding=embedding,
						model_version=settings.MODEL_VERSION
					)

					success = await typesense_service.upsert_snippet(snippet_with_embedding)
					if success:
						successful += 1
					else:
						failed += 1
						errors.append(f"Failed to index snippet {snippet.id}")

				except Exception as e:
					failed += 1
					errors.append(f"Error processing snippet {snippet.id}: {str(e)}")

			processing_time = (time.time() - start_time) * 1000

			return BatchIndexResponse(
				success=failed == 0,
				total_processed=len(request.snippets),
				successful=successful,
				failed=failed,
				errors=errors,
				processing_time_ms=processing_time
			)
		else:
			# For large batches, use background task
			background_tasks.add_task(
				process_batch_indexing,
				request.snippets,
				embedding_service,
				typesense_service,
				request.batch_size
			)

			processing_time = (time.time() - start_time) * 1000

			return BatchIndexResponse(
				success=True,
				total_processed=len(request.snippets),
				successful=0,  # Will be updated by background task
				failed=0,
				errors=[],
				processing_time_ms=processing_time
			)

	except Exception as e:
		logger.error(f"Batch indexing failed: {e}")
		raise HTTPException(status_code=500, detail=str(e))