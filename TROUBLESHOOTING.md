# Troubleshooting Guide

## Common Errors and Solutions

### 1. SQLAlchemy Error: "Attribute name 'metadata' is reserved"

**Error Message:**
```
sqlalchemy.exc.InvalidRequestError: Attribute name 'metadata' is reserved when using the Declarative API.
```

**Solution:**
This has been fixed in the latest version. The column name has been changed from `metadata` to `source_metadata` in the `KnowledgeSource` model.

**If you still see this error:**
1. Delete the old database: `rm app.db`
2. Update to the latest code
3. Restart the application

---

### 2. NLTK Data Not Found

**Error Message:**
```
LookupError: Resource punkt not found.
```

**Solution:**
Download NLTK data manually:
```bash
python3 -c "import nltk; nltk.download('punkt'); nltk.download('averaged_perceptron_tagger')"
```

Or run the installation script:
```bash
./install.sh
```

---

### 3. SQLite3 Version Issues on Ubuntu 23

**Error Message:**
```
ImportError: cannot import name 'SQLITE_...' from 'sqlite3'
```

**Solution:**
Update SQLite3:
```bash
sudo apt-get update
sudo apt-get install sqlite3 libsqlite3-dev
```

Then reinstall Python packages:
```bash
pip install --upgrade --force-reinstall pysqlite3-binary
```

---

### 4. Virtual Environment Not Working

**Problem:**
Cannot activate virtual environment or packages not found

**Solution:**
```bash
# Remove old virtual environment
rm -rf .venv

# Create new one
python3 -m venv .venv

# Activate it
source .venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

---

### 5. OpenAI API Key Error

**Error Message:**
```
openai.error.AuthenticationError: Incorrect API key provided
```

**Solution:**
1. Check your `.env` file
2. Ensure `OPENAI_API_KEY` is set correctly
3. Verify the key is valid at https://platform.openai.com/api-keys
4. Make sure there are no extra spaces or quotes around the key

Example `.env`:
```bash
OPENAI_API_KEY=sk-proj-abc123xyz...
```

---

### 6. Module Import Errors

**Error Message:**
```
ModuleNotFoundError: No module named 'langchain'
```

**Solution:**
Make sure your virtual environment is activated and dependencies are installed:
```bash
source .venv/bin/activate
pip install -r requirements.txt
```

---

### 7. ChromaDB Persistence Issues

**Error Message:**
```
Error initializing database: ...
```

**Solution:**
1. Delete the ChromaDB directory:
```bash
rm -rf chroma_db/
```

2. Restart the application - it will recreate the database automatically

---

### 8. File Upload Errors

**Problem:**
Cannot upload PDF or DOCX files

**Solution:**
Ensure the required libraries are installed:
```bash
pip install pypdf python-docx
```

Check that the file is not corrupted and is a valid format.

---

### 9. Port Already in Use

**Error Message:**
```
[ERROR] [Errno 98] Address already in use
```

**Solution:**
Find and kill the process using port 8000:
```bash
# Find the process
lsof -i :8000

# Kill it
kill -9 <PID>

# Or use a different port
uvicorn main:app --port 8001
```

---

### 10. Permission Denied Errors

**Problem:**
Cannot write to database or chroma_db directory

**Solution:**
```bash
# Fix permissions
chmod -R 755 .
chown -R $USER:$USER .

# Or run with sudo (not recommended)
sudo python3 main.py
```

---

## Installation Issues

### Ubuntu/Debian

```bash
# Update system
sudo apt-get update
sudo apt-get upgrade

# Install Python development tools
sudo apt-get install python3-dev python3-pip python3-venv

# Install system dependencies
sudo apt-get install build-essential libssl-dev libffi-dev
```

### macOS

```bash
# Install Homebrew if not installed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Python
brew install python@3.11

# Install dependencies
pip3 install -r requirements.txt
```

---

## Performance Issues

### Slow Response Times

**Solutions:**
1. Reduce chunk size in `config/settings.py`:
   ```python
   dense_chunk_size = 500  # Instead of 800
   ```

2. Reduce retrieval_k (number of chunks retrieved):
   ```python
   retrieval_k = 2  # Instead of 4
   ```

3. Use a faster OpenAI model:
   ```python
   chat_model = "gpt-3.5-turbo"  # Instead of gpt-4o-mini
   ```

### High Memory Usage

**Solutions:**
1. Limit the number of documents per tenant
2. Implement pagination for large datasets
3. Use a lighter embedding model
4. Clear old ChromaDB data periodically

---

## Database Issues

### Corrupted Database

**Solution:**
```bash
# Backup current database
cp app.db app.db.backup

# Remove corrupted database
rm app.db

# Restart application (new database will be created)
python3 main.py
```

### Migration Issues

**Solution:**
If you're upgrading from an old version:
```bash
# Delete old database
rm app.db

# Delete old ChromaDB
rm -rf chroma_db/

# Restart application
python3 main.py
```

---

## Network Issues

### Cannot Access API

**Check:**
1. Firewall settings:
   ```bash
   sudo ufw allow 8000
   ```

2. Application is running:
   ```bash
   curl http://localhost:8000/health
   ```

3. Using correct URL:
   - Local: `http://localhost:8000`
   - Network: `http://YOUR_IP:8000`

---

## Getting Help

If you're still experiencing issues:

1. Check the application logs for detailed error messages
2. Verify all environment variables are set correctly
3. Ensure you're using Python 3.11 or higher
4. Try the automated installation script: `./install.sh`
5. Open an issue on GitHub with:
   - Error message
   - Steps to reproduce
   - Python version
   - Operating system
   - Contents of your `.env` file (without sensitive keys)
