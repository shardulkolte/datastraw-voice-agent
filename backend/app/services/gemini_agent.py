
import os

from dotenv import load_dotenv
from google import genai
from google.genai import types

from backend.app.database import SessionLocal
from backend.app.models import OrderRecord
from backend.app.tools.orders import (
    get_order_details as lookup_order,
)
from backend.app.services.policies import (
    get_shipping_policy as shipping_policy,
    check_return_policy,
    check_damage_policy,
    check_cancellation_policy,
    check_cod_policy,
)


load_dotenv()

MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")

SYSTEM_INSTRUCTION = """
You are Aria, a friendly and professional customer support
specialist for Aura Skincare.

Keep responses concise, natural, and helpful.

Use tools whenever verified order information or a policy
decision is required. Never invent order details, tracking
numbers, delivery dates, or policy results.

Ask the customer for an order ID when it is required but
missing. Ask follow-up questions when required information
for a policy decision is missing.

Use actual tool results when answering order-related questions.
Do not claim that an action was completed when it was only checked.

Aura policies:
- Free shipping above ₹499.
- Shipping costs ₹50 below ₹499.
- Standard delivery takes 3–5 business days.
- Returns are allowed within 7 days of delivery only for
  unopened, unused products in original packaging.
- Damage must be reported within 48 hours with photos.
- Cancellation is allowed only while Processing.
- Shipped or Out for Delivery orders cannot be cancelled;
  the customer may refuse delivery at the doorstep.
- COD is available up to ₹2,500, payable by cash or UPI.

For an order worth exactly ₹499, the shipping rule requires
clarification. Do not guess the fee.
"""


def get_order_details(order_id: str) -> dict:
    """Look up an order using its ID in the SQLite database."""

    db = SessionLocal()

    try:
        order = lookup_order(db, order_id)

        if order is None:
            return {
                "found": False,
                "message": "No order was found with that ID.",
            }

        return {
            "found": True,
            "order_id": order.order_id,
            "customer": order.customer,
            "product": order.product,
            "value": order.value,
            "status": order.status,
            "courier": order.courier,
            "tracking_id": order.tracking_id,
            "notes": order.notes,
            "cancellation_eligible": order.cancellation_eligible,
        }
    finally:
        db.close()


def check_order_cancellation(order_id: str) -> dict:
    """Check cancellation using the order's actual database status."""

    order_data = get_order_details(order_id)

    if not order_data["found"]:
        return order_data

    result = check_cancellation_policy(order_data["status"])

    return {
        "order_id": order_data["order_id"],
        "order_status": order_data["status"],
        **result,
    }


def get_order_shipping_policy(order_id: str) -> dict:
    """Check shipping using the order value stored in the database."""

    order_data = get_order_details(order_id)

    if not order_data["found"]:
        return order_data

    return {
        "order_id": order_data["order_id"],
        **shipping_policy(order_data["value"]),
    }


def get_return_eligibility(
    days_since_delivery: int,
    unopened: bool,
    unused: bool,
    original_packaging: bool,
) -> dict:
    """Check return eligibility against Aura's return policy."""

    return check_return_policy(
        days_since_delivery,
        unopened,
        unused,
        original_packaging,
    )


def get_damage_eligibility(
    hours_since_delivery: int,
    photos_provided: bool,
) -> dict:
    """Check damage reporting time and photo requirements."""

    return check_damage_policy(
        hours_since_delivery,
        photos_provided,
    )


def get_cod_eligibility(order_value: int) -> dict:
    """Check COD eligibility against Aura's payment limit."""

    return check_cod_policy(order_value)



def ask_gemini(message: str) -> str:
    """Send a customer message to Gemini with available tools."""

    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is missing. Add it to your .env file."
        )

    client = genai.Client(api_key=api_key)

    chat = client.chats.create(
        model=MODEL_NAME,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTION,
            temperature=0.3,
            tools=[
                get_order_details,
                check_order_cancellation,
                get_order_shipping_policy,
                get_return_eligibility,
                get_damage_eligibility,
                get_cod_eligibility,
            ],
        ),
    )

    response = chat.send_message(message)

    if not response.text:
        return (
            "I'm sorry, I couldn't prepare a response just now. "
            "Could you please try again?"
        )

    return response.text
