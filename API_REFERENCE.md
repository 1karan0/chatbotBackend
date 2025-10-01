# API Reference

Complete API documentation for the Multi-Tenant RAG Chatbot.

Base URL: `http://localhost:8000`

## Authentication

All endpoints except tenant creation and login require a JWT token in the Authorization header:
```
Authorization: Bearer <your_token>
```

---

## Auth Endpoints

### Create Tenant
Create a new tenant account with an admin user.

**Endpoint**: `POST /auth/tenants`

**Request Body**:
```json
{
  "tenant_id": "string",
  "tenant_name": "string",
  "username": "string",
  "password": "string"
}
```

**Response**: `201 Created`
```json
{
  "message": "Tenant and admin user created successfully"
}
```

**Example**:
```bash
curl -X POST "http://localhost:8000/auth/tenants" \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "acme_corp",
    "tenant_name": "ACME Corporation",
    "username": "admin",
    "password": "securepassword123"
  }'
```

---

### Login
Authenticate and receive JWT token.

**Endpoint**: `POST /auth/token`

**Request Body** (form-urlencoded):
```
username=string
password=string
```

**Response**: `200 OK`
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

**Example**:
```bash
curl -X POST "http://localhost:8000/auth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=securepassword123"
```

---

### Create User
Create additional user for existing tenant.

**Endpoint**: `POST /auth/users`

**Request Body**:
```json
{
  "tenant_id": "string",
  "username": "string",
  "password": "string"
}
```

**Response**: `201 Created`
```json
{
  "message": "User created successfully"
}
```

---

### List Tenants
Get all tenants.

**Endpoint**: `GET /auth/tenants`

**Response**: `200 OK`
```json
[
  {
    "tenant_id": "string",
    "tenant_name": "string",
    "created_at": "2024-01-01T00:00:00",
    "is_active": true
  }
]
```

---

## Knowledge Management Endpoints

### Add URL Source
Add a website URL as a knowledge source. The system will automatically scrape and process the content.

**Endpoint**: `POST /knowledge/sources/url`

**Headers**:
```
Authorization: Bearer <token>
Content-Type: multipart/form-data
```

**Form Data**:
```
url: string (required)
```

**Response**: `201 Created`
```json
{
  "source_id": "uuid",
  "status": "completed",
  "message": "URL processed successfully",
  "error_message": null
}
```

**Example**:
```bash
curl -X POST "http://localhost:8000/knowledge/sources/url" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "url=https://example.com/about"
```

**Error Response**: `400 Bad Request`
```json
{
  "detail": "Invalid URL format"
}
```

---

### Add Text Source
Add raw text as a knowledge source.

**Endpoint**: `POST /knowledge/sources/text`

**Headers**:
```
Authorization: Bearer <token>
Content-Type: multipart/form-data
```

**Form Data**:
```
text: string (required)
title: string (optional, default: "Text Document")
```

**Response**: `201 Created`
```json
{
  "source_id": "uuid",
  "status": "completed",
  "message": "Text processed successfully"
}
```

**Example**:
```bash
curl -X POST "http://localhost:8000/knowledge/sources/text" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "text=We offer AI consulting and custom chatbot development." \
  -F "title=Services Overview"
```

---

### Upload File
Upload a file as a knowledge source.

**Endpoint**: `POST /knowledge/sources/file`

**Headers**:
```
Authorization: Bearer <token>
Content-Type: multipart/form-data
```

**Form Data**:
```
file: file (required)
```

**Supported File Types**: `.txt`, `.md`, `.csv`

**Response**: `201 Created`
```json
{
  "source_id": "uuid",
  "status": "completed",
  "message": "File processed successfully"
}
```

**Example**:
```bash
curl -X POST "http://localhost:8000/knowledge/sources/file" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@documentation.txt"
```

**Error Response**: `400 Bad Request`
```json
{
  "detail": "File type not supported. Allowed: .txt, .md, .csv"
}
```

---

### List Knowledge Sources
Get all knowledge sources for the authenticated tenant.

**Endpoint**: `GET /knowledge/sources`

**Headers**:
```
Authorization: Bearer <token>
```

**Response**: `200 OK`
```json
[
  {
    "source_id": "uuid",
    "tenant_id": "string",
    "source_type": "url",
    "source_url": "https://example.com",
    "file_name": null,
    "status": "completed",
    "error_message": null,
    "created_at": "2024-01-01T00:00:00"
  },
  {
    "source_id": "uuid",
    "tenant_id": "string",
    "source_type": "text",
    "source_url": null,
    "file_name": null,
    "status": "completed",
    "error_message": null,
    "created_at": "2024-01-01T00:10:00"
  }
]
```

**Example**:
```bash
curl -X GET "http://localhost:8000/knowledge/sources" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

### Delete Knowledge Source
Remove a knowledge source.

**Endpoint**: `DELETE /knowledge/sources/{source_id}`

**Headers**:
```
Authorization: Bearer <token>
```

**Response**: `200 OK`
```json
{
  "message": "Knowledge source deleted successfully"
}
```

**Example**:
```bash
curl -X DELETE "http://localhost:8000/knowledge/sources/abc-123-def" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

### Rebuild Index
Rebuild the search index for the authenticated tenant.

**Endpoint**: `POST /knowledge/rebuild-index`

**Headers**:
```
Authorization: Bearer <token>
```

**Response**: `200 OK`
```json
{
  "message": "Index rebuilt successfully for tenant acme_corp",
  "sources_processed": 5
}
```

**Example**:
```bash
curl -X POST "http://localhost:8000/knowledge/rebuild-index" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## Chat Endpoints

### Ask Question
Send a question and get an AI-generated answer based on the tenant's knowledge base.

**Endpoint**: `POST /chat/ask`

**Headers**:
```
Authorization: Bearer <token>
Content-Type: application/json
```

**Request Body**:
```json
{
  "question": "string"
}
```

**Response**: `200 OK`
```json
{
  "answer": "string",
  "sources": ["source1", "source2"],
  "tenant_id": "string"
}
```

**Example**:
```bash
curl -X POST "http://localhost:8000/chat/ask" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What are your business hours?"
  }'
```

**Example Response**:
```json
{
  "answer": "Our business hours are Monday through Friday, 9 AM to 5 PM EST. We are closed on weekends and major holidays.",
  "sources": [
    "https://example.com/contact",
    "Company Info.txt"
  ],
  "tenant_id": "acme_corp"
}
```

**Error Cases**:

No knowledge available:
```json
{
  "answer": "I don't have any information to answer that question. Please add relevant content to the knowledge base.",
  "sources": [],
  "tenant_id": "acme_corp"
}
```

---

### Get Chat Status
Check the status of the chatbot for the authenticated tenant.

**Endpoint**: `GET /chat/status`

**Headers**:
```
Authorization: Bearer <token>
```

**Response**: `200 OK`
```json
{
  "tenant_id": "string",
  "document_count": 42,
  "status": "ready",
  "message": "Chatbot has 42 document chunks indexed"
}
```

**Example**:
```bash
curl -X GET "http://localhost:8000/chat/status" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Status Values**:
- `ready`: Chatbot has knowledge and is ready to answer questions
- `no_knowledge`: No knowledge sources have been added yet

---

### Get Embed Code
Get HTML embed code for integrating the chatbot into a website.

**Endpoint**: `GET /chat/embed-code`

**Headers**:
```
Authorization: Bearer <token>
```

**Response**: `200 OK`
```json
{
  "tenant_id": "string",
  "embed_code": "<!-- HTML code here -->",
  "instructions": "Copy and paste this code before the closing </body> tag of your website"
}
```

**Example**:
```bash
curl -X GET "http://localhost:8000/chat/embed-code" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## Health Check

### Health Check
Check if the API is running.

**Endpoint**: `GET /health`

**Response**: `200 OK`
```json
{
  "status": "healthy",
  "service": "Multi-Tenant RAG Chatbot",
  "version": "1.0.0"
}
```

**Example**:
```bash
curl -X GET "http://localhost:8000/health"
```

---

## Error Responses

All endpoints may return the following error responses:

### 400 Bad Request
Invalid request parameters or body.
```json
{
  "detail": "Error message describing what's wrong"
}
```

### 401 Unauthorized
Missing or invalid authentication token.
```json
{
  "detail": "Not authenticated"
}
```

### 404 Not Found
Resource not found.
```json
{
  "detail": "Resource not found"
}
```

### 500 Internal Server Error
Server error during processing.
```json
{
  "detail": "Error processing request: <error details>"
}
```

---

## Rate Limiting

Currently no rate limiting is implemented. For production use, consider implementing rate limiting per tenant.

---

## Interactive Documentation

For interactive API documentation with the ability to test endpoints directly in your browser:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

Both provide the same API reference with a user-friendly interface for testing.
