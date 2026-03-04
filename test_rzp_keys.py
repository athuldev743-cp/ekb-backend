import os
from dotenv import load_dotenv
import razorpay

# load .env
load_dotenv()

KEY_ID = os.getenv("RAZORPAY_KEY_ID")
KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET")

print("Using key:", KEY_ID)

# create client
client = razorpay.Client(auth=(KEY_ID, KEY_SECRET))

try:
    order = client.order.create({
        "amount": 100,  # ₹1.00 (amount in paise)
        "currency": "INR",
        "receipt": "test_order_1"
    })

    print("Order created successfully")
    print("Order ID:", order["id"])
    print("Status:", order["status"])

except Exception as e:
    print("Error:", str(e))