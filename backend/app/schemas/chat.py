from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Union
from enum import Enum


class MessageRole(str, Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    FUNCTION = "function"
    TOOL = "tool"


class ChatMessage(BaseModel):
    role: MessageRole
    content: Optional[str] = None
    name: Optional[str] = None
    function_call: Optional[Dict[str, Any]] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None


class ChatCompletionRequest(BaseModel):
    model: str = Field(..., description="Model to use for completion")
    messages: List[ChatMessage]
    temperature: Optional[float] = Field(1.0, ge=0, le=2)
    top_p: Optional[float] = Field(1.0, ge=0, le=1)
    n: Optional[int] = Field(1, ge=1, le=10)
    stream: Optional[bool] = False
    max_tokens: Optional[int] = None
    presence_penalty: Optional[float] = Field(0, ge=-2, le=2)
    frequency_penalty: Optional[float] = Field(0, ge=-2, le=2)
    stop: Optional[Union[str, List[str]]] = None
    user: Optional[str] = None
    functions: Optional[List[Dict[str, Any]]] = None
    function_call: Optional[Union[str, Dict[str, str]]] = None
    tools: Optional[List[Dict[str, Any]]] = None
    tool_choice: Optional[Union[str, Dict[str, Any]]] = None


class ChatChoice(BaseModel):
    index: int
    message: ChatMessage
    finish_reason: Optional[str] = None


class Usage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class ChatCompletionResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[ChatChoice]
    usage: Usage
    system_fingerprint: Optional[str] = None


class EmbeddingRequest(BaseModel):
    model: str
    input: Union[str, List[str]]
    encoding_format: Optional[str] = "float"
    dimensions: Optional[int] = None
    user: Optional[str] = None


class EmbeddingData(BaseModel):
    object: str = "embedding"
    embedding: List[float]
    index: int


class EmbeddingResponse(BaseModel):
    object: str = "list"
    data: List[EmbeddingData]
    model: str
    usage: Dict[str, int]


class ImageGenerationRequest(BaseModel):
    model: str = "dall-e-3"
    prompt: str
    n: Optional[int] = 1
    size: Optional[str] = "1024x1024"
    quality: Optional[str] = "standard"
    style: Optional[str] = "vivid"
    response_format: Optional[str] = "url"
    user: Optional[str] = None


class ImageData(BaseModel):
    url: Optional[str] = None
    b64_json: Optional[str] = None
    revised_prompt: Optional[str] = None


class ImageGenerationResponse(BaseModel):
    created: int
    data: List[ImageData]
