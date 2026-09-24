from typing import List, Optional, Literal
from pydantic import BaseModel, Field


class PageIndexRequest(BaseModel):
    url: str = Field(..., min_length=1, max_length=2048)
    title: str = Field(default="", max_length=1000)
    text: str = Field(..., min_length=1)
    truncated: bool = Field(default=False)
    lang: str = Field(default="en", max_length=20)


class PageIndexResponse(BaseModel):
    page_id: str
    title: str
    char_count: int
    chunk_count: int
    truncated: bool
    cached: bool


class SourceItem(BaseModel):
    id: int
    chunk_id: int
    text: str
    score: float


class ChatHistoryMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(..., max_length=2000)


class ChatRequest(BaseModel):
    page_id: str = Field(..., min_length=8, max_length=64)
    question: str = Field(..., min_length=1, max_length=1000)
    style: Literal["simple", "detailed"] = Field(default="simple")
    history: List[ChatHistoryMessage] = Field(default_factory=list, max_length=8)


class SummarizeRequest(BaseModel):
    page_id: str = Field(..., min_length=8, max_length=64)
    style: Literal["simple", "detailed"] = Field(default="simple")


class ExplainSelectionRequest(BaseModel):
    page_id: str = Field(..., min_length=8, max_length=64)
    selection: str = Field(..., min_length=1, max_length=4000)
    style: Literal["simple", "detailed"] = Field(default="simple")
