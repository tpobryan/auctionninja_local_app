from __future__ import annotations

import base64
from pathlib import Path
from typing import Any, Dict, List

import anthropic

from ..config import settings
from .base import AIService
from .utils import (
    guess_mime_type,
    parse_model_json,
    normalize_output,
)

# TODO: The prompt is very OpenAI specific. We will need to generalize it.
from .openai import MASTER_INSTRUCTION, MARKETPLACE_INSTRUCTION


class ClaudeClient(AIService):
    def __init__(self, api_key: str | None = None, model: str | None = None) -> None:
        self.client = anthropic.Anthropic(api_key=api_key or settings.CLAUDE_API_KEY)
        self.model = model or "claude-opus-4-5"

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

        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt}
                ],
            }
        ]

        for path in image_paths:
            path = Path(path)
            mime_type = guess_mime_type(path)
            with open(path, "rb") as f:
                image_data = base64.b64encode(f.read()).decode("utf-8")
            
            messages[0]["content"].insert(0, 
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": mime_type,
                        "data": image_data,
                    },
                }
            )

        response = self.client.messages.create(
            model=self.model,
            max_tokens=2000,
            messages=messages,
        )

        raw_content = response.content[0].text
        data = parse_model_json(raw_content)
        return normalize_output(data)
