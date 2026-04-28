"""
Small web-search helpers for Jarvis.

Uses public RSS/HTML endpoints so the assistant can fetch current information
without requiring another API key.
"""

from __future__ import annotations

from dataclasses import dataclass
from html import unescape
import re
from urllib.parse import quote_plus, urlparse, parse_qs, unquote
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET


USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) JarvisDesktop/1.0"
)


@dataclass
class SearchResult:
    title: str
    url: str
    snippet: str = ""
    source: str = ""


def _fetch_text(url: str, timeout: int = 5) -> str:
    req = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(req, timeout=timeout) as res:
        charset = res.headers.get_content_charset() or "utf-8"
        return res.read().decode(charset, errors="replace")


def _clean_html(text: str) -> str:
    text = re.sub(r"<[^>]+>", " ", text)
    text = unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def _google_news_source(item: ET.Element) -> str:
    source = item.find("source")
    return source.text.strip() if source is not None and source.text else ""


def technology_headlines(limit: int = 5) -> list[SearchResult]:
    query = quote_plus("major technology news artificial intelligence chips cybersecurity startups")
    url = f"https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"
    root = ET.fromstring(_fetch_text(url, timeout=3))
    items = root.findall("./channel/item")
    results = []
    for item in items[:limit]:
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        desc = _clean_html(item.findtext("description") or "")
        if title and link:
            results.append(
                SearchResult(
                    title=title,
                    url=link,
                    snippet=desc,
                    source=_google_news_source(item),
                )
            )
    return results


def search_web(query: str, limit: int = 5) -> list[SearchResult]:
    url = f"https://duckduckgo.com/html/?q={quote_plus(query)}"
    html = _fetch_text(url)
    blocks = re.findall(
        r'<a rel="nofollow" class="result__a" href="(?P<url>.*?)".*?>(?P<title>.*?)</a>.*?'
        r'<a class="result__snippet".*?>(?P<snippet>.*?)</a>',
        html,
        flags=re.DOTALL,
    )
    results = []
    for raw_url, raw_title, raw_snippet in blocks[:limit]:
        result_url = unescape(raw_url)
        if "duckduckgo.com/l/" in result_url:
            parsed = urlparse(result_url)
            uddg = parse_qs(parsed.query).get("uddg", [""])[0]
            result_url = unquote(uddg) if uddg else result_url
        title = _clean_html(raw_title)
        snippet = _clean_html(raw_snippet)
        if title and result_url:
            source = urlparse(result_url).netloc.replace("www.", "")
            results.append(SearchResult(title=title, url=result_url, snippet=snippet, source=source))
    return results


def format_results(results: list[SearchResult]) -> str:
    if not results:
        return "No current web results were found."
    lines = []
    for idx, result in enumerate(results, start=1):
        source = f" ({result.source})" if result.source else ""
        snippet = f" - {result.snippet}" if result.snippet else ""
        lines.append(f"{idx}. {result.title}{source}{snippet}")
    return "\n".join(lines)
