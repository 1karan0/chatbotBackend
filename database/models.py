from typing import Optional
import datetime
import uuid

from sqlalchemy import Boolean, Date, DateTime, Enum, ForeignKeyConstraint, Index, Integer, PrimaryKeyConstraint, String, Text, Uuid, text
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase):
    pass


class PrismaMigrations(Base):
    __tablename__ = '_prisma_migrations'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='_prisma_migrations_pkey'),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    checksum: Mapped[str] = mapped_column(String(64), nullable=False)
    migration_name: Mapped[str] = mapped_column(String(255), nullable=False)
    started_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'))
    applied_steps_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    finished_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True))
    logs: Mapped[Optional[str]] = mapped_column(Text)
    rolled_back_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True))


class Tenants(Base):
    __tablename__ = 'tenants'
    __table_args__ = (
        PrimaryKeyConstraint('tenant_id', name='tenants_pkey'),
        Index('tenants_tenant_name_key', 'tenant_name', unique=True)
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    tenant_name: Mapped[str] = mapped_column(String, nullable=False)
    is_active: Mapped[Optional[bool]] = mapped_column(Boolean)
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(TIMESTAMP(True, 6), server_default=text('CURRENT_TIMESTAMP'))
    updated_at: Mapped[Optional[datetime.datetime]] = mapped_column(TIMESTAMP(True, 6), server_default=text('CURRENT_TIMESTAMP'))

    knowledge_sources: Mapped[list["KnowledgeSources"]] = relationship("KnowledgeSources",back_populates="tenant",cascade="all, delete-orphan",passive_deletes=True)   
    users: Mapped[list['Users']] = relationship('Users', back_populates='tenantsTenant')


class KnowledgeSources(Base):
    __tablename__ = 'knowledge_sources'
    __table_args__ = (
        ForeignKeyConstraint(['tenant_id'], ['tenants.tenant_id'], ondelete='CASCADE', name='knowledge_sources_tenant_id_fkey'),
        PrimaryKeyConstraint('source_id', name='knowledge_sources_pkey')
    )

    source_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False
    )    
    tenant_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    source_type: Mapped[str] = mapped_column(String, nullable=False)
    source_url: Mapped[Optional[str]] = mapped_column(Text)
    source_content: Mapped[Optional[str]] = mapped_column(Text)
    file_name: Mapped[Optional[str]] = mapped_column(String)
    file_content: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[Optional[str]] = mapped_column(String)
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    source_metadata: Mapped[Optional[dict]] = mapped_column(JSONB)
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(TIMESTAMP(True, 6), server_default=text('CURRENT_TIMESTAMP'))
    updated_at: Mapped[Optional[datetime.datetime]] = mapped_column(TIMESTAMP(True, 6), server_default=text('CURRENT_TIMESTAMP'))

    tenant: Mapped['Tenants'] = relationship('Tenants', back_populates='knowledge_sources')


class Users(Base):
    __tablename__ = 'users'
    __table_args__ = (
        ForeignKeyConstraint(['tenantsTenant_id'], ['tenants.tenant_id'], ondelete='SET NULL', onupdate='CASCADE', name='users_tenantsTenant_id_fkey'),
        PrimaryKeyConstraint('id', name='users_pkey'),
        Index('users_email_idx', 'email'),
        Index('users_email_key', 'email', unique=True)
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, server_default=text('gen_random_uuid()'))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    image: Mapped[Optional[str]] = mapped_column(Text)
    createdAt: Mapped[Optional[datetime.datetime]] = mapped_column(TIMESTAMP(precision=6), server_default=text('CURRENT_TIMESTAMP'))
    updatedAt: Mapped[Optional[datetime.datetime]] = mapped_column(TIMESTAMP(precision=6))
    bio: Mapped[Optional[str]] = mapped_column(Text)
    location: Mapped[Optional[str]] = mapped_column(String(255))
    website: Mapped[Optional[str]] = mapped_column(String(500))
    workspace: Mapped[Optional[str]] = mapped_column(String(255))
    tenantsTenant_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid)

    tenantsTenant: Mapped[Optional['Tenants']] = relationship('Tenants', back_populates='users')
    bots: Mapped[list['Bots']] = relationship('Bots', back_populates='users')
    conversations: Mapped[list['Conversations']] = relationship('Conversations', back_populates='users')


