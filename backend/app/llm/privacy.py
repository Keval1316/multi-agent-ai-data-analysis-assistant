import re
from typing import Any, Dict, List, Union


class DataPrivacyFilter:
    """Heuristic data redaction filter to prevent accidental leakage of sensitive PII to external LLMs."""

    # Regex patterns for sensitive entities
    EMAIL_REGEX = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", re.IGNORECASE)
    PHONE_REGEX = re.compile(r"\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b")
    SSN_REGEX = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
    CREDIT_CARD_REGEX = re.compile(r"\b(?:\d{4}[-\s]?){3}\d{4}\b")
    API_KEY_REGEX = re.compile(r"\b(?:api[_-]?key|secret|token|bearer|password)[=:\s]+[A-Za-z0-9_\-\.]{8,}\b", re.IGNORECASE)

    @classmethod
    def redact_text(cls, text: str) -> str:
        """Redacts sensitive PII from text."""
        if not text or not isinstance(text, str):
            return text

        redacted = cls.EMAIL_REGEX.sub("[EMAIL_REDACTED]", text)
        redacted = cls.PHONE_REGEX.sub("[PHONE_REDACTED]", redacted)
        redacted = cls.SSN_REGEX.sub("[SSN_REDACTED]", redacted)
        redacted = cls.CREDIT_CARD_REGEX.sub("[CARD_REDACTED]", redacted)
        redacted = cls.API_KEY_REGEX.sub("[SECRET_REDACTED]", redacted)
        return redacted

    @classmethod
    def sanitize_sample_values(cls, samples: List[Any]) -> List[Any]:
        """Sanitizes a list of sample values."""
        clean_samples = []
        for val in samples:
            if isinstance(val, str):
                clean_samples.append(cls.redact_text(val))
            else:
                clean_samples.append(val)
        return clean_samples

    @classmethod
    def sanitize_metadata_dict(cls, data: Union[Dict, List, Any]) -> Any:
        """Recursively sanitizes dictionary or list data structures."""
        if isinstance(data, dict):
            return {k: cls.sanitize_metadata_dict(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [cls.sanitize_metadata_dict(item) for item in data]
        elif isinstance(data, str):
            return cls.redact_text(data)
        return data
