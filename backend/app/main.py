
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session

from backend.app.database import Base, SessionLocal, engine, get_db
from backend.app.models import OrderRecord, OrderResponse
from backend.app.services.order_seed import seed_orders
from backend.app.tools.orders import get_order_details
from fastapi import HTTPException
from backend.app.schemas import ChatRequest, ChatResponse
from backend.app.services.gemini_agent import ask_gemini

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


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    try:
        reply = ask_gemini(request.message)
        return ChatResponse(reply=reply)

    except RuntimeError as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        # Keep detailed provider errors in server logs,
        # rather than exposing them to the customer.
        print(f"Gemini request failed: {exc}")

        raise HTTPException(
            status_code=502,
            detail="The AI service is temporarily unavailable.",
        ) from exc