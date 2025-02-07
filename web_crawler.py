import urllib
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import requests
import mimetypes
import os
from collections import defaultdict

class WebCrawler:
    def __init__(self):
        self.visited_urls = set()
        self.files_by_type = defaultdict(list)
        self.errors = []
        self.session = requests.Session()
        
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

    def is_valid_url(self, url, start_domain):
        """Check if URL is valid and belongs to start domain"""
        try:
            parsed = urlparse(url)
            return bool(parsed.netloc) and parsed.netloc == start_domain
        except:
            return False

    def crawl(self, start_url, max_pages=100):
        """Main crawling function"""
        start_domain = urlparse(start_url).netloc
        urls_to_visit = [start_url]

        try:
            while urls_to_visit and len(self.visited_urls) < max_pages:
                url = urls_to_visit.pop(0)

                if url in self.visited_urls:
                    continue

                self.visited_urls.add(url)

                try:
                    # Use session for better performance
                    response = self.session.get(url, timeout=10)
                    response.raise_for_status()

                    # Categorize the current URL
                    file_type = self.get_file_type(url)
                    self.files_by_type[file_type].append(url)

                    # Only parse HTML content for links
                    if 'text/html' in response.headers.get('Content-Type', '').lower():
                        soup = BeautifulSoup(response.text, 'html.parser')

                        # Find all links
                        for link in soup.find_all(['a', 'link', 'script', 'img']):
                            href = link.get('href') or link.get('src')
                            if href:
                                full_url = urljoin(url, href)
                                if self.is_valid_url(full_url, start_domain):
                                    urls_to_visit.append(full_url)

                except Exception as e:
                    self.errors.append(f"Error crawling {url}: {str(e)}")

        except KeyboardInterrupt:
            print("\nCrawling interrupted by user")

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

def main():
    url = input("Enter website to crawl: ")
    max_pages = int(input("Enter maximum number of pages to crawl (default 100): ") or 100)

    crawler = WebCrawler()
    results = crawler.crawl(url, max_pages)

    # Print results
    print("\n=== Crawling Summary ===")
    print(f"Total files found: {results['summary']['total_files']}")

    print("\n=== Files by Type ===")
    for file_type, files in results['files_by_type'].items():
        print(f"{file_type}: {len(files)} files")

        url_tree = build_url_tree(files)
        print_tree(url_tree, prefix="  ")  # Print hierarchy


if __name__ == "__main__":
    main()
