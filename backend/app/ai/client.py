import os
import json
import logging
from typing import Type, TypeVar, Optional, Dict, Any
import httpx
from pydantic import BaseModel, ValidationError

from app.services.exceptions import ProcessingError

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


class LLMClient:
    """Environment-based OpenAI-compatible HTTP LLM client with offline deterministic fallback.

    Configured via:
    - LLM_API_KEY (or GEMINI_API_KEY / OPENAI_API_KEY)
    - LLM_MODEL (default: "gpt-4o-mini")
    - LLM_BASE_URL (default: "https://api.openai.com/v1")
    - LLM_TIMEOUT_SECONDS (default: 20.0)
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: float = 20.0,
    ):
        self.api_key = (
            api_key
            or os.getenv("LLM_API_KEY")
            or os.getenv("GEMINI_API_KEY")
            or os.getenv("OPENAI_API_KEY")
        )
        self.model = model or os.getenv("LLM_MODEL", "gpt-4o-mini")
        self.base_url = (base_url or os.getenv("LLM_BASE_URL", "https://api.openai.com/v1")).rstrip("/")
        self.timeout = float(os.getenv("LLM_TIMEOUT_SECONDS", str(timeout)))
        self.is_live = bool(self.api_key and self.api_key.strip() and not self.api_key.startswith("sk-dummy"))

    def generate_structured_output(
        self,
        system_prompt: str,
        user_prompt: str,
        response_schema: Type[T],
        fallback_data: Optional[Dict[str, Any]] = None,
    ) -> T:
        """Execute LLM call and parse structured response into target Pydantic schema, or return fallback."""
        if not self.is_live:
            logger.info("LLMClient running in offline deterministic fallback mode (no API key configured).")
            if fallback_data is not None:
                try:
                    return response_schema.model_validate(fallback_data)
                except ValidationError as err:
                    raise ProcessingError(f"Offline fallback data failed validation: {err}")
            raise ProcessingError("LLM API key not configured and no offline fallback data provided.")

        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.1,
        }

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(url, headers=headers, json=payload)
                if response.status_code != 200:
                    raise ProcessingError(f"LLM provider error (status {response.status_code}): {response.text}")

                res_json = response.json()
                choices = res_json.get("choices", [])
                if not choices:
                    raise ProcessingError("LLM response contained empty choices.")

                content_str = choices[0].get("message", {}).get("content", "")
                parsed_json = json.loads(content_str)
                return response_schema.model_validate(parsed_json)

        except (httpx.TimeoutException, httpx.RequestError) as net_err:
            logger.warning(f"LLM network call failed ({net_err}). Attempting fallback if available.")
            if fallback_data is not None:
                return response_schema.model_validate(fallback_data)
            raise ProcessingError(f"LLM network timeout or connection error: {net_err}")
        except (json.JSONDecodeError, ValidationError) as parse_err:
            logger.warning(f"LLM output validation error ({parse_err}). Attempting fallback if available.")
            if fallback_data is not None:
                return response_schema.model_validate(fallback_data)
            raise ProcessingError(f"Invalid JSON or schema validation error from LLM output: {parse_err}")
        except Exception as e:
            if isinstance(e, ProcessingError):
                raise
            raise ProcessingError(f"LLM processing failure: {e}")
