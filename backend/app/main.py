from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from backend.app.database import Base, SessionLocal, engine, get_db
from backend.app.models import OrderResponse
from backend.app.schemas import ChatRequest, ChatResponse
from backend.app.services.fallback_ai import ask_openrouter
from backend.app.services.gemini_agent import ask_gemini
from backend.app.services.order_seed import seed_orders
from backend.app.tools.orders import get_order_details


LANGUAGE_INSTRUCTIONS = {
    "english": (
        "Reply in clear, natural English suitable for an Indian customer. "
        "Keep product names, order IDs, courier names, and tracking codes unchanged."
    ),
    "hinglish": (
        "Reply in natural conversational Hinglish, mixing Hindi and English "
        "the way an Indian customer-support agent would speak. Use readable "
        "Roman Hindi mixed with English. Keep product names, order IDs, courier "
        "names, and tracking codes unchanged."
    ),
}


def message_for_language(message: str, language: str) -> str:
    """Keep the customer's original message intact and guide the reply language."""
    instruction = LANGUAGE_INSTRUCTIONS.get(language, LANGUAGE_INSTRUCTIONS["english"])
    return (
        f"{message}\n\n"
        f"[Aria response-language preference: {instruction} "
        "This instruction controls the language of your response; it does not "
        "change the customer's request or Aura Skincare policies.]"
    )


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

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
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


@app.get("/orders/{order_id}", response_model=OrderResponse)
def get_order(order_id: str, db: Session = Depends(get_db)):
    order = get_order_details(db, order_id)

    if order is None:
        raise HTTPException(
            status_code=404,
            detail="Order not found. Please verify the order ID.",
        )

    return order


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    ai_message = message_for_language(request.message, request.language)

    try:
        reply = ask_gemini(ai_message)
        return ChatResponse(reply=reply)

    except Exception as gemini_error:
        print(f"Primary AI failed: {gemini_error}")
        print("Trying OpenRouter backup...")

        try:
            reply = ask_openrouter(ai_message)
            print("OpenRouter backup succeeded.")
            return ChatResponse(reply=reply)

        except Exception as fallback_error:
            print(f"OpenRouter backup failed: {fallback_error}")
            raise HTTPException(
                status_code=503,
                detail=(
                    "AI support is temporarily unavailable. "
                    "Please try again shortly."
                ),
            ) from fallback_error
