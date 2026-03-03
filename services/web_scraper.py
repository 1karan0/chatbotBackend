import aiohttp
import asyncio
from bs4 import BeautifulSoup
from typing import Optional, Dict, Any
from urllib.parse import urljoin, urlparse
import re

# Playwright is optional; used for React/Next.js and other JS-rendered pages
try:
    from playwright.async_api import async_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    async_playwright = None
    PLAYWRIGHT_AVAILABLE = False


class WebScraper:
    """Handles web scraping and content extraction from URLs."""

    # Timeout for Playwright page load and network idle (seconds)
    PLAYWRIGHT_TIMEOUT_MS = 30_000
    PLAYWRIGHT_NETWORK_IDLE_MS = 5_000
    # Extra wait after load for React/Next.js hydration (ms)
    PLAYWRIGHT_HYDRATION_WAIT_MS = 2_000

    def __init__(self):
        self.timeout = aiohttp.ClientTimeout(total=30)
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }

    async def scrape_url(self, url: str, force_playwright: bool = False) -> Dict[str, Any]:
        """
        Scrape content + images from a URL.

        Args:
            url: Page URL to scrape.
            force_playwright: If True, use Playwright (headless browser) for React/Next.js and other JS-rendered pages.

        Returns:
            Dict with 'success', 'content', 'title', 'images', 'error' keys
        """
        if force_playwright:
            if not PLAYWRIGHT_AVAILABLE:
                return {
                    'success': False,
                    'error': 'Playwright is not installed. Run: pip install playwright && playwright install chromium',
                    'content': None,
                    'title': None,
                    'images': []
                }
            return await self._scrape_with_playwright(url)

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

    async def _scrape_with_playwright(self, url: str) -> Dict[str, Any]:
        """
        Scrape a URL using Playwright for full JS execution (React/Next.js, etc.).
        Waits for network idle and optional hydration delay before extracting content.
        """
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(
                    headless=True,
                    args=[
                        '--no-sandbox',
                        '--disable-setuid-sandbox',
                        '--disable-dev-shm-usage',
                        '--disable-gpu',
                        '--single-process',
                    ]
                )
                try:
                    context = await browser.new_context(
                        user_agent=self.headers['User-Agent'],
                        viewport={'width': 1920, 'height': 1080},
                        ignore_https_errors=True,
                        java_script_enabled=True,
                    )
                    page = await context.new_page()

                    # Navigate and wait for DOM + network idle (good for SPAs)
                    await page.goto(
                        url,
                        wait_until='domcontentloaded',
                        timeout=self.PLAYWRIGHT_TIMEOUT_MS,
                    )
                    # Wait for network to settle (React/Next.js data fetching)
                    try:
                        await page.wait_for_load_state('networkidle', timeout=self.PLAYWRIGHT_NETWORK_IDLE_MS)
                    except Exception:
                        pass  # Proceed even if network never fully idles
                    # Extra wait for client-side hydration (Next.js, React)
                    await page.wait_for_timeout(self.PLAYWRIGHT_HYDRATION_WAIT_MS)

                    html = await page.content()
                finally:
                    await browser.close()

            soup = BeautifulSoup(html, 'html.parser')

            for tag in soup(['script', 'style', 'nav', 'footer', 'header', 'noscript']):
                tag.decompose()

            title = soup.title.string if soup.title else url
            if title:
                title = title.strip()

            text = soup.get_text(separator='\n', strip=True)
            text = re.sub(r'\n\s*\n', '\n\n', text)

            images = self._extract_images(soup, url)

            print("Extracted text (playwright):", text[:200])
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
                'error': 'Playwright: request timeout',
                'content': None,
                'title': None,
                'images': []
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Playwright: {str(e)}',
                'content': None,
                'title': None,
                'images': []
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
