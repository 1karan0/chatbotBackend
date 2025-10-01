# 🚀 Quick Start Guide - Multi-Tenant RAG Chatbot

Welcome! This guide will help you get your chatbot backend up and running in minutes.

## 📋 Prerequisites

- Python 3.11 or higher
- OpenAI API key ([Get one here](https://platform.openai.com/api-keys))
- Linux, macOS, or Windows with WSL

## 🔧 Installation Steps

### Step 1: Run the Installation Script

```bash
./install.sh
```

This will:
- Create a virtual environment
- Install all required dependencies
- Download NLTK data
- Set up the project structure

### Step 2: Configure Your API Key

Edit the `.env` file and add your OpenAI API key:

```bash
nano .env
```

Update this line:
```
OPENAI_API_KEY=your_openai_api_key_here
```

Replace `your_openai_api_key_here` with your actual API key from OpenAI.

### Step 3: Validate Your Setup

```bash
source .venv/bin/activate
python3 validate_setup.py
```

This will check that everything is configured correctly.

### Step 4: Start the Server

```bash
source .venv/bin/activate
python3 main.py
```

The API will be available at: **http://localhost:8000**

## 🎯 First Steps

### 1. Access API Documentation

Open your browser and go to:
- **Swagger UI:** http://localhost:8000/docs
- **Health Check:** http://localhost:8000/health

### 2. Create Your First Tenant

Using the Swagger UI or curl:

```bash
curl -X POST "http://localhost:8000/auth/tenants" \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "my_company",
    "tenant_name": "My Company",
    "username": "admin",
    "password": "secure_password123"
  }'
```

### 3. Login and Get Token

```bash
curl -X POST "http://localhost:8000/auth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=secure_password123"
```

Save the `access_token` from the response - you'll need it for all API calls.

### 4. Add Knowledge Source

Add a URL:
```bash
curl -X POST "http://localhost:8000/knowledge/sources/url" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -F "url=https://example.com/about-us"
```

Add text:
```bash
curl -X POST "http://localhost:8000/knowledge/sources/text" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -F "text=Our business hours are Monday-Friday, 9 AM to 5 PM" \
  -F "title=Business Hours"
```

Upload a file:
```bash
curl -X POST "http://localhost:8000/knowledge/sources/file" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -F "file=@document.pdf"
```

### 5. Ask Questions

```bash
curl -X POST "http://localhost:8000/chat/ask" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{"question": "What are your business hours?"}'
```

## 🐛 Troubleshooting

If something goes wrong, check:

1. **Virtual environment is activated:**
   ```bash
   source .venv/bin/activate
   ```

2. **All dependencies are installed:**
   ```bash
   pip install -r requirements.txt
   ```

3. **NLTK data is downloaded:**
   ```bash
   python3 -c "import nltk; nltk.download('punkt'); nltk.download('averaged_perceptron_tagger')"
   ```

4. **OpenAI API key is set correctly** in `.env`

5. **Port 8000 is not already in use:**
   ```bash
   lsof -i :8000
   ```

For more detailed troubleshooting, see [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

## 📚 Next Steps

- Read the full [README.md](README.md) for detailed documentation
- Check [API_REFERENCE.md](API_REFERENCE.md) for complete API documentation
- Review [IMPROVEMENTS.md](IMPROVEMENTS.md) for advanced features

## 🔑 Important Files

- `.env` - Configuration and API keys
- `main.py` - Application entry point
- `app.db` - SQLite database (created automatically)
- `chroma_db/` - Vector database storage (created automatically)
- `data/` - Document storage (created automatically)

## 🚨 Common Errors & Quick Fixes

### Error: "ModuleNotFoundError: No module named 'sqlalchemy'"
**Fix:** Activate virtual environment
```bash
source .venv/bin/activate
```

### Error: "Attribute name 'metadata' is reserved"
**Fix:** This is already fixed in the current version. Delete old database:
```bash
rm app.db
python3 main.py
```

### Error: "Resource punkt not found"
**Fix:** Download NLTK data
```bash
python3 -c "import nltk; nltk.download('punkt'); nltk.download('averaged_perceptron_tagger')"
```

### Error: "Incorrect API key provided"
**Fix:** Update `.env` with valid OpenAI API key

## 💡 Pro Tips

1. **Always activate virtual environment** before running commands:
   ```bash
   source .venv/bin/activate
   ```

2. **Check health status** to verify server is running:
   ```bash
   curl http://localhost:8000/health
   ```

3. **Use Swagger UI** for easy API testing:
   http://localhost:8000/docs

4. **Monitor logs** for debugging:
   The application prints detailed logs to the console

5. **Backup your data** before major changes:
   ```bash
   cp app.db app.db.backup
   cp -r chroma_db chroma_db.backup
   ```

## 🎉 You're All Set!

Your multi-tenant RAG chatbot is now ready to use. Start adding knowledge sources and asking questions!

For help or questions, check the documentation or open an issue on GitHub.
