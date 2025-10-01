import aiohttp
import asyncio
from bs4 import BeautifulSoup
from typing import Optional, Dict, Any
from urllib.parse import urljoin, urlparse
import re

class WebScraper:
    """Handles web scraping and content extraction from URLs."""

    def __init__(self):
        self.timeout = aiohttp.ClientTimeout(total=30)
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

    async def scrape_url(self, url: str) -> Dict[str, Any]:
        """
        Scrape content from a URL.

        Returns:
            Dict with 'success', 'content', 'title', 'error' keys
        """
        try:
            async with aiohttp.ClientSession(timeout=self.timeout, headers=self.headers) as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        return {
                            'success': False,
                            'error': f"HTTP {response.status}: Failed to fetch URL",
                            'content': None,
                            'title': None
                        }

                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')

                    for script in soup(['script', 'style', 'nav', 'footer', 'header']):
                        script.decompose()

                    title = soup.title.string if soup.title else url

                    text = soup.get_text(separator='\n', strip=True)
                    text = re.sub(r'\n\s*\n', '\n\n', text)
                    print("Extracted text :", {text})
                    print("Extracted title :", {title})

                    return {
                        'success': True,
                        'content': text,
                        'title': title,
                        'url': url,
                        'error': None
                    }

        except asyncio.TimeoutError:
            return {
                'success': False,
                'error': 'Request timeout',
                'content': None,
                'title': None
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'content': None,
                'title': None
            }

    def validate_url(self, url: str) -> bool:
        """Validate if URL is properly formatted."""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except:
            return False

web_scraper = WebScraper()
