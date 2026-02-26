import os
os.environ["LANGCHAIN_TELEMETRY"] = "false"
import sys
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from contextlib import asynccontextmanager

# Fix SQLite for ChromaDB compatibility
try:
    __import__('pysqlite3')
    sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
except ImportError:
    pass

from config.settings import settings
from database.connection import create_tables
from services.retrieval_service_v2 import retrieval_service
from api.auth_routes import router as auth_router
from api.chat_routes import router as chat_router
from api.knowledge_routes import router as knowledge_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    print("Starting up Multi-Tenant RAG Chatbot...")
    
    # Set OpenAI API key
    if settings.openai_api_key:
        os.environ["OPENAI_API_KEY"] = settings.openai_api_key
    else:
        print("Warning: OPENAI_API_KEY not set!")
    
    # Create database tables
    create_tables()
    print("Database tables created/verified")
    
    # Initialize retrieval service
    success = retrieval_service.initialize_database()
    if not success:
        print("Warning: Failed to initialize retrieval database")
    else:
        print("Retrieval service initialized successfully")
    
    yield
    
    # Shutdown
    print("Shutting down Multi-Tenant RAG Chatbot...")

# Create FastAPI application
app = FastAPI(
    title="Multi-Tenant RAG Chatbot",
    description="A multi-tenant chatbot using RAG (Retrieval-Augmented Generation) with JWT authentication",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router)
app.include_router(chat_router)
app.include_router(knowledge_router)

@app.get("/", include_in_schema=False)
async def root():
    """Redirect root to docs."""
    return RedirectResponse(url="/docs")

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "Multi-Tenant RAG Chatbot",
        "version": "1.0.0"
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )