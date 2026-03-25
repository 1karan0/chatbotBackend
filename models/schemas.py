from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from uuid import UUID


# 🔐 ---------------- AUTH ----------------
class TokenRequest(BaseModel):
    """Request model for authentication token."""
    username: str = Field(..., description="Username for authentication")
    password: str = Field(..., description="Password for authentication")


class TokenResponse(BaseModel):
    """Response model for authentication token."""
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration in seconds")


# 💬 ---------------- QUESTION ----------------
class QuestionRequest(BaseModel):
    """Request model for asking questions."""
    question: str = Field(..., description="The question to ask", min_length=1)
    tenant_id: UUID = Field(..., description="Tenant ID for the question")
    session_id: Optional[str] = Field(None, description="Session ID to group messages in one conversation. Omit or set new_conversation=true when starting a new chat to get a new id.")
    new_conversation: bool = Field(False, description="If true, start a new conversation: a new session_id is generated and returned; use it for all later messages in this chat.")


class SourceImage(BaseModel):
    """Image from a knowledge source (e.g. scraped from a URL)."""
    url: str = Field(..., description="Image URL to display")
    alt: Optional[str] = Field("", description="Alt text")
    title: Optional[str] = Field(None, description="Title attribute")


class QuestionResponse(BaseModel):
    """Response model for question answers."""
    answer: str = Field(..., description="The answer to the question")
    sources: List[str] = Field(..., description="Sources used for the answer")
    tenant_id: UUID = Field(..., description="Tenant ID that provided the answer")
    session_id: str = Field(..., description="Session ID used for this message. Use this same value for GET /chat/conversation and for the next POST /chat/ask to keep the thread.")
    suggestions: Optional[List[str]] = []
    images: Optional[List[SourceImage]] = Field(default_factory=list, description="Image URLs from the sources used (e.g. from web pages)")
    question_hint: Optional[str] = Field(None, description="Optional friendly hint when the question was very long, suggesting the user shorten it for better results")


# 💬 ---------------- CONVERSATION (for frontend display) ----------------
class ConversationMessage(BaseModel):
    """Single message in a conversation (user or bot)."""
    role: str = Field(..., description="'user' or 'bot'")
    text: str = Field(..., description="Message content")
    timestamp: Optional[str] = Field(None, description="ISO timestamp when the message was sent")
    images: Optional[List[SourceImage]] = Field(default_factory=list, description="Images attached to this message (e.g. bot response images)")


class ConversationResponse(BaseModel):
    """Response model for conversation history (chatbot + user messages)."""
    conversation_id: Optional[UUID] = Field(None, description="Conversation ID")
    session_id: str = Field(..., description="Session identifier for this chat")
    tenant_id: str = Field(..., description="Tenant ID")
    messages: List[ConversationMessage] = Field(default_factory=list, description="Ordered list of user and bot messages")
    created_at: Optional[datetime] = Field(None, description="When the conversation was created")
    updated_at: Optional[datetime] = Field(None, description="When the conversation was last updated")

    class Config:
        json_encoders = {UUID: lambda v: str(v)}


class ConversationListItem(BaseModel):
    """Summary of one conversation for the list view."""
    conversation_id: UUID = Field(..., description="Conversation ID")
    session_id: str = Field(..., description="Session ID; use this for GET /chat/conversation")
    tenant_id: str = Field(..., description="Tenant ID")
    messages: List[ConversationMessage] = Field(default_factory=list, description="Ordered list of user and bot messages")
    preview: Optional[str] = Field(None, description="Short preview of the last message (e.g. first 80 chars)")
    created_at: Optional[datetime] = Field(None, description="When the conversation was created")
    updated_at: Optional[datetime] = Field(None, description="When the conversation was last updated")

    class Config:
        json_encoders = {UUID: lambda v: str(v)}


class ConversationListResponse(BaseModel):
    """Response model for listing all conversations (total conversations)."""
    conversations: List[ConversationListItem] = Field(default_factory=list, description="All conversations for the tenant, newest first")
    total: int = Field(0, description="Total number of conversations") 


# 🏢 ---------------- TENANT ----------------
class TenantCreate(BaseModel):
    """Request model for creating a new tenant."""
    tenant_id: Optional[UUID] = Field(None, description="Unique tenant identifier")
    tenant_name: str = Field(..., description="Human-readable tenant name")
    user_id: str = Field(..., description="User ID for the tenant")



class UserInfo(BaseModel):
    """Response model for user information."""
    user_id: UUID
    username: Optional[str] = None
    tenant_id: Optional[UUID] = None
    tenant_ids: List[UUID] = Field(default_factory=list, description="Tenant IDs linked to this user")
    is_active: Optional[bool] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
        json_encoders = {UUID: lambda v: str(v)}



class TenantUserInfo(BaseModel):
    """User summary in tenant response."""
    user_id: UUID
    username: Optional[str] = None

    class Config:
        json_encoders = {UUID: lambda v: str(v)}


class TenantInfo(BaseModel):
    """Response model for tenant information."""
    tenant_id: UUID
    tenant_name: str
    created_at: Optional[datetime] = None
    user_id: Optional[UUID] = Field(None, description="Linked user ID for the tenant")
    user: Optional[UserInfo] = None

    class Config:
        from_attributes = True
        json_encoders = {UUID: lambda v: str(v)}


# 👤 ---------------- USER ----------------
class UserCreate(BaseModel):
    """Request model for creating a new user."""
    username: str = Field(..., description="Unique username")
    password: str = Field(..., description="User password", min_length=8)
    tenant_id: UUID = Field(..., description="Tenant ID the user belongs to")

    class Config:
        from_attributes = True


# ⚠️ ---------------- ERROR ----------------
class ErrorResponse(BaseModel):
    """Standard error response model."""
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error information")
    code: Optional[str] = Field(None, description="Error code")


# 📚 ---------------- KNOWLEDGE SOURCE ----------------
class KnowledgeSourceCreate(BaseModel):
    """Request model for creating a knowledge source."""
    source_type: str = Field(..., description="Type: url, text, or file")
    source_url: Optional[str] = Field(None, description="URL if type is url")
    source_content: Optional[str] = Field(None, description="Text content if type is text")
    file_name: Optional[str] = Field(None, description="File name if type is file")
    file_content: Optional[str] = Field(None, description="File content if type is file")


class KnowledgeSourceInfo(BaseModel):
    """Response model for knowledge source information."""
    source_id: UUID
    tenant_id: UUID
    source_type: str
    source_url: Optional[str]
    file_name: Optional[str]
    status: str
    error_message: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True
        json_encoders = {UUID: lambda v: str(v)}


# ⚙️ ---------------- PROCESS STATUS ----------------
class ProcessingStatus(BaseModel):
    """Response model for processing status."""
    source_id: UUID
    status: str
    message: str
    error_message: Optional[str] = None

    class Config:
        json_encoders = {UUID: lambda v: str(v)}
