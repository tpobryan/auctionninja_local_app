from __future__ import annotations

from typing import List

from ..config import settings
from ..integrations.base import AIService
from ..integrations.openai import OpenAIClient
from ..integrations.claude import ClaudeClient
from ..integrations.gemini import GeminiClient


def get_ai_services() -> List[AIService]:
    services: List[AIService] = []

    if settings.OPENAI_API_KEY and settings.OPENAI_API_KEY != "dummy-key-if-missing":
        services.append(OpenAIClient())

    if settings.CLAUDE_API_KEY and settings.CLAUDE_API_KEY != "dummy-key-if-missing":
        services.append(ClaudeClient())

    if settings.GEMINI_API_KEY and settings.GEMINI_API_KEY != "dummy-key-if-missing":
        services.append(GeminiClient())

    return services
