import json
from typing import List, Dict, Type, TypeVar
from pydantic import BaseModel, ValidationError
from google import genai
from google.genai import types
from backend.app.llm.base import LLMProvider
from backend.app.core.exceptions import LLMProviderError
from backend.app.core.logging import logger

T = TypeVar("T", bound=BaseModel)


class GeminiProvider(LLMProvider):
    """Google Gemini LLM provider using the google-genai SDK."""

    def __init__(self, api_key: str, model: str = "gemini-2.5-flash"):
        self.api_key = api_key
        self.model = model
        self.client = genai.Client(api_key=api_key)

    @property
    def provider_name(self) -> str:
        return f"gemini:{self.model}"

    def generate_structured(
        self,
        messages: List[Dict[str, str]],
        response_model: Type[T],
        temperature: float = 0.1,
    ) -> T:
        try:
            # Combine messages into system instruction + user contents
            system_instruction = (
                "You are an expert AI data analyst. You MUST output ONLY a valid JSON object matching the requested schema. "
                "Do NOT include markdown formatting (like ```json ... ```). Return raw JSON only."
            )

            prompt_parts = []
            for msg in messages:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                prompt_parts.append(f"[{role.upper()}]:\n{content}")

            full_prompt = "\n\n".join(prompt_parts)

            config = types.GenerateContentConfig(
                temperature=temperature,
                response_mime_type="application/json",
                response_schema=response_model,
                system_instruction=system_instruction
            )

            response = self.client.models.generate_content(
                model=self.model,
                contents=full_prompt,
                config=config,
            )

            raw_text = response.text or "{}"
            return response_model.model_validate_json(raw_text)

        except ValidationError as ve:
            logger.warning(f"Gemini structured validation failed: {str(ve)}")
            raise LLMProviderError(f"Gemini structured validation failed: {str(ve)}")
        except Exception as e:
            logger.error(f"Gemini provider API error: {str(e)}")
            raise LLMProviderError(f"Gemini API error: {str(e)}")
