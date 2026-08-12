# Ekabhumi — E-Commerce Backend

Production backend for an e-commerce platform: product catalog, orders, admin content management (blog, hero banners, offers, reviews), Google OAuth authentication, and Razorpay payment processing with defense-in-depth signature verification against tampering.

**Live site:** https://www.ekabhumih.in

---

## Why the payment layer is the interesting part

Payment integrations are easy to get wrong in ways that don't show up until money is actually lost — trusting a client-supplied amount, skipping signature verification "just for testing," or not handling the same webhook event arriving twice. This backend verifies payment integrity at three independent points rather than trusting any single source, and treats the client and the webhook as two separate, individually-verified paths rather than one flow.

---

## Payment security architecture

Every payment goes through **three independent checks** before an order is marked paid — no single point of trust:

**1. Client-side signature verification** (`/payments/razorpay/verify`)
After checkout, the frontend sends back Razorpay's order ID, payment ID, and signature. The backend recomputes the HMAC-SHA256 signature itself from the order+payment IDs using the secret key and compares it with `hmac.compare_digest` (constant-time comparison — prevents timing attacks that could otherwise leak the correct signature byte-by-byte).

**2. Server-side payment fetch cross-check**
Even after signature verification passes, the backend doesn't trust the client's claim of success — it calls Razorpay's API directly to fetch the actual payment record and independently verifies:
- the payment's `order_id` matches what was expected
- the payment amount matches the order's actual total (**recomputed server-side from the database**, in paise, using `Decimal` arithmetic to avoid floating-point rounding errors — never trusts a client-supplied amount)
- the payment status is `captured` or `authorized`, not just "exists"

**3. Webhook signature verification** (`/payments/razorpay/webhook`)
Razorpay's webhook is verified independently using a *separate* secret (`RAZORPAY_WEBHOOK_SECRET`, distinct from the API key secret) against the raw request body — this is the path that confirms payment even if the user closes their browser before the client-side verify call completes, so payment confirmation doesn't depend on the customer's browser staying open.

**Additional safeguards:**
- **Idempotency**: both the verify endpoint and the webhook check `payment_status == "paid"` first and short-circuit — replayed webhook events or duplicate verify calls can't double-process an order
- **Cross-reference locking**: once an order has a `razorpay_payment_id` or `razorpay_order_id` attached, any future request claiming a *different* ID for that order is rejected outright — prevents one order's payment confirmation from being attached to another order
- **Receipt fallback resolution**: if a webhook payload doesn't carry `db_order_id` in its notes, the backend falls back to fetching the Razorpay order directly to resolve the receipt, rather than dropping the event

---

## Authentication

Google OAuth 2.0 (ID token verification) issues a self-signed JWT rather than relying on session cookies or storing Google tokens:

- Google's ID token is verified server-side against `GOOGLE_CLIENT_ID` before any session is created — the backend never trusts a client-asserted email
- Role assignment (`admin` vs `user`) is determined server-side by comparing the verified email against a configured `ADMIN_EMAIL` — not a client-supplied claim
- Issued JWTs carry an `iss` (issuer) claim checked on every request, guarding against tokens forged for a different service using a leaked or shared secret
- 30-day token expiry with a `/auth/refresh` endpoint — the frontend can silently renew a token nearing expiry without forcing re-login, while `admin_required`/`user_required` dependency guards still reject anything expired or malformed

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend framework | FastAPI |
| Database | SQLite (SQLAlchemy ORM) |
| Auth | Google OAuth 2.0, JWT (PyJWT) |
| Payments | Razorpay (signature-verified webhooks + client verification) |
| Media | Cloudinary |
| Deployment | Render (Docker) |

---

## API Surface

| Domain | Routes |
|---|---|
| Products | `app/products/router.py` |
| Orders | `app/orders/router.py` |
| Payments | `app/payments/router.py` — create-order, verify, webhook |
| Auth | `app/auth/router.py` — Google login, token refresh |
| Reviews | `app/reviews/router.py` |
| Admin | `app/admin/` — blog, offers, reviews moderation, hero banner |
| Public content | `/blogs` (filtered by publish date, ordered) |

---

## Getting Started

### Prerequisites
- Python 3.11+
- Razorpay account (API keys + webhook secret)
- Google Cloud OAuth client ID
- Cloudinary account (for media uploads)

### Setup

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env  # fill in your own values — see Configuration below
uvicorn app.main:app --reload
```

### Configuration

Create `.env` with:

```
SECRET_KEY=your_jwt_signing_secret
GOOGLE_CLIENT_ID=your_google_oauth_client_id
ADMIN_EMAIL=your_admin_email@example.com
RAZORPAY_KEY_ID=your_razorpay_key_id
RAZORPAY_KEY_SECRET=your_razorpay_key_secret
RAZORPAY_WEBHOOK_SECRET=your_razorpay_webhook_secret
CLOUDINARY_URL=your_cloudinary_url
```

**Note**: `RAZORPAY_KEY_SECRET` and `RAZORPAY_WEBHOOK_SECRET` are intentionally separate values — using the same secret for both would mean a leak of one compromises the other verification path too.

---

## Project Structure

```
app/
├── admin/              # Blog, offers, reviews moderation, hero banner (admin-only)
├── auth/                # Google OAuth login, JWT issuance, refresh
├── core/
│   ├── config.py         # Environment-driven settings
│   └── security.py         # (auth dependency helpers)
├── orders/                # Order creation, listing
├── payments/                # Razorpay create-order, verify, webhook
├── products/                  # Product catalog
├── reviews/                    # Customer reviews
├── cloudinary_setup.py           # Media upload config
├── database.py                     # SQLAlchemy engine/session
├── models.py                         # ORM models
├── schemas.py                          # Pydantic request/response schemas
└── main.py                               # App entrypoint, router mounting, CORS
```

---

## Roadmap

- [ ] Migrate from SQLite to PostgreSQL for production concurrency (SQLite's single-writer model limits concurrent order processing under real traffic)
- [ ] Rate limiting on `/auth/google` and `/payments/razorpay/verify` to reduce brute-force/abuse surface
- [ ] Structured logging around payment state transitions for easier reconciliation with Razorpay's dashboard
- [ ] Automated tests for the three-layer payment verification path (signature tampering, amount mismatch, replayed webhook)

---

## License

Private project — not currently licensed for reuse.