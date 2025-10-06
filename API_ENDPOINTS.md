# API Endpoints Summary

## Base URL
`http://localhost:8000`

## Authentication Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/auth/register` | Register new tenant with admin user | No |
| POST | `/auth/token` | Login and get JWT token | No |
| GET | `/auth/me` | Get current user info | Yes |

## Knowledge Management Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/knowledge/sources/url` | Add single URL | Yes |
| POST | `/knowledge/sources/urls/batch` | Add multiple URLs at once | Yes |
| POST | `/knowledge/sources/text` | Add text content | Yes |
| POST | `/knowledge/sources/file` | Upload single file | Yes |
| POST | `/knowledge/sources/files/batch` | Upload multiple files | Yes |
| POST | `/knowledge/sources/sitemap` | Crawl sitemap and add all URLs | Yes |
| GET | `/knowledge/sources` | List all knowledge sources | Yes |
| DELETE | `/knowledge/sources/{source_id}` | Delete a knowledge source | Yes |
| POST | `/knowledge/rebuild-index` | Rebuild search index | Yes |

## Chat Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/chat/ask` | Ask a question | Yes |
| GET | `/chat/status` | Get chatbot status | Yes |
| GET | `/chat/embed-code` | Get embed code for website | Yes |

## System Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/health` | Health check | No |
| GET | `/docs` | Interactive API documentation | No |

## New Features Added

### 1. Batch URL Processing
- **Endpoint**: `POST /knowledge/sources/urls/batch`
- **Input**: JSON array or comma-separated URLs
- **Returns**: Processing status for each URL with success/failure counts

### 2. Batch File Upload
- **Endpoint**: `POST /knowledge/sources/files/batch`
- **Input**: Multiple files in multipart form
- **Returns**: Processing status for each file

### 3. Sitemap Crawling
- **Endpoint**: `POST /knowledge/sources/sitemap`
- **Input**: Sitemap URL and optional max URLs limit
- **Returns**: Processes all URLs from sitemap with image extraction

### 4. Image Extraction
- All URL-based endpoints now automatically extract images
- Metadata stored includes:
  - Image URL
  - Alt text
  - Title
  - Dimensions (if available)

## Request/Response Examples

### Batch URLs
```bash
curl -X POST "http://localhost:8000/knowledge/sources/urls/batch" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F 'urls=["https://example.com/page1", "https://example.com/page2"]'
```

Response:
```json
{
  "message": "Processed 2 URLs: 2 successful, 0 failed",
  "results": [
    {
      "url": "https://example.com/page1",
      "source_id": "uuid-1",
      "status": "completed",
      "images_found": 5
    }
  ],
  "summary": {
    "total": 2,
    "successful": 2,
    "failed": 0
  }
}
```

### Batch Files
```bash
curl -X POST "http://localhost:8000/knowledge/sources/files/batch" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "files=@file1.pdf" \
  -F "files=@file2.docx"
```

### Sitemap Crawl
```bash
curl -X POST "http://localhost:8000/knowledge/sources/sitemap" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "sitemap_url=https://example.com/sitemap.xml" \
  -F "max_urls=50"
```

## Supported File Types
- `.txt` - Plain text
- `.md` - Markdown
- `.csv` - CSV files
- `.pdf` - PDF documents
- `.docx` - Word documents

## Image Processing
When URLs are processed, images are automatically extracted with:
- Full image URL (resolved relative URLs)
- Alt text
- Title attribute
- Width and height (if specified)

Images metadata is stored in `source_metadata.images` field.
