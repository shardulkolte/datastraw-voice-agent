from typing import Literal

from pydantic import BaseModel, Field


ConversationLanguage = Literal["english", "hinglish"]


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    language: ConversationLanguage = "english"


class ChatResponse(BaseModel):
    reply: str
