import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from models.schemas import SearchRequest, SearchResponse
from services.embedding import EmbeddingService
from services.typesense_service import TypesenseService
from main import get_embedding_service, get_typesense_service

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/search-snippets", response_model=SearchResponse)
async def search_snippets(
	request: SearchRequest,
	search_type: str = Query("hybrid", enum=["text", "vector", "hybrid"]),
	embedding_service: EmbeddingService = Depends(get_embedding_service),
	typesense_service: TypesenseService = Depends(get_typesense_service)
):
	"""Search snippets using text, vector, or hybrid search"""
	try:
		if search_type == "text":
			# Text-only search
			results = await typesense_service.search_snippets(request)
		elif search_type == "vector":
			# Vector-only search
			query_embedding = await embedding_service.get_embedding(request.query)
			results = await typesense_service.vector_search_snippets(query_embedding, request)
		else:
			# Hybrid search - combine text and vector results
			# For now, prioritize text search with vector as fallback
			text_results = await typesense_service.search_snippets(request)

			if text_results['total_found'] < request.limit:
				# Get additional results using vector search
				query_embedding = await embedding_service.get_embedding(request.query)
				vector_results = await typesense_service.vector_search_snippets(query_embedding, request)

				# Simple merge strategy - could be improved with ranking
				combined_results = text_results['results'] + vector_results['results']
				# Remove duplicates based on ID
				seen_ids = set()
				unique_results = []
				for result in combined_results:
					doc_id = result['document']['id']
					if doc_id not in seen_ids:
						seen_ids.add(doc_id)
						unique_results.append(result)
						if len(unique_results) >= request.limit:
							break

				results = {
					'results': unique_results,
					'total_found': len(unique_results),
					'search_time_ms': text_results['search_time_ms'] + vector_results['search_time_ms'],
					'query_by': 'hybrid_text_vector'
				}
			else:
				results = text_results

		return SearchResponse(**results)

	except Exception as e:
		logger.error(f"Search failed: {e}")
		raise HTTPException(status_code=500, detail=str(e))

@router.get("/search-stats")
async def get_search_stats(
	embedding_service: EmbeddingService = Depends(get_embedding_service),
	typesense_service: TypesenseService = Depends(get_typesense_service)
):
	"""Get search and embedding statistics"""
	try:
		cache_stats = embedding_service.get_cache_stats()
		ts_health = await typesense_service.health_check()

		return {
			"embedding_cache": cache_stats,
			"typesense_status": "healthy" if ts_health else "unhealthy",
			"model_version": embedding_service.model_version
		}
	except Exception as e:
		logger.error(f"Failed to get stats: {e}")
		raise HTTPException(status_code=500, detail=str(e))