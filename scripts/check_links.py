#!/usr/bin/env python3
"""KubeDojo Link Crawler — crawls the built site and finds real 404s.

Usage:
    npm run build
    npx astro preview &
    python scripts/check_links.py [--base http://localhost:4321] [--max 500]
"""

import argparse
import re
import sys
import urllib.request
import urllib.error
from collections import defaultdict
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse

class LinkExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            for name, value in attrs:
                if name == 'href' and value:
                    self.links.append(value)


def crawl(base_url: str, max_pages: int = 2000) -> dict:
    visited: set[str] = set()
    queue: list[tuple[str, str]] = [(base_url + '/', '(start)')]
    broken: list[tuple[str, str, int]] = []
    ok_count = 0
    skipped = 0

    while queue and len(visited) < max_pages:
        url, referrer = queue.pop(0)

        # Normalize
        parsed = urlparse(url)
        if parsed.fragment:
            url = url.split('#')[0]
        if not url.endswith('/') and '.' not in parsed.path.split('/')[-1]:
            url = url + '/'

        if url in visited:
            continue
        visited.add(url)

        # Only crawl internal links
        if not url.startswith(base_url):
            continue

        try:
            req = urllib.request.Request(url, method='GET')
            req.add_header('User-Agent', 'KubeDojo-LinkChecker/1.0')
            resp = urllib.request.urlopen(req, timeout=10)
            status = resp.getcode()
            content_type = resp.headers.get('Content-Type', '')

            if status == 200:
                ok_count += 1
                if 'text/html' in content_type:
                    html = resp.read().decode('utf-8', errors='replace')
                    parser = LinkExtractor()
                    parser.feed(html)
                    for link in parser.links:
                        abs_link = urljoin(url, link)
                        if abs_link.startswith(base_url) and abs_link not in visited:
                            queue.append((abs_link, url))
            else:
                broken.append((url, referrer, status))

        except urllib.error.HTTPError as e:
            broken.append((url, referrer, e.code))
        except Exception as e:
            broken.append((url, referrer, 0))

        # Progress
        if len(visited) % 100 == 0:
            print(f"  Crawled {len(visited)} pages, {len(broken)} broken, {len(queue)} queued...", flush=True)

    return {
        'visited': len(visited),
        'ok': ok_count,
        'broken': broken,
        'skipped': skipped,
    }


def main():
    parser = argparse.ArgumentParser(description='Crawl KubeDojo site for broken links')
    parser.add_argument('--base', default='http://localhost:4321', help='Base URL')
    parser.add_argument('--max', type=int, default=2000, help='Max pages to crawl')
    args = parser.parse_args()

    print(f"Crawling {args.base} (max {args.max} pages)...")
    print()

    result = crawl(args.base, args.max)

    print()
    print("=" * 60)
    print(f"Pages crawled: {result['visited']}")
    print(f"OK: {result['ok']}")
    print(f"Broken: {len(result['broken'])}")
    print("=" * 60)

    if result['broken']:
        # Group by referrer
        by_referrer: dict[str, list[tuple[str, int]]] = defaultdict(list)
        for url, referrer, status in result['broken']:
            by_referrer[referrer].append((url, status))

        print(f"\nBROKEN LINKS ({len(result['broken'])}):\n")
        for referrer, links in sorted(by_referrer.items()):
            short_ref = referrer.replace(args.base, '')
            print(f"  On page: {short_ref}")
            for url, status in links:
                short_url = url.replace(args.base, '')
                print(f"    → {status} {short_url}")
            print()

        sys.exit(1)
    else:
        print("\nAll links OK!")
        sys.exit(0)


if __name__ == '__main__':
    main()
