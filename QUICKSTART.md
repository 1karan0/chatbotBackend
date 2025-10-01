# Quick Start Guide

## Setup (5 minutes)

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Add Your OpenAI API Key
Edit the `.env` file and replace `your_openai_api_key_here` with your actual OpenAI API key:
```bash
OPENAI_API_KEY=sk-your-actual-key-here
```

### 3. Start the Server
```bash
python main.py
```

The API will be running at http://localhost:8000

## Test the API (5 minutes)

### Step 1: Create a Tenant Account

Open http://localhost:8000/docs in your browser and use the Swagger UI, or use curl:

```bash
curl -X POST "http://localhost:8000/auth/tenants" \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "demo_company",
    "tenant_name": "Demo Company",
    "username": "demo_admin",
    "password": "demo123456"
  }'
```

### Step 2: Login and Get Token

```bash
curl -X POST "http://localhost:8000/auth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=demo_admin&password=demo123456"
```

Save the `access_token` from the response.

### Step 3: Add Knowledge (Choose One)

**Option A: Add a URL**
```bash
curl -X POST "http://localhost:8000/knowledge/sources/url" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -F "url=https://example.com"
```

**Option B: Add Text**
```bash
curl -X POST "http://localhost:8000/knowledge/sources/text" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -F "text=We are a software company. We offer web development and AI solutions." \
  -F "title=Company Info"
```

**Option C: Upload a File**
Create a file called `info.txt` with some content, then:
```bash
curl -X POST "http://localhost:8000/knowledge/sources/file" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -F "file=@info.txt"
```

### Step 4: Ask a Question

```bash
curl -X POST "http://localhost:8000/chat/ask" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{"question": "What services do you offer?"}'
```

## Using the Swagger UI

The easiest way to test is using the interactive Swagger UI:

1. Go to http://localhost:8000/docs
2. Click "Authorize" button at the top
3. Create a tenant using `/auth/tenants`
4. Login using `/auth/token`
5. Copy the access token
6. Click "Authorize" again and paste the token
7. Now you can use all the endpoints!

## Next Steps

- Read the full [README.md](README.md) for complete documentation
- Integrate with your Next.js frontend
- Add more knowledge sources
- Deploy to production

## Common Issues

**"OPENAI_API_KEY not set"**
- Make sure you edited the `.env` file with your actual OpenAI API key

**"No information to answer question"**
- You need to add knowledge sources first (URLs, text, or files)
- Wait a few seconds after adding sources before asking questions

**Authentication errors**
- Make sure you're including the token in the Authorization header
- Format: `Bearer YOUR_TOKEN_HERE`
