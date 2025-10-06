# Backend Changes Summary

## Overview
Your multi-tenant RAG chatbot backend has been enhanced to be more like Botpress with comprehensive batch processing, image extraction, and sitemap crawling capabilities.

## What Was Changed

### 1. Enhanced Knowledge Routes (`api/knowledge_routes.py`)
- ✅ Added `POST /knowledge/sources/urls/batch` - Process multiple URLs in one request
- ✅ Added `POST /knowledge/sources/files/batch` - Upload multiple files at once
- ✅ Added `POST /knowledge/sources/sitemap` - Crawl entire sitemaps with URL limits
- ✅ Updated single URL endpoint to store image metadata
- ✅ All batch operations return detailed status for each item processed

### 2. Enhanced Web Scraper (`services/web_scraper.py`)
- ✅ Added `_extract_images()` method - Extracts all images from web pages
- ✅ Added `scrape_sitemap()` method - Parses XML sitemaps and extracts URLs
- ✅ Updated `scrape_url()` to automatically extract and return images with metadata
- ✅ Image metadata includes: URL, alt text, title, width, height
- ✅ Handles relative URLs and converts them to absolute URLs

### 3. Updated Dependencies (`requirements.txt`)
- ✅ Added `lxml==4.9.3` for better XML/sitemap parsing

### 4. Documentation Created
- ✅ `FRONTEND_INTEGRATION.md` - Complete guide for Next.js integration
- ✅ `API_ENDPOINTS.md` - Quick reference for all API endpoints

## Comparison: Your Backend vs Botpress

| Feature | Your Backend | Botpress |
|---------|--------------|----------|
| Multi-tenant | ✅ Yes | ✅ Yes |
| JWT Auth | ✅ Yes | ✅ Yes |
| Single URL upload | ✅ Yes | ✅ Yes |
| **Batch URL upload** | ✅ **Now Added** | ✅ Yes |
| Single file upload | ✅ Yes | ✅ Yes |
| **Batch file upload** | ✅ **Now Added** | ✅ Yes |
| Text content | ✅ Yes | ✅ Yes |
| **Sitemap crawling** | ✅ **Now Added** | ✅ Yes |
| **Image extraction** | ✅ **Now Added** | ✅ Yes |
| RAG-based chat | ✅ Yes | ✅ Yes |
| Knowledge base mgmt | ✅ Yes | ✅ Yes |
| Embed code | ✅ Yes | ✅ Yes |

## New API Endpoints

### 1. Batch URL Processing
```
POST /knowledge/sources/urls/batch
```
- Accepts JSON array or comma-separated URLs
- Processes all URLs concurrently
- Returns status for each URL
- Extracts images automatically

### 2. Batch File Upload
```
POST /knowledge/sources/files/batch
```
- Accepts multiple files in multipart form
- Processes PDF, DOCX, TXT, MD, CSV
- Returns status for each file
- Validation for each file type

### 3. Sitemap Crawler
```
POST /knowledge/sources/sitemap
```
- Crawls XML sitemaps
- Configurable max URLs limit (default: 50)
- Processes each URL with image extraction
- Returns detailed status

## How Images Are Handled

When URLs are scraped, the system now:
1. Extracts all `<img>` tags from the page
2. Resolves relative URLs to absolute URLs
3. Captures metadata: alt text, title, dimensions
4. Stores in `source_metadata.images[]` as JSON
5. Removes duplicate images

Example image metadata structure:
```json
{
  "title": "Page Title",
  "images": [
    {
      "url": "https://example.com/image.jpg",
      "alt": "Image description",
      "title": "Image title",
      "width": "800",
      "height": "600"
    }
  ]
}
```

## Frontend Connection

### Quick Start for Next.js

1. **Set environment variable**
```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

2. **Add multiple URLs from frontend**
```typescript
const addUrls = async (urls: string[]) => {
  const formData = new FormData();
  formData.append('urls', JSON.stringify(urls));

  const response = await fetch(
    `${process.env.NEXT_PUBLIC_API_BASE_URL}/knowledge/sources/urls/batch`,
    {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
      body: formData,
    }
  );
  return response.json();
};
```

3. **Upload multiple files**
```typescript
const uploadFiles = async (files: FileList) => {
  const formData = new FormData();
  Array.from(files).forEach(file => {
    formData.append('files', file);
  });

  const response = await fetch(
    `${process.env.NEXT_PUBLIC_API_BASE_URL}/knowledge/sources/files/batch`,
    {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
      body: formData,
    }
  );
  return response.json();
};
```

4. **Chat with bot**
```typescript
const ask = async (question: string) => {
  const response = await fetch(
    `${process.env.NEXT_PUBLIC_API_BASE_URL}/chat/ask`,
    {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ question }),
    }
  );
  return response.json();
};
```

## What's Already Working

Your existing functionality remains unchanged:
- ✅ Tenant registration and authentication
- ✅ Single URL/file/text processing
- ✅ RAG-based question answering
- ✅ Multi-tenant data isolation
- ✅ ChromaDB vector storage
- ✅ OpenAI embeddings and chat
- ✅ Knowledge source management
- ✅ Index rebuilding

## Testing the New Features

### 1. Test batch URLs
```bash
curl -X POST "http://localhost:8000/knowledge/sources/urls/batch" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F 'urls=["https://example.com/page1", "https://example.com/page2"]'
```

### 2. Test batch files
```bash
curl -X POST "http://localhost:8000/knowledge/sources/files/batch" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "files=@file1.pdf" \
  -F "files=@file2.docx"
```

### 3. Test sitemap
```bash
curl -X POST "http://localhost:8000/knowledge/sources/sitemap" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "sitemap_url=https://example.com/sitemap.xml" \
  -F "max_urls=20"
```

### 4. Check images in metadata
```bash
curl -X GET "http://localhost:8000/knowledge/sources" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Database Schema

No database changes were needed! The existing schema already supports:
- `source_metadata` (JSON) - Now stores images array
- `source_content` (Text) - Still stores scraped text
- All other fields remain the same

## Next Steps

1. **Install new dependency**
```bash
pip install lxml==4.9.3
```

2. **Restart backend**
```bash
python main.py
```

3. **Test new endpoints** via `/docs` at http://localhost:8000/docs

4. **Integrate with Next.js frontend** using examples in `FRONTEND_INTEGRATION.md`

5. **Build UI components** for:
   - Batch URL input (textarea with one URL per line)
   - Multiple file selector
   - Sitemap URL input
   - Display images from sources

## Benefits

1. **User Experience**: Users can now add dozens of URLs or files at once
2. **Efficiency**: Batch processing is faster than sequential single uploads
3. **Completeness**: Sitemap crawling enables ingesting entire websites
4. **Rich Content**: Image extraction provides context and metadata
5. **Botpress-like**: Your backend now matches commercial chatbot platforms

## Files Modified

- `api/knowledge_routes.py` - Added 3 new endpoints
- `services/web_scraper.py` - Added image extraction and sitemap parsing
- `requirements.txt` - Added lxml

## Files Created

- `FRONTEND_INTEGRATION.md` - Complete Next.js integration guide
- `API_ENDPOINTS.md` - Quick API reference
- `CHANGES_SUMMARY.md` - This file

## No Breaking Changes

All existing endpoints work exactly as before. New functionality is purely additive.
