
import re
from typing import Optional

from backend.app.database import SessionLocal
from backend.app.tools.orders import get_order_details as lookup_order


def normalize_order_id(raw: str) -> str:
    value = re.sub(r"\s+", "", raw).upper()

    if value.startswith("ORD") and not value.startswith("ORD-"):
        value = "ORD-" + value[3:]

    return value


def extract_order_id(message: str) -> Optional[str]:
    patterns = [
        # Standard IDs: ORD-101, WORK-400
        r"\b([A-Z]{2,12})\s*-\s*(\d{2,})\b",

        # Spoken/written IDs: ORD 101, ORD101
        r"\b(ORD)\s*-?\s*(\d{2,})\b",
    ]

    for pattern in patterns:
        match = re.search(pattern, message, re.IGNORECASE)

        if match:
            return normalize_order_id(
                f"{match.group(1)}-{match.group(2)}"
            )

    return None


def extract_amount(message: str) -> Optional[int]:
    """Extract an explicitly stated monetary amount."""
    patterns = [
        r"(?:₹|rs\.?|inr)\s*([\d,]+)\b",
        r"\b([\d,]+)\s*(?:rupees?|rs\.?|inr)\b",
        (
            r"\b(?:worth(?:\s+of)?|valued\s+at|value\s+of|"
            r"amount\s+of)\s*(?:₹|rs\.?|inr)?\s*([\d,]+)\b"
        ),
    ]

    for pattern in patterns:
        match = re.search(pattern, message, re.IGNORECASE)

        if match:
            return int(match.group(1).replace(",", ""))

    return None


def get_order(order_id: str) -> Optional[dict]:
    db = SessionLocal()

    try:
        order = lookup_order(db, normalize_order_id(order_id))

        if order is None:
            return None

        return {
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


def format_order_details(order: dict) -> str:
    parts = [
        f"Here are the details for order {order['order_id']}.",
        f"Customer: {order['customer']}.",
        f"Product: {order['product']}.",
        f"Order total: ₹{order['value']}.",
        f"Status: {order['status']}.",
    ]

    if order.get("courier"):
        parts.append(f"Courier: {order['courier']}.")

    if order.get("tracking_id"):
        parts.append(f"Tracking ID: {order['tracking_id']}.")

    if order.get("notes"):
        parts.append(str(order["notes"]).strip().rstrip(".") + ".")

    return " ".join(parts)


def shipping_reply(amount: int) -> str:
    if amount < 499:
        return (
            f"For an order worth ₹{amount}, the shipping fee is ₹50."
        )

    if amount > 499:
        return (
            f"For an order worth ₹{amount}, shipping is free "
            "under Aura Skincare's policy."
        )

    return (
        "Aura Skincare's policy does not specify the shipping fee "
        "for an order worth exactly ₹499. Please contact customer "
        "support to confirm."
    )


def route_local(message: str) -> Optional[str]:
    text = message.strip()

    if not text:
        return "Sorry, I didn't catch that. Could you repeat your question?"

    order_id = extract_order_id(text)

    cancellation_intent = re.search(
        r"\b(cancel|cancellation|cancelled|canceled)\b",
        text,
        re.IGNORECASE,
    )

    shipping_intent = re.search(
        r"\b(shipping|shipping fee|shipping charge|delivery fee|"
        r"delivery charge|delivery cost)\b",
        text,
        re.IGNORECASE,
    )

    order_lookup_intent = re.search(
        r"\b(order|tracking|track|parcel)\b",
        text,
        re.IGNORECASE,
    ) and re.search(
        r"\b(tell me|about|details|status|track|tracking|"
        r"where|check|find|look up|information|update|my)\b",
        text,
        re.IGNORECASE,
    )

    # 1. Cancellation always uses verified order data.
    if cancellation_intent:
        if not order_id:
            return "I can check cancellation eligibility. What is your order ID?"

        order = get_order(order_id)

        if order is None:
            return (
                f"I couldn't find an order with ID {order_id}. "
                "Please check the ID and try again."
            )

        status = order["status"].strip().lower()

        if status == "processing":
            return (
                f"Order {order['order_id']} is currently Processing "
                "and is eligible for cancellation. I have checked "
                "eligibility, but I have not cancelled the order."
            )

        if status in {"shipped", "out for delivery"}:
            return (
                f"Order {order['order_id']} is currently "
                f"{order['status']}, so it cannot be cancelled now. "
                "You may refuse delivery at your doorstep."
            )

        return (
            f"Order {order['order_id']} is currently {order['status']}. "
            "Please contact customer support to confirm your options."
        )

    # 2. Shipping questions containing an order ID use its real value.
    if shipping_intent and order_id:
        order = get_order(order_id)

        if order is None:
            return (
                f"I couldn't find an order with ID {order_id}. "
                "Please check the ID and try again."
            )

        return (
            f"Order {order['order_id']} is worth ₹{order['value']}. "
            + shipping_reply(int(order["value"]))
        )

    # 3. Order-detail questions use SQLite, not an LLM guess.
    if order_id and order_lookup_intent:
        order = get_order(order_id)

        if order is None:
            return (
                f"I couldn't find an order with ID {order_id}. "
                "Please check the ID and try again."
            )

        return format_order_details(order)

    # 4. Shipping questions about an explicitly stated amount.
    # Never treat the number in an order ID as the order's value.
    if shipping_intent:
        amount = extract_amount(text)

        if amount is not None:
            return shipping_reply(amount)

        return (
            "I can help calculate the shipping fee. "
            "What is the order value in rupees, or what is your order ID?"
        )

    # 5. An explicit order ID with an order-related question
    # must not be sent to an LLM that cannot access the database.
    if order_id and re.search(
        r"\b(order|tracking|track|parcel|delivery|status)\b",
        text,
        re.IGNORECASE,
    ):
        order = get_order(order_id)

        if order is None:
            return (
                f"I couldn't find an order with ID {order_id}. "
                "Please check the ID and try again."
            )

        return format_order_details(order)

    # All other questions continue to Gemini/OpenRouter.
    return None
