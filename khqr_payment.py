from fastapi import HTTPException
import hashlib
import hmac
import httpx
import os
from urllib.parse import urlencode
from dotenv import load_dotenv

load_dotenv()

# --- Configurations ---
GATEWAY_URL = os.getenv("ANAJAKPAY_GATEWAY_URL", "https://anajakpay.com/api/payment/requestv2")
PROFILE_ID = os.getenv("ANAJAKPAY_PROFILE_ID", os.getenv("KHQR_PROFILE_ID", "m7viCXltfrLnkor24AGZuz5itSHqUu91"))
SECRET_KEY = os.getenv("ANAJAKPAY_SECRET_KEY", os.getenv("KHQR_SECRET_KEY", ""))
PROFILE_KEY = os.getenv("KHQR_PROFILE_KEY", SECRET_KEY)
DEFAULT_SUCCESS_URL = os.getenv("PAYMENT_SUCCESS_URL", "http://localhost:3000/payment-success")

# Verify URL v2 & QR API URL
VERIFY_URL = f"https://anajakpay.com/api/{PROFILE_ID}/payment-gateway/v1/payments/check-trans"
QR_API_URL = f"https://anajakpay.com/api/{PROFILE_ID}/payment-gateway/v1/payments/create-qr"

print(f"KHQR Config - Gateway URL: {GATEWAY_URL}")
print(f"KHQR Config - Profile ID: {PROFILE_ID}")
print(f"KHQR Config - Secret Key exists: {bool(SECRET_KEY)}")


# --- Hash Helper Functions ---

def generate_payment_hash(secret: str, transaction_id: str, amount: float, success_url: str, remark: str = "") -> str:
    """
    Generate SHA1 hash for payment request
    Formula: sha1(secret + transaction_id + amount + success_url + remark)
    """
    amount_str = f"{amount:.2f}"
    raw_string = f"{secret}{transaction_id}{amount_str}{success_url}{remark}"
    return hashlib.sha1(raw_string.encode("utf-8")).hexdigest()


def generate_qr_api_hash(secret: str, transaction_id: str, amount: float) -> str:
    """Generate SHA1 hash for Direct QR API Request"""
    amount_str = f"{amount:.2f}"
    raw_string = f"{secret}{transaction_id}{amount_str}"
    return hashlib.sha1(raw_string.encode("utf-8")).hexdigest()


def generate_webhook_hash(secret: str, req_time: str, transaction_id: str, amount: str, status: str = "SUCCESS") -> str:
    """
    Generate SHA256 hash for callback/webhook verification
    Formula: sha256(secret + req_time + transaction_id + amount + 'SUCCESS')
    """
    raw_string = f"{secret}{req_time}{transaction_id}{amount}{status}"
    return hashlib.sha256(raw_string.encode("utf-8")).hexdigest()


def generate_verify_hash(profile_key: str, transaction_id: str) -> str:
    """Generate SHA1 hash for check-trans status"""
    raw_string = f"{profile_key}{transaction_id}"
    return hashlib.sha1(raw_string.encode("utf-8")).hexdigest()


# --- Payment Core Functions ---

async def create_khqr_payment(transaction_id: str, amount_usd: float, success_url: str = None, remark: str = ""):
    """
    បង្កើត KHQR Payment Session និងបញ្ជូនត្រឡប់ Checkout URL សម្រាប់ Iframe Modal
    """
    try:
        if not SECRET_KEY:
            raise HTTPException(status_code=500, detail="ANAJAKPAY_SECRET_KEY / KHQR_SECRET_KEY not configured")
        
        if not PROFILE_ID:
            raise HTTPException(status_code=500, detail="ANAJAKPAY_PROFILE_ID / KHQR_PROFILE_ID not configured")
        
        if amount_usd <= 0:
            raise HTTPException(status_code=400, detail=f"Amount must be greater than 0, got: {amount_usd}")

        target_success_url = success_url or DEFAULT_SUCCESS_URL
        amount_str = f"{amount_usd:.2f}"

        # 1. បង្កើត SHA1 Signature
        payment_hash = generate_payment_hash(
            secret=SECRET_KEY,
            transaction_id=transaction_id,
            amount=amount_usd,
            success_url=target_success_url,
            remark=remark
        )

        params = {
            "transaction_id": transaction_id,
            "amount": amount_str,
            "success_url": target_success_url,
            "hash": payment_hash
        }
        if remark:
            params["remark"] = remark

        # 2. បង្កើត Checkout URL
        endpoint_base = f"{GATEWAY_URL.rstrip('/')}/{PROFILE_ID}"
        full_checkout_url = f"{endpoint_base}?{urlencode(params)}"

        return {
            "status": "success",
            "transaction_id": transaction_id,
            "amount": amount_str,
            "checkout_url": full_checkout_url,
            "payment_url": full_checkout_url,
            "full_url": full_checkout_url,
            "params": params
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"KHQR payment creation error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create payment: {str(e)}")


async def verify_khqr_transaction(transaction_id: str):
    """Verify transaction status with Gateway (Check V2)"""
    try:
        key_for_verify = PROFILE_KEY if PROFILE_KEY else SECRET_KEY
        verify_hash = generate_verify_hash(key_for_verify, transaction_id)
        
        post_data = {
            "transaction_id": transaction_id,
            "hash": verify_hash
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(VERIFY_URL, data=post_data, timeout=30.0)
            result = response.json()
        
        print(f"Transaction verify response raw: {result}")
        
        # ពិនិត្យ status ពិតប្រាកដ (ហាមប្រើ responseCode == 0 ព្រោះវាគ្រាន់តែជា API code)
        status_root = str(result.get("status", "")).upper()
        data_block = result.get("data") if isinstance(result.get("data"), dict) else {}
        status_inner = str(data_block.get("status", "")).upper()
        payment_status = str(result.get("payment_status", "")).upper()
        
        valid_success_keywords = ["SUCCESS", "PAID", "COMPLETED"]
        
        is_verified = (
            status_root in valid_success_keywords or
            status_inner in valid_success_keywords or
            payment_status in valid_success_keywords
        )
        
        return {
            "verified": is_verified,
            "response": result
        }
    except Exception as e:
        print(f"Failed to verify transaction: {str(e)}")
        return {
            "verified": False,
            "response": {"error": str(e)}
        }


def verify_webhook_signature(req_time: str, transaction_id: str, amount: str, hash_signature: str) -> bool:
    """Verify webhook POST signature"""
    try:
        expected_hash = generate_webhook_hash(
            secret=SECRET_KEY, 
            req_time=str(req_time), 
            transaction_id=str(transaction_id), 
            amount=str(amount), 
            status="SUCCESS"
        )
        return hmac.compare_digest(expected_hash.lower(), hash_signature.lower())
    except Exception as e:
        print(f"Signature verification error: {str(e)}")
        return False