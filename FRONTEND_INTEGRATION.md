# Frontend Integration Guide

## Overview

This backend provides a complete multi-tenant RAG chatbot API similar to Botpress. Your Next.js frontend can connect to it using REST API calls.

## Base Configuration

### Environment Variables (.env.local in Next.js)

```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

## Authentication Flow

### 1. Register a Tenant (Initial Setup)

```typescript
const registerTenant = async (tenantData: {
  tenant_id: string;
  tenant_name: string;
  username: string;
  password: string;
}) => {
  const response = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}/auth/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(tenantData),
  });
  return response.json();
};
```

### 2. Login and Get JWT Token

```typescript
const login = async (username: string, password: string) => {
  const formData = new FormData();
  formData.append('username', username);
  formData.append('password', password);

  const response = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}/auth/token`, {
    method: 'POST',
    body: formData,
  });

  const data = await response.json();
  // Store token in localStorage or secure storage
  localStorage.setItem('access_token', data.access_token);
  return data;
};
```

### 3. Create API Client with Auth Headers

```typescript
const getAuthHeaders = () => ({
  'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
  'Content-Type': 'application/json',
});
```

## Knowledge Management Endpoints

### Add Single URL

```typescript
const addUrl = async (url: string) => {
  const formData = new FormData();
  formData.append('url', url);

  const response = await fetch(
    `${process.env.NEXT_PUBLIC_API_BASE_URL}/knowledge/sources/url`,
    {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
      },
      body: formData,
    }
  );
  return response.json();
};
```

### Add Multiple URLs (Batch)

```typescript
const addMultipleUrls = async (urls: string[]) => {
  const formData = new FormData();
  formData.append('urls', JSON.stringify(urls));

  const response = await fetch(
    `${process.env.NEXT_PUBLIC_API_BASE_URL}/knowledge/sources/urls/batch`,
    {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
      },
      body: formData,
    }
  );
  return response.json();
};

// Example usage
const urls = [
  'https://example.com/page1',
  'https://example.com/page2',
  'https://example.com/page3',
];
const result = await addMultipleUrls(urls);
console.log(`${result.summary.successful} URLs processed successfully`);
```

### Add Text Content

```typescript
const addText = async (text: string, title?: string) => {
  const formData = new FormData();
  formData.append('text', text);
  if (title) formData.append('title', title);

  const response = await fetch(
    `${process.env.NEXT_PUBLIC_API_BASE_URL}/knowledge/sources/text`,
    {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
      },
      body: formData,
    }
  );
  return response.json();
};
```

### Upload Single File

```typescript
const uploadFile = async (file: File) => {
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch(
    `${process.env.NEXT_PUBLIC_API_BASE_URL}/knowledge/sources/file`,
    {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
      },
      body: formData,
    }
  );
  return response.json();
};
```

### Upload Multiple Files (Batch)

```typescript
const uploadMultipleFiles = async (files: FileList | File[]) => {
  const formData = new FormData();
  Array.from(files).forEach(file => {
    formData.append('files', file);
  });

  const response = await fetch(
    `${process.env.NEXT_PUBLIC_API_BASE_URL}/knowledge/sources/files/batch`,
    {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
      },
      body: formData,
    }
  );
  return response.json();
};

// Example usage with file input
const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
  const files = event.target.files;
  if (!files) return;

  const result = await uploadMultipleFiles(files);
  console.log(`${result.summary.successful} files uploaded successfully`);
};
```

### Crawl Sitemap

```typescript
const crawlSitemap = async (sitemapUrl: string, maxUrls: number = 50) => {
  const formData = new FormData();
  formData.append('sitemap_url', sitemapUrl);
  formData.append('max_urls', maxUrls.toString());

  const response = await fetch(
    `${process.env.NEXT_PUBLIC_API_BASE_URL}/knowledge/sources/sitemap`,
    {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
      },
      body: formData,
    }
  );
  return response.json();
};

// Example usage
const result = await crawlSitemap('https://example.com/sitemap.xml', 100);
```

### List Knowledge Sources

```typescript
const listSources = async () => {
  const response = await fetch(
    `${process.env.NEXT_PUBLIC_API_BASE_URL}/knowledge/sources`,
    {
      method: 'GET',
      headers: getAuthHeaders(),
    }
  );
  return response.json();
};
```

### Delete Knowledge Source

```typescript
const deleteSource = async (sourceId: string) => {
  const response = await fetch(
    `${process.env.NEXT_PUBLIC_API_BASE_URL}/knowledge/sources/${sourceId}`,
    {
      method: 'DELETE',
      headers: getAuthHeaders(),
    }
  );
  return response.json();
};
```

## Chat Endpoints

### Ask a Question

```typescript
const askQuestion = async (question: string) => {
  const response = await fetch(
    `${process.env.NEXT_PUBLIC_API_BASE_URL}/chat/ask`,
    {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({ question }),
    }
  );
  return response.json();
};

// Example usage
const result = await askQuestion('What services do you offer?');
console.log(result.answer);
console.log('Sources:', result.sources);
```

### Get Chat Status

```typescript
const getChatStatus = async () => {
  const response = await fetch(
    `${process.env.NEXT_PUBLIC_API_BASE_URL}/chat/status`,
    {
      method: 'GET',
      headers: getAuthHeaders(),
    }
  );
  return response.json();
};
```

### Get Embed Code

```typescript
const getEmbedCode = async () => {
  const response = await fetch(
    `${process.env.NEXT_PUBLIC_API_BASE_URL}/chat/embed-code`,
    {
      method: 'GET',
      headers: getAuthHeaders(),
    }
  );
  return response.json();
};
```

