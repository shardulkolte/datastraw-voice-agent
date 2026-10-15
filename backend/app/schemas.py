# from typing import Literal

# from pydantic import BaseModel, Field


# ConversationLanguage = Literal["english", "hinglish"]


# class ChatRequest(BaseModel):
#     message: str = Field(min_length=1, max_length=2000)
#     language: ConversationLanguage = "english"


# class ChatResponse(BaseModel):
#     reply: str





from typing import Literal

from pydantic import BaseModel, Field


ConversationLanguage = Literal["english", "hinglish"]


class ConversationTurn(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=2000)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    language: ConversationLanguage = "english"
    history: list[ConversationTurn] = Field(
        default_factory=list,
        max_length=40,
    )


class ChatResponse(BaseModel):
    reply: str
