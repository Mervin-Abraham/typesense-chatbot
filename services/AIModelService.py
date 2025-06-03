import logging
import openai
import google.generativeai as genai
from config import settings

logger = logging.getLogger(__name__)

class AIModelService:
	"""
	Service to interact with AI models: OpenAI and Google Gemini.
	Provides methods to generate chat completions based on system prompt and conversation history.
	"""
	def __init__(self):
		# Initialize OpenAI API key
		openai.api_key = settings.OPENAI_API_KEY
		# Initialize Google Gemini client if key provided
		self.genai = None
		if settings.GEMINI_API_KEY:
			try:
				self.genai = genai.configure(api_key=settings.GEMINI_API_KEY)
				logger.info("Google Gemini client initialized")
			except Exception as e:
				logger.error(f"Failed to initialize Google Gemini: {e}")
		# System prompt from settings
		self.system_prompt = settings.SYSTEM_PROMPT

	async def get_openai_response(self, user_message: str, conversation_history: list) -> str:
		"""
		Generate a response from OpenAI chat completion API.
		"""
		# Build message list
		messages = [{"role": "system", "content": self.system_prompt}]
		for msg in conversation_history:
			messages.append({"role": msg.get("role"), "content": msg.get("content")})
		messages.append({"role": "user", "content": user_message})

		try:
			resp = await openai.ChatCompletion.acreate(
				model=settings.OPENAI_MODEL,
				messages=messages,
				temperature=settings.OPENAI_TEMPERATURE,
				max_tokens=settings.OPENAI_MAX_TOKENS
			)
			return resp.choices[0].message.content
		except Exception as e:
			logger.error(f"OpenAI generation error: {e}")
			raise

	async def get_gemini_response(self, user_message: str, conversation_history: list) -> str:
		"""
		Generate a response from Google Gemini API if initialized.
		"""
		if not self.genai:
			raise RuntimeError("Gemini client not configured")

		# Build history in Gemini format
		history = []
		for msg in conversation_history:
			history.append({"role": msg.get("role"), "content": msg.get("content")})

		try:
			model = genai.GenerativeModel('gemini-2.0-flash')
			response = model.generate_content(user_message)
			print(response.text)
			response = await self.genie.chat.complete(
				model=settings.GEMINI_MODEL,
				prompt=user_message,
				context=history,
				temperature=settings.GEMINI_TEMPERATURE,
				max_output_tokens=settings.GEMINI_MAX_TOKENS
			)
			return response.generated_text
		except Exception as e:
			logger.error(f"Gemini generation error: {e}")
			raise

	async def get_response(self, user_message: str, conversation_history: list) -> str:
		"""
		Try OpenAI first, fallback to Gemini if configured.
		"""
		try:
			return await self.get_openai_response(user_message, conversation_history)
		except Exception:
			if self.genie:
				return await self.get_gemini_response(user_message, conversation_history)
			raise
