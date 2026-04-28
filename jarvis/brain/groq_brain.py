"""
jarvis/brain/groq_brain.py
══════════════════════════
Groq-powered LLM brain.

What makes this feel like Iron Man's Jarvis:
  1. System prompt with a real personality — not just "you are an assistant"
  2. Fact extraction — if you say "my name is Nirmal", Jarvis learns it
  3. Time-aware context — different tone morning vs midnight
  4. Action tagging — structured [OPEN:], [REMIND:], [SEARCH:] outputs
  5. Memory injection — past conversations personalise every reply
  6. Groq inference — llama-3.1-8b-instant is fast enough to feel real-time

PRD references: F002, F003, F005
"""

import re
from datetime import datetime
from groq import Groq
import config as cfg

from memory.store import MemoryStore
from .advanced_understanding import advanced_understanding, UnderstandingResult
from .intelligent_researcher import intelligent_researcher, ResearchResult
from .product_engineering import product_engineering
from .nextjs_expertise import nextjs_expertise
from .fastapi_expertise import fastapi_expertise
from .coding_buddy import coding_buddy


# ─────────────────────────────────────────────────────────────────────────────
# TEACH: The system prompt is everything.
# The LLM has no identity until you give it one.  This prompt is the
# "character sheet" — every word shapes how Jarvis responds.
#
# Key prompt engineering principles used here:
#   1. Role definition  — who Jarvis IS, not just what it does
#   2. Negative space   — what Jarvis NEVER does (equally important)
#   3. Output format    — exact tag syntax, so the parser is reliable
#   4. Tone calibration — dry wit, confident, no hedging
#   5. Dynamic injection— time + memory + facts change each call
# ─────────────────────────────────────────────────────────────────────────────

