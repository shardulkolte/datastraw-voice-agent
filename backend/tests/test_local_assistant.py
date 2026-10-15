
from unittest.mock import patch

from backend.app.services.local_assistant import (
    extract_order_id,
    route_local,
)


def fake_order(order_id: str):
    orders = {
        "ORD-101": {
            "order_id": "ORD-101",
            "customer": "Priya Sharma",
            "product": "Vitamin C Serum (30ml)",
            "value": 699,
            "status": "Out for Delivery",
            "courier": "BlueDart",
            "tracking_id": "BD-982103",
            "notes": "Expected by 6 PM today",
            "cancellation_eligible": False,
        },
        "ORD-103": {
            "order_id": "ORD-103",
            "customer": "Ananya Patel",
            "product": "Green Tea Face Wash + Toner",
            "value": 850,
            "status": "Processing",
            "courier": None,
            "tracking_id": None,
            "notes": "Ordered 3 hours ago",
            "cancellation_eligible": True,
        },
    }
    return orders.get(order_id)


def test_extract_order_id():
    assert extract_order_id("Check order ORD-101") == "ORD-101"
    assert extract_order_id("Check order ORD 101") == "ORD-101"
    assert extract_order_id("Check order ORD101") == "ORD-101"
    assert extract_order_id("My number is 101") is None


@patch("backend.app.services.local_assistant.get_order", side_effect=fake_order)
def test_known_order_lookup(mock_get_order):
    reply = route_local("Please check order ORD-101")

    assert reply is not None
    assert "Priya Sharma" in reply
    assert "Vitamin C Serum" in reply
    assert "Out for Delivery" in reply


@patch("backend.app.services.local_assistant.get_order", return_value=None)
def test_unknown_order(mock_get_order):
    reply = route_local("Please check order ORD-999")

    assert reply is not None
    assert "couldn't find" in reply.lower()
    assert "ORD-999" in reply


@patch("backend.app.services.local_assistant.get_order", side_effect=fake_order)
def test_cancellation_eligible_order(mock_get_order):
    reply = route_local("Can I cancel order ORD-103?")

    assert reply is not None
    assert "eligible for cancellation" in reply.lower()
    assert "not cancelled" in reply.lower()


@patch("backend.app.services.local_assistant.get_order", side_effect=fake_order)
def test_out_for_delivery_cannot_be_cancelled(mock_get_order):
    reply = route_local("Can I cancel order ORD-101?")

    assert reply is not None
    assert "cannot be cancelled" in reply.lower()
    assert "refuse the delivery" in reply.lower()


def test_cod_policy():
    reply = route_local("Do you offer COD?")

    assert reply is not None
    assert "2,500 rupees" in reply
    assert "UPI" in reply


def test_shipping_policy():
    reply = route_local("What is the shipping fee?")

    assert reply is not None
    assert "499 rupees" in reply
    assert "50 rupees" in reply


def test_unknown_question_uses_fallback():
    reply = route_local("Can you recommend a skincare routine for dry skin?")

    assert reply is None
