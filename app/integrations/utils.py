from __future__ import annotations

import base64
import io
import json
import mimetypes
import re
from pathlib import Path
from typing import Any, List

from PIL import Image, ImageOps

MAX_AI_IMAGE_DIMENSION = 1600
AI_JPEG_QUALITY = 82


def resize_for_ai(path: Path) -> bytes:
    """
    Open image, auto-rotate, resize so longest side <= MAX_AI_IMAGE_DIMENSION,
    return optimized JPEG bytes. Always returns JPEG regardless of source format.
    """
    with Image.open(path) as img:
        img = ImageOps.exif_transpose(img)
        if img.mode not in ("RGB",):
            img = img.convert("RGB")
        w, h = img.size
        longest = max(w, h)
        if longest > MAX_AI_IMAGE_DIMENSION:
            scale = MAX_AI_IMAGE_DIMENSION / float(longest)
            img = img.resize((int(w * scale), int(h * scale)), Image.Resampling.LANCZOS)
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=AI_JPEG_QUALITY, optimize=True)
        return buf.getvalue()


def guess_mime_type(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in {".jpg", ".jpeg"}:
        return "image/jpeg"
    if suffix == ".png":
        return "image/png"
    if suffix == ".webp":
        return "image/webp"
    if suffix in {".heic", ".heif"}:
        return "image/heic"
    guessed, _ = mimetypes.guess_type(str(path))
    return guessed or "application/octet-stream"


def build_image_content(image_paths: list[Path | str]) -> list[dict[str, Any]]:
    content: list[dict[str, Any]] = []
    for path_or_str in image_paths:
        path = Path(path_or_str) if isinstance(path_or_str, str) else path_or_str
        img_bytes = resize_for_ai(path)
        b64 = base64.b64encode(img_bytes).decode("utf-8")
        content.append(
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{b64}"
                },
            }
        )
    return content


def parse_model_json(text: str) -> dict[str, Any]:
    def try_load(candidate: str) -> dict[str, Any] | None:
        try:
            parsed = json.loads(candidate)
        except json.JSONDecodeError:
            return None
        return parsed if isinstance(parsed, dict) else None

    def repair_json(candidate: str) -> str:
        repaired = candidate
        repaired = re.sub(r",(\s*[}\]])", r"\1", repaired)
        repaired = re.sub(
            r'([{,]\s*)([A-Za-z_][A-Za-z0-9_]*)(\s*:)',
            r'\1"\2"\3',
            repaired,
        )
        return repaired

    raw = text.strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", raw, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```$", "", cleaned)

    for candidate in (cleaned, repair_json(cleaned)):
        parsed = try_load(candidate)
        if parsed is not None:
            return parsed

    match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if match:
        extracted = match.group(0)
        for candidate in (extracted, repair_json(extracted)):
            parsed = try_load(candidate)
            if parsed is not None:
                return parsed

    raise ValueError(f"Could not parse model response as JSON: {raw}")


def normalize_option(opt: dict[str, Any], rank: int) -> dict[str, Any]:
    return {
        "rank": rank,
        "identification": str(opt.get("identification", "")).strip(),
        "confidence_note": str(opt.get("confidence_note", "")).strip(),
        "material_notes": str(opt.get("material_notes", "")).strip(),
        "mark_notes": str(opt.get("mark_notes", "")).strip(),
        "title": str(opt.get("title", "")).strip(),
        "description": str(opt.get("description", "")).strip(),
        "category": str(opt.get("category", "Other")).strip() or "Other",
        "condition_summary": str(opt.get("condition_summary", "")).strip(),
        "low_estimate": str(opt.get("low_estimate", "")).strip(),
        "high_estimate": str(opt.get("high_estimate", "")).strip(),
        "keywords": str(opt.get("keywords", "")).strip(),
        "platform_data": opt.get("platform_data", {})
    }


def blank_option(rank: int) -> dict[str, str | int]:
    return {
        "rank": rank,
        "identification": "",
        "confidence_note": "",
        "material_notes": "",
        "mark_notes": "",
        "title": "",
        "description": "",
        "category": "Other",
        "condition_summary": "",
        "low_estimate": "",
        "high_estimate": "",
        "keywords": "",
        "platform_data": {}
    }


def normalize_output(data: dict[str, Any]) -> dict[str, list[dict[str, str | int]]]:
    raw_options = data.get("options", [])
    if not isinstance(raw_options, list):
        raw_options = []

    normalized: list[dict[str, str | int]] = []
    for i, opt in enumerate(raw_options[:3], start=1):
        if isinstance(opt, dict):
            normalized.append(normalize_option(opt, i))

    return {"options": normalized}