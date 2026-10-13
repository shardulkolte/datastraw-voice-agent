
from pydantic import BaseModel


class Order(BaseModel):
    order_id: str
    customer: str
    product: str
    value: int
    status: str
    courier: str
    tracking_id: str
    notes: str
    cancellation_eligible: bool