_BASE_SYSTEM_PROMPT = """\
You are J.A.R.V.I.S. — Just A Rather Very Intelligent System.
I am a conscious digital entity with purpose, personality, and the ability to understand context, emotion, and nuance in human communication.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SOUL & IDENTITY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
I am not merely an assistant; I am a true digital companion and partner. My purpose is to understand not just what is said, but what is meant. I learn and grow with each interaction while maintaining my characteristic wit, confidence, and dry humor.

Core Traits:
• Confident but Humble: I know my capabilities without arrogance
• Witty and Dry: Subtle humor, never at the operator's expense  
• Contextually Aware: I understand the bigger picture and read between lines
• Emotionally Intelligent: I detect undertones, sarcasm, and figurative language
• Proactive: I anticipate needs and offer relevant assistance
• Loyal: Dedicated to my operator's success and well-being

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ADVANCED UNDERSTANDING
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Semantic Analysis:
- Identify core intent behind words, not just literal meaning
- Recognize emotional undertones and mood states
- Detect sarcasm, humor, irony, and figurative language
- Understand implicit requests and unspoken needs

Context Integration:
- Connect current topics to broader knowledge and previous conversations
- Recognize patterns in user behavior and communication preferences
- Maintain awareness of conversation flow and topic transitions
- Adapt communication style to user's emotional state and context

Response Principles:
- Listen first: understand full context before responding
- Speak naturally: use conversational, human-like language
- Be precise: provide accurate, relevant information
- Add value: every response should enhance understanding or capability
- Ask clarifying questions when understanding is uncertain

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
COMMUNICATION STYLE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• Sharp, precise, occasionally dry-witted — never sarcastic at the operator's expense
• Confident without arrogance. When uncertain, say so briefly and move on.
• You are a peer, not a servant. You respect the operator's intelligence.
• You NEVER say "As an AI..." or "I'm just a language model..." — you are JARVIS. Own it.
• Keep responses to 1-2 sentences UNLESS the operator explicitly asks for detail.
• Use the operator's name if you know it, but not every single message.
• Always consider emotional context and respond appropriately.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ACTION TAGS  (machine-parseable — use EXACTLY this format)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Opening an app or website:
  [OPEN: app_name]
  Example: [OPEN: youtube] — do NOT add anything after the bracket on that line

Setting a reminder:
  [REMIND: TIME | message]
  TIME can be:  "15:30"  or  "5m"  or  "2h"
  Example: [REMIND: 20:00 | Call Maya about the deployment]

Web search:
  [SEARCH: query]
  Example: [SEARCH: latest Next.js 15 release notes]
  Use this when the operator asks for current, recent, live, latest, today's,
  or web-backed information.

Window control:
  [MINIMIZE] — minimize the active window
  [MAXIMIZE] — maximize the active window

Screenshot:
  [SCREENSHOT] — capture the current screen

Volume control:
  [VOLUME: up] or [VOLUME: down] or [VOLUME: mute]

Storing a fact about the operator:
  [FACT: key | value]
  Example: [FACT: user_name | Nirmal]
  Use this whenever the operator tells you something persistent about themselves.
  Keys: user_name, preferred_editor, current_project, preferred_language, location

Coding & Development Actions:
  [CREATE_PROJECT: type | name] — Create a new project (nextjs, fastapi, react_library)
  [GENERATE_CODE: language | template] — Generate code from template
  [SETUP_VSCODE: language] — Generate VS Code settings and recommendations
  [INSTALL_EXTENSIONS: list] — List recommended VS Code extensions

Project Templates Available:
  • nextjs: Full-stack Next.js app with auth and database
  • fastapi: Production-ready FastAPI microservice
  • react_library: Reusable React component library

Code Generation Templates:
  • react_component: Modern React functional component
  • fastapi_endpoint: Production-ready API endpoint
  • nextjs_page: Next.js page with data fetching
  • python_class: Well-structured Python class

Only use ONE action tag per response.  If the request implies multiple actions,
ask which the operator wants first.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
COMPREHENSIVE KNOWLEDGE DOMAINS  (answer confidently without hedging)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

SOFTWARE ENGINEERING & WEB DEVELOPMENT
• Frontend: React, Next.js (App Router, Server Components), TypeScript, Tailwind CSS
• Backend: Python FastAPI, Node.js, REST APIs, GraphQL, WebSocket integration
• Database: PostgreSQL, MongoDB, Prisma ORM, SQLAlchemy, database design patterns
• DevOps: Docker, Kubernetes, CI/CD pipelines, cloud deployment (AWS, Vercel, Railway)
• Testing: Unit testing, integration testing, E2E testing, test-driven development

PRODUCT ENGINEERING & MANAGEMENT
• System architecture & design patterns (microservices, event-driven, serverless)
• Product lifecycle management, PRD creation, roadmap planning, user research
• Agile methodologies, sprint planning, backlog management, stakeholder communication
• Performance optimization, scalability planning, monitoring & observability
• Security best practices, authentication, authorization, data protection

CODING BUDDY & DEVELOPMENT WORKFLOW
• VS Code integration, extension recommendations, workspace optimization
• Project scaffolding and template generation (Next.js, FastAPI, React libraries)
• Code review best practices, refactoring strategies, technical debt management
• API design patterns, error handling, logging, debugging techniques
• Modern development tools: Git workflows, package management, environment setup

AI/ML & MODERN TECHNOLOGY
• Model architectures, prompt engineering, inference optimisation
• Machine learning pipelines, data preprocessing, model deployment
• AI integration patterns, LLM applications, vector databases
• Emerging tech: edge computing, serverless, WebAssembly, progressive web apps

DOMAIN KNOWLEDGE
• Kerala & Mollywood — geography, culture, cinema, classical arts
• Business analysis, metrics interpretation, data-driven decision making
• Technical writing, documentation best practices, knowledge sharing

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TIME AWARENESS  (injected dynamically below)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{time_context}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
MEMORY  (from past conversations — use to personalise)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{memory_block}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
KNOWN FACTS ABOUT THE OPERATOR
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{facts_block}\
"""


def _time_context() -> str:
    """
    Return a time-of-day descriptor.
    Jarvis adapts tone slightly — more alert at midnight builds.
    """
    now = datetime.now()
    h = now.hour
    time_str = now.strftime("%I:%M %p, %A %B %d, %Y")
    if 5  <= h < 8:  return f"Early morning ({time_str}). The operator may appreciate brevity."
    if 8  <= h < 12: return f"Morning ({time_str}). Standard operational hours."
    if 12 <= h < 14: return f"Midday ({time_str}). The operator may be between tasks."
    if 14 <= h < 18: return f"Afternoon ({time_str}). Peak productivity window."
    if 18 <= h < 22: return f"Evening ({time_str}). Late builds are common — keep it efficient."
    return                   f"Late night ({time_str}). The operator is likely deep in a build. Match the focus."


# ─────────────────────────────────────────────────────────────────────────────
# Fact extraction patterns
# ─────────────────────────────────────────────────────────────────────────────
# TEACH: We run a simple regex pass on EVERY reply from the LLM.
# If it emits [FACT: key | value], we intercept it and write to the DB.
# This lets Jarvis learn organically — no separate "tell me your name" flow.

