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
    suggestions: Optional[List[str]] = []
    images: Optional[List[SourceImage]] = Field(default_factory=list, description="Image URLs from the sources used (e.g. from web pages)") 


# 🏢 ---------------- TENANT ----------------
class TenantCreate(BaseModel):
    """Request model for creating a new tenant."""
    tenant_id: Optional[UUID] = Field(None, description="Unique tenant identifier")
    tenant_name: str = Field(..., description="Human-readable tenant name")
    username: str = Field(..., description="Admin username for the tenant")
    password: str = Field(..., description="Admin password for the tenant")


class TenantInfo(BaseModel):
    """Response model for tenant information."""
    tenant_id: UUID
    tenant_name: str
    created_at: datetime

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


class UserInfo(BaseModel):
    """Response model for user information."""
    user_id: UUID
    username: str
    tenant_id: UUID
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True
        json_encoders = {UUID: lambda v: str(v)}


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
