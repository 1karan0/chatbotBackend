# ⚡ Quick Reference Card

## One-Liner Commands

### Setup & Installation
```bash
# Install everything
./install.sh

# Validate setup
python3 validate_setup.py

# Test imports
python3 test_imports.py
```

### Running the Server
```bash
# Activate environment
source .venv/bin/activate

# Start server
python3 main.py

# Test API (in another terminal)
./test_api.sh
```

### Common Operations
```bash
# Check health
curl http://localhost:8000/health

# View docs
open http://localhost:8000/docs

# Remove old database
rm app.db

# Reinstall dependencies
pip install -r requirements.txt

# Download NLTK data
python3 -c "import nltk; nltk.download('punkt'); nltk.download('averaged_perceptron_tagger')"
```

---

## Quick Troubleshooting

| Problem | Solution |
|---------|----------|
| Module not found | `source .venv/bin/activate` |
| SQLAlchemy metadata error | `rm app.db` then restart |
| NLTK data missing | Run: `python3 -c "import nltk; nltk.download('punkt')"` |
| Port in use | `lsof -i :8000` then `kill -9 <PID>` |
| API key error | Edit `.env` and set `OPENAI_API_KEY` |

---

## API Cheat Sheet

### Authentication
```bash
# Create tenant
POST /auth/tenants
{
  "tenant_id": "company",
  "tenant_name": "Company Name",
  "username": "user",
  "password": "pass"
}

# Login
POST /auth/token
username=user&password=pass

# Response
{
  "access_token": "eyJ...",
  "token_type": "bearer"
}
```

### Knowledge Management
```bash
# Add URL (requires token)
POST /knowledge/sources/url
Authorization: Bearer <token>
url=https://example.com

# Add text
POST /knowledge/sources/text
Authorization: Bearer <token>
text=Your content&title=Title

# Upload file
POST /knowledge/sources/file
Authorization: Bearer <token>
file=@document.pdf

# List sources
GET /knowledge/sources
Authorization: Bearer <token>

# Delete source
DELETE /knowledge/sources/{id}
Authorization: Bearer <token>
```

### Chat
```bash
# Ask question
POST /chat/ask
Authorization: Bearer <token>
{
  "question": "Your question?"
}

# Get status
GET /chat/status
Authorization: Bearer <token>
```

---

## File Types Supported

✅ Text (.txt)
✅ Markdown (.md)
✅ CSV (.csv)
✅ PDF (.pdf)
✅ Word (.docx)

---

## Important URLs

| Purpose | URL |
|---------|-----|
| API Docs | http://localhost:8000/docs |
| ReDoc | http://localhost:8000/redoc |
| Health | http://localhost:8000/health |

---

## Environment Variables

```bash
# Required
OPENAI_API_KEY=sk-...

# Database
DATABASE_URL=sqlite:///./app.db

# JWT
JWT_SECRET_KEY=your_secret
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=1440
```

---

## Project Structure

```
project/
├── main.py              # Start here
├── .env                 # Configure here
├── app.db               # Database (auto-created)
├── chroma_db/           # Vector DB (auto-created)
├── api/                 # API endpoints
├── services/            # Business logic
├── database/            # DB models
└── docs/                # Documentation
```

---

## Testing Checklist

- [ ] Run `./install.sh`
- [ ] Configure `.env` with API key
- [ ] Run `python3 validate_setup.py`
- [ ] Start server: `python3 main.py`
- [ ] Run `./test_api.sh`
- [ ] Visit http://localhost:8000/docs
- [ ] Create tenant
- [ ] Login
- [ ] Add knowledge source
- [ ] Ask question

---

## Common curl Examples

### Create tenant
```bash
curl -X POST http://localhost:8000/auth/tenants \
  -H "Content-Type: application/json" \
  -d '{"tenant_id":"test","tenant_name":"Test","username":"admin","password":"pass123"}'
```

### Login
```bash
curl -X POST http://localhost:8000/auth/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=pass123"
```

### Add text
```bash
curl -X POST http://localhost:8000/knowledge/sources/text \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "text=Sample content" \
  -F "title=Sample"
```

### Ask question
```bash
curl -X POST http://localhost:8000/chat/ask \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"question":"Hello?"}'
```

---

## Python Quick Test

```python
# Test imports
from database.models import KnowledgeSource, Tenant, User
from services.retrieval_service_v2 import retrieval_service
from services.document_processor import document_processor

# Check attribute (metadata fix)
assert hasattr(KnowledgeSource, 'source_metadata')
print("✅ All imports work!")
```

---

## Documentation Quick Links

| Doc | Purpose |
|-----|---------|
| [INDEX.md](INDEX.md) | Find any document |
| [START_HERE.md](START_HERE.md) | First time setup |
| [README.md](README.md) | Full documentation |
| [TROUBLESHOOTING.md](TROUBLESHOOTING.md) | Fix errors |
| [API_REFERENCE.md](API_REFERENCE.md) | API details |

---

## Status Indicators

✅ Working correctly
⚠️ Needs attention
❌ Not working
🔄 In progress
📝 Documented

---

## Port Reference

- **8000** - API Server (default)
- **3000** - Frontend (if applicable)

---

## Keyboard Shortcuts (Swagger UI)

- **Ctrl + /** - Toggle docs
- **Ctrl + Enter** - Execute request
- **Esc** - Close modal

---

## Log Levels

```
INFO  - Normal operation
WARN  - Warning, check this
ERROR - Something failed
DEBUG - Detailed info
```

---

## Quick Python Version Check

```bash
python3 --version  # Should be 3.11+
```

---

## Memory Tips

💡 Always activate venv: `source .venv/bin/activate`
💡 API needs token for most endpoints
💡 Database auto-creates on first run
💡 NLTK data downloads automatically
💡 Use Swagger UI for easy testing

---

**Print this page for quick reference!**

**Version:** 1.1.0 | **Date:** 2025-10-01
