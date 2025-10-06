# Multi-Tenant RAG Chatbot API

A production-ready multi-tenant chatbot backend using Retrieval-Augmented Generation (RAG) with JWT authentication. This system allows multiple tenants to create custom chatbots trained on their own knowledge sources (URLs, text, and files).

## Features

- **Multi-tenant architecture** with complete data isolation
- **Dynamic knowledge ingestion** from URLs, text content, and file uploads
- **Vector-based semantic search** using OpenAI embeddings and ChromaDB
- **JWT authentication** for secure API access
- **RESTful API** with automatic Swagger documentation
- **Web scraping** for automatic URL content extraction
- **Per-tenant index management** and rebuilding
- **Embed code generation** for website integration
- **Async processing** for handling large documents

## Quick Start

### 1. Install Dependencies

**Option A: Automated Setup (Recommended)**
```bash
./install.sh
```

**Option B: Manual Setup**
```bash
# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
source .venv/bin/activate  # On Linux/Mac
# or
.venv\Scripts\activate  # On Windows

# Install dependencies
pip install -r requirements.txt

# Download NLTK data
python3 -c "import nltk; nltk.download('punkt'); nltk.download('averaged_perceptron_tagger')"
```

### 2. Configure Environment

Edit the `.env` file and add your OpenAI API key:

```bash
OPENAI_API_KEY=your_openai_api_key_here
DATABASE_URL=sqlite:///./app.db
JWT_SECRET_KEY=your_secret_key_change_this_in_production
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=1440
```

### 3. Run the Application

```bash
# Make sure virtual environment is activated
source .venv/bin/activate

# Run the application
python3 main.py
```

The API will be available at: http://localhost:8000

### 4. Access API Documentation

Open your browser and navigate to:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

## API Endpoints

### Authentication

#### Create Tenant
```bash
POST /auth/tenants
Content-Type: application/json

{
  "tenant_id": "my_company",
  "tenant_name": "My Company",
  "username": "admin",
  "password": "secure_password"
}
```

#### Login
```bash
POST /auth/token
Content-Type: application/x-www-form-urlencoded

username=admin&password=secure_password
```

Response:
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

### Knowledge Management

All knowledge endpoints require authentication. Include the token in the Authorization header:
```
Authorization: Bearer eyJ...
```

#### Add URL Source
```bash
POST /knowledge/sources/url
Content-Type: multipart/form-data

url=https://example.com/about-us
```

#### Add Text Source
```bash
POST /knowledge/sources/text
Content-Type: multipart/form-data

text=Your text content here...
title=Product Documentation
```

#### Upload File
```bash
POST /knowledge/sources/file
Content-Type: multipart/form-data

file=@document.txt
```

Supported file types: `.txt`, `.md`, `.csv`, `.pdf`, `.docx`

#### List Knowledge Sources
```bash
GET /knowledge/sources
Authorization: Bearer eyJ...
```

#### Delete Knowledge Source
```bash
DELETE /knowledge/sources/{source_id}
Authorization: Bearer eyJ...
```

#### Rebuild Index
```bash
POST /knowledge/rebuild-index
Authorization: Bearer eyJ...
```

### Chat

#### Ask Question
```bash
POST /chat/ask
Authorization: Bearer eyJ...
Content-Type: application/json

{
  "question": "What are your business hours?"
}
```

Response:
```json
{
  "answer": "Our business hours are Monday-Friday, 9 AM to 5 PM.",
  "sources": ["https://example.com/contact", "Business Info.txt"],
  "tenant_id": "my_company"
}
```

#### Get Chat Status
```bash
GET /chat/status
Authorization: Bearer eyJ...
```

#### Get Embed Code
```bash
GET /chat/embed-code
Authorization: Bearer eyJ...
```

## Architecture

### Technology Stack

- **FastAPI**: Modern, fast web framework for building APIs
- **LangChain**: Framework for building LLM applications
- **ChromaDB**: Vector database for semantic search
- **OpenAI**: Embeddings (text-embedding-3-small) and chat models (gpt-4o-mini)
- **SQLAlchemy**: Database ORM for user and knowledge management
- **BeautifulSoup**: Web scraping and HTML parsing
- **JWT**: Token-based authentication

### Directory Structure

```
├── api/
│   ├── auth_routes.py        # Authentication endpoints
│   ├── chat_routes.py        # Chat and status endpoints
│   └── knowledge_routes.py   # Knowledge management endpoints
├── auth/
│   ├── dependencies.py       # Auth dependencies
│   └── jwt_handler.py        # JWT token handling
├── config/
│   └── settings.py           # Application configuration
├── database/
│   ├── connection.py         # Database connection
│   └── models.py             # SQLAlchemy models
├── models/
│   └── schemas.py            # Pydantic schemas
├── services/
│   ├── data_loader.py        # Legacy data loader
│   ├── document_processor.py # Document processing
│   ├── retrieval_service_v2.py # RAG retrieval service
│   └── web_scraper.py        # Web scraping utility
├── data/                     # Tenant data storage
├── chroma_db/                # Vector database storage
└── main.py                   # Application entry point
```

### Data Flow

1. **Knowledge Ingestion:**
   - User uploads URL/text/file via API
   - Content is extracted and processed
   - Text is chunked into smaller segments
   - Chunks are embedded using OpenAI
   - Embeddings stored in ChromaDB with tenant metadata

2. **Query Processing:**
   - User asks question via API
   - Question is embedded
   - Similar chunks retrieved (filtered by tenant_id)
   - Retrieved context + question sent to GPT
   - Answer returned with sources

3. **Multi-Tenancy:**
   - Each tenant has isolated knowledge base
   - Vector DB uses metadata filtering for tenant isolation
   - JWT tokens contain tenant_id for authorization
   - All queries automatically filtered by tenant

