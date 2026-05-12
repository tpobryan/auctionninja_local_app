import os
import json
from pathlib import Path
from typing import Any, Dict, List
from flask import current_app
from ..database import get_platform_credentials, update_platform_status
from .etsy import EtsyIntegration
from .ebay import EbayIntegration

# Registry of platform integrations
PLATFORMS = {
    "etsy": EtsyIntegration(),
    "ebay": EbayIntegration()
}

def process_platform_publishing(lot_number: int, form: Dict[str, Any], image_folder: str):
    """
    Deprecated: Now we initialize status and let the user trigger publish manually.
    """
    pass

def publish_to_platform(platform_id: str, lot_number: int, form: Dict[str, Any], image_folder: str, existing_status: Dict[str, Any] = None):
    """Orchestrates the publishing for a specific platform with detailed tracking."""
    integration = PLATFORMS.get(platform_id)
    if not integration:
        return {"success": False, "error": f"Platform {platform_id} not supported"}
    
    # 1. Get credentials
    creds = get_platform_credentials(platform_id)
    if not creds or not creds.get("access_token"):
        update_platform_status(lot_number, platform_id, "failed", last_error="Platform not connected", last_error_code="AUTH_REQUIRED", stage="validating")
        return {"success": False, "error": f"{platform_id} is not connected"}

    # 2. Prepare item data
    from ..config import settings
    uploads_dir = settings.UPLOADS_DIR
    final_dir = uploads_dir / image_folder
    image_paths = []
    if final_dir.exists():
        image_paths = sorted([str(p) for p in final_dir.iterdir() if p.is_file() and p.suffix.lower() in [".jpg", ".jpeg", ".png"]])

    item_data = {
        **form,
        "access_token": creds["access_token"],
        "shop_id": creds["settings"].get("shop_id"),
        "image_paths": image_paths,
        "remote_id": existing_status.get("remote_id") if existing_status else None
    }

    # 3. Mark as publishing
    update_platform_status(lot_number, platform_id, "publishing", stage="starting", increment_attempt=True)

    # 4. Call integration
    try:
        res = integration.publish_listing(lot_number, item_data)
        
        if res.get("success"):
            update_platform_status(
                lot_number, 
                platform_id, 
                "published", 
                remote_id=res.get("listing_id"),
                remote_url=res.get("remote_url"),
                last_error="",
                last_error_code="",
                stage="complete"
            )
            return {"success": True, "listing_id": res.get("listing_id")}
        else:
            status = "failed"
            if res.get("partial"):
                status = "partial_success"
            
            update_platform_status(
                lot_number, 
                platform_id, 
                status, 
                remote_id=res.get("listing_id"),
                last_error=res.get("error", "Unknown error"),
                last_error_code=res.get("error_code", ""),
                stage=res.get("stage", "unknown")
            )
            return {"success": False, "error": res.get("error"), "partial": res.get("partial")}
            
    except Exception as exc:
        current_app.logger.exception(f"Exception during {platform_id} publishing")
        update_platform_status(lot_number, platform_id, "failed", last_error=str(exc), stage="exception")
        return {"success": False, "error": str(exc)}
