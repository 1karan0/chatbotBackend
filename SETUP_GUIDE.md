# Setup Guide - SQLite and ChromaDB Fixes

This guide explains the fixes applied to resolve SQLite and ChromaDB compatibility issues in your multi-tenant RAG chatbot.

## Issues Fixed

### 1. SQLite3 Compatibility Issue
**Problem**: ChromaDB uses SQLite internally for metadata storage, but the default `sqlite3` module may not be compatible with your system.

**Solution**:
- Added `pysqlite3-binary` to requirements.txt
- Implemented automatic SQLite module replacement in key files
- ChromaDB now uses the compatible `pysqlite3` module

### 2. PostgreSQL Configuration Issue
**Problem**: PostgreSQL environment variables were not loading properly from the `.env` file.

**Solution**:
- Updated `config/settings.py` to properly load PostgreSQL settings with defaults
- Fixed `.env` file with correct PostgreSQL connection string format
- Added proper fallback values for all PostgreSQL settings

### 3. ChromaDB Initialization
**Problem**: ChromaDB needed proper initialization and error handling.

**Solution**:
- Added SQLite module fix before ChromaDB imports in all service files
- Improved error handling in database initialization
- Updated to ChromaDB version 0.4.22 for better stability

## Changes Made

### 1. Environment Configuration (`.env`)
```bash
# PostgreSQL Database
DATABASE_URL=postgresql://charbot_user:5E4TfARMyCzcSqsOEqckkbYCRG2kMVED@dpg-d3ads5gdl3ps73enmr5g-a.singapore-postgres.render.com/charbot
PG_USER=charbot_user
PG_DB=charbot
PG_PASSWORD=5E4TfARMyCzcSqsOEqckkbYCRG2kMVED
PG_PORT=5432

# ChromaDB and Data
CHROMA_PATH=./chroma_db
DATA_PATH=./data
```

### 2. Updated Files
- `main.py` - Added SQLite fix at startup
- `services/retrieval_service.py` - Added SQLite fix before imports
- `services/retrieval_service_v2.py` - Added SQLite fix before imports
- `config/settings.py` - Fixed PostgreSQL settings loading
- `requirements.txt` - Added `pysqlite3-binary==0.5.2`

### 3. New Files
- `fix_chromadb_sqlite.py` - Standalone script to test SQLite fix
- `verify_setup.py` - Comprehensive setup verification script

## Installation Steps

1. **Install Dependencies**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Linux/Mac
   # or
   venv\Scripts\activate  # On Windows

   pip install -r requirements.txt
   ```

2. **Verify Your Setup**
   ```bash
   python verify_setup.py
   ```

   This will check:
   - Environment variables
   - PostgreSQL connection
   - ChromaDB initialization
   - Data directory structure

3. **Run Database Migrations**
   ```bash
   # Apply PostgreSQL migrations
   python run_migration.py
   ```

4. **Start the Application**
   ```bash
   python main.py
   ```

   The application will start on http://0.0.0.0:8000

## How It Works

### SQLite Module Replacement
The fix works by replacing Python's built-in `sqlite3` module with `pysqlite3` before ChromaDB is imported:

```python
import sys

# Replace sqlite3 with pysqlite3 for ChromaDB compatibility
try:
    __import__('pysqlite3')
    sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
except ImportError:
    pass
```

This ensures that ChromaDB uses the compatible SQLite version without requiring any changes to ChromaDB's code.

### Database Architecture

Your application now uses:
- **PostgreSQL**: For application data (users, tenants, knowledge sources)
- **ChromaDB**: For vector embeddings and semantic search (uses SQLite internally for metadata)

Both databases are properly configured and isolated from each other.

## Verification

Run the verification script to ensure everything is working:

```bash
python verify_setup.py
```

Expected output:
```
============================================================
Multi-Tenant RAG Chatbot - Setup Verification
============================================================

=== Checking Environment Variables ===
✓ OPENAI_API_KEY: sk-proj-...
✓ DATABASE_URL: postgresql://...
✓ PG_USER: charbot_user
✓ PG_DB: charbot
✓ PG_PASSWORD: 5E4TfARMy...
✓ PG_PORT: 5432
✓ CHROMA_PATH: ./chroma_db
✓ DATA_PATH: ./data

=== Checking PostgreSQL Connection ===
✓ PostgreSQL connected successfully

=== Checking ChromaDB ===
✓ SQLite module configured for ChromaDB
✓ ChromaDB initialized successfully

=== Checking Data Directory ===
✓ Data directory exists: ./data

============================================================
Verification Summary
============================================================
Environment Variables: ✓ PASSED
PostgreSQL Connection: ✓ PASSED
ChromaDB: ✓ PASSED
Data Directory: ✓ PASSED

✓ All checks passed! Your application is ready to run.
```

## Troubleshooting

### Issue: "No module named 'pysqlite3'"
**Solution**: Install dependencies again:
```bash
pip install -r requirements.txt
```

### Issue: PostgreSQL connection failed
**Solution**: Verify your DATABASE_URL in `.env` is correct and the database is accessible.

### Issue: ChromaDB initialization failed
**Solution**:
1. Delete the existing ChromaDB directory: `rm -rf ./chroma_db`
2. Restart the application - it will create a fresh ChromaDB instance

### Issue: "sqlite3.OperationalError"
**Solution**: The SQLite fix may not have been applied. Ensure you're running the application with:
```bash
python main.py
```
(Not with `uvicorn main:app` directly)

## API Documentation

Once the application is running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Architecture Summary

```
┌─────────────────────────────────────────────┐
│         FastAPI Application                 │
├─────────────────────────────────────────────┤
│                                             │
│  ┌─────────────┐      ┌─────────────┐      │
│  │ PostgreSQL  │      │  ChromaDB   │      │
│  │             │      │ (w/SQLite)  │      │
│  │ - Users     │      │ - Vectors   │      │
│  │ - Tenants   │      │ - Embeddings│      │
│  │ - Knowledge │      │ - Search    │      │
│  └─────────────┘      └─────────────┘      │
│                                             │
│  Application Data     Vector Search         │
└─────────────────────────────────────────────┘
```

## Next Steps

1. Add test data to your tenant directories in `./data/`
2. Use the API to create tenants and users
3. Upload knowledge sources via the `/knowledge/` endpoints
4. Test the chatbot with queries via the `/chat/` endpoint

For detailed API usage, refer to the main README.md file.
