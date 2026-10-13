
from sqlalchemy.orm import Session

from backend.app.models import OrderRecord


SAMPLE_ORDERS = [
    {
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
    {
        "order_id": "ORD-102",
        "customer": "Rahul Verma",
        "product": "Hydrating Sunscreen SPF 50",
        "value": 499,
        "status": "Delivered",
        "courier": "Delhivery",
        "tracking_id": "DL-441029",
        "notes": "Delivered 14 days ago",
        "cancellation_eligible": False,
    },
    {
        "order_id": "ORD-103",
        "customer": "Ananya Patel",
        "product": "Green Tea Face Wash + Toner",
        "value": 850,
        "status": "Processing",
        "courier": "Not yet shipped",
        "tracking_id": "Not available",
        "notes": "Ordered 3 hours ago",
        "cancellation_eligible": True,
    },
]


def seed_orders(db: Session):
    for data in SAMPLE_ORDERS:
        order = db.get(OrderRecord, data["order_id"])

        if order is None:
            db.add(OrderRecord(**data))

    db.commit()
