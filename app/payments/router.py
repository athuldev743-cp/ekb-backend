from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from datetime import datetime, timezone
import hmac
import hashlib
import json
import razorpay

from app.database import get_db
from app.models import Order

router = APIRouter(prefix="/payments/razorpay", tags=["Razorpay"])


# Read from environment (preferably via app/core/config.py if you add these there)
import os
RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET")
RAZORPAY_WEBHOOK_SECRET = os.getenv("RAZORPAY_WEBHOOK_SECRET")


def _client() -> razorpay.Client:
    if not RAZORPAY_KEY_ID or not RAZORPAY_KEY_SECRET:
        raise HTTPException(status_code=500, detail="Razorpay credentials not configured")
    return razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))


@router.post("/create-order")
def create_razorpay_order(payload: dict, db: Session = Depends(get_db)):
    order_id = payload.get("order_id")
    email = payload.get("email")
    phone = payload.get("phone")

    if order_id is None:
        raise HTTPException(status_code=400, detail="order_id is required")

    order = db.query(Order).filter(Order.id == int(order_id)).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if (order.payment_status or "").lower() == "paid":
        raise HTTPException(status_code=400, detail="Order already paid")

    try:
        amount_paise = int(round(float(order.total_amount) * 100))
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid order total")

    if amount_paise <= 0:
        raise HTTPException(status_code=400, detail="Amount must be > 0")

    client = _client()

    rp_order = client.order.create(
        {
            "amount": amount_paise,
            "currency": "INR",
            "receipt": str(order.id),
            "notes": {
                "db_order_id": str(order.id),
                "customer_email": order.customer_email or (email or ""),
                "customer_phone": order.customer_phone or (phone or ""),
            },
        }
    )

    # Store created Razorpay order id for reconciliation
    order.razorpay_order_id = rp_order.get("id")
    order.updated_at = datetime.now(timezone.utc)
    db.commit()

    return {
        "keyId": RAZORPAY_KEY_ID,
        "razorpayOrderId": rp_order["id"],
        "amount": amount_paise,
        "currency": "INR",
        "dbOrderId": order.id,
        "prefill": {"email": order.customer_email or email, "contact": order.customer_phone or phone},
    }


@router.post("/verify")
def verify_razorpay_payment(payload: dict, db: Session = Depends(get_db)):
    if not RAZORPAY_KEY_SECRET:
        raise HTTPException(status_code=500, detail="Razorpay secret not configured")

    db_order_id = payload.get("dbOrderId")
    rp_order_id = payload.get("razorpay_order_id")
    rp_payment_id = payload.get("razorpay_payment_id")
    rp_signature = payload.get("razorpay_signature")

    if not all([db_order_id, rp_order_id, rp_payment_id, rp_signature]):
        raise HTTPException(status_code=400, detail="Missing verification fields")

    order = db.query(Order).filter(Order.id == int(db_order_id)).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # Idempotency: if already paid, return success
    if (order.payment_status or "").lower() == "paid":
        return {"ok": True, "status": "paid", "dbOrderId": order.id}

    # Strong linkage check: the rp_order_id MUST match the one we created for this DB order
    if order.razorpay_order_id and order.razorpay_order_id != rp_order_id:
        raise HTTPException(status_code=400, detail="Razorpay order_id mismatch")

    # Signature verification (client-side return verification)
    message = f"{rp_order_id}|{rp_payment_id}".encode("utf-8")
    expected = hmac.new(
        RAZORPAY_KEY_SECRET.encode("utf-8"),
        message,
        hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(expected, rp_signature):
        # Do NOT flip to failed on a single bad attempt; keep pending.
        order.updated_at = datetime.now(timezone.utc)
        db.commit()
        raise HTTPException(status_code=400, detail="Signature verification failed")

    # Success
    order.payment_status = "paid"
    if not order.status:
        order.status = "pending"
    order.razorpay_order_id = rp_order_id
    order.razorpay_payment_id = rp_payment_id
    order.updated_at = datetime.now(timezone.utc)
    db.commit()

    return {"ok": True, "status": "paid", "dbOrderId": order.id}


@router.post("/webhook")
async def razorpay_webhook(request: Request, db: Session = Depends(get_db)):
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

    if event != "payment.captured":
        return {"ok": True, "ignored": True, "event": event}

    entity = payload.get("payload", {}).get("payment", {}).get("entity", {})
    notes = entity.get("notes") or {}
    receipt = notes.get("db_order_id") or entity.get("receipt")
    payment_id = entity.get("id")
    rp_order_id = entity.get("order_id")

    if not receipt:
        raise HTTPException(status_code=400, detail="Missing db_order_id/receipt")

    order = db.query(Order).filter(Order.id == int(receipt)).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # Idempotency: if already paid, don't re-write unnecessarily
    if (order.payment_status or "").lower() != "paid":
        # Linkage check if we have rp_order_id
        if order.razorpay_order_id and rp_order_id and order.razorpay_order_id != rp_order_id:
            raise HTTPException(status_code=400, detail="Razorpay order_id mismatch")

        order.payment_status = "paid"
        if not order.status:
            order.status = "pending"
        if rp_order_id:
            order.razorpay_order_id = rp_order_id
        if payment_id:
            order.razorpay_payment_id = payment_id
        order.updated_at = datetime.now(timezone.utc)
        db.commit()

    return {"ok": True}