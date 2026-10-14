
def get_shipping_policy(order_value: int) -> dict:
    """Calculate shipping charges and explain the delivery policy."""

    if order_value < 0:
        return {
            "status": "invalid",
            "message": "Order value cannot be negative.",
        }

    if order_value > 499:
        shipping_fee = 0
        message = "Shipping is free for this order."
    elif order_value < 499:
        shipping_fee = 50
        message = "A shipping fee of ₹50 applies to this order."
    else:
        # The assessment does not explicitly define the ₹499 boundary.
        return {
            "status": "clarification_required",
            "message": (
                "The shipping fee for an order of exactly ₹499 "
                "needs confirmation."
            ),
        }

    return {
        "status": "success",
        "order_value": order_value,
        "shipping_fee": shipping_fee,
        "delivery_estimate": "3–5 business days",
        "message": message,
    }


def check_return_policy(
    days_since_delivery: int,
    unopened: bool,
    unused: bool,
    original_packaging: bool,
) -> dict:
    """Check whether an order meets Aura's return conditions."""

    if days_since_delivery < 0:
        return {
            "eligible": False,
            "message": "The delivery date is invalid.",
        }

    if days_since_delivery > 7:
        return {
            "eligible": False,
            "message": "Returns are allowed only within 7 days of delivery.",
        }

    if not unopened or not unused or not original_packaging:
        return {
            "eligible": False,
            "message": (
                "The product must be unopened, unused, "
                "and in its original packaging."
            ),
        }

    return {
        "eligible": True,
        "message": "The order meets Aura's return conditions.",
    }


def check_damage_policy(
    hours_since_delivery: int,
    photos_provided: bool,
) -> dict:
    """Check the reporting deadline and photo requirement for damage."""

    if hours_since_delivery < 0:
        return {
            "eligible": False,
            "message": "The delivery time is invalid.",
        }

    if hours_since_delivery > 48:
        return {
            "eligible": False,
            "message": "Damage must be reported within 48 hours of delivery.",
        }

    if not photos_provided:
        return {
            "eligible": False,
            "message": "Please provide photos of the damaged product.",
        }

    return {
        "eligible": True,
        "message": (
            "The damage report meets the time and photo requirements "
            "for replacement review."
        ),
    }


def check_cancellation_policy(order_status: str) -> dict:
    """Allow cancellation only while an order is Processing."""

    status = order_status.strip().lower()

    if status == "processing":
        return {
            "eligible": True,
            "message": "The order is eligible for cancellation.",
        }

    if status in {"shipped", "out for delivery"}:
        return {
            "eligible": False,
            "message": (
                "The order cannot be cancelled at this stage. "
                "The customer may refuse delivery at the doorstep."
            ),
        }

    return {
        "eligible": False,
        "message": (
            "Cancellation is available only while the order is Processing."
        ),
    }


def check_cod_policy(order_value: int) -> dict:
    """Check whether the order qualifies for cash on delivery."""

    if order_value < 0:
        return {
            "eligible": False,
            "message": "Order value cannot be negative.",
        }

    if order_value > 2500:
        return {
            "eligible": False,
            "message": "Cash on delivery is available for orders up to ₹2,500.",
        }

    return {
        "eligible": True,
        "payment_methods": ["Cash", "UPI"],
        "message": "Cash on delivery is available. Pay by cash or UPI at the doorstep.",
    }
