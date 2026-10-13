
from backend.app.models import Order


ORDERS = {
    "ORD-101": Order(
        order_id="ORD-101",
        customer="Priya Sharma",
        product="Vitamin C Serum (30ml)",
        value=699,
        status="Out for Delivery",
        courier="BlueDart",
        tracking_id="BD-982103",
        notes="Expected by 6 PM today",
        cancellation_eligible=False,
    ),
    "ORD-102": Order(
        order_id="ORD-102",
        customer="Rahul Verma",
        product="Hydrating Sunscreen SPF 50",
        value=499,
        status="Delivered",
        courier="Delhivery",
        tracking_id="DL-441029",
        notes="Delivered 14 days ago",
        cancellation_eligible=False,
    ),
    "ORD-103": Order(
        order_id="ORD-103",
        customer="Ananya Patel",
        product="Green Tea Face Wash + Toner",
        value=850,
        status="Processing",
        courier="Not yet shipped",
        tracking_id="Not available",
        notes="Ordered 3 hours ago",
        cancellation_eligible=True,
    ),
}


def get_order_details(order_id: str) -> Order | None:
    order_id = order_id.strip().upper()
    return ORDERS.get(order_id)
