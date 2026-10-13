
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session

from backend.app.database import Base, SessionLocal, engine, get_db
from backend.app.models import OrderRecord, OrderResponse
from backend.app.services.order_seed import seed_orders
from backend.app.tools.orders import get_order_details


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        seed_orders(db)
    finally:
        db.close()

    yield


app = FastAPI(
    title="Aura Skincare Voice Agent",
    description="AI-powered customer support API for Aura Skincare",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/")
def home():
    return {
        "message": "Welcome to Aura Skincare Voice Agent!",
        "status": "running",
    }


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.get(
    "/orders/{order_id}",
    response_model=OrderResponse,
)
def get_order(
    order_id: str,
    db: Session = Depends(get_db),
):
    order = get_order_details(db, order_id)

    if order is None:
        raise HTTPException(
            status_code=404,
            detail="Order not found. Please verify the order ID.",
        )

    return order
