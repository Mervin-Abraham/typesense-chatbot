import time
import logging
from typing import List, Dict, Any, Optional
import typesense
from models.schemas import SnippetWithEmbedding, SearchRequest
from config import settings

logger = logging.getLogger(__name__)

class TypesenseService:
	def __init__(self):
		self.client = typesense.Client({
			'nodes': [{
				'host': settings.TYPESENSE_HOST,
				'port': settings.TYPESENSE_PORT,
				'protocol': settings.TYPESENSE_PROTOCOL
			}],
			'api_key': settings.TYPESENSE_API_KEY,
			'connection_timeout_seconds': 10
		})
		self.collection_name = settings.TYPESENSE_COLLECTION

	async def health_check(self) -> bool:
		"""Check Typesense connection"""
		try:
			health = self.client.operations.health_check()
			return health['ok'] == True
		except Exception as e:
			logger.error(f"Typesense health check failed: {e}")
			return False

	async def ensure_collection_exists(self):
		"""Ensure the snippets collection exists with proper schema"""
		schema = {
			'name': self.collection_name,
			'fields': [
				{'name': 'id', 'type': 'string'},
				{'name': 'title', 'type': 'string'},
				{'name': 'description', 'type': 'string'},
				{'name': 'created_on', 'type': 'int64'},
				{'name': 'snippet_type', 'type': 'string', 'facet': True},
				{'name': 'published', 'type': 'bool', 'facet': True},
				{'name': 'category_ids', 'type': 'int32[]', 'facet': True, 'optional': True},
				{'name': 'embedding', 'type': f'float[{settings.EMBEDDING_DIMENSION}]'},
				{'name': 'model_version', 'type': 'string', 'facet': True}
			]
		}

		try:
			# Check if collection exists
			self.client.collections[self.collection_name].retrieve()
			logger.info(f"Collection {self.collection_name} already exists")
		except typesense.exceptions.ObjectNotFound:
			# Create collection
			self.client.collections.create(schema)
			logger.info(f"Created collection {self.collection_name}")
		except Exception as e:
			logger.error(f"Error checking/creating collection: {e}")
			raise

	async def upsert_snippet(self, snippet: SnippetWithEmbedding) -> bool:
		"""Upsert a snippet with embedding to Typesense"""
		try:
			await self.ensure_collection_exists()

			document = {
				'id': snippet.id,
				'title': snippet.title,
				'description': snippet.description,
				'created_on': int(snippet.created_on.timestamp()),
				'snippet_type': snippet.snippet_type,
				'published': snippet.published,
				'category_ids': snippet.product_category_ids or [],
				'embedding': snippet.embedding,
				'model_version': snippet.model_version
			}

			self.client.collections[self.collection_name].documents.upsert(document)
			logger.info(f"Upserted snippet {snippet.id}")
			return True

		except Exception as e:
			logger.error(f"Failed to upsert snippet {snippet.id}: {e}")
			return False

	async def search_snippets(self, request: SearchRequest) -> Dict[str, Any]:
		"""Perform hybrid search on snippets"""
		start_time = time.time()

		try:
			# Build search parameters
			search_params = {
				'q': request.query,
				'query_by': 'title,description',
				'per_page': request.limit,
				'page': 1
			}

			# Add filters
			filters = []
			if request.published_only:
				filters.append('published:=true')
			if request.snippet_type:
				filters.append(f'snippet_type:={request.snippet_type}')
			if request.category_ids:
				category_filter = ' || '.join([f'category_ids:={cat_id}' for cat_id in request.category_ids])
				filters.append(f'({category_filter})')

			if filters:
				search_params['filter_by'] = ' && '.join(filters)

			# Perform search
			results = self.client.collections[self.collection_name].documents.search(search_params)

			search_time = (time.time() - start_time) * 1000

			return {
				'results': results['hits'],
				'total_found': results['found'],
				'search_time_ms': search_time,
				'query_by': search_params['query_by']
			}

		except Exception as e:
			logger.error(f"Search failed: {e}")
			raise

	async def vector_search_snippets(self, query_embedding: List[float], request: SearchRequest) -> Dict[str, Any]:
		"""Perform vector similarity search"""
		start_time = time.time()

		try:
			# Build search parameters for vector search
			search_params = {
				'q': '*',
				'vector_query': f'embedding:([{",".join(map(str, query_embedding))}], k:{request.limit})',
				'per_page': request.limit,
				'page': 1
			}

			# Add filters (same as text search)
			filters = []
			if request.published_only:
				filters.append('published:=true')
			if request.snippet_type:
				filters.append(f'snippet_type:={request.snippet_type}')
			if request.category_ids:
				category_filter = ' || '.join([f'category_ids:={cat_id}' for cat_id in request.category_ids])
				filters.append(f'({category_filter})')

			if filters:
				search_params['filter_by'] = ' && '.join(filters)

			# Perform vector search
			results = self.client.collections[self.collection_name].documents.search(search_params)

			search_time = (time.time() - start_time) * 1000

			return {
				'results': results['hits'],
				'total_found': results['found'],
				'search_time_ms': search_time,
				'query_by': 'vector_similarity'
			}

		except Exception as e:
			logger.error(f"Vector search failed: {e}")
			raise

	async def delete_snippet(self, snippet_id: str) -> bool:
		"""Delete a snippet from Typesense"""
		try:
			self.client.collections[self.collection_name].documents[snippet_id].delete()
			logger.info(f"Deleted snippet {snippet_id}")
			return True
		except Exception as e:
			logger.error(f"Failed to delete snippet {snippet_id}: {e}")
			return False