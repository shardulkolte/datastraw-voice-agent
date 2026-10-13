
from fastapi import FastAPI, HTTPException

from backend.app.models import Order
from backend.app.tools.orders import get_order_details


app = FastAPI(
    title="Aura Skincare Voice Agent",
    description="AI-powered customer support API for Aura Skincare",
    version="1.0.0",
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


@app.get("/orders/{order_id}", response_model=Order)
def get_order(order_id: str):
    order = get_order_details(order_id)

    if order is None:
        raise HTTPException(
            status_code=404,
            detail="Order not found. Please verify the order ID.",
        )

    return order