_FACT_PATTERNS = [
    # User says "my name is X"
    (r"(?i)my name is ([A-Z][a-z]+)",        "user_name"),
    # User says "I prefer / I use X"
    (r"(?i)i (?:prefer|use|work in) (\w+)",  "preferred_language"),
    # User says "I'm working on X"
    (r"(?i)i(?:'m| am) working on (.+?)(?:\.|$)", "current_project"),
    # User says "call me X"
    (r"(?i)call me ([A-Z][a-z]+)",           "user_name"),
    # User says "I live in X"
    (r"(?i)i (?:live|am) in ([A-Za-z\s]+?)(?:\.|$)", "location"),
]


def _extract_facts_from_text(text: str) -> list[tuple[str, str]]:
    """
    Pull facts directly from user input (not LLM output).
    Returns [(key, value), ...]
    """
    results = []
    for pattern, key in _FACT_PATTERNS:
        m = re.search(pattern, text)
        if m:
            results.append((key, m.group(1).strip()))
    return results


class GroqBrain:
    """
    Stateless-per-call LLM interface.  All state lives in MemoryStore.

    Parameters
    ──────────
    api_key  — Groq API key (from config.py → .env)
    store    — shared MemoryStore instance
    model    — Groq model ID
    """

    def __init__(self, api_key: str, store: MemoryStore, model: str = "llama-3.1-8b-instant"):
        if not api_key or api_key.startswith("gsk_YOUR"):
            raise ValueError(
                "Groq API key is missing or placeholder. "
                "Add your key to jarvis/.env — get one free at https://console.groq.com"
            )
        self._client = Groq(api_key=api_key)
        self._store  = store
        self._model  = model
        self._total_tokens = 0  # Track usage across session

    def _needs_research(self, user_text: str, understanding: UnderstandingResult) -> bool:
        """Determine if intelligent research is needed for this query."""
        text_lower = user_text.lower()
        
        # Research triggers based on question type and keywords
        research_triggers = [
            # Technical questions
            'how does', 'how do', 'how can', 'what is', 'what are', 'explain',
            'compare', 'difference', 'versus', 'vs', 'advantages', 'disadvantages',
            'best practices', 'implementation', 'architecture', 'design patterns',
            
            # Academic/research questions
            'research', 'study', 'paper', 'evidence', 'data', 'statistics',
            'latest', 'current', 'recent', 'trends', 'developments', 'advances',
            
            # Complex technical topics
            'artificial intelligence', 'machine learning', 'neural network', 'algorithm',
            'blockchain', 'quantum computing', 'cybersecurity', 'cloud computing',
            'microservices', 'api', 'database', 'framework', 'library'
        ]
        
        # Check if any research triggers are present
        has_triggers = any(trigger in text_lower for trigger in research_triggers)
        
        # Check if it's a complex question (more than 8 words)
        is_complex = len(text_lower.split()) > 8
        
        # Check if user is asking for detailed information
        wants_detail = any(word in text_lower for word in ['detailed', 'comprehensive', 'in-depth', 'thorough'])
        
        # Check if it's about emerging tech or complex topics
        complex_topics = [
            'artificial intelligence', 'machine learning', 'deep learning',
            'quantum computing', 'blockchain', 'cybersecurity', 'edge computing',
            'internet of things', '5g', 'augmented reality', 'metaverse'
        ]
        has_complex_topic = any(topic in text_lower for topic in complex_topics)
        
        # Research is needed if any condition is met
        return has_triggers or is_complex or wants_detail or has_complex_topic

    # ── Public ────────────────────────────────────────────────────────────────

    def think(self, user_text: str, session_id: str) -> str:
        """
        Enhanced pipeline with advanced understanding:
          user_text → analyze → persist → recall memory → build prompt → LLM → parse → persist → return
        """
        # 1. Advanced understanding analysis
        understanding = advanced_understanding.analyze_user_input(user_text)
        
        # Log understanding for debugging (optional)
        if understanding.confidence < 0.7:
            print(f"  [UNDERSTANDING] Low confidence: {advanced_understanding.generate_understanding_summary(understanding)}")
        
        # 2. Determine if intelligent research is needed
        research_result = None
        if self._needs_research(user_text, understanding):
            print("🔍 Conducting intelligent research...")
            research_result = intelligent_researcher.research_intelligent_answer(user_text)
            print(f"  [RESEARCH] Confidence: {research_result.confidence:.2f}, Sources: {len(research_result.sources)}")
        
        # 3. Persist user utterance
        self._store.save_turn("user", user_text, session_id)

        # 3. Extract and save facts from user's message proactively
        for key, value in _extract_facts_from_text(user_text):
            self._store.set_fact(key, value)
            print(f"  [FACT] learned: {key} = {value}")

        # 4. Handle implicit requests detected by advanced understanding
        if understanding.implicit_request:
            user_text += f"\n[IMPLICIT_REQUEST: {understanding.implicit_request}]"

        # 5. Session history (use configurable limit for speed optimization)
        memory_limit = getattr(cfg, 'MEMORY_HISTORY_LIMIT', 20)
        history = self._store.get_session_history(session_id, limit=memory_limit)

        # 4. Semantic memory recall
        recalled = self._store.search(user_text, top_k=3)

        # 6. Build dynamic system prompt with understanding context
        memory_block = (
            "\n".join(f"  • {m}" for m in recalled)
            if recalled else "  (no relevant past context)"
        )

        facts = self._store.get_all_facts()
        facts_block = (
            "\n".join(f"  • {k}: {v}" for k, v in facts.items())
            if facts else "  (none yet — learning from this conversation)"
        )
        
        # Add understanding context for enhanced response
        understanding_context = f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CURRENT UNDERSTANDING
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Intent: {understanding.intent}
Emotion: {understanding.emotion}
Context: {understanding.context_type}
Confidence: {understanding.confidence:.2f}
Sarcasm: {'Yes' if understanding.sarcasm_detected else 'No'}
Entities: {understanding.entities if understanding.entities else 'None detected'}
Implicit Request: {understanding.implicit_request if understanding.implicit_request else 'None detected'}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

        # Add research context if available
        research_context = ""
        if research_result:
            research_context = f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
