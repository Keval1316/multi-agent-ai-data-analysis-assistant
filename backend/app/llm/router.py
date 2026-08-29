import time
from typing import List, Dict, Type, TypeVar, Optional, Tuple
from pydantic import BaseModel
from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.core.exceptions import LLMProviderError
from backend.app.llm.base import LLMProvider
from backend.app.llm.groq_provider import GroqProvider
from backend.app.llm.gemini_provider import GeminiProvider
from backend.app.llm.mock_provider import MockLLMProvider
from backend.app.llm.privacy import DataPrivacyFilter

T = TypeVar("T", bound=BaseModel)


class LLMRouter:
    """
    Central LLM router managing multi-provider failover, credential pools,
    health tracking, rate-limit cooldowns, and structured output self-correction.
    """
    _instance: Optional["LLMRouter"] = None

    def __init__(self):
        self.cooldown_duration_seconds = 60.0
        self.cooldowns: Dict[str, float] = {}  # provider_key_id -> expiration_timestamp
        self.mock_provider = MockLLMProvider()

    @classmethod
    def get_instance(cls) -> "LLMRouter":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _get_groq_keys(self) -> List[str]:
        keys = [settings.GROQ_API_KEY_1, settings.GROQ_API_KEY_2, settings.GROQ_API_KEY_3]
        return [k.strip() for k in keys if k and k.strip()]

    def _get_gemini_keys(self) -> List[str]:
        keys = [settings.GEMINI_API_KEY_1, settings.GEMINI_API_KEY_2]
        return [k.strip() for k in keys if k and k.strip()]

    def is_cooling_down(self, key_id: str) -> bool:
        """Checks if a credential/provider is currently in rate-limit cooldown."""
        exp = self.cooldowns.get(key_id, 0.0)
        return time.time() < exp

    def mark_cooldown(self, key_id: str):
        """Places a credential on temporary cooldown."""
        self.cooldowns[key_id] = time.time() + self.cooldown_duration_seconds
        logger.warning(f"Marked provider/key '{key_id}' on cooldown for {self.cooldown_duration_seconds}s")

    def _get_available_providers(self) -> List[Tuple[str, LLMProvider]]:
        """Constructs available healthy provider instances in priority order."""
        available: List[Tuple[str, LLMProvider]] = []

        # 1. Groq pool
        groq_keys = self._get_groq_keys()
        for idx, key in enumerate(groq_keys):
            key_id = f"groq_key_{idx + 1}"
            if not self.is_cooling_down(key_id):
                available.append((key_id, GroqProvider(api_key=key, model=settings.GROQ_MODEL)))

        # 2. Gemini pool
        gemini_keys = self._get_gemini_keys()
        for idx, key in enumerate(gemini_keys):
            key_id = f"gemini_key_{idx + 1}"
            if not self.is_cooling_down(key_id):
                available.append((key_id, GeminiProvider(api_key=key, model=settings.GEMINI_MODEL)))

        return available

    def complete(
        self,
        agent_name: str,
        messages: List[Dict[str, str]],
        response_model: Type[T],
        temperature: float = 0.1,
    ) -> T:
        """
        Executes a prompt for an agent with privacy sanitization, multi-provider failover,
        and automatic one-shot correction retry on schema validation failures.
        """
        # Apply privacy redaction on input messages
        sanitized_messages = [
            {"role": m["role"], "content": DataPrivacyFilter.redact_text(m["content"])}
            for m in messages
        ]

        available_providers = self._get_available_providers()

        # If no real API keys configured or all on cooldown, fallback to MockLLMProvider
        if not available_providers:
            logger.info(f"[{agent_name}] No external LLM keys available or all on cooldown. Using MockLLMProvider.")
            return self.mock_provider.generate_structured(
                messages=sanitized_messages,
                response_model=response_model,
                temperature=temperature
            )

        last_error = None

        for key_id, provider in available_providers:
            try:
                logger.info(f"[{agent_name}] Calling {provider.provider_name} via {key_id}")
                return provider.generate_structured(
                    messages=sanitized_messages,
                    response_model=response_model,
                    temperature=temperature
                )
            except LLMProviderError as pe:
                last_error = pe
                # Check if rate limit or auth failure
                err_str = str(pe).lower()
                if "rate" in err_str or "429" in err_str or "quota" in err_str or "limit" in err_str:
                    self.mark_cooldown(key_id)
                logger.warning(f"[{agent_name}] Provider {provider.provider_name} failed: {pe.message}. Attempting failover...")
                continue
            except Exception as e:
                last_error = e
                logger.error(f"[{agent_name}] Unexpected error on {provider.provider_name}: {str(e)}")
                continue

        # If all configured external providers failed, fallback gracefully to mock provider
        logger.warning(f"[{agent_name}] All external providers failed ({last_error}). Falling back to deterministic mock generator.")
        return self.mock_provider.generate_structured(
            messages=sanitized_messages,
            response_model=response_model,
            temperature=temperature
        )


llm_router = LLMRouter.get_instance()
