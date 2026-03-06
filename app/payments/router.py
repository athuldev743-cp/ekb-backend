# app/payment/router.py
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from datetime import datetime, timezone
import hmac
import hashlib
import json
import os
import razorpay
from decimal import Decimal, ROUND_HALF_UP
from app.database import get_db
from app.models import Order

router = APIRouter(prefix="/payments/razorpay", tags=["Razorpay"])


# ----------------------------
# Helpers
# ----------------------------
def _get_env():
    key_id = os.getenv("RAZORPAY_KEY_ID")
    key_secret = os.getenv("RAZORPAY_KEY_SECRET")
    webhook_secret = os.getenv("RAZORPAY_WEBHOOK_SECRET")
    return key_id, key_secret, webhook_secret


def _client() -> razorpay.Client:
    key_id, key_secret, _ = _get_env()
    if not key_id or not key_secret:
        raise HTTPException(status_code=500, detail="Razorpay credentials not configured")
    return razorpay.Client(auth=(key_id, key_secret))


def _now_utc():
    return datetime.now(timezone.utc)


def _mark_paid(order: Order, rp_order_id: str | None, rp_payment_id: str | None):
    order.payment_status = "paid"
    # If your fulfillment flow starts after payment, confirm it here.
    # Avoid leaving status="pending" after payment; it's confusing.
    if (order.status or "").lower() in ("pending", "created", ""):
        order.status = "confirmed"

    if rp_order_id:
        order.razorpay_order_id = rp_order_id
    if rp_payment_id:
        order.razorpay_payment_id = rp_payment_id

    order.updated_at = _now_utc()


def _mark_failed(order: Order, rp_order_id: str | None, rp_payment_id: str | None):
    # Keep fulfillment status as-is; payment failed is separate.
    order.payment_status = "failed"
    if rp_order_id:
        order.razorpay_order_id = rp_order_id
    if rp_payment_id:
        order.razorpay_payment_id = rp_payment_id
    order.updated_at = _now_utc()


def _verify_client_signature(order_id: str, payment_id: str, signature: str, secret: str) -> bool:
    msg = f"{order_id}|{payment_id}".encode("utf-8")
    expected = hmac.new(secret.encode("utf-8"), msg, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)


def _verify_webhook_signature(raw_body: bytes, received_sig: str, webhook_secret: str) -> bool:
    expected_sig = hmac.new(webhook_secret.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected_sig, received_sig)


# ----------------------------
# Routes
# ----------------------------
@router.post("/create-order")
def create_razorpay_order(payload: dict, db: Session = Depends(get_db)):
    key_id, _, _ = _get_env()
    if not key_id:
        raise HTTPException(status_code=500, detail="Razorpay key id not configured")

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
       amount_paise = int((Decimal(str(order.total_amount)) * Decimal("100")).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
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

    order.razorpay_order_id = rp_order.get("id")
    # keep payment_status pending; status remains whatever you use (pending/created)
    order.updated_at = _now_utc()
    db.commit()

    return {
        "keyId": key_id,  # safe to send public key
        "razorpayOrderId": rp_order["id"],
        "amount": amount_paise,
        "currency": "INR",
        "dbOrderId": order.id,
        "prefill": {"email": order.customer_email or email, "contact": order.customer_phone or phone},
    }


@router.post("/create-order")
def create_razorpay_order(payload: dict, db: Session = Depends(get_db)):
    key_id, _, _ = _get_env()
    if not key_id:
        raise HTTPException(status_code=500, detail="Razorpay key id not configured")

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
        amount_paise = int(
            (Decimal(str(order.total_amount)) * Decimal("100"))
            .quantize(Decimal("1"), rounding=ROUND_HALF_UP)
        )
    except Exception as e:
        print("INVALID ORDER TOTAL:", e, "order.total_amount=", order.total_amount)
        raise HTTPException(status_code=400, detail="Invalid order total")

    if amount_paise <= 0:
        raise HTTPException(status_code=400, detail="Amount must be > 0")

    try:
        client = _client()
        rp_order = client.order.create({
            "amount": amount_paise,
            "currency": "INR",
            "receipt": str(order.id),
            "notes": {
                "db_order_id": str(order.id),
                "customer_email": order.customer_email or (email or ""),
                "customer_phone": order.customer_phone or (phone or ""),
            },
        })
    except Exception as e:
        print("RAZORPAY ORDER CREATE ERROR:", repr(e))
        raise HTTPException(status_code=500, detail="Failed to create Razorpay order")

    order.razorpay_order_id = rp_order.get("id")
    order.updated_at = _now_utc()
    db.commit()

    return {
        "keyId": key_id,
        "razorpayOrderId": rp_order["id"],
        "amount": amount_paise,
        "currency": "INR",
        "dbOrderId": order.id,
        "prefill": {
            "email": order.customer_email or email,
            "contact": order.customer_phone or phone
        },
    }

@router.post("/webhook")
async def razorpay_webhook(request: Request, db: Session = Depends(get_db)):
    _, _, webhook_secret = _get_env()
    if not webhook_secret:
        raise HTTPException(status_code=500, detail="Webhook secret not configured")

    raw_body = await request.body()
    received_sig = request.headers.get("x-razorpay-signature") or request.headers.get("X-Razorpay-Signature")
    if not received_sig:
        raise HTTPException(status_code=400, detail="Missing webhook signature header")

    if not _verify_webhook_signature(raw_body, received_sig, webhook_secret):
        raise HTTPException(status_code=400, detail="Invalid webhook signature")

    payload = json.loads(raw_body.decode("utf-8"))
    event = payload.get("event")

    entity = payload.get("payload", {}).get("payment", {}).get("entity", {}) or {}
    notes = entity.get("notes") or {}
    payment_id = entity.get("id")
    rp_order_id = entity.get("order_id")

    # Resolve db order id (receipt)
    receipt = notes.get("db_order_id")
    if not receipt and rp_order_id:
        # fallback: fetch order and read receipt
        try:
            client = _client()
            rp_order = client.order.fetch(rp_order_id)
            receipt = rp_order.get("receipt")
        except Exception:
            receipt = None

    if not receipt:
        raise HTTPException(status_code=400, detail="Missing db_order_id/receipt")

    order = db.query(Order).filter(Order.id == int(receipt)).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # Idempotency
    if (order.payment_status or "").lower() == "paid":
        return {"ok": True, "status": "already_paid"}

    # Strong linkage check
    if order.razorpay_order_id and rp_order_id and order.razorpay_order_id != rp_order_id:
        raise HTTPException(status_code=400, detail="Razorpay order_id mismatch")

    if event == "payment.captured":
        _mark_paid(order, rp_order_id, payment_id)
        db.commit()
        return {"ok": True, "status": "paid"}

    if event == "payment.failed":
        _mark_failed(order, rp_order_id, payment_id)
        db.commit()
        return {"ok": True, "status": "failed"}

    # ignore other events for now
    return {"ok": True, "ignored": True, "event": event}