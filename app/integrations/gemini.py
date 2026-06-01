from __future__ import annotations

import base64
from pathlib import Path
from typing import Any, Dict, List

from google import genai
from google.genai import types

from ..config import settings
from .base import AIService
from .utils import (
    parse_model_json,
    normalize_output,
)

# TODO: The prompt is very OpenAI specific. We will need to generalize it.
from .openai import MASTER_INSTRUCTION, MARKETPLACE_INSTRUCTION


class GeminiClient(AIService):
    def __init__(self, api_key: str | None = None, model: str | None = None) -> None:
        self.client = genai.Client(api_key=api_key or settings.GEMINI_API_KEY)
        self.model_name = model or "gemini-2.0-flash"

    def generate_options(
        self,
        image_paths: list[Path | str],
        seller_notes: str = "",
        strategy: str = "auction",
    ) -> Dict[str, List[Dict[str, Any]]]:
        if not image_paths:
            raise ValueError("No images provided.")

        seller_notes = seller_notes.strip()

        master_instruction = MASTER_INSTRUCTION
        if strategy == "retail":
            master_instruction = MARKETPLACE_INSTRUCTION

        prompt = f"""
{master_instruction}

Task:
Generate the most plausible InventoryManager listing options from the item photos and optional seller notes.
- If you are highly certain about the item, return exactly ONE option.
- If the item is ambiguous or could be multiple things, return 2-3 distinct options.

Seller notes:
{seller_notes if seller_notes else "None provided."}

Use seller notes only as supplied facts.
Do not invent missing details.
If the photos are unclear, use cautious wording.
Prefer practical resale phrasing.

Return only valid JSON.
""".strip()

        parts: list[Any] = [prompt]
        for path in image_paths:
            path = Path(path)
            mime_type = "image/jpeg"
            suffix = path.suffix.lower()
            if suffix == ".png":
                mime_type = "image/png"
            elif suffix == ".webp":
                mime_type = "image/webp"
            elif suffix == ".gif":
                mime_type = "image/gif"
            image_bytes = path.read_bytes()
            parts.append(types.Part.from_bytes(data=image_bytes, mime_type=mime_type))

        response = self.client.models.generate_content(
            model=self.model_name,
            contents=parts,
        )

        raw_content = response.text
        data = parse_model_json(raw_content)
        return normalize_output(data)
