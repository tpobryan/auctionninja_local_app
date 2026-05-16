import os
import requests
import base64
import json
from typing import Any, Dict
from .base import PlatformIntegration
from ..config import settings

class EbayIntegration(PlatformIntegration):
    """
    eBay Platform Integration (RESTful Inventory API)
    """

    def __init__(self):
        self.client_id = settings.EBAY_CLIENT_ID
        self.client_secret = settings.EBAY_CLIENT_SECRET
        self.runame = settings.EBAY_RUNAME
        self.redirect_uri = settings.EBAY_REDIRECT_URI
        self.api_base = "https://api.ebay.com/sell/inventory/v1"
        self.auth_base = "https://auth.ebay.com/oauth2/authorize"
        self.token_url = "https://api.ebay.com/identity/v1/oauth2/token"
        self.account_base = "https://api.ebay.com/sell/account/v1"

    @property
    def platform_id(self) -> str:
        return "ebay"

    def _get_headers(self, access_token: str = None) -> Dict[str, str]:
        """Helper to generate eBay API headers."""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Content-Language": "en-US"
        }
        if access_token:
            headers["Authorization"] = f"Bearer {access_token}"
        return headers

    def _refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """Exchanges a refresh token for a new access token."""
        auth_str = f"{self.client_id}:{self.client_secret}"
        b64_auth = base64.b64encode(auth_str.encode()).decode()
        
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": f"Basic {b64_auth}"
        }
        
        data = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "scope": " ".join([
                "https://api.ebay.com/oauth/api_scope/sell.inventory",
                "https://api.ebay.com/oauth/api_scope/sell.marketing",
                "https://api.ebay.com/oauth/api_scope/sell.account"
            ])
        }
        
        response = requests.post(self.token_url, headers=headers, data=data)
        if response.status_code == 200:
            return response.json()
        return {"error": f"eBay token refresh failed: {response.text}"}

    def get_fulfillment_policies(self, access_token: str, marketplace_id: str = "EBAY_US") -> list[Dict[str, Any]]:
        url = f"{self.account_base}/fulfillment_policy?marketplace_id={marketplace_id}"
        response = requests.get(url, headers=self._get_headers(access_token))
        if response.status_code == 200:
            return response.json().get("fulfillmentPolicies", [])
        return []

    def get_payment_policies(self, access_token: str, marketplace_id: str = "EBAY_US") -> list[Dict[str, Any]]:
        url = f"{self.account_base}/payment_policy?marketplace_id={marketplace_id}"
        response = requests.get(url, headers=self._get_headers(access_token))
        if response.status_code == 200:
            return response.json().get("paymentPolicies", [])
        return []

    def get_return_policies(self, access_token: str, marketplace_id: str = "EBAY_US") -> list[Dict[str, Any]]:
        url = f"{self.account_base}/return_policy?marketplace_id={marketplace_id}"
        response = requests.get(url, headers=self._get_headers(access_token))
        if response.status_code == 200:
            return response.json().get("returnPolicies", [])
        return []

    def get_merchant_locations(self, access_token: str) -> list[Dict[str, Any]]:
        url = f"{self.api_base}/location"
        response = requests.get(url, headers=self._get_headers(access_token))
        if response.status_code == 200:
            return response.json().get("locations", [])
        return []

    def authenticate(self, request_args: Dict[str, Any], session_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Handles eBay OAuth2 flow.
        """
        code = request_args.get("code")
        state = request_args.get("state")

        if not code:
            # Phase 1: Redirect to eBay for consent
            import secrets
            state = secrets.token_urlsafe(16)
            
            # Scopes for Inventory API
            scopes = [
                "https://api.ebay.com/oauth/api_scope/sell.inventory",
                "https://api.ebay.com/oauth/api_scope/sell.marketing",
                "https://api.ebay.com/oauth/api_scope/sell.account"
            ]
            
            auth_url = (
                f"{self.auth_base}?"
                f"client_id={self.client_id}&"
                f"redirect_uri={self.runame}&"
                f"response_type=code&"
                f"state={state}&"
                f"scope={' '.join(scopes)}"
            )
            
            return {
                "redirect_url": auth_url,
                "pkce": {"state": state} # We use this to verify the state on return
            }

        # Phase 2: Exchange code for token
        # Note: eBay requires Basic Auth with Base64(client_id:client_secret)
        auth_str = f"{self.client_id}:{self.client_secret}"
        b64_auth = base64.b64encode(auth_str.encode()).decode()
        
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": f"Basic {b64_auth}"
        }
        
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": self.runame
        }
        
        response = requests.post(self.token_url, headers=headers, data=data)
        
        if response.status_code == 200:
            token_data = response.json()
            return {
                "access_token": token_data.get("access_token"),
                "refresh_token": token_data.get("refresh_token"),
                "settings": {
                    "expires_in": token_data.get("expires_in"),
                    "refresh_token_expires_in": token_data.get("refresh_token_expires_in")
                }
            }
        else:
            return {"error": f"eBay token exchange failed: {response.text}"}

    def publish_listing(self, lot_number: int, item_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Publishes the listing to eBay using the Inventory API (3-step flow).
        Returns a dict with success status and any error info.
        """
        access_token = item_data.get("access_token")
        if not access_token:
            return {"success": False, "error": "Missing eBay access token", "stage": "validating"}

        # 1. Validation
        validation = self.validate_listing_data(item_data)
        if not validation["success"]:
            return validation

        sku = f"lot_{lot_number}"
        headers = self._get_headers(access_token)
        
        # 2. Step 1: Create or Replace Inventory Item
        # URL: /inventory_item/{sku}
        item_payload = {
            "product": {
                "title": item_data.get("eBay SEO Title") or item_data.get("Title"),
                "description": item_data.get("Description"),
                "aspects": item_data.get("aspects", {}),
                "imageUrls": item_data.get("image_urls", [])
            },
            "condition": item_data.get("eBay Condition") or "USED_EXCELLENT",
            "availability": {
                "shipToLocationAvailability": {
                    "quantity": int(item_data.get("Quantity", 1))
                }
            }
        }
        
        item_url = f"{self.api_base}/inventory_item/{sku}"
        item_res = requests.put(item_url, headers=headers, json=item_payload)
        
        if item_res.status_code not in [200, 204]:
            return {"success": False, "error": f"eBay Item Creation Failed: {item_res.text}", "stage": "inventory_item"}

        # 3. Step 2: Create Offer
        # We need a merchantLocationKey. Let's fetch and use the first one, or use 'default'.
        locations = self.get_merchant_locations(access_token)
        location_key = "default"
        if locations:
            location_key = locations[0].get("merchantLocationKey", "default")
        
        offer_payload = {
            "sku": sku,
            "marketplaceId": item_data.get("marketplace_id") or "EBAY_US",
            "format": "FIXED_PRICE",
            "listingPolicies": {
                "fulfillmentPolicyId": item_data.get("eBay Fulfillment Policy ID"),
                "paymentPolicyId": item_data.get("eBay Payment Policy ID"),
                "returnPolicyId": item_data.get("eBay Return Policy ID")
            },
            "categoryId": item_data.get("eBay Category ID"),
            "merchantLocationKey": location_key,
            "pricingSummary": {
                "price": {
                    "value": str(item_data.get("Price")),
                    "currency": "USD"
                }
            }
        }
        
        offer_url = f"{self.api_base}/offer"
        offer_res = requests.post(offer_url, headers=headers, json=offer_payload)
        
        if offer_res.status_code not in [200, 201]:
            # If offer already exists for this SKU, we might need to find it and update it, 
            # or just handle the error. For now, let's report the error.
            return {"success": False, "error": f"eBay Offer Creation Failed: {offer_res.text}", "stage": "create_offer"}
            
        offer_id = offer_res.json().get("offerId")
        
        # 4. Step 3: Publish Offer
        publish_url = f"{self.api_base}/offer/{offer_id}/publish"
        publish_res = requests.post(publish_url, headers=headers)
        
        if publish_res.status_code in [200, 204]:
            res_data = publish_res.json() if publish_res.text else {}
            listing_id = res_data.get("listingId")
            return {
                "success": True, 
                "listing_id": listing_id,
                "remote_url": f"https://www.ebay.com/itm/{listing_id}" if listing_id else None
            }
        else:
            return {"success": False, "error": f"eBay Publish Failed: {publish_res.text}", "stage": "publish_offer"}

    def validate_listing_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Pre-flight check for required eBay fields."""
        required = [
            ("Title", "Title is required"),
            ("Price", "Price is required"),
            ("eBay Category ID", "eBay Category ID is required"),
            ("eBay Fulfillment Policy ID", "eBay Fulfillment Policy ID is required"),
            ("eBay Payment Policy ID", "eBay Payment Policy ID is required"),
            ("eBay Return Policy ID", "eBay Return Policy ID is required"),
        ]
        
        for field, msg in required:
            val = data.get(field)
            if not val or str(val).strip() in ["", "0", "0.00"]:
                return {"success": False, "error": msg, "stage": "validating"}
                
        return {"success": True}

    def update_listing(self, lot_number: int, remote_id: str, item_data: Dict[str, Any]) -> bool:
        return True

    def delete_listing(self, lot_number: int, remote_id: str) -> bool:
        return True

    def handle_webhook(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "event_type": "sale",
            "platform_id": self.platform_id,
            "remote_id": payload.get("listing_id")
        }
