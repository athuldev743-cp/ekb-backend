# app/payments/router.py
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from datetime import datetime, timezone
import os
import hmac
import hashlib
import json
import razorpay

from app.database import get_db
from app.models import Order

router = APIRouter(prefix="/payments/razorpay", tags=["Razorpay"])

RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET")
RAZORPAY_WEBHOOK_SECRET = os.getenv("RAZORPAY_WEBHOOK_SECRET")  # optional

def _client() -> razorpay.Client:
    if not RAZORPAY_KEY_ID or not RAZORPAY_KEY_SECRET:
        raise HTTPException(status_code=500, detail="Razorpay credentials not configured")
    return razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))


# ---------------------------------
# 1) CREATE RAZORPAY ORDER (INITIATE)
# ---------------------------------
@router.post("/create-order")
def create_razorpay_order(payload: dict, db: Session = Depends(get_db)):
    """
    payload example:
    {
      "order_id": 123,          # your DB order id
      "amount": 499.0,          # INR (float or int) - we convert to paise
      "email": "a@b.com",
      "phone": "9999999999"
    }
    """
    order_id = payload.get("order_id")
    amount_inr = payload.get("amount")
    email = payload.get("email")
    phone = payload.get("phone")

    if order_id is None or amount_inr is None:
        raise HTTPException(status_code=400, detail="order_id and amount are required")

    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # Razorpay expects amount in paise (integer)
    try:
        amount_paise = int(round(float(amount_inr) * 100))
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid amount")

    if amount_paise <= 0:
        raise HTTPException(status_code=400, detail="Amount must be > 0")

    client = _client()

    # receipt is your reference (often your DB order id)
    rp_order = client.order.create(
        {
            "amount": amount_paise,
            "currency": "INR",
            "receipt": str(order_id),
            "notes": {
                "db_order_id": str(order_id),
                "customer_email": email or "",
                "customer_phone": phone or "",
            },
        }
    )

    # OPTIONAL: store razorpay_order_id on your Order model if you have a field for it
    # order.razorpay_order_id = rp_order["id"]
    # db.commit()

    return {
        "keyId": RAZORPAY_KEY_ID,
        "razorpayOrderId": rp_order["id"],
        "amount": amount_paise,
        "currency": "INR",
        "dbOrderId": order_id,
        "prefill": {"email": email, "contact": phone},
    }


# ---------------------------------
# 2) VERIFY PAYMENT SIGNATURE (MANDATORY)
# ---------------------------------
@router.post("/verify")
def verify_razorpay_payment(payload: dict, db: Session = Depends(get_db)):
    db_order_id = payload.get("dbOrderId")
    rp_order_id = payload.get("razorpay_order_id")
    rp_payment_id = payload.get("razorpay_payment_id")
    rp_signature = payload.get("razorpay_signature")

    if not all([db_order_id, rp_order_id, rp_payment_id, rp_signature]):
        raise HTTPException(status_code=400, detail="Missing verification fields")

    order = db.query(Order).filter(Order.id == int(db_order_id)).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # Signature verification logic
    message = f"{rp_order_id}|{rp_payment_id}".encode("utf-8")
    expected = hmac.new(
        RAZORPAY_KEY_SECRET.encode("utf-8"),
        message,
        hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(expected, rp_signature):
        order.payment_status = "failed"
        db.commit()
        raise HTTPException(status_code=400, detail="Signature verification failed")

    # ✅ SUCCESS: Mark paid and STORE THE IDs
    order.payment_status = "paid"
    order.status = "confirmed"
    order.razorpay_order_id = rp_order_id      # Store RP Order ID
    order.razorpay_payment_id = rp_payment_id  # Store RP Payment ID
    order.updated_at = datetime.now(timezone.utc)

    db.commit()
    return {"ok": True, "status": "paid"}


# ---------------------------------
# 3) WEBHOOK (OPTIONAL BUT RECOMMENDED)
# ---------------------------------
@router.post("/webhook")
async def razorpay_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Configure webhook in Razorpay dashboard with a secret.
    Razorpay sends X-Razorpay-Signature header (HMAC SHA256 of raw body using webhook secret). :contentReference[oaicite:4]{index=4}
    Also handle idempotency using x-razorpay-event-id. :contentReference[oaicite:5]{index=5}
    """
    if not RAZORPAY_WEBHOOK_SECRET:
        raise HTTPException(status_code=500, detail="Webhook secret not configured")

    raw_body = await request.body()
    received_sig = request.headers.get("x-razorpay-signature") or request.headers.get("X-Razorpay-Signature")

    if not received_sig:
        raise HTTPException(status_code=400, detail="Missing webhook signature header")

    expected_sig = hmac.new(
        RAZORPAY_WEBHOOK_SECRET.encode("utf-8"),
        raw_body,
        hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(expected_sig, received_sig):
        raise HTTPException(status_code=400, detail="Invalid webhook signature")

    payload = json.loads(raw_body.decode("utf-8"))
    event = payload.get("event")

    # Example: handle payment.captured (you can expand based on your needs)
    if event == "payment.captured":
        entity = payload.get("payload", {}).get("payment", {}).get("entity", {})
        receipt = entity.get("notes", {}).get("db_order_id") or entity.get("receipt")

        if receipt:
            order = db.query(Order).filter(Order.id == int(receipt)).first()
            if order:
                order.payment_status = "paid"
                order.updated_at = datetime.now(timezone.utc)
                db.commit()

    return {"ok": True}