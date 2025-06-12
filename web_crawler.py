from urllib.parse import urljoin, urlparse
from collections import defaultdict
import mimetypes
import os
import asyncio
from playwright.async_api import async_playwright
import requests
class WebCrawler:
    def __init__(self):
        self.visited_urls = set()
        self.files_by_type = defaultdict(list)
        self.errors = []
        self.session = requests.Session()
        self.session.headers.update({
    'User-Agent': 'Mozilla/5.0 (compatible; MyCrawler/1.0; +https://example.com/bot)'
})
        # Add common file extensions
        mimetypes.add_type('application/pdf', '.pdf')
        mimetypes.add_type('application/msword', '.doc')
        mimetypes.add_type('application/vnd.openxmlformats-officedocument.wordprocessingml.document', '.docx')
        mimetypes.add_type('application/vnd.ms-excel', '.xls')
        mimetypes.add_type('application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', '.xlsx')

    def get_file_type(self, url):
        """Determine file type from URL"""
        parsed = urlparse(url)
        path = parsed.path.lower()
        ext = os.path.splitext(path)[1]

        if ext:
            # Get mime type
            mime_type = mimetypes.guess_type(url)[0]
            if mime_type:
                # Return general category
                if 'image' in mime_type:
                    return 'Images'
                elif 'pdf' in mime_type:
                    return 'PDFs'
                elif 'word' in mime_type or 'document' in mime_type:
                    return 'Documents'
                elif 'excel' in mime_type or 'spreadsheet' in mime_type:
                    return 'Spreadsheets'
                elif 'video' in mime_type:
                    return 'Videos'
                elif 'audio' in mime_type:
                    return 'Audio'
                elif 'text' in mime_type:
                    return 'Text Files'
                elif 'application' in mime_type:
                    return 'Applications'
            return f'Other ({ext})'
        return 'Webpages'
    def normalize_url(self, url):
        parsed = urlparse(url)
        return parsed._replace(fragment="", query="").geturl()
    def is_valid_url(self, url, start_domain):
        """Check if URL is valid and belongs to start domain"""
        try:
            parsed = urlparse(url)
            return parsed.scheme in ['http', 'https'] and start_domain in parsed.netloc
        except:
            return False

    async def crawl(self, start_url, max_pages=100):
        start_domain = urlparse(start_url).netloc
        urls_to_visit = [start_url]

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()

            try:
                while urls_to_visit and len(self.visited_urls) < max_pages:
                    url = urls_to_visit.pop(0)
                    norm_url = self.normalize_url(url)

                    if norm_url in self.visited_urls:
                        continue

                    try:
                        await page.goto(norm_url, timeout=100000, wait_until='networkidle')
                        await page.evaluate("""() => {
                            window.scrollBy(0, document.body.scrollHeight);
                        }""")
                        self.visited_urls.add(norm_url)

                        self.files_by_type[self.get_file_type(norm_url)].append(norm_url)

                        anchors = await page.query_selector_all("a[href]")
                        links = []
                        for anchor in anchors:
                            href = await anchor.get_attribute("href")
                            if href:
                                absolute_url = urljoin(norm_url, href)
                                if self.is_valid_url(absolute_url, start_domain) and absolute_url not in self.visited_urls:
                                    links.append(self.normalize_url(absolute_url))
                        for link in links:
                            link = self.normalize_url(link)
                            if self.is_valid_url(link, start_domain) and link not in self.visited_urls:
                                urls_to_visit.append(link)

                    except Exception as e:
                        self.errors.append(f"Error at {url}: {e}")

            finally:
                await browser.close()

        return self.generate_report()

    def generate_report(self):
        """Generate formatted report of findings"""
        return {
            'summary': {
                'total_files': sum(len(files) for files in self.files_by_type.values()),
                'file_types': {k: len(v) for k, v in self.files_by_type.items()}
            },
            'files_by_type': dict(self.files_by_type),
            'errors': self.errors
        }

def build_url_tree(urls):
    """Builds a nested dictionary representing the URL hierarchy."""
    tree = {}

    for url in urls:
        parts = urlparse(url).path.strip("/").split("/")
        current = tree
        for part in parts:
            if part not in current:
                current[part] = {}
            current = current[part]

    return tree

def print_tree(tree, prefix="  "):
    """Recursively prints the URL hierarchy."""
    for key, sub_tree in tree.items():
        print(f"{prefix}- {key}/")
        print_tree(sub_tree, prefix + "   ")

async def main():
    url = input("Enter website to crawl: ").strip()
    max_pages = int(input("Enter maximum number of pages to crawl (default 100): ") or 100)
    crawler = WebCrawler()
    results = await crawler.crawl(url, max_pages)

    # Print results
    print("\n=== Crawling Summary ===")
    print(f"Total files found: {results['summary']['total_files']}")

    print("\n=== Files by Type ===")
    for file_type, files in results['files_by_type'].items():
        print(f"{file_type}: {len(files)} files")

        url_tree = build_url_tree(files)
        print_tree(url_tree, prefix="  ") 
    if results['errors']:
        print("\n=== Errors ===")
        for error in results['errors']:
            print(error)

if __name__ == "__main__":
    asyncio.run(main()) 