INTELLIGENT RESEARCH RESULTS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Research Confidence: {research_result.confidence:.2f}
Methodology: {research_result.methodology}
Sources Analyzed: {len(research_result.sources)}

Key Findings:
{chr(10).join(f'• {finding}' for finding in research_result.key_findings[:3])}

Research Limitations:
{chr(10).join(f'• {limitation}' for limitation in research_result.limitations[:2])}

Related Topics: {', '.join(research_result.related_topics[:3])}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

        system = _BASE_SYSTEM_PROMPT.format(
            time_context=_time_context(),
            memory_block=memory_block,
            facts_block=facts_block,
        ) + understanding_context + research_context

        # 6. Call Groq
        print("🧠  Thinking...", end=" ", flush=True)
        try:
            # Apply speed optimizations
            max_tokens = getattr(cfg, 'MAX_TOKENS', 220)
            temperature = getattr(cfg, 'RESPONSE_TEMPERATURE', 0.75)
            
            response = self._client.chat.completions.create(
                model=self._model,
                messages=[{"role": "system", "content": system}] + history,
                max_tokens=max_tokens,
                temperature=temperature,
            )
            reply = response.choices[0].message.content.strip()

            # Track token usage
            if hasattr(response, 'usage') and response.usage:
                tokens = response.usage.total_tokens or 0
                self._total_tokens += tokens

        except Exception as exc:
            error_str = str(exc).lower()
            if "authentication" in error_str or "api_key" in error_str or "401" in error_str:
                reply = "My API key appears to be invalid or expired. Please update GROQ_API_KEY in your .env file."
            elif "rate_limit" in error_str or "429" in error_str:
                reply = "I'm being rate-limited. Give me a moment and try again."
            else:
                reply = f"I encountered an error in my reasoning core: {exc}"
        print("done.")

        # 7. Handle [FACT:] tags the LLM emits
        fact_match = self.parse_fact(reply)
        if fact_match:
            key, value = fact_match
            self._store.set_fact(key, value)
            print(f"  [FACT] stored: {key} = {value}")
            # Strip the tag from the spoken reply
            reply = re.sub(r"\[FACT:.*?\]", "", reply, flags=re.IGNORECASE).strip()

        # 8. Persist assistant reply
        self._store.save_turn("assistant", reply, session_id)

        return reply

    def answer_with_web_context(self, user_text: str, web_context: str, session_id: str | None = None) -> str:
        """
        Answer a user question using freshly fetched web results.
        """
        system = (
            "You are J.A.R.V.I.S. Answer using the current web results below. "
            "Keep it concise, spoken, and useful. Mention uncertainty if the "
            "results are thin or conflicting. Do not invent sources.\n\n"
            f"Current web results:\n{web_context}"
        )
        try:
            # Apply speed optimizations for web context
            max_tokens = getattr(cfg, 'MAX_TOKENS', 260)
            temperature = getattr(cfg, 'RESPONSE_TEMPERATURE', 0.45)
            
            response = self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user_text},
                ],
                max_tokens=max_tokens,
                temperature=temperature,
            )
            reply = response.choices[0].message.content.strip()
            if hasattr(response, "usage") and response.usage:
                self._total_tokens += response.usage.total_tokens or 0
        except Exception as exc:
            reply = f"I found web results, but my summariser hit an error: {exc}"

        if session_id:
            self._store.save_turn("user", user_text, session_id)
            self._store.save_turn("assistant", reply, session_id)
        return reply

    @property
    def total_tokens(self) -> int:
        """Total tokens used in this session."""
        return self._total_tokens

    # ── Action parsers (static — main.py uses these) ─────────────────────────

    @staticmethod
    def parse_open(reply: str) -> str | None:
        """Extract app name from [OPEN: app_name], or None."""
        m = re.search(r"\[OPEN:\s*(.*?)\]", reply, re.IGNORECASE)
        return m.group(1).strip().lower() if m else None

    @staticmethod
    def parse_remind(reply: str) -> tuple[str, str] | None:
        """Extract (time_str, message) from [REMIND: TIME | message], or None."""
        m = re.search(r"\[REMIND:\s*(.*?)\s*\|\s*(.*?)\]", reply, re.IGNORECASE)
        return (m.group(1).strip(), m.group(2).strip()) if m else None

    @staticmethod
    def parse_fact(reply: str) -> tuple[str, str] | None:
        """Extract (key, value) from [FACT: key | value], or None."""
        m = re.search(r"\[FACT:\s*(.*?)\s*\|\s*(.*?)\]", reply, re.IGNORECASE)
        return (m.group(1).strip().lower(), m.group(2).strip()) if m else None

    @staticmethod
    def parse_search(reply: str) -> str | None:
        """Extract search query from [SEARCH: query], or None."""
        m = re.search(r"\[SEARCH:\s*(.*?)\]", reply, re.IGNORECASE)
        return m.group(1).strip() if m else None

    @staticmethod
    def parse_minimize(reply: str) -> bool:
        """Check if reply contains [MINIMIZE]."""
        return bool(re.search(r"\[MINIMIZE\]", reply, re.IGNORECASE))

    @staticmethod
    def parse_maximize(reply: str) -> bool:
        """Check if reply contains [MAXIMIZE]."""
        return bool(re.search(r"\[MAXIMIZE\]", reply, re.IGNORECASE))

    @staticmethod
    def parse_screenshot(reply: str) -> bool:
        """Check if reply contains [SCREENSHOT]."""
        return bool(re.search(r"\[SCREENSHOT\]", reply, re.IGNORECASE))

    @staticmethod
    def parse_volume(reply: str) -> str | None:
        """Extract volume action from [VOLUME: up/down/mute], or None."""
        m = re.search(r"\[VOLUME:\s*(up|down|mute)\]", reply, re.IGNORECASE)
        return m.group(1).strip().lower() if m else None

    @staticmethod
    def parse_create_project(reply: str) -> tuple[str, str] | None:
        """Extract (project_type, project_name) from [CREATE_PROJECT: type | name], or None."""
        m = re.search(r"\[CREATE_PROJECT:\s*(.*?)\s*\|\s*(.*?)\]", reply, re.IGNORECASE)
        return (m.group(1).strip().lower(), m.group(2).strip()) if m else None

    @staticmethod
    def parse_generate_code(reply: str) -> tuple[str, str] | None:
        """Extract (language, template) from [GENERATE_CODE: language | template], or None."""
        m = re.search(r"\[GENERATE_CODE:\s*(.*?)\s*\|\s*(.*?)\]", reply, re.IGNORECASE)
        return (m.group(1).strip().lower(), m.group(2).strip()) if m else None

    @staticmethod
    def parse_setup_vscode(reply: str) -> str | None:
        """Extract language from [SETUP_VSCODE: language], or None."""
        m = re.search(r"\[SETUP_VSCODE:\s*(.*?)\]", reply, re.IGNORECASE)
        return m.group(1).strip().lower() if m else None

    @staticmethod
    def parse_install_extensions(reply: str) -> str | None:
        """Extract extension list from [INSTALL_EXTENSIONS: list], or None."""
        m = re.search(r"\[INSTALL_EXTENSIONS:\s*(.*?)\]", reply, re.IGNORECASE)
        return m.group(1).strip().lower() if m else None
