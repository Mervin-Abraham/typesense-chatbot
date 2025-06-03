from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class SnippetInput(BaseModel):
	id: str
	title: str
	description: str
	created_on: datetime
	snippet_type: str
	published: bool
	product_category_ids: Optional[List[int]] = []

class SnippetWithEmbedding(SnippetInput):
	embedding: List[float]
	model_version: str

class EmbedRequest(BaseModel):
	text: str

class EmbedResponse(BaseModel):
	embedding: List[float]
	model_version: str
	processing_time_ms: float

class IndexRequest(BaseModel):
	snippet: SnippetInput

class IndexResponse(BaseModel):
	success: bool
	snippet_id: str
	message: str
	processing_time_ms: float

class BatchIndexRequest(BaseModel):
	snippets: List[SnippetInput]
	batch_size: Optional[int] = 10

class BatchIndexResponse(BaseModel):
	success: bool
	total_processed: int
	successful: int
	failed: int
	errors: List[str]
	processing_time_ms: float

class SearchRequest(BaseModel):
	query: str
	limit: Optional[int] = 10
	snippet_type: Optional[str] = None
	published_only: Optional[bool] = True
	category_ids: Optional[List[int]] = None

class SearchResponse(BaseModel):
	results: List[Dict[str, Any]]
	total_found: int
	search_time_ms: float
	query_by: str