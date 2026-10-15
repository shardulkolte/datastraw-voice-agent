
import os
import re
import time
import logging

from dotenv import load_dotenv
from google import genai
from google.genai import types

from backend.app.services.local_assistant import route_local
from backend.app.database import SessionLocal
from backend.app.tools.orders import get_order_details as lookup_order
from backend.app.services.policies import (
    get_shipping_policy as shipping_policy,
    check_return_policy,
    check_damage_policy,
    check_cancellation_policy,
    check_cod_policy,
)

load_dotenv()

MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
logger = logging.getLogger(__name__)

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
    """Check cancellation using the actual database status."""
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
    """Check shipping using the stored order value."""
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
    """Check return eligibility against Aura's policy."""
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


def handle_direct_order_lookup(message: str) -> str | None:
    """Handle explicit order-detail requests directly from SQLite."""
    match = re.search(
        r"\b(?:check|track|find|show|look up|details of)"
        r"\s+(?:my\s+)?order\s+"
        r"([A-Za-z]{2,12}\s*-\s*\d{2,}|[A-Za-z]{2,12}\s+\d{2,})\b",
        message,
        re.IGNORECASE,
    )

    if not match:
        return None

    order_id = re.sub(r"\s+", "", match.group(1)).upper()

    if "-" in order_id:
        prefix, number = order_id.split("-", 1)
    else:
        prefix, number = order_id.split(None, 1)

    order_id = f"{prefix}-{number}"
    order_data = get_order_details(order_id)

    if not order_data["found"]:
        return (
            f"I couldn't find an order with ID {order_id}. "
            "Please check the order ID and try again."
        )

    return (
        f"Here are the details for order {order_data['order_id']}. "
        f"Customer: {order_data['customer']}. "
        f"Product: {order_data['product']}. "
        f"Order total: ₹{order_data['value']}. "
        f"Status: {order_data['status']}. "
        f"Courier: {order_data['courier']}. "
        f"Tracking ID: {order_data['tracking_id']}. "
        f"{order_data['notes']}"
    )



def ask_gemini(
    message: str,
    history: list[dict] | None = None,
    language: str = "english",
) -> str:
    """Handle local workflows, conversation history, and Gemini responses."""

    # Preserve the existing local order and policy handling.
    # Route only the latest message to avoid interference from old messages.
    local_reply = route_local(message)

    if local_reply is not None:
        return local_reply

    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is missing. Add it to your .env file."
        )

    language_instruction = (
        "Reply in clear, natural English suitable for an Indian customer."
        if language == "english"
        else (
            "Reply in natural conversational Hinglish using readable "
            "Roman Hindi mixed with English. Keep product names, order IDs, "
            "courier names, and tracking codes unchanged."
        )
    )

    system_instruction = (
        SYSTEM_INSTRUCTION
        + "\n\nRESPONSE LANGUAGE:\n"
        + language_instruction
        + "\nUse previous conversation turns to understand follow-up questions. "
        "Do not invent details or claim to remember information absent "
        "from the conversation or verified backend results."
    )

    # Convert frontend conversation history to Gemini's content format.
    gemini_history = []

    for turn in (history or [])[-40:]:
        content = turn.get("content", "").strip()
        role = turn.get("role")

        if not content or role not in ("user", "assistant"):
            continue

        gemini_history.append(
            types.Content(
                role="user" if role == "user" else "model",
                parts=[types.Part(text=content)],
            )
        )

    client = genai.Client(api_key=api_key)

    chat = client.chats.create(
        model=MODEL_NAME,
        history=gemini_history,
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
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

    # Preserve the previous retry and fallback behavior.
    for attempt in range(2):
        try:
            response = chat.send_message(message)

            if response.text:
                return response.text

            return (
                "I'm sorry, I couldn't prepare a response just now. "
                "Could you please try again?"
            )

        except Exception as exc:
            error_text = str(exc).lower()

            quota_markers = (
                "resource_exhausted",
                "quota exceeded",
                "quota_exceeded",
                "rate limit",
                "too many requests",
                "429",
            )

            if any(marker in error_text for marker in quota_markers):
                logger.warning(
                    "Gemini quota/rate limit reached. "
                    "Switching to the configured fallback."
                )
                raise

            temporary_markers = (
                "503",
                "service unavailable",
                "temporarily unavailable",
                "500",
                "internal server error",
                "deadline_exceeded",
                "timeout",
                "connection reset",
            )

            is_temporary = any(
                marker in error_text for marker in temporary_markers
            )

            if is_temporary and attempt == 0:
                logger.warning(
                    "Temporary Gemini failure. Retrying once in 1 second."
                )
                time.sleep(1)
                continue

            logger.exception(
                "Gemini request failed; handing control to fallback."
            )
            raise

    raise RuntimeError("Gemini failed after its retry.")
