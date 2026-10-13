
from pydantic import BaseModel, ConfigDict
from sqlalchemy import Boolean, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.database import Base


class OrderRecord(Base):
    __tablename__ = "orders"

    order_id: Mapped[str] = mapped_column(
        String(20), primary_key=True
    )
    customer: Mapped[str] = mapped_column(String(100))
    product: Mapped[str] = mapped_column(String(200))
    value: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(50))
    courier: Mapped[str] = mapped_column(String(50))
    tracking_id: Mapped[str] = mapped_column(String(50))
    notes: Mapped[str] = mapped_column(String(200))
    cancellation_eligible: Mapped[bool] = mapped_column(Boolean)


class OrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    order_id: str
    customer: str
    product: str
    value: int
    status: str
    courier: str
    tracking_id: str
    notes: str
    cancellation_eligible: bool