## Integration with Frontend

### Next.js Integration Example

```javascript
// api/chatbot.js
const API_URL = 'http://localhost:8000';
let authToken = null;

export async function login(username, password) {
  const formData = new URLSearchParams();
  formData.append('username', username);
  formData.append('password', password);

  const response = await fetch(`${API_URL}/auth/token`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
    },
    body: formData,
  });

  const data = await response.json();
  authToken = data.access_token;
  return data;
}

export async function addURL(url) {
  const formData = new FormData();
  formData.append('url', url);

  const response = await fetch(`${API_URL}/knowledge/sources/url`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${authToken}`,
    },
    body: formData,
  });

  return await response.json();
}

export async function addText(text, title) {
  const formData = new FormData();
  formData.append('text', text);
  formData.append('title', title);

  const response = await fetch(`${API_URL}/knowledge/sources/text`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${authToken}`,
    },
    body: formData,
  });

  return await response.json();
}

export async function uploadFile(file) {
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch(`${API_URL}/knowledge/sources/file`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${authToken}`,
    },
    body: formData,
  });

  return await response.json();
}

export async function askQuestion(question) {
  const response = await fetch(`${API_URL}/chat/ask`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${authToken}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ question }),
  });

  return await response.json();
}

export async function getKnowledgeSources() {
  const response = await fetch(`${API_URL}/knowledge/sources`, {
    headers: {
      'Authorization': `Bearer ${authToken}`,
    },
  });

  return await response.json();
}
```

## Configuration

### Environment Variables

Create a `.env` file with the following:

```bash
# Required
OPENAI_API_KEY=sk-...

# JWT Configuration
SECRET_KEY=your-super-secret-jwt-key-change-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=30
ALGORITHM=HS256

# Database
DATABASE_URL=sqlite:///./app.db
CHROMA_PATH=./chroma_db
DATA_PATH=./data
```

### Settings

You can customize the following in `config/settings.py`:

- **embedding_model**: OpenAI embedding model (default: text-embedding-3-small)
- **chat_model**: OpenAI chat model (default: gpt-4o-mini)
- **temperature**: LLM temperature (default: 0.0)
- **dense_chunk_size**: Chunk size for documents (default: 800)
- **dense_chunk_overlap**: Chunk overlap (default: 100)
- **retrieval_k**: Number of chunks to retrieve (default: 4)

## Production Deployment

### Security Best Practices

1. **Use strong SECRET_KEY**
   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

2. **Configure CORS properly**
   ```python
   app.add_middleware(
       CORSMiddleware,
       allow_origins=["https://yourdomain.com"],
       allow_credentials=True,
       allow_methods=["*"],
       allow_headers=["*"],
   )
   ```

3. **Use HTTPS** in production

4. **Store secrets securely** (use environment variables, not .env files)

5. **Implement rate limiting**

### Deployment Options

#### Docker
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### Gunicorn (Production)
```bash
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

## Troubleshooting

### Common Issues

**1. "Error: Vector database not available"**
- Ensure OPENAI_API_KEY is set correctly
- Check that ChromaDB directory is writable
- Try reinitializing: DELETE chroma_db folder and restart

**2. "No information to answer question"**
- Add knowledge sources first via /knowledge/sources endpoints
- Check if knowledge sources status is "completed"
- Verify tenant_id matches between sources and chat

**3. "Failed to scrape URL"**
- Check if URL is accessible
- Some websites block automated scraping
- Try adding the content as text instead

**4. Authentication errors**
- Verify token is included in Authorization header
- Check token hasn't expired (default: 30 minutes)
- Ensure format is: `Bearer <token>`

## Recent Updates

### v2.0.0 (Latest) - Botpress-Level Features 🚀
- ✅ **Batch URL Processing** - Add multiple URLs in a single request
- ✅ **Batch File Upload** - Upload multiple files simultaneously
- ✅ **Sitemap Crawler** - Automatically crawl entire websites
- ✅ **Image Extraction** - Extract images with metadata from URLs
- ✅ **Enhanced Error Handling** - Detailed status for each processed item
- ✅ **Comprehensive Documentation** - 6 detailed guides created

### v1.1.0
- ✅ Fixed SQLAlchemy error: Changed `metadata` column to `source_metadata`
- ✅ Added NLTK support and automatic data downloads
- ✅ Added support for PDF and DOCX file uploads
- ✅ Improved document processor with better file type handling
- ✅ Created automated installation script

## 📚 Documentation

| Document | Description |
|----------|-------------|
| `WHATS_NEW.md` | ⭐ Start here! Overview of new features |
| `QUICK_START_FRONTEND.md` | 5-minute Next.js integration guide |
| `FRONTEND_INTEGRATION.md` | Complete integration documentation |
| `API_ENDPOINTS.md` | Quick API reference |
| `CHANGES_SUMMARY.md` | Detailed technical changes |
| `BACKEND_COMPARISON.md` | Compare with Botpress |

## New API Endpoints

### Batch Processing
- `POST /knowledge/sources/urls/batch` - Add multiple URLs at once
- `POST /knowledge/sources/files/batch` - Upload multiple files
- `POST /knowledge/sources/sitemap` - Crawl sitemap and add all pages

See `API_ENDPOINTS.md` for complete details.

## Roadmap

- [x] Support for more file types (PDF, DOCX) - **Completed**
- [x] Batch URL/file processing - **Completed**
- [x] Sitemap crawling - **Completed**
- [x] Image extraction - **Completed**
- [ ] Conversation history and context
- [ ] Streaming responses
- [ ] Webhooks for events
- [ ] Analytics dashboard
- [ ] Rate limiting per tenant

## License

This project is licensed under the MIT License.

## Support

For issues and questions, please open an issue in the repository.
