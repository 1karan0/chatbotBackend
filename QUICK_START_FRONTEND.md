# Quick Start: Connecting Next.js Frontend

## 5-Minute Integration Guide

### Step 1: Install Dependencies (Backend)

```bash
cd backend
./install_updates.sh
python3 main.py
```

Backend runs on: `http://localhost:8000`

### Step 2: Setup Next.js Environment

Create `.env.local`:
```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

### Step 3: Create API Client

Create `lib/api.ts`:
```typescript
const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL;

const getToken = () => localStorage.getItem('access_token');

const getHeaders = () => ({
  'Authorization': `Bearer ${getToken()}`,
  'Content-Type': 'application/json',
});

export const api = {
  // Auth
  login: async (username: string, password: string) => {
    const formData = new FormData();
    formData.append('username', username);
    formData.append('password', password);
    const res = await fetch(`${API_BASE}/auth/token`, { method: 'POST', body: formData });
    const data = await res.json();
    localStorage.setItem('access_token', data.access_token);
    return data;
  },

  // Add multiple URLs
  addUrls: async (urls: string[]) => {
    const formData = new FormData();
    formData.append('urls', JSON.stringify(urls));
    const res = await fetch(`${API_BASE}/knowledge/sources/urls/batch`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${getToken()}` },
      body: formData,
    });
    return res.json();
  },

  // Upload files
  uploadFiles: async (files: FileList) => {
    const formData = new FormData();
    Array.from(files).forEach(f => formData.append('files', f));
    const res = await fetch(`${API_BASE}/knowledge/sources/files/batch`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${getToken()}` },
      body: formData,
    });
    return res.json();
  },

  // Add text
  addText: async (text: string, title: string = 'Text Document') => {
    const formData = new FormData();
    formData.append('text', text);
    formData.append('title', title);
    const res = await fetch(`${API_BASE}/knowledge/sources/text`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${getToken()}` },
      body: formData,
    });
    return res.json();
  },

  // Crawl sitemap
  crawlSitemap: async (sitemapUrl: string, maxUrls: number = 50) => {
    const formData = new FormData();
    formData.append('sitemap_url', sitemapUrl);
    formData.append('max_urls', maxUrls.toString());
    const res = await fetch(`${API_BASE}/knowledge/sources/sitemap`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${getToken()}` },
      body: formData,
    });
    return res.json();
  },

  // List sources
  listSources: async () => {
    const res = await fetch(`${API_BASE}/knowledge/sources`, {
      headers: getHeaders(),
    });
    return res.json();
  },

  // Delete source
  deleteSource: async (id: string) => {
    const res = await fetch(`${API_BASE}/knowledge/sources/${id}`, {
      method: 'DELETE',
      headers: getHeaders(),
    });
    return res.json();
  },

  // Ask question
  askQuestion: async (question: string) => {
    const res = await fetch(`${API_BASE}/chat/ask`, {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify({ question }),
    });
    return res.json();
  },
};
```

### Step 4: Create Knowledge Upload Component

Create `components/KnowledgeUpload.tsx`:
```typescript
'use client';
import { useState } from 'react';
import { api } from '@/lib/api';

export default function KnowledgeUpload() {
  const [urls, setUrls] = useState('');
  const [loading, setLoading] = useState(false);

  const handleUpload = async () => {
    setLoading(true);
    try {
      const urlList = urls.split('\n').filter(u => u.trim());
      const result = await api.addUrls(urlList);
      alert(`✅ ${result.summary.successful} URLs added!`);
      setUrls('');
    } catch (error) {
      alert('❌ Error adding URLs');
    } finally {
      setLoading(false);
    }
  };

  const handleFiles = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files) return;
    setLoading(true);
    try {
      const result = await api.uploadFiles(e.target.files);
      alert(`✅ ${result.summary.successful} files uploaded!`);
    } catch (error) {
      alert('❌ Error uploading files');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6 p-6 max-w-2xl">
      <div>
        <h2 className="text-xl font-bold mb-2">Add URLs</h2>
        <textarea
          value={urls}
          onChange={(e) => setUrls(e.target.value)}
          placeholder="https://example.com/page1&#10;https://example.com/page2"
          className="w-full h-32 p-3 border rounded"
          disabled={loading}
        />
        <button
          onClick={handleUpload}
          disabled={loading}
          className="mt-2 px-6 py-2 bg-blue-600 text-white rounded disabled:opacity-50"
        >
          {loading ? 'Processing...' : 'Add URLs'}
        </button>
      </div>

      <div>
        <h2 className="text-xl font-bold mb-2">Upload Files</h2>
        <input
          type="file"
          multiple
          accept=".txt,.md,.csv,.pdf,.docx"
          onChange={handleFiles}
          disabled={loading}
          className="w-full p-2 border rounded"
        />
      </div>
    </div>
  );
}
```

### Step 5: Create Chat Component

Create `components/Chat.tsx`:
```typescript
'use client';
import { useState } from 'react';
import { api } from '@/lib/api';

