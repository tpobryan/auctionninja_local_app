from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

import google.generativeai as genai
from PIL import Image

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
        genai.configure(api_key=api_key or settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel(model or "gemini-1.5-flash")

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

        content = [prompt]
        for path in image_paths:
            path = Path(path)
            img = Image.open(path)
            content.append(img)

        response = self.model.generate_content(content)

        raw_content = response.text
        data = parse_model_json(raw_content)
        return normalize_output(data)
