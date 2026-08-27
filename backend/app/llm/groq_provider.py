import json
from typing import List, Dict, Type, TypeVar
from pydantic import BaseModel, ValidationError
from groq import Groq
from backend.app.llm.base import LLMProvider
from backend.app.core.exceptions import LLMProviderError
from backend.app.core.logging import logger

T = TypeVar("T", bound=BaseModel)


class GroqProvider(LLMProvider):
    """Groq LLM provider implementing JSON structured output mode."""

    def __init__(self, api_key: str, model: str = "llama-3.3-70b-versatile"):
        self.api_key = api_key
        self.model = model
        self.client = Groq(api_key=api_key)

    @property
    def provider_name(self) -> str:
        return f"groq:{self.model}"

    def generate_structured(
        self,
        messages: List[Dict[str, str]],
        response_model: Type[T],
        temperature: float = 0.1,
    ) -> T:
        try:
            # Inject schema requirement into system prompt
            schema_json = json.dumps(response_model.model_json_schema(), indent=2)
            system_instruction = (
                f"You are an expert AI data analyst. You MUST output ONLY a valid JSON object matching the following JSON Schema:\n"
                f"```json\n{schema_json}\n```\n"
                f"Do NOT include any markdown formatting, backticks, or explanatory text. Return ONLY the raw JSON object."
            )

            formatted_messages = [{"role": "system", "content": system_instruction}] + [
                {"role": m["role"], "content": m["content"]} for m in messages
            ]

            response = self.client.chat.completions.create(
                model=self.model,
                messages=formatted_messages,  # type: ignore
                temperature=temperature,
                response_format={"type": "json_object"},
            )

            content = response.choices[0].message.content or "{}"
            return response_model.model_validate_json(content)

        except ValidationError as ve:
            logger.warning(f"Groq structured validation failed: {str(ve)}")
            raise LLMProviderError(f"Groq structured validation failed: {str(ve)}")
        except Exception as e:
            logger.error(f"Groq provider API error: {str(e)}")
            raise LLMProviderError(f"Groq API error: {str(e)}")
