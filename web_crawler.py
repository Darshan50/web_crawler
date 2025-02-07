import urllib 
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import requests
# crawl the website
visited_urls = []
directories = {}
directories_list = []
def crawl(url):
    start_url=url
    # Only crawl links within the start domain
    if urlparse(url).netloc != urlparse(start_url).netloc:
        return
    # Check if this URL has already been visited
    if url in visited_urls:
        return
    visited_urls.append(url)
    # Make a request to the URL and parse the HTML
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    # Extract all links on the page
    links = soup.find_all('a')
    for link in links:
        href = link.get('href')
        if href is not None:
            # Construct the full URL of the link
            full_url = urljoin(url, href)
            # Check if the link is a directory or a page and is part of the start URL
            parsed_url = urlparse(full_url)
            if parsed_url.netloc == urlparse(start_url).netloc and parsed_url.path.startswith(urlparse(start_url).path):
                if parsed_url.path.endswith('/'):
                    # If the link is a directory, crawl it recursively
                    if full_url not in visited_urls:
                        directories[parsed_url.path] = []
                        crawl(full_url)
                else:
                    # If the link is a page, add it to the directory's list of pages
                    directory = parsed_url.path.rsplit('/', 1)[0] + '/'
                    directories.setdefault(directory, []).append(full_url)
    return

url = input("Enter website to crawl:")
crawl(url)
print(directories)
