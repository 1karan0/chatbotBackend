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
        Scrape content + images from a URL.

        Returns:
            Dict with 'success', 'content', 'title', 'images', 'error' keys
        """
        try:
            async with aiohttp.ClientSession(timeout=self.timeout, headers=self.headers) as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        return {
                            'success': False,
                            'error': f"HTTP {response.status}: Failed to fetch URL",
                            'content': None,
                            'title': None,
                            'images': []
                        }

                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')

                    for script in soup(['script', 'style', 'nav', 'footer', 'header']):
                        script.decompose()

                    title = soup.title.string if soup.title else url

                    text = soup.get_text(separator='\n', strip=True)
                    text = re.sub(r'\n\s*\n', '\n\n', text)

                    images = self._extract_images(soup, url)

                    print("Extracted text:", text[:200])
                    print("Extracted title:", title)
                    print(f"Extracted {len(images)} images")

                    return {
                        'success': True,
                        'content': text,
                        'title': title,
                        'url': url,
                        'images': images,
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

    def _extract_images(self, soup: BeautifulSoup, base_url: str) -> list:
        """Extract images from parsed HTML."""
        images = []
        seen_urls = set()

        for img in soup.find_all('img'):
            img_url = img.get('src') or img.get('data-src')
            if not img_url:
                continue

            img_url = urljoin(base_url, img_url)

            if img_url in seen_urls:
                continue
            seen_urls.add(img_url)

            if not self.validate_url(img_url):
                continue

            images.append({
                'url': img_url,
                'alt': img.get('alt', ''),
                'title': img.get('title', ''),
                'width': img.get('width'),
                'height': img.get('height')
            })

        return images

    def validate_url(self, url: str) -> bool:
        """Validate if URL is properly formatted."""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except:
            return False

    async def scrape_sitemap(self, sitemap_url: str) -> Dict[str, Any]:
        """Extract URLs from a sitemap."""
        try:
            async with aiohttp.ClientSession(timeout=self.timeout, headers=self.headers) as session:
                async with session.get(sitemap_url) as response:
                    if response.status != 200:
                        return {
                            'success': False,
                            'error': f"HTTP {response.status}: Failed to fetch sitemap",
                            'urls': []
                        }

                    xml_content = await response.text()
                    soup = BeautifulSoup(xml_content, 'xml')

                    urls = []
                    for loc in soup.find_all('loc'):
                        url = loc.text.strip()
                        if self.validate_url(url):
                            urls.append(url)

                    return {
                        'success': True,
                        'urls': urls,
                        'count': len(urls),
                        'error': None
                    }

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'urls': []
            }

web_scraper = WebScraper()