## Complete React Component Example

```typescript
// components/KnowledgeManager.tsx
'use client';

import { useState } from 'react';

export default function KnowledgeManager() {
  const [urls, setUrls] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);

  const handleAddUrls = async () => {
    setLoading(true);
    try {
      const urlList = urls.split('\n').filter(u => u.trim());
      const formData = new FormData();
      formData.append('urls', JSON.stringify(urlList));

      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_BASE_URL}/knowledge/sources/urls/batch`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
          },
          body: formData,
        }
      );

      const data = await response.json();
      setResult(data);
    } catch (error) {
      console.error('Error:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files) return;

    setLoading(true);
    try {
      const formData = new FormData();
      Array.from(files).forEach(file => {
        formData.append('files', file);
      });

      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_BASE_URL}/knowledge/sources/files/batch`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
          },
          body: formData,
        }
      );

      const data = await response.json();
      setResult(data);
    } catch (error) {
      console.error('Error:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold mb-4">Add Knowledge Sources</h2>

        {/* URLs Input */}
        <div className="mb-4">
          <label className="block mb-2 font-semibold">Add URLs (one per line)</label>
          <textarea
            value={urls}
            onChange={(e) => setUrls(e.target.value)}
            placeholder="https://example.com/page1&#10;https://example.com/page2"
            className="w-full p-2 border rounded h-32"
          />
          <button
            onClick={handleAddUrls}
            disabled={loading}
            className="mt-2 px-4 py-2 bg-blue-600 text-white rounded disabled:opacity-50"
          >
            {loading ? 'Processing...' : 'Add URLs'}
          </button>
        </div>

        {/* File Upload */}
        <div className="mb-4">
          <label className="block mb-2 font-semibold">Upload Files</label>
          <input
            type="file"
            multiple
            accept=".txt,.md,.csv,.pdf,.docx"
            onChange={handleFileUpload}
            className="w-full p-2 border rounded"
          />
        </div>

        {/* Results */}
        {result && (
          <div className="mt-4 p-4 bg-gray-100 rounded">
            <h3 className="font-semibold mb-2">Result:</h3>
            <pre className="text-sm overflow-auto">
              {JSON.stringify(result, null, 2)}
            </pre>
          </div>
        )}
      </div>
    </div>
  );
}
```

## Complete Chat Component Example

```typescript
// components/ChatInterface.tsx
'use client';

import { useState } from 'react';

export default function ChatInterface() {
  const [messages, setMessages] = useState<Array<{role: string; content: string; sources?: string[]}>>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);

  const sendMessage = async () => {
    if (!input.trim()) return;

    const userMessage = { role: 'user', content: input };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_BASE_URL}/chat/ask`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ question: input }),
        }
      );

      const data = await response.json();
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: data.answer,
        sources: data.sources
      }]);
    } catch (error) {
      console.error('Error:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-screen max-w-4xl mx-auto">
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((msg, i) => (
          <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-xl p-3 rounded-lg ${
              msg.role === 'user' ? 'bg-blue-600 text-white' : 'bg-gray-200'
            }`}>
              <p>{msg.content}</p>
              {msg.sources && msg.sources.length > 0 && (
                <div className="mt-2 text-xs opacity-75">
                  <p>Sources: {msg.sources.join(', ')}</p>
                </div>
              )}
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex justify-start">
            <div className="bg-gray-200 p-3 rounded-lg">
              <p>Thinking...</p>
            </div>
          </div>
        )}
      </div>

      <div className="border-t p-4">
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
            placeholder="Ask a question..."
            className="flex-1 p-2 border rounded"
          />
          <button
            onClick={sendMessage}
            disabled={loading || !input.trim()}
            className="px-6 py-2 bg-blue-600 text-white rounded disabled:opacity-50"
          >
            Send
          </button>
        </div>
      </div>
    </div>
  );
}
```

## Features Summary

### Supported Operations

1. **Authentication**
   - Tenant registration
   - User login with JWT tokens
   - Multi-tenant isolation

2. **Knowledge Management**
   - ✅ Add single URL
   - ✅ Add multiple URLs (batch processing)
   - ✅ Add text content
   - ✅ Upload single file
   - ✅ Upload multiple files (batch)
   - ✅ Crawl entire sitemaps
   - ✅ Image extraction from URLs
   - ✅ List all sources
   - ✅ Delete sources
   - ✅ Rebuild search index

3. **Supported File Types**
   - TXT
   - MD (Markdown)
   - CSV
   - PDF
   - DOCX

4. **Chat Features**
   - RAG-based question answering
   - Source attribution
   - Tenant-specific knowledge isolation
   - Chat status monitoring
   - Embed code generation

5. **Image Processing**
   - Automatic image URL extraction
   - Alt text and metadata capture
   - Image dimensions tracking

## CORS Configuration

The backend has CORS enabled for all origins. For production, update `main.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],  # Replace with your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Error Handling

All endpoints return consistent error responses:

```typescript
{
  "detail": "Error message here"
}
```

Handle errors in your frontend:

```typescript
try {
  const response = await fetch(url, options);
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail);
  }
  return response.json();
} catch (error) {
  console.error('API Error:', error);
  // Show user-friendly error message
}
```

## Running the Backend

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export OPENAI_API_KEY=your_key_here

# Run the server
python main.py
```

Backend will run on `http://localhost:8000`

API documentation available at: `http://localhost:8000/docs`
