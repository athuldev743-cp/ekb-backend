import os
from dotenv import load_dotenv
import razorpay

load_dotenv()
client = razorpay.Client(auth=(os.getenv("RAZORPAY_KEY_ID"), os.getenv("RAZORPAY_KEY_SECRET")))

order = client.order.create({"amount": 100, "currency": "INR"})  # ₹1.00
print(order["id"], order["status"])