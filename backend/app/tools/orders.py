
from sqlalchemy.orm import Session

from backend.app.models import OrderRecord


def get_order_details(
    db: Session,
    order_id: str,
) -> OrderRecord | None:
    order_id = order_id.strip().upper()

    return db.get(OrderRecord, order_id)
