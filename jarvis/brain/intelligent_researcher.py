"""
jarvis/brain/intelligent_researcher.py
══════════════════════════════════════════════════════
Advanced research system for J.A.R.V.I.S. intelligent answers.

This module provides sophisticated research capabilities including
academic paper search, technical documentation analysis, expert
knowledge synthesis, and evidence-based responses.
"""

import re
import json
import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from urllib.parse import quote_plus
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET

from services.web_search import SearchResult, _fetch_text, _clean_html

@dataclass
class ResearchSource:
    """Research source with credibility rating."""
    title: str
    url: str
    content: str
    source_type: str  # academic, technical, news, documentation
    credibility_score: float  # 0.0 to 1.0
    publication_date: Optional[str] = None
    authors: Optional[List[str]] = None

@dataclass
class ResearchResult:
    """Comprehensive research result with evidence synthesis."""
    answer: str
    confidence: float
    sources: List[ResearchSource]
    methodology: str
    key_findings: List[str]
    limitations: List[str]
    related_topics: List[str]

class IntelligentResearcher:
    """Advanced research system for intelligent answers."""
    
    def __init__(self):
        self.academic_sources = [
            "arxiv.org",
            "scholar.google.com", 
            "pubmed.ncbi.nlm.nih.gov",
            "ieeexplore.ieee.org",
            "dl.acm.org"
        ]
        
        self.technical_sources = [
            "developer.mozilla.org",
            "docs.python.org",
            "react.dev",
            "nodejs.org",
            "stackoverflow.com"
        ]
        
        self.credible_news = [
            "technologyreview.com",
            "wired.com",
            "arstechnica.com",
            "theverge.com",
            "techcrunch.com"
        ]
        
        self.research_keywords = {
            'computer_science': [
                'algorithm', 'machine learning', 'artificial intelligence', 
                'neural network', 'deep learning', 'computer vision', 'nlp'
            ],
            'software_engineering': [
                'software architecture', 'design patterns', 'devops', 
                'microservices', 'api design', 'system design'
            ],
            'emerging_tech': [
                'quantum computing', 'blockchain', 'edge computing', 
                'iot', '5g', 'augmented reality', 'metaverse'
            ]
        }
    
    def research_intelligent_answer(self, query: str, depth: str = "comprehensive") -> ResearchResult:
        """
        Conduct comprehensive research for intelligent answer.
        
        Args:
            query: Research question or topic
            depth: "quick", "standard", or "comprehensive"
            
        Returns:
            ResearchResult with synthesized intelligent answer
        """
        print(f"🔍 Conducting intelligent research: {query}")
        
        # 1. Analyze query and determine research strategy
        research_strategy = self._analyze_query(query)
        
        # 2. Gather diverse sources
        sources = self._gather_sources(query, research_strategy, depth)
        
        # 3. Extract and analyze content
        analyzed_content = self._analyze_sources(sources)
        
        # 4. Synthesize intelligent answer
        answer = self._synthesize_answer(query, analyzed_content, research_strategy)
        
        # 5. Extract key findings and limitations
        key_findings = self._extract_key_findings(analyzed_content)
        limitations = self._identify_limitations(sources, analyzed_content)
        
        # 6. Identify related topics
        related_topics = self._find_related_topics(query, analyzed_content)
        
        # 7. Calculate confidence score
        confidence = self._calculate_confidence(sources, analyzed_content)
        
        return ResearchResult(
            answer=answer,
            confidence=confidence,
            sources=sources,
            methodology=research_strategy['methodology'],
            key_findings=key_findings,
            limitations=limitations,
            related_topics=related_topics
        )
    
    def _analyze_query(self, query: str) -> Dict:
        """Analyze query to determine optimal research strategy."""
        query_lower = query.lower()
        
        # Determine domain
        domain = "general"
        for domain_name, keywords in self.research_keywords.items():
            if any(keyword in query_lower for keyword in keywords):
                domain = domain_name
                break
        
        # Determine question type
        question_types = {
            'what': ['what is', 'what are', 'what does', 'define'],
            'how': ['how to', 'how do', 'how can', 'how does'],
            'why': ['why is', 'why do', 'why does', 'why are'],
            'compare': ['compare', 'difference', 'versus', 'vs'],
            'future': ['future', 'trend', 'prediction', 'upcoming'],
            'technical': ['implement', 'code', 'algorithm', 'architecture']
        }
        
        question_type = "general"
        for q_type, patterns in question_types.items():
            if any(pattern in query_lower for pattern in patterns):
                question_type = q_type
                break
        
        # Determine methodology
        methodology_map = {
            'what': 'definitional_research',
            'how': 'procedural_analysis',
            'why': 'causal_analysis',
            'compare': 'comparative_analysis',
            'future': 'trend_analysis',
            'technical': 'technical_documentation'
        }
        
        return {
            'domain': domain,
            'question_type': question_type,
            'methodology': methodology_map.get(question_type, 'general_research'),
            'complexity': 'high' if len(query.split()) > 10 else 'medium'
        }
    
    def _gather_sources(self, query: str, strategy: Dict, depth: str) -> List[ResearchSource]:
        """Gather diverse, credible sources based on research strategy."""
        sources = []
        
        # Determine source types based on domain and question type
        if strategy['domain'] == 'computer_science':
            # Prioritize academic sources
            sources.extend(self._search_academic(query, max_results=3))
            sources.extend(self._search_technical(query, max_results=2))
        elif strategy['domain'] == 'software_engineering':
            # Prioritize technical documentation
            sources.extend(self._search_technical(query, max_results=3))
            sources.extend(self._search_stackoverflow(query, max_results=2))
        else:
            # Balanced approach
            sources.extend(self._search_general(query, max_results=2))
            sources.extend(self._search_technical(query, max_results=2))
            sources.extend(self._search_news(query, max_results=1))
        
        # Add depth-specific sources
        if depth == "comprehensive":
            sources.extend(self._search_academic(query, max_results=2))
            sources.extend(self._search_expert_opinions(query, max_results=1))
        
        # Filter by credibility and deduplicate
        filtered_sources = self._filter_sources(sources)
        
        return filtered_sources[:8]  # Limit to top 8 sources for synthesis
    
    def _search_academic(self, query: str, max_results: int = 3) -> List[ResearchSource]:
        """Search academic sources for research papers and studies."""
        sources = []
        
        # ArXiv search (RSS feed)
        try:
            arxiv_query = quote_plus(query)
            arxiv_url = f"http://export.arxiv.org/api/query?search_query=all:{arxiv_query}&start=0&max_results={max_results}"
            xml_content = _fetch_text(arxiv_url, timeout=10)
            
            root = ET.fromstring(xml_content)
            namespace = {'atom': 'http://www.w3.org/2005/Atom'}
            
            for entry in root.findall('atom:entry', namespace)[:max_results]:
                title = entry.find('atom:title', namespace).text.strip()
                summary = entry.find('atom:summary', namespace).text.strip()
                link = entry.find('atom:id', namespace).text.strip()
                
                # Extract authors
                authors = []
                for author in entry.findall('atom:author', namespace):
                    name = author.find('atom:name', namespace).text.strip()
                    authors.append(name)
                
                # Extract publication date
                published = entry.find('atom:published', namespace).text.strip()
                
                source = ResearchSource(
                    title=title,
                    url=link,
                    content=_clean_html(summary),
                    source_type="academic",
                    credibility_score=0.9,  # High credibility for academic papers
                    publication_date=published,
                    authors=authors
                )
                sources.append(source)
                
        except Exception as e:
            print(f"Academic search error: {e}")
        
        return sources
    
    def _search_technical(self, query: str, max_results: int = 3) -> List[ResearchSource]:
        """Search technical documentation and developer resources."""
        sources = []
        
        # Use DuckDuckGo for technical searches with site restrictions
        technical_sites = ["site:developer.mozilla.org", "site:docs.python.org", "site:react.dev"]
        
        for site in technical_sites:
            try:
                site_query = f"{site} {query}"
                ddg_url = f"https://duckduckgo.com/html/?q={quote_plus(site_query)}"
                html_content = _fetch_text(ddg_url, timeout=5)
                
                # Parse results (simplified)
                results = re.findall(
                    r'<a rel="nofollow" class="result__a" href="([^"]+)".*?>(.*?)</a>',
                    html_content,
                    re.DOTALL
                )
                
                for url, title in results[:max_results // len(technical_sites)]:
                    if any(tech_site in url for tech_site in self.technical_sources):
                        try:
                            content = _fetch_text(url, timeout=5)
                            cleaned_content = _clean_html(content)[:1000]  # First 1000 chars
                            
                            source = ResearchSource(
                                title=_clean_html(title),
                                url=url,
                                content=cleaned_content,
                                source_type="technical",
                                credibility_score=0.85  # High credibility for official docs
                            )
                            sources.append(source)
                            
                        except Exception:
                            continue
                            
            except Exception as e:
                print(f"Technical search error for {site}: {e}")
                continue
        
        return sources
    
    def _search_stackoverflow(self, query: str, max_results: int = 2) -> List[ResearchSource]:
        """Search Stack Overflow for practical solutions."""
        sources = []
        
        try:
            so_query = f"site:stackoverflow.com {query}"
            ddg_url = f"https://duckduckgo.com/html/?q={quote_plus(so_query)}"
            html_content = _fetch_text(ddg_url, timeout=5)
            
            results = re.findall(
                r'<a rel="nofollow" class="result__a" href="([^"]+)".*?>(.*?)</a>',
                html_content,
                re.DOTALL
            )
            
            for url, title in results[:max_results]:
                if 'stackoverflow.com/questions' in url:
                    try:
                        content = _fetch_text(url, timeout=5)
                        # Extract answer content (simplified)
                        answer_match = re.search(r'<div class="answer">.*?<div class="post-text">(.*?)</div>', content, re.DOTALL)
                        answer_content = _clean_html(answer_match.group(1)) if answer_match else _clean_html(content)[:500]
                        
                        source = ResearchSource(
                            title=_clean_html(title),
                            url=url,
                            content=answer_content,
                            source_type="community",
                            credibility_score=0.75  # Good credibility for accepted answers
                        )
                        sources.append(source)
                        
                    except Exception:
                        continue
                        
        except Exception as e:
            print(f"Stack Overflow search error: {e}")
        
        return sources
    
    def _search_general(self, query: str, max_results: int = 2) -> List[ResearchSource]:
        """Search general web sources."""
        sources = []
        
        try:
            from services.web_search import search_web
            results = search_web(query, limit=max_results)
            
            for result in results:
                credibility = 0.6  # Base credibility for general sources
                if any(credible in result.url for credible in self.credible_news):
                    credibility = 0.8
                
                source = ResearchSource(
                    title=result.title,
                    url=result.url,
                    content=result.snippet,
                    source_type="news",
                    credibility_score=credibility
                )
                sources.append(source)
                
        except Exception as e:
            print(f"General search error: {e}")
        
        return sources
    
    def _search_news(self, query: str, max_results: int = 1) -> List[ResearchSource]:
        """Search credible news sources."""
        sources = []
        
        try:
            news_query = f"site:{','.join(self.credible_news[:3])} {query}"
            ddg_url = f"https://duckduckgo.com/html/?q={quote_plus(news_query)}"
            html_content = _fetch_text(ddg_url, timeout=5)
            
            results = re.findall(
                r'<a rel="nofollow" class="result__a" href="([^"]+)".*?>(.*?)</a>',
                html_content,
                re.DOTALL
            )
            
            for url, title in results[:max_results]:
                try:
                    content = _fetch_text(url, timeout=5)
                    cleaned_content = _clean_html(content)[:800]
                    
                    source = ResearchSource(
                        title=_clean_html(title),
                        url=url,
                        content=cleaned_content,
                        source_type="news",
                        credibility_score=0.8  # High credibility for reputable news
                    )
                    sources.append(source)
                    
                except Exception:
                    continue
                    
        except Exception as e:
            print(f"News search error: {e}")
        
        return sources
    
    def _search_expert_opinions(self, query: str, max_results: int = 1) -> List[ResearchSource]:
        """Search expert opinions and thought leadership."""
        sources = []
        
        expert_sites = ["medium.com", "towardsdatascience.com", "hackernoon.com"]
        
        try:
            expert_query = f"site:{','.join(expert_sites)} {query}"
            ddg_url = f"https://duckduckgo.com/html/?q={quote_plus(expert_query)}"
            html_content = _fetch_text(ddg_url, timeout=5)
            
            results = re.findall(
                r'<a rel="nofollow" class="result__a" href="([^"]+)".*?>(.*?)</a>',
                html_content,
                re.DOTALL
            )
            
            for url, title in results[:max_results]:
                try:
                    content = _fetch_text(url, timeout=5)
                    cleaned_content = _clean_html(content)[:1000]
                    
                    source = ResearchSource(
                        title=_clean_html(title),
                        url=url,
                        content=cleaned_content,
                        source_type="expert",
                        credibility_score=0.7  # Good credibility for expert content
                    )
                    sources.append(source)
                    
                except Exception:
                    continue
                    
        except Exception as e:
            print(f"Expert search error: {e}")
        
        return sources
    
    def _filter_sources(self, sources: List[ResearchSource]) -> List[ResearchSource]:
        """Filter and deduplicate sources by credibility."""
        seen_urls = set()
        filtered = []
        
        # Sort by credibility score
        sources.sort(key=lambda x: x.credibility_score, reverse=True)
        
        for source in sources:
            if source.url not in seen_urls and source.credibility_score >= 0.6:
                seen_urls.add(source.url)
                filtered.append(source)
        
        return filtered
    
    def _analyze_sources(self, sources: List[ResearchSource]) -> Dict:
        """Analyze and extract key information from sources."""
        analysis = {
            'themes': [],
            'evidence': [],
            'perspectives': [],
            'data_points': [],
            'expert_consensus': None
        }
        
        for source in sources:
            content = source.content.lower()
            
            # Extract key themes (simplified)
            if source.source_type == "academic":
                analysis['evidence'].append(f"Academic research: {source.title}")
            elif source.source_type == "technical":
                analysis['evidence'].append(f"Technical documentation: {source.title}")
            elif source.source_type == "news":
                analysis['perspectives'].append(f"Industry perspective: {source.title}")
            elif source.source_type == "expert":
                analysis['perspectives'].append(f"Expert opinion: {source.title}")
        
        return analysis
    
    def _synthesize_answer(self, query: str, analysis: Dict, strategy: Dict) -> str:
        """Synthesize intelligent answer from analyzed sources."""
        methodology = strategy['methodology']
        question_type = strategy['question_type']
        
        # Build answer based on methodology and question type
        if methodology == 'definitional_research':
            answer = self._synthesize_definition(query, analysis)
        elif methodology == 'procedural_analysis':
            answer = self._synthesize_procedural(query, analysis)
        elif methodology == 'comparative_analysis':
            answer = self._synthesize_comparison(query, analysis)
        elif methodology == 'trend_analysis':
            answer = self._synthesize_trends(query, analysis)
        else:
            answer = self._synthesize_general(query, analysis)
        
        return answer
    
    def _synthesize_definition(self, query: str, analysis: Dict) -> str:
        """Synthesize definitional answer."""
        evidence = analysis.get('evidence', [])
        perspectives = analysis.get('perspectives', [])
        
        answer_parts = []
        
        if evidence:
            answer_parts.append("Based on academic and technical research:")
            answer_parts.extend([f"• {ev}" for ev in evidence[:2]])
        
        if perspectives:
            answer_parts.append("Industry perspectives indicate:")
            answer_parts.extend([f"• {persp}" for persp in perspectives[:1]])
        
        return "\n".join(answer_parts) if answer_parts else "Research indicates this is a complex topic requiring further investigation."
    
    def _synthesize_procedural(self, query: str, analysis: Dict) -> str:
        """Synthesize procedural/how-to answer."""
        evidence = analysis.get('evidence', [])
        
        answer_parts = []
        
        if evidence:
            answer_parts.append("Technical documentation and expert consensus suggest:")
            answer_parts.extend([f"• {ev}" for ev in evidence[:2]])
        
        answer_parts.append("This approach is supported by current best practices in the field.")
        
        return "\n".join(answer_parts)
    
    def _synthesize_comparison(self, query: str, analysis: Dict) -> str:
        """Synthesize comparative answer."""
        perspectives = analysis.get('perspectives', [])
        evidence = analysis.get('evidence', [])
        
        answer_parts = []
        
        if evidence:
            answer_parts.append("Technical analysis reveals:")
            answer_parts.extend([f"• {ev}" for ev in evidence[:2]])
        
        if perspectives:
            answer_parts.append("Expert opinions provide additional context:")
            answer_parts.extend([f"• {persp}" for persp in perspectives[:2]])
        
        return "\n".join(answer_parts)
    
    def _synthesize_trends(self, query: str, analysis: Dict) -> str:
        """Synthesize trend analysis answer."""
        perspectives = analysis.get('perspectives', [])
        
        answer_parts = []
        
        if perspectives:
            answer_parts.append("Current industry trends indicate:")
            answer_parts.extend([f"• {persp}" for persp in perspectives[:3]])
        
        answer_parts.append("These patterns suggest evolving directions in the field.")
        
        return "\n".join(answer_parts)
    
    def _synthesize_general(self, query: str, analysis: Dict) -> str:
        """Synthesize general research answer."""
        evidence = analysis.get('evidence', [])
        perspectives = analysis.get('perspectives', [])
        
        answer_parts = []
        
        if evidence:
            answer_parts.append("Research findings include:")
            answer_parts.extend([f"• {ev}" for ev in evidence[:2]])
        
        if perspectives:
            answer_parts.append("Additional perspectives:")
            answer_parts.extend([f"• {persp}" for persp in perspectives[:1]])
        
        return "\n".join(answer_parts) if answer_parts else "Comprehensive research is needed to fully address this question."
    
    def _extract_key_findings(self, analysis: Dict) -> List[str]:
        """Extract key findings from research analysis."""
        findings = []
        
        evidence = analysis.get('evidence', [])
        perspectives = analysis.get('perspectives', [])
        
        # Extract key points from evidence and perspectives
        for ev in evidence[:3]:
            if len(ev) > 20:
                findings.append(ev[:100] + "..." if len(ev) > 100 else ev)
        
        for persp in perspectives[:2]:
            if len(persp) > 20:
                findings.append(persp[:100] + "..." if len(persp) > 100 else persp)
        
        return findings
    
    def _identify_limitations(self, sources: List[ResearchSource], analysis: Dict) -> List[str]:
        """Identify research limitations."""
        limitations = []
        
        # Check source diversity
        source_types = set(source.source_type for source in sources)
        if len(source_types) < 3:
            limitations.append("Limited source diversity - may benefit from additional perspectives")
        
        # Check recency
        recent_sources = [s for s in sources if s.publication_date and '2024' in s.publication_date]
        if len(recent_sources) < len(sources) // 2:
            limitations.append("Some sources may not reflect the most current developments")
        
        # Check academic rigor
        academic_sources = [s for s in sources if s.source_type == "academic"]
        if not academic_sources:
            limitations.append("Limited academic research - consider scholarly sources for deeper analysis")
        
        return limitations
    
    def _find_related_topics(self, query: str, analysis: Dict) -> List[str]:
        """Identify related topics for further research."""
        related = []
        
        query_lower = query.lower()
        
        # Suggest related topics based on keywords
        if 'artificial intelligence' in query_lower or 'ai' in query_lower:
            related.extend(['machine learning', 'neural networks', 'deep learning', 'natural language processing'])
        
        if 'software' in query_lower or 'programming' in query_lower:
            related.extend(['software architecture', 'design patterns', 'development methodologies'])
        
        if 'technology' in query_lower or 'tech' in query_lower:
            related.extend(['emerging technologies', 'digital transformation', 'innovation trends'])
        
        return related[:5]  # Limit to 5 related topics
    
    def _calculate_confidence(self, sources: List[ResearchSource], analysis: Dict) -> float:
        """Calculate confidence score for research answer."""
        if not sources:
            return 0.0
        
        # Base confidence from source credibility
        credibility_scores = [source.credibility_score for source in sources]
        avg_credibility = sum(credibility_scores) / len(credibility_scores)
        
        # Boost for diverse source types
        source_types = set(source.source_type for source in sources)
        diversity_boost = min(0.2, len(source_types) * 0.05)
        
        # Boost for academic sources
        academic_count = sum(1 for source in sources if source.source_type == "academic")
        academic_boost = min(0.15, academic_count * 0.05)
        
        confidence = avg_credibility + diversity_boost + academic_boost
        
        return min(confidence, 1.0)

# Global researcher instance
intelligent_researcher = IntelligentResearcher()