export default function Chat() {
  const [messages, setMessages] = useState<any[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);

  const send = async () => {
    if (!input.trim()) return;

    setMessages(prev => [...prev, { role: 'user', content: input }]);
    setInput('');
    setLoading(true);

    try {
      const result = await api.askQuestion(input);
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: result.answer,
        sources: result.sources
      }]);
    } catch (error) {
      alert('Error sending message');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-screen max-w-4xl mx-auto">
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((msg, i) => (
          <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-md p-3 rounded-lg ${
              msg.role === 'user' ? 'bg-blue-600 text-white' : 'bg-gray-200'
            }`}>
              <p>{msg.content}</p>
              {msg.sources && (
                <p className="text-xs mt-2 opacity-75">
                  Sources: {msg.sources.join(', ')}
                </p>
              )}
            </div>
          </div>
        ))}
      </div>

      <div className="border-t p-4">
        <div className="flex gap-2">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && send()}
            placeholder="Ask anything..."
            className="flex-1 p-3 border rounded"
            disabled={loading}
          />
          <button
            onClick={send}
            disabled={loading}
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

### Step 6: Use in Your Pages

```typescript
// app/dashboard/page.tsx
import KnowledgeUpload from '@/components/KnowledgeUpload';
import Chat from '@/components/Chat';

export default function Dashboard() {
  return (
    <div className="container mx-auto">
      <h1 className="text-3xl font-bold mb-8">Chatbot Dashboard</h1>

      <div className="grid md:grid-cols-2 gap-8">
        <div>
          <h2 className="text-2xl mb-4">Knowledge Base</h2>
          <KnowledgeUpload />
        </div>

        <div>
          <h2 className="text-2xl mb-4">Chat</h2>
          <Chat />
        </div>
      </div>
    </div>
  );
}
```

## Testing Checklist

- [ ] Backend running on `http://localhost:8000`
- [ ] Can access `/docs` endpoint
- [ ] Environment variable set in Next.js
- [ ] Login works and token stored
- [ ] Can upload URLs
- [ ] Can upload files
- [ ] Chat responds with answers
- [ ] Sources are displayed

## Common Issues

### CORS Error
**Solution**: Check backend CORS settings in `main.py`

### 401 Unauthorized
**Solution**: Login again to refresh token

### Files not uploading
**Solution**: Check file types (only .txt, .md, .csv, .pdf, .docx)

### Chat not responding
**Solution**: Add knowledge sources first

## Next Steps

1. **Add loading states** - Show spinners during processing
2. **Add error handling** - Display user-friendly errors
3. **Add source list** - Show all uploaded sources
4. **Add delete function** - Remove unwanted sources
5. **Style components** - Use Tailwind or your CSS framework
6. **Add authentication** - Protect routes with auth guards

## API Endpoints Reference

```
POST   /auth/token                      - Login
POST   /knowledge/sources/url           - Single URL
POST   /knowledge/sources/urls/batch    - Multiple URLs ⭐
POST   /knowledge/sources/file          - Single file
POST   /knowledge/sources/files/batch   - Multiple files ⭐
POST   /knowledge/sources/text          - Text content
POST   /knowledge/sources/sitemap       - Sitemap crawler ⭐
GET    /knowledge/sources               - List sources
DELETE /knowledge/sources/{id}          - Delete source
POST   /chat/ask                        - Ask question
GET    /chat/status                     - Bot status
```

⭐ = New batch endpoints

## Full Documentation

- `FRONTEND_INTEGRATION.md` - Complete integration guide
- `API_ENDPOINTS.md` - All API endpoints
- `CHANGES_SUMMARY.md` - What changed
- `BACKEND_COMPARISON.md` - Compare with Botpress

Ready to build your chatbot! 🚀
