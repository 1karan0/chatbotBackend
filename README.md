# Multi-Tenant RAG Chatbot

A production-ready multi-tenant chatbot application using RAG (Retrieval-Augmented Generation) with JWT authentication, built with FastAPI, LangChain, Chroma DB, and OpenAI.

## Features

- **Multi-tenant architecture** with strict data isolation
- **JWT-based authentication** with secure password hashing
- **RAG system** combining dense (Chroma) and sparse (BM25) retrieval
- **REST API** with automatic documentation
- **Tenant-specific data folders** for enhanced security
- **SQL database** for tenant and user management
- **ngrok integration** for easy public access

## Quick Start

### 1. Setup

```bash
# Clone and setup
git clone <repository>
cd multi-tenant-rag-chatbot

# Run setup script
python setup.py
```

### 2. Configure Environment

Edit the `.env` file with your actual credentials:

```bash
OPENAI_API_KEY=your_actual_openai_api_key
SECRET_KEY=your_super_secret_jwt_key
NGROK_AUTH_TOKEN=326XQY64T2IlwvoXxgWZZgCURGR_3Dzi2gaTewvfUasE3NWiH
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the Application

```bash
# Local development
python main.py

# With ngrok (public access)
python run_with_ngrok.py
```

### 5. Access the API

- **Local:** http://localhost:8000/docs
- **With ngrok:** The public URL will be displayed in the console

## API Usage

### Authentication

First, get an authentication token:

```bash
curl -X POST "http://localhost:8000/auth/token" \
  -H "Content-Type: application/json" \
  -d '{"username": "london_user", "password": "london123"}'
```

### Ask Questions

Use the token to ask questions:

```bash
curl -X POST "http://localhost:8000/chat/ask" \
  -H "Authorization: Bearer <your_token>" \
  -H "Content-Type: application/json" \
  -d '{"question": "What services do you offer?"}'
```

## Sample Credentials

The setup creates these sample accounts:

- **tenant_a (London):** london_user / london123
- **tenant_b (Manchester):** manchester_user / manchester123  
- **tenant_c (Birmingham):** birmingham_user / birmingham123
- **tenant_d (Glasgow):** glasgow_user / glasgow123
- **tenant_e (Midlands):** midlands_user / midlands123

## Architecture

### Directory Structure

```
├── config/           # Configuration and settings
├── models/           # Pydantic models and schemas
├── database/         # SQLAlchemy models and connection
├── auth/             # JWT handling and dependencies
├── services/         # Business logic (data loading, retrieval)
├── api/              # FastAPI route handlers
├── data/             # Tenant-specific data folders
├── chroma_db/        # Vector database storage
├── main.py           # Application entry point
├── run_with_ngrok.py # ngrok integration
└── setup.py          # Setup and initialization
```

### Multi-Tenancy

- **Data Isolation:** Each tenant has a separate data folder
- **Vector Database:** Shared Chroma DB with tenant metadata filtering
- **Authentication:** JWT tokens include tenant_id claims
- **SQL Database:** Separate tables for tenants and users

### RAG Pipeline

1. **Document Loading:** Tenant-specific documents from separate folders
2. **Text Splitting:** Different chunk sizes for dense vs sparse retrieval
3. **Vector Storage:** OpenAI embeddings stored in Chroma DB
4. **Retrieval:** Ensemble of semantic (Chroma) + keyword (BM25) search
5. **Generation:** OpenAI GPT models generate responses from retrieved context

## Adding New Tenants

### Via API

```bash
curl -X POST "http://localhost:8000/auth/tenants" \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "tenant_new",
    "tenant_name": "New Office",
    "username": "new_admin",
    "password": "secure_password123"
  }'
```

### Manually

1. Create data folder: `mkdir -p data/tenant_new`
2. Add text files to the folder
3. Use the tenant creation API or add directly to database
4. Rebuild the search index: `POST /chat/rebuild-index`

## Configuration

Key settings in `.env`:

- **OPENAI_API_KEY:** Required for embeddings and chat completion
- **SECRET_KEY:** JWT signing key (use a strong random key in production)
- **DATABASE_URL:** SQLite by default, supports PostgreSQL/MySQL
- **CHROMA_PATH:** Vector database storage location
- **DATA_PATH:** Root directory for tenant data folders

## Production Deployment

1. **Security:**
   - Use strong, random SECRET_KEY
   - Configure CORS origins appropriately
   - Use HTTPS in production
   - Store API keys securely

2. **Database:**
   - Use PostgreSQL or MySQL instead of SQLite
   - Set up proper backup strategies
   - Configure connection pooling

3. **Scaling:**
   - Use multiple workers with Gunicorn
   - Consider separate vector database instances
   - Implement caching for frequently accessed data

## Troubleshooting

### Common Issues

1. **"Vector database not available"**
   - Check if OPENAI_API_KEY is set
   - Verify data files exist in tenant folders
   - Run the rebuild index endpoint

2. **Authentication errors**
   - Verify JWT token format
   - Check token expiration
   - Ensure user exists and is active

3. **No relevant documents found**
   - Check tenant_id in token matches data folder
   - Verify documents contain relevant content
   - Check document format (should be .txt files)

## License

This project is licensed under the MIT License.