from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

Base = declarative_base()

# ---------- TENANTS ----------
class Tenant(Base):
    """Tenant model for multi-tenant architecture."""
    __tablename__ = "tenants"

    tenant_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_name = Column(String, nullable=False, unique=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    users = relationship("User", back_populates="tenant", cascade="all, delete-orphan")
    knowledge_sources = relationship("KnowledgeSource", back_populates="tenant", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Tenant(id={self.tenant_id}, name={self.tenant_name})>"


# ---------- USERS ----------
class User(Base):
    """User model aligned with Prisma 'users' table."""
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    image = Column(String, nullable=True)
    bio = Column(Text, nullable=True)
    location = Column(String(255), nullable=True)
    website = Column(String(500), nullable=True)
    workspace = Column(String(255), nullable=True)
    tenantsTenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.tenant_id", ondelete="SET NULL"), nullable=True)

    createdAt = Column(DateTime(timezone=True), server_default=func.now())
    updatedAt = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    tenant = relationship("Tenant", back_populates="users")

    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, tenant={self.tenantsTenant_id})>"


# ---------- KNOWLEDGE SOURCES ----------
class KnowledgeSource(Base):
    """Knowledge source model aligned with Prisma 'knowledge_sources' table."""
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

    # Relationship
    tenant = relationship("Tenant", back_populates="knowledge_sources")

    def __repr__(self):
        return f"<KnowledgeSource(id={self.source_id}, type={self.source_type}, tenant={self.tenant_id})>"
