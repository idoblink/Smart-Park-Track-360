"""
ParkTrack 360 — server/phonepe.py
PhonePe Payment Gateway V1 integration supporting Sandbox and Production.
Provides payment order initiation, SHA-256 checksum signing, status verification,
and webhook signature verification for automatic gate opening.
"""

import os
import json
import base64
import hashlib
import logging
from typing import Dict, Any, Optional, Tuple
import httpx

logger = logging.getLogger("parktrack.phonepe")

class PhonePeClient:
    def __init__(self, config: Dict[str, Any]):
        phonepe_cfg = config.get("phonepe", {})
        self.enabled = phonepe_cfg.get("enabled", True)
        self.merchant_id = phonepe_cfg.get("merchant_id", "PGTESTPAYUAT86")
        self.salt_key = phonepe_cfg.get("salt_key", "96434309-7796-489d-8924-ab56988a6076")
        self.salt_index = str(phonepe_cfg.get("salt_index", "1"))
        self.env = phonepe_cfg.get("env", "sandbox").lower()

        # URLs
        if self.env == "production":
            self.base_url = phonepe_cfg.get("production_url", "https://api.phonepe.com/apis/hermes")
        else:
            self.base_url = phonepe_cfg.get("sandbox_url", "https://api-preprod.phonepe.com/apis/pg-sandbox")

    def is_configured(self) -> bool:
        return bool(self.enabled and self.merchant_id and self.salt_key)

    def _compute_checksum(self, payload_str: str, endpoint: str) -> str:
        string_to_hash = f"{payload_str}{endpoint}{self.salt_key}"
        sha256_hash = hashlib.sha256(string_to_hash.encode("utf-8")).hexdigest()
        return f"{sha256_hash}###{self.salt_index}"

    def create_payment_order(
        self,
        car_id: int,
        fare_inr: float,
        redirect_url: str,
        callback_url: str,
        user_phone: str = "9999999999"
    ) -> Dict[str, Any]:
        """
        Initiates a payment request with PhonePe (/pg/v1/pay).
        Returns transaction details and payment redirect URL.
        """
        txn_id = f"PT360_CAR_{car_id}_{int(os.times().elapsed * 1000)}"
        amount_paise = max(100, int(round(fare_inr * 100)))  # minimum 100 paise (₹1)

        payload_dict = {
            "merchantId": self.merchant_id,
            "merchantTransactionId": txn_id,
            "merchantUserId": f"MUID_CAR_{car_id}",
            "amount": amount_paise,
            "redirectUrl": redirect_url,
            "redirectMode": "REDIRECT",
            "callbackUrl": callback_url,
            "mobileNumber": user_phone,
            "paymentInstrument": {
                "type": "PAY_PAGE"
            }
        }

        payload_bytes = json.dumps(payload_dict).encode("utf-8")
        payload_b64 = base64.b64encode(payload_bytes).decode("utf-8")
        x_verify = self._compute_checksum(payload_b64, "/pg/v1/pay")

        headers = {
            "Content-Type": "application/json",
            "X-VERIFY": x_verify,
            "accept": "application/json"
        }

        url = f"{self.base_url}/pg/v1/pay"
        logger.info(f"Initiating PhonePe payment for Car #{car_id}: {fare_inr} INR (txn_id={txn_id})")

        try:
            with httpx.Client(timeout=10.0) as client:
                resp = client.post(url, json={"request": payload_b64}, headers=headers)
                data = resp.json()

            if resp.status_code == 200 and data.get("success"):
                redirect_info = data.get("data", {}).get("instrumentResponse", {}).get("redirectInfo", {})
                payment_url = redirect_info.get("url", "")
                return {
                    "ok": True,
                    "provider": "phonepe",
                    "merchant_id": self.merchant_id,
                    "txn_id": txn_id,
                    "amount_inr": fare_inr,
                    "amount_paise": amount_paise,
                    "payment_url": payment_url,
                    "env": self.env
                }
            else:
                logger.error(f"PhonePe order initiation failed: {data}")
                return {
                    "ok": False,
                    "error": data.get("message", "Payment initiation failed"),
                    "code": data.get("code")
                }
        except Exception as e:
            logger.error(f"PhonePe request exception: {e}")
            return {"ok": False, "error": str(e)}

    def check_payment_status(self, txn_id: str) -> Dict[str, Any]:
        """
        Polls PhonePe for current transaction status (/pg/v1/status/{merchant_id}/{txn_id}).
        """
        path = f"/pg/v1/status/{self.merchant_id}/{txn_id}"
        string_to_hash = f"{path}{self.salt_key}"
        sha256_hash = hashlib.sha256(string_to_hash.encode("utf-8")).hexdigest()
        x_verify = f"{sha256_hash}###{self.salt_index}"

        headers = {
            "Content-Type": "application/json",
            "X-VERIFY": x_verify,
            "X-MERCHANT-ID": self.merchant_id,
            "accept": "application/json"
        }

        url = f"{self.base_url}{path}"
        try:
            with httpx.Client(timeout=10.0) as client:
                resp = client.get(url, headers=headers)
                data = resp.json()

            code = data.get("code", "")
            is_success = (code == "PAYMENT_SUCCESS")
            is_pending = (code in ["PAYMENT_PENDING", "PAYMENT_INITIATED"])
            
            return {
                "ok": True,
                "code": code,
                "is_paid": is_success,
                "is_pending": is_pending,
                "message": data.get("message", ""),
                "txn_id": txn_id,
                "data": data.get("data", {})
            }
        except Exception as e:
            logger.error(f"PhonePe check status exception: {e}")
            return {"ok": False, "is_paid": False, "error": str(e)}

    def verify_webhook_checksum(self, response_b64: str, x_verify: str) -> bool:
        """Verifies server-to-server webhook callback checksum."""
        if not x_verify or "###" not in x_verify:
            return False
        string_to_hash = f"{response_b64}{self.salt_key}"
        expected_hash = hashlib.sha256(string_to_hash.encode("utf-8")).hexdigest()
        received_hash = x_verify.split("###")[0]
        return expected_hash.lower() == received_hash.lower()

    def decode_webhook_payload(self, response_b64: str) -> Dict[str, Any]:
        """Decodes base64 payload from PhonePe callback."""
        try:
            raw_json = base64.b64decode(response_b64).decode("utf-8")
            return json.loads(raw_json)
        except Exception as e:
            logger.error(f"Failed to decode PhonePe webhook payload: {e}")
            return {}

