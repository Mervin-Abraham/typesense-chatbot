import logging
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional

from services.embedding import EmbeddingService
from services.typesense_service import TypesenseService
from services.AIModelService import AIModelService
from main import get_embedding_service, get_typesense_service, verify_token
from config import settings

logger = logging.getLogger(__name__)
router = APIRouter()

# --- Request / Response Schemas ---
class ChatMessage(BaseModel):
	role: str      # "user" or "assistant"
	content: str

class ChatRequest(BaseModel):
	query: str
	history: Optional[List[ChatMessage]] = []
	snippet_type: Optional[str] = "faq"
	category_ids: Optional[List[int]] = []

class ChatResponse(BaseModel):
	answer: str
	contexts: List[str]
	docs: List[dict]

# --- Endpoint ---
@router.post(
	"/chat",
	response_model=ChatResponse,
	dependencies=[Depends(verify_token)] if settings.REQUIRE_AUTH else []
)
async def chat(
	payload: ChatRequest,
	embedding_svc: EmbeddingService = Depends(get_embedding_service),
	typesense_svc: TypesenseService = Depends(get_typesense_service),
	ai_svc: AIModelService = Depends()
):
	"""
	1) Embed the user query
	2) Perform Typesense conversational search
	3) Call LLM with system prompt + contexts
	4) Return answer, contexts, and top_documents
	"""
	try:
		# embed query
		vec = await embedding_svc.get_embedding(payload.query)
		# build typesense payload
		filters = [f"snippet_type:={payload.snippet_type}"]
		if payload.category_ids:
			cats = " || ".join(f"category_ids:={cid}" for cid in payload.category_ids)
			filters.append(f"({cats})")
		conv_req = {
			"q": payload.query,
			"history": [msg.dict() for msg in payload.history],
			"vector_query": f"embedding:([{','.join(map(str, vec))}], k:{settings.DEFAULT_K})",
			"semantic_ranker": True,
			"include_contexts": True,
			"filter_by": " && ".join(filters)
		}
		resp = typesense_svc.client.collections[typesense_svc.collection_name] \
			.documents.conversational_search(conv_req)

		contexts = [c['text'] for c in resp.get('contexts', [])]
		docs     = resp.get('top_documents', [])

		# build prompt
		context_block = "\n\n".join(contexts)
		prompt = (
			f"{ai_svc.system_prompt}\n\n"
			f"---\nRelevant Contexts:\n{context_block}\n---\n"
			f"User: {payload.query}\n"
			f"Assistant:" 
		)
		# get LLM answer
		answer = await ai_svc.get_openai_response(prompt, [])

		return ChatResponse(answer=answer, contexts=contexts, docs=docs)

	except Exception as e:
		logger.error(f"Chat error: {e}")
		raise HTTPException(status_code=500, detail=str(e))