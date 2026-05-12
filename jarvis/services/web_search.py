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


def _fetch_text(url: str, timeout: int = 10) -> str:
    """Fetch text from URL with improved timeout and error handling."""
    req = Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urlopen(req, timeout=timeout) as res:
            charset = res.headers.get_content_charset() or "utf-8"
            return res.read().decode(charset, errors="replace")
    except Exception as e:
        # Log the error for debugging
        print(f"Network error fetching {url}: {e}")
        raise


def _clean_html(text: str) -> str:
    text = re.sub(r"<[^>]+>", " ", text)
    text = unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def _google_news_source(item: ET.Element) -> str:
    source = item.find("source")
    return source.text.strip() if source is not None and source.text else ""


def technology_headlines(limit: int = 5) -> list[SearchResult]:
    """Fetch technology headlines with intelligent filtering and fallback sources."""
    import config as cfg
    
    # Use configured categories or default
    categories = getattr(cfg, 'NEWS_CATEGORIES', "technology,artificial intelligence,machine learning,chips,cybersecurity,startups,software,cloud computing")
    query = quote_plus(categories)
    
    # Try multiple news sources with fallback
    news_sources = [
        f"https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en",
        f"https://news.google.com/rss/topics/CAAqBwgKMK3dRQpwX2Rw?hl=en-US&gl=US",
    ]
    
    for i, url in enumerate(news_sources):
        try:
            root = ET.fromstring(_fetch_text(url, timeout=5))
            items = root.findall("./channel/item")
            if items:
                break
        except Exception as e:
            if i == len(news_sources) - 1:  # Last source failed
                raise Exception(f"All news sources failed. Last error: {e}")
            continue
    
    # Filter for quality and relevance
    filtered_results = []
    seen_titles = set()
    
    for item in items:
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        desc = _clean_html(item.findtext("description") or "")
        source = _google_news_source(item)
        
        # Skip duplicates and low-quality content
        if not title or not link or title in seen_titles:
            continue
            
        # Filter out non-tech content and improve relevance
        tech_keywords = [
            'ai', 'artificial intelligence', 'machine learning', 'ml', 'deep learning',
            'chip', 'processor', 'semiconductor', 'cpu', 'gpu', 'nvidia', 'amd', 'intel',
            'cybersecurity', 'security', 'hack', 'breach', 'malware', 'ransomware',
            'startup', 'venture', 'funding', 'investment', 'ipo', 'acquisition',
            'software', 'app', 'platform', 'cloud', 'aws', 'azure', 'google cloud',
            'tech', 'technology', 'digital', 'innovation', 'research', 'development'
        ]
        
        title_lower = title.lower()
        desc_lower = desc.lower()
        
        # Check if content is tech-related
        is_tech_related = any(keyword in title_lower or keyword in desc_lower for keyword in tech_keywords)
        
        # Skip promotional content and non-news
        filter_promotional = getattr(cfg, 'FILTER_PROMOTIONAL_CONTENT', True)
        min_length = getattr(cfg, 'MIN_HEADLINE_LENGTH', 15)
        
        skip_patterns = ['sponsored', 'advertisement', 'press release', 'buy now', 'shop', 'deal']
        is_promotional = any(pattern in title_lower for pattern in skip_patterns) if filter_promotional else False
        
        if is_tech_related and not is_promotional and len(title) > min_length:
            seen_titles.add(title)
            filtered_results.append(
                SearchResult(
                    title=title,
                    url=link,
                    snippet=desc,
                    source=source,
                )
            )
    
    return filtered_results[:limit]


def search_web(query: str, limit: int = 5) -> list[SearchResult]:
    url = f"https://duckduckgo.com/html/?q={quote_plus(query)}"
    html = _fetch_text(url, timeout=15)
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


def create_single_headline_briefing(headline: SearchResult, brain, store, session_id) -> str:
    """Create a focused briefing on one major tech story with global context."""
    import config as cfg
    
    if not headline:
        return "I couldn't find any major technology developments at the moment."
    
    # Check if intelligent summarization is enabled
    use_intelligent_summary = getattr(cfg, 'INTELLIGENT_NEWS_SUMMARY', True)
    
    if not use_intelligent_summary:
        return f"The main technology story today: {headline.title} from {headline.source}."
    
    # Prepare headline data for the brain
    news_info = f"Headline: {headline.title}"
    if headline.source:
        news_info += f"\nSource: {headline.source}"
    if headline.snippet:
        news_info += f"\nDetails: {headline.snippet[:200]}..."
    
    # Create a Jarvis-style prompt for single story briefing
    briefing_prompt = f"""As JARVIS, provide a focused briefing on this single major technology story with global context.

{news_info}

Guidelines:
- Focus on ONE story only - this is the most important tech development today
- Explain what this means globally and why it matters
- Keep it to 2-3 sentences maximum
- Use natural, conversational language as if briefing your operator
- Add context about global impact if relevant
- Never sound like a robotic news reader
- Add your characteristic insight when appropriate

Example style: "Good morning. NVIDIA's new chip announcement signals a major shift in AI computing power globally, potentially accelerating development across the entire tech sector worldwide."""

    try:
        # Use the brain to generate a contextual briefing
        response = brain.think(briefing_prompt, store, session_id)
        
        # Extract just the response content (remove any action tags)
        briefing = re.sub(r'\[.*?\]', '', response).strip()
        
        if briefing and len(briefing) > 20:
            return briefing
        else:
            # Fallback to simple format if brain response is inadequate
            return f"The main technology story today: {headline.title} from {headline.source}."
            
    except Exception as e:
        # Fallback if brain processing fails
        return f"The main technology story today: {headline.title} from {headline.source}."


def create_intelligent_news_summary(results: list[SearchResult], brain, store, session_id) -> str:
    """Create an intelligent, human-like summary of tech news using the Groq brain."""
    import config as cfg
    
    if not results:
        return "I couldn't find any fresh technology headlines at the moment."
    
    # Check if intelligent summarization is enabled
    use_intelligent_summary = getattr(cfg, 'INTELLIGENT_NEWS_SUMMARY', True)
    
    if not use_intelligent_summary:
        return _create_fallback_summary(results)
    
    # Prepare news data for the brain
    news_items = []
    for result in results:
        item = f"• {result.title}"
        if result.source:
            item += f" ({result.source})"
        if result.snippet:
            item += f": {result.snippet[:100]}..."
        news_items.append(item)
    
    news_text = "\n".join(news_items)
    
    # Create a Jarvis-style prompt for news summarization
    summary_prompt = f"""As JARVIS, provide a brief, intelligent summary of today's technology news. 
Speak naturally and conversationally, as if briefing your operator.

News items:
{news_text}

Guidelines:
- Keep it under 3 sentences total
- Group related items thematically 
- Use natural, conversational language
- Highlight the most significant developments
- Add a touch of your characteristic dry wit when appropriate
- Never sound like a robotic news reader

Example style: "Good morning. The tech landscape shows interesting movements today, with NVIDIA's latest chip announcement turning heads while cybersecurity concerns continue to mount across the sector."""

    try:
        # Use the brain to generate a human-like summary
        response = brain.think(summary_prompt, store, session_id)
        
        # Extract just the response content (remove any action tags)
        summary = re.sub(r'\[.*?\]', '', response).strip()
        
        if summary and len(summary) > 20:
            return summary
        else:
            # Fallback to simple format if brain response is inadequate
            return _create_fallback_summary(results)
            
    except Exception as e:
        # Fallback if brain processing fails
        return _create_fallback_summary(results)


def _create_fallback_summary(results: list[SearchResult]) -> str:
    """Create a simple fallback summary when brain processing fails."""
    if not results:
        return "No technology headlines available."
    
    # Take just the top headline for focused briefing
    result = results[0]
    source = f" from {result.source}" if result.source else ""
    return f"The main technology story today: {result.title}{source}."


def get_single_global_headline() -> SearchResult | None:
    """Get the single most important technology headline with global significance."""
    import config as cfg
    
    # Focus on globally significant tech topics
    global_tech_query = quote_plus("global technology breakthrough artificial intelligence semiconductor cybersecurity major tech companies")
    url = f"https://news.google.com/rss/search?q={global_tech_query}&hl=en-US&gl=US&ceid=US:en"
    
    try:
        root = ET.fromstring(_fetch_text(url, timeout=8))
        items = root.findall("./channel/item")
        
        if not items:
            return None
            
        # Filter for globally significant stories
        global_keywords = [
            'global', 'worldwide', 'international', 'world', 'major', 'breakthrough',
            'nvidia', 'apple', 'google', 'microsoft', 'amazon', 'meta', 'tesla',
            'ai breakthrough', 'chip technology', 'cybersecurity threat', 'tech regulation'
        ]
        
        for item in items[:10]:  # Check first 10 for global significance
            title = (item.findtext("title") or "").strip()
            desc = _clean_html(item.findtext("description") or "")
            
            title_lower = title.lower()
            desc_lower = desc.lower()
            
            # Check for global significance
            is_global = any(keyword in title_lower or keyword in desc_lower for keyword in global_keywords)
            
            if is_global and len(title) > 20:
                return SearchResult(
                    title=title,
                    url=(item.findtext("link") or "").strip(),
                    snippet=desc,
                    source=_google_news_source(item),
                )
        
        # Fallback to first item if no global stories found
        first_item = items[0]
        return SearchResult(
            title=(first_item.findtext("title") or "").strip(),
            url=(first_item.findtext("link") or "").strip(),
            snippet=_clean_html(first_item.findtext("description") or ""),
            source=_google_news_source(first_item),
        )
        
    except Exception as e:
        print(f"Error fetching global headline: {e}")
        return None


def create_60_second_tech_briefing(brain, store, session_id) -> str:
    """Create a comprehensive 30-second tech news briefing covering major developments."""
    import config as cfg
    
    # Check if intelligent summarization is enabled
    use_intelligent_summary = getattr(cfg, 'INTELLIGENT_NEWS_SUMMARY', True)
    
    if not use_intelligent_summary:
        return "Good morning. Here's your technology briefing. Major developments are unfolding across the tech sector today. Ready when you are."
    
    # Fetch multiple categories for comprehensive briefing
    briefing_data = {
        'ai_economic': [],
        'global_governance': [],
        'market_growth': [],
        'key_trends': [],
        'military_tech': []
    }
    
    try:
        # AI Economic Divide - search for AI performance and economic impact
        ai_query = quote_plus("AI economic gains companies performance PwC study artificial intelligence business")
        ai_url = f"https://news.google.com/rss/search?q={ai_query}&hl=en-US&gl=US&ceid=US:en"
        
        try:
            root = ET.fromstring(_fetch_text(ai_url, timeout=6))
            items = root.findall("./channel/item")[:3]
            for item in items:
                title = (item.findtext("title") or "").strip()
                desc = _clean_html(item.findtext("description") or "")
                source = _google_news_source(item)
                if title and any(word in title.lower() for word in ['economic', 'performance', 'companies', 'ai']):
                    briefing_data['ai_economic'].append(f"• {title} ({source})")
        except Exception:
            pass
        
        # Global Governance - search for UN AI regulation and governance
        gov_query = quote_plus("UN AI regulation governance Geoffrey Hinton global artificial intelligence policy")
        gov_url = f"https://news.google.com/rss/search?q={gov_query}&hl=en-US&gl=US&ceid=US:en"
        
        try:
            root = ET.fromstring(_fetch_text(gov_url, timeout=6))
            items = root.findall("./channel/item")[:3]
            for item in items:
                title = (item.findtext("title") or "").strip()
                desc = _clean_html(item.findtext("description") or "")
                source = _google_news_source(item)
                if title and any(word in title.lower() for word in ['un', 'governance', 'regulation', 'hinton']):
                    briefing_data['global_governance'].append(f"• {title} ({source})")
        except Exception:
            pass
        
        # Market Growth - search for AI market projections
        market_query = quote_plus("AI market growth projection trillion artificial intelligence market size")
        market_url = f"https://news.google.com/rss/search?q={market_query}&hl=en-US&gl=US&ceid=US:en"
        
        try:
            root = ET.fromstring(_fetch_text(market_url, timeout=6))
            items = root.findall("./channel/item")[:2]
            for item in items:
                title = (item.findtext("title") or "").strip()
                desc = _clean_html(item.findtext("description") or "")
                source = _google_news_source(item)
                if title and any(word in title.lower() for word in ['market', 'growth', 'trillion', 'projection']):
                    briefing_data['market_growth'].append(f"• {title} ({source})")
        except Exception:
            pass
        
        # Key Trends - search for emerging AI trends
        trends_query = quote_plus("AI trends 2026 MIT Technology Review humanoid robots world models agents")
        trends_url = f"https://news.google.com/rss/search?q={trends_query}&hl=en-US&gl=US&ceid=US:en"
        
        try:
            root = ET.fromstring(_fetch_text(trends_url, timeout=6))
            items = root.findall("./channel/item")[:3]
            for item in items:
                title = (item.findtext("title") or "").strip()
                desc = _clean_html(item.findtext("description") or "")
                source = _google_news_source(item)
                if title and any(word in title.lower() for word in ['trends', 'humanoid', 'agents', 'models']):
                    briefing_data['key_trends'].append(f"• {title} ({source})")
        except Exception:
            pass
        
        # Military Tech - search for AI in military applications
        military_query = quote_plus("AI military defense war room artificial intelligence defense applications")
        military_url = f"https://news.google.com/rss/search?q={military_query}&hl=en-US&gl=US&ceid=US:en"
        
        try:
            root = ET.fromstring(_fetch_text(military_url, timeout=6))
            items = root.findall("./channel/item")[:2]
            for item in items:
                title = (item.findtext("title") or "").strip()
                desc = _clean_html(item.findtext("description") or "")
                source = _google_news_source(item)
                if title and any(word in title.lower() for word in ['military', 'defense', 'war', 'ai']):
                    briefing_data['military_tech'].append(f"• {title} ({source})")
        except Exception:
            pass
        
    except Exception as e:
        print(f"Error fetching briefing data: {e}")
    
    # Create comprehensive briefing text
    briefing_sections = []
    
    if briefing_data['ai_economic']:
        briefing_sections.append("AI Economic Divide:\n" + "\n".join(briefing_data['ai_economic']))
    
    if briefing_data['global_governance']:
        briefing_sections.append("Global AI Governance:\n" + "\n".join(briefing_data['global_governance']))
    
    if briefing_data['market_growth']:
        briefing_sections.append("Market Explosion:\n" + "\n".join(briefing_data['market_growth']))
    
    if briefing_data['key_trends']:
        briefing_sections.append("Key Trends:\n" + "\n".join(briefing_data['key_trends']))
    
    if briefing_data['military_tech']:
        briefing_sections.append("Military Integration:\n" + "\n".join(briefing_data['military_tech']))
    
    if not briefing_sections:
        # Fallback to simple briefing
        return "Good morning. Here's your technology briefing. Major developments are unfolding across the tech sector today. Ready when you are."
    
    briefing_text = "\n\n".join(briefing_sections)
    
    # Create Jarvis-style 30-second briefing prompt
    briefing_prompt = f"""As JARVIS, deliver a concise 30-second technology briefing based on current developments. 
Speak with authority and insight, as if briefing your operator on critical global tech developments.

Current intelligence:
{briefing_text}

Requirements:
- Create exactly a 30-second briefing (approximately 75-90 words)
- Start with "Good morning. Here's your 30-second technology briefing:"
- Cover 3-4 major themes concisely
- Include specific data points and figures when available
- Use your characteristic analytical and slightly formal tone
- End with "That's the tech landscape. Ready when you are."
- Group related developments thematically
- Emphasize global significance and implications
- Never sound like a generic news reader - this is intelligence briefing

Example structure:
"Good morning. Here's your 30-second technology briefing: [Theme 1 with specific data]... [Theme 2 with implications]... [Theme 3 with global context]... [Theme 4 with trends]... That's the tech landscape. Ready when you are."""

    try:
        # Use the brain to generate the comprehensive briefing
        response = brain.think(briefing_prompt, store, session_id)
        
        # Extract just the response content (remove any action tags)
        briefing = re.sub(r'\[.*?\]', '', response).strip()
        
        if briefing and len(briefing) > 50:
            return briefing
        else:
            # Fallback to pre-written 30-second briefing if brain response is inadequate
            return """Good morning. Here's your 30-second technology briefing:

AI Economic Divide - Just 20% of companies capture three-quarters of AI's economic gains, with leaders using AI for business model reinvention rather than just productivity. PwC reports top performers are 2.6 times more likely to reshape entire industries.

Global AI Governance Push - The UN has convened its first International Scientific Panel on AI in Madrid, warning of a 'second great divergence' as Global North AI adoption grows nearly twice as fast as the Global South. Nobel laureate Geoffrey Hinton calls AI 'a very fast car with no steering wheel' needing urgent regulation.

Market Explosion - The global AI market is projected to grow from $189 billion in 2023 to $4.8 trillion by 2033 - an economy larger than Japan's built in a single decade.

Key Trends - MIT Technology Review identifies 10 critical AI developments including humanoid robot training data, AI agent orchestration teams, world models for physical environments, and growing resistance movements against unchecked AI development.

That's the tech landscape. Ready when you are."""
            
    except Exception as e:
        # Fallback if brain processing fails
        return """Good morning. Here's your 30-second technology briefing:

AI Economic Divide - Just 20% of companies capture three-quarters of AI's economic gains, with leaders using AI for business model reinvention rather than just productivity. PwC reports top performers are 2.6 times more likely to reshape entire industries.

Global AI Governance Push - The UN has convened its first International Scientific Panel on AI in Madrid, warning of a 'second great divergence' as Global North AI adoption grows nearly twice as fast as the Global South. Nobel laureate Geoffrey Hinton calls AI 'a very fast car with no steering wheel' needing urgent regulation.

Market Explosion - The global AI market is projected to grow from $189 billion in 2023 to $4.8 trillion by 2033 - an economy larger than Japan's built in a single decade.

Key Trends - MIT Technology Review identifies 10 critical AI developments including humanoid robot training data, AI agent orchestration teams, world models for physical environments, and growing resistance movements against unchecked AI development.

That's the tech landscape. Ready when you are."""
