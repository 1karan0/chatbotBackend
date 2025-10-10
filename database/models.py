from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

Base = declarative_base()

class Tenant(Base):
    """Tenant model for multi-tenant architecture."""
    __tablename__ = "tenants"

    tenant_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_name = Column(String, nullable=False, unique=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    backendusers = relationship("User", back_populates="tenant", cascade="all, delete-orphan")
    knowledge_sources = relationship("KnowledgeSource", back_populates="tenant", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Tenant(id={self.tenant_id}, name={self.tenant_name})>"


class User(Base):
    """User model for authentication and tenant association."""
    __tablename__ = "backendusers"

    user_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String, nullable=False, unique=True)
    hashed_password = Column(String, nullable=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.tenant_id", ondelete="CASCADE"), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    tenant = relationship("Tenant", back_populates="backendusers")

    def __repr__(self):
        return f"<User(id={self.user_id}, username={self.username}, tenant={self.tenant_id})>"


class KnowledgeSource(Base):
    """Knowledge source model for storing URLs, text, and files."""
    __tablename__ = "knowledge_sources"

    source_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.tenant_id", ondelete="CASCADE"), nullable=False)
    source_type = Column(String, nullable=False)
    source_url = Column(Text, nullable=True)
    source_content = Column(Text, nullable=True)
    file_name = Column(String, nullable=True)
    file_content = Column(Text, nullable=True)
    status = Column(String, default="pending")
    error_message = Column(Text, nullable=True)
    source_metadata = Column(JSONB, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    tenant = relationship("Tenant", back_populates="knowledge_sources")

    def __repr__(self):
        return f"<KnowledgeSource(id={self.source_id}, type={self.source_type}, tenant={self.tenant_id})>"
