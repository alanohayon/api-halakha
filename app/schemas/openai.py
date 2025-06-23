from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from enum import Enum


class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"


class ToolResources(BaseModel):
    code_interpreter: Optional[Dict[str, Any]] = None
    file_search: Optional[Dict[str, Any]] = None


class ThreadMessage(BaseModel):
    role: MessageRole
    content: str
    attachments: Optional[List[Dict[str, Any]]] = None
    metadata: Optional[Dict[str, str]] = None


class CreateThreadRequest(BaseModel):
    messages: Optional[List[ThreadMessage]] = Field(default=None, description="Messages initiaux du thread")
    metadata: Optional[Dict[str, str]] = Field(default=None, description="Métadonnées du thread")
    tool_resources: Optional[ToolResources] = Field(default=None, description="Ressources d'outils")


class ThreadResponse(BaseModel):
    id: str
    object: str = "thread"
    created_at: int
    metadata: Optional[Dict[str, str]] = None
    tool_resources: Optional[Dict[str, Any]] = None


class ModifyThreadRequest(BaseModel):
    metadata: Optional[Dict[str, str]] = Field(default=None, description="Nouvelles métadonnées")
    tool_resources: Optional[ToolResources] = Field(default=None, description="Nouvelles ressources d'outils")


class DeleteThreadResponse(BaseModel):
    id: str
    object: str = "thread.deleted"
    deleted: bool


class CreateMessageRequest(BaseModel):
    role: MessageRole
    content: str
    attachments: Optional[List[Dict[str, Any]]] = None
    metadata: Optional[Dict[str, str]] = None


class MessageResponse(BaseModel):
    id: str
    object: str = "thread.message"
    created_at: int
    thread_id: str
    role: MessageRole
    content: List[Dict[str, Any]]
    attachments: Optional[List[Dict[str, Any]]] = None
    metadata: Optional[Dict[str, str]] = None


class ListMessagesResponse(BaseModel):
    object: str = "list"
    data: List[MessageResponse]
    first_id: Optional[str] = None
    last_id: Optional[str] = None
    has_more: bool


class CreateRunRequest(BaseModel):
    assistant_id: str
    model: Optional[str] = None
    instructions: Optional[str] = None
    additional_instructions: Optional[str] = None
    additional_messages: Optional[List[ThreadMessage]] = None
    tools: Optional[List[Dict[str, Any]]] = None
    metadata: Optional[Dict[str, str]] = None
    temperature: Optional[float] = Field(default=None, ge=0.0, le=2.0)
    top_p: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    max_prompt_tokens: Optional[int] = Field(default=None, ge=256)
    max_completion_tokens: Optional[int] = Field(default=None, ge=256)
    truncation_strategy: Optional[Dict[str, Any]] = None
    tool_choice: Optional[Dict[str, Any]] = None
    parallel_tool_calls: Optional[bool] = None
    response_format: Optional[Dict[str, Any]] = None


class RunResponse(BaseModel):
    id: str
    object: str = "thread.run"
    created_at: int
    thread_id: str
    assistant_id: str
    status: str
    required_action: Optional[Dict[str, Any]] = None
    last_error: Optional[Dict[str, Any]] = None
    expires_at: Optional[int] = None
    started_at: Optional[int] = None
    cancelled_at: Optional[int] = None
    failed_at: Optional[int] = None
    completed_at: Optional[int] = None
    incomplete_details: Optional[Dict[str, Any]] = None
    model: str
    instructions: Optional[str] = None
    tools: List[Dict[str, Any]]
    metadata: Optional[Dict[str, str]] = None
    usage: Optional[Dict[str, Any]] = None
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    max_prompt_tokens: Optional[int] = None
    max_completion_tokens: Optional[int] = None
    truncation_strategy: Optional[Dict[str, Any]] = None
    tool_choice: Optional[Dict[str, Any]] = None
    parallel_tool_calls: Optional[bool] = None
    response_format: Optional[Dict[str, Any]] = None


class ThreadWithRunRequest(BaseModel):
    assistant_id: str
    thread: Optional[CreateThreadRequest] = None
    model: Optional[str] = None
    instructions: Optional[str] = None
    tools: Optional[List[Dict[str, Any]]] = None
    tool_resources: Optional[ToolResources] = None
    metadata: Optional[Dict[str, str]] = None
    temperature: Optional[float] = Field(default=None, ge=0.0, le=2.0)
    top_p: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    max_prompt_tokens: Optional[int] = Field(default=None, ge=256)
    max_completion_tokens: Optional[int] = Field(default=None, ge=256)
    truncation_strategy: Optional[Dict[str, Any]] = None
    tool_choice: Optional[Dict[str, Any]] = None
    parallel_tool_calls: Optional[bool] = None
    response_format: Optional[Dict[str, Any]] = None


class ThreadWithRunResponse(BaseModel):
    id: str
    object: str = "thread.run"
    created_at: int
    thread_id: str
    assistant_id: str
    status: str
    required_action: Optional[Dict[str, Any]] = None
    last_error: Optional[Dict[str, Any]] = None
    expires_at: Optional[int] = None
    started_at: Optional[int] = None
    cancelled_at: Optional[int] = None
    failed_at: Optional[int] = None
    completed_at: Optional[int] = None
    incomplete_details: Optional[Dict[str, Any]] = None
    model: str
    instructions: Optional[str] = None
    tools: List[Dict[str, Any]]
    metadata: Optional[Dict[str, str]] = None
    usage: Optional[Dict[str, Any]] = None
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    max_prompt_tokens: Optional[int] = None
    max_completion_tokens: Optional[int] = None
    truncation_strategy: Optional[Dict[str, Any]] = None
    tool_choice: Optional[Dict[str, Any]] = None
    parallel_tool_calls: Optional[bool] = None
    response_format: Optional[Dict[str, Any]] = None


class OpenAIErrorResponse(BaseModel):
    error: Dict[str, Any]
    message: str
    type: str
    param: Optional[str] = None
    code: Optional[str] = None