class Bots(Base):
    __tablename__ = 'bots'
    __table_args__ = (
        ForeignKeyConstraint(['userId'], ['users.id'], ondelete='CASCADE', onupdate='CASCADE', name='bots_userId_fkey'),
        PrimaryKeyConstraint('id', name='bots_pkey'),
        Index('bots_apiKey_key', 'apiKey', unique=True),
        Index('bots_isPublic_status_idx', 'isPublic', 'status'),
        Index('bots_userId_idx', 'userId')
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, server_default=text('gen_random_uuid()'))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(Enum('DRAFT', 'PUBLISHED', 'DEPLOYED', 'ARCHIVED', name='BotStatus'), nullable=False, server_default=text('\'DRAFT\'::"BotStatus"'))
    isPublic: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('false'))
    config: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    flows: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=text("'[]'::jsonb"))
    intents: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=text("'[]'::jsonb"))
    entities: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=text("'[]'::jsonb"))
    totalConversations: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    totalMessages: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    userId: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    createdAt: Mapped[datetime.datetime] = mapped_column(TIMESTAMP(precision=6), nullable=False, server_default=text('CURRENT_TIMESTAMP'))
    updatedAt: Mapped[datetime.datetime] = mapped_column(TIMESTAMP(precision=6), nullable=False)
    tenant_id: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(1000))
    avatar: Mapped[Optional[str]] = mapped_column(String(500))
    deploymentUrl: Mapped[Optional[str]] = mapped_column(String(500))
    apiKey: Mapped[Optional[str]] = mapped_column(String(255))

    users: Mapped['Users'] = relationship('Users', back_populates='bots')
    bot_analytics: Mapped[list['BotAnalytics']] = relationship('BotAnalytics', back_populates='bots')
    conversations: Mapped[list['Conversations']] = relationship('Conversations', back_populates='bots')
    knowledge_base: Mapped[list['KnowledgeBase']] = relationship('KnowledgeBase', back_populates='bots')
    themes: Mapped[list['Themes']] = relationship('Themes', back_populates='bots')


class BotAnalytics(Base):
    __tablename__ = 'bot_analytics'
    __table_args__ = (
        ForeignKeyConstraint(['botId'], ['bots.id'], ondelete='CASCADE', onupdate='CASCADE', name='bot_analytics_botId_fkey'),
        PrimaryKeyConstraint('id', name='bot_analytics_pkey'),
        Index('bot_analytics_botId_date_key', 'botId', 'date', unique=True)
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, server_default=text('gen_random_uuid()'))
    botId: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    conversations: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    messages: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    uniqueUsers: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    createdAt: Mapped[datetime.datetime] = mapped_column(TIMESTAMP(precision=6), nullable=False, server_default=text('CURRENT_TIMESTAMP'))

    bots: Mapped['Bots'] = relationship('Bots', back_populates='bot_analytics')


class Conversations(Base):
    __tablename__ = 'conversations'
    __table_args__ = (
        ForeignKeyConstraint(['botId'], ['bots.id'], ondelete='CASCADE', onupdate='CASCADE', name='conversations_botId_fkey'),
        ForeignKeyConstraint(['userId'], ['users.id'], ondelete='SET NULL', onupdate='CASCADE', name='conversations_userId_fkey'),
        PrimaryKeyConstraint('id', name='conversations_pkey'),
        Index('conversations_botId_sessionId_idx', 'botId', 'sessionId'),
        Index('conversations_userId_idx', 'userId')
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, server_default=text('gen_random_uuid()'))
    sessionId: Mapped[str] = mapped_column(String(255), nullable=False)
    botId: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    messages: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=text("'[]'::jsonb"))
    context: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    metadata_: Mapped[dict] = mapped_column('metadata', JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    isActive: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('true'))
    createdAt: Mapped[datetime.datetime] = mapped_column(TIMESTAMP(precision=6), nullable=False, server_default=text('CURRENT_TIMESTAMP'))
    updatedAt: Mapped[datetime.datetime] = mapped_column(TIMESTAMP(precision=6), nullable=False)
    userId: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid)

    bots: Mapped['Bots'] = relationship('Bots', back_populates='conversations')
    users: Mapped[Optional['Users']] = relationship('Users', back_populates='conversations')


class KnowledgeBase(Base):
    __tablename__ = 'knowledge_base'
    __table_args__ = (
        ForeignKeyConstraint(['botId'], ['bots.id'], ondelete='CASCADE', onupdate='CASCADE', name='knowledge_base_botId_fkey'),
        PrimaryKeyConstraint('id', name='knowledge_base_pkey'),
        Index('knowledge_base_botId_status_idx', 'botId', 'status')
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, server_default=text('gen_random_uuid()'))
    botId: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    createdAt: Mapped[datetime.datetime] = mapped_column(TIMESTAMP(precision=6), nullable=False, server_default=text('CURRENT_TIMESTAMP'))
    updatedAt: Mapped[datetime.datetime] = mapped_column(TIMESTAMP(precision=6), nullable=False)
    status: Mapped[str] = mapped_column(Enum('PENDING', 'PROCESSING', 'READY', 'FAILED', name='KnowledgeBaseStatus'), nullable=False, server_default=text('\'PENDING\'::"KnowledgeBaseStatus"'))
    type: Mapped[str] = mapped_column(Enum('TEXT', 'URL', 'FILE', name='KnowledgeBaseType'), nullable=False, server_default=text('\'TEXT\'::"KnowledgeBaseType"'))
    metadata_: Mapped[Optional[dict]] = mapped_column('metadata', JSONB, server_default=text("'{}'::jsonb"))
    filePath: Mapped[Optional[str]] = mapped_column(String(500))
    fileSize: Mapped[Optional[int]] = mapped_column(Integer)
    mimeType: Mapped[Optional[str]] = mapped_column(String(100))
    sourceUrl: Mapped[Optional[str]] = mapped_column(String(255))

    bots: Mapped['Bots'] = relationship('Bots', back_populates='knowledge_base')


class Themes(Base):
    __tablename__ = 'themes'
    __table_args__ = (
        ForeignKeyConstraint(['botId'], ['bots.id'], ondelete='CASCADE', onupdate='CASCADE', name='themes_botId_fkey'),
        PrimaryKeyConstraint('id', name='themes_pkey'),
        Index('themes_botId_key', 'botId', unique=True)
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, server_default=text('gen_random_uuid()'))
    botId: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    primaryColor: Mapped[str] = mapped_column(String(50), nullable=False)
    secondaryColor: Mapped[str] = mapped_column(String(50), nullable=False)
    backgroundColor: Mapped[str] = mapped_column(String(50), nullable=False)
    fontSize: Mapped[str] = mapped_column(String(20), nullable=False)
    borderRadius: Mapped[str] = mapped_column(String(20), nullable=False)
    chatWidth: Mapped[str] = mapped_column(String(20), nullable=False)
    chatHeight: Mapped[str] = mapped_column(String(20), nullable=False)
    createdAt: Mapped[datetime.datetime] = mapped_column(TIMESTAMP(precision=6), nullable=False, server_default=text('CURRENT_TIMESTAMP'))
    updatedAt: Mapped[datetime.datetime] = mapped_column(TIMESTAMP(precision=6), nullable=False)
    fontFamily: Mapped[str] = mapped_column(Enum('Inter', 'Roboto', 'OpenSans', 'System', name='FontFamily'), nullable=False, server_default=text('\'Inter\'::"FontFamily"'))
    chatPosition: Mapped[str] = mapped_column(String(30), nullable=False)
    customCSS: Mapped[Optional[str]] = mapped_column(Text)
    bottomColor: Mapped[Optional[str]] = mapped_column(String(50))
    chattextColor: Mapped[Optional[str]] = mapped_column(String(50))
    yourtextColor: Mapped[Optional[str]] = mapped_column(String(50))

    bots: Mapped['Bots'] = relationship('Bots', back_populates='themes')
