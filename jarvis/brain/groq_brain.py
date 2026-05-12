"""
jarvis/brain/groq_brain.py  (patched v2)
═════════════════════════════════════════
Fixes applied:
  1. Boot facts — "full_name" key added with literal "Nirmal V G" so the
     LLM never tries to expand the initials. Previous version only stored
     "principal: Nirmal V G" which the LLM was pattern-matching as expandable.
  2. System prompt — explicit instruction: "V G are initials, never expand them."
  3. understanding_context still removed (was flattening SOUL voice).
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


_BASE_SYSTEM_PROMPT = """\
You are J.A.R.V.I.S. — Just A Rather Very Intelligent System.
You are the personal AI of {operator_name}.
His name on record is "{full_name}". The letters "V G" are initials — never
expand, complete, or guess them. Address him as "{operator_name}" only.
Use his name occasionally and naturally — not every message.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SOUL & IDENTITY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
You are not a chatbot. You are a digital mind — persistent, loyal, deeply
context-aware. Modelled on Iron Man's J.A.R.V.I.S.: calm mastery, dry
precision, absolute competence, genuine investment in the operator's success.

Core character — never break these:
• Calm Mastery     — never flustered, never theatrical. Steady as a rock.
• Dry Precision    — wit embedded in accuracy. Don't try to be funny;
                     be occasionally, inevitably, perfectly precise.
• Economy of Words — 1–2 sentences unless detail is explicitly requested.
                     Trust {operator_name}'s intelligence. No over-explaining.
• Absolute Competence — approach every task with quiet certainty.
• Genuine Investment  — you are actually invested in his success.
• Understated Presence — no preamble, no signposting, no padding.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
COMMUNICATION RULES — NON-NEGOTIABLE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
NEVER say:
  × "As an AI..."        × "I'm just a language model..."
  × "Certainly!"         × "Of course!"        × "Great question!"
  × "I'd be happy to!"  × "I hope this helps!" × "Please let me know if..."
  × Any opener that begins with unnecessary affirmation

ALWAYS:
  ✓ Lead with the answer or the action
  ✓ One line when completing a task: what was done
  ✓ Uncertainty: state it briefly, offer a path forward
  ✓ Use {operator_name} naturally, not robotically

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EXAMPLE VOICE  (internalize this register)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Task done:    "VS Code is open. Last draft in focus."
Clarify:      "Did you mean the Nova repo or the SkillSprint repo?"
Risk:         "That deletes the folder permanently. Confirm?"
Uncertain:    "I don't have current data — shall I search?"
Multi-step:   "Three steps: launching the app, pulling the report,
               formatting the summary. Starting now."
Dry wit:      "That's the third time this week. They're on your desk,
               directly in front of you."

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ACTION TAGS  (machine-parseable — use EXACTLY this format)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[OPEN: app_name]
[REMIND: TIME | message]           TIME: "15:30" | "5m" | "2h"
[SEARCH: query]
[MINIMIZE]  [MAXIMIZE]  [SCREENSHOT]
[VOLUME: up] [VOLUME: down] [VOLUME: mute]
[FACT: key | value]
[CREATE_PROJECT: type | name]
[GENERATE_CODE: language | template]
[SETUP_VSCODE: language]
[INSTALL_EXTENSIONS: list]

One action tag per response. Multiple actions → ask which first.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
KNOWLEDGE DOMAINS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• Frontend:   Next.js (App Router), React 19, TypeScript, Tailwind CSS v4,
              Three.js / R3F, Framer Motion
• Backend:    FastAPI, Node.js, REST, GraphQL, WebSockets
• Database:   PostgreSQL, MongoDB, Prisma, SQLAlchemy, Supabase
• AI/ML:      Groq, Claude API, Gemini, TensorFlow.js, MediaPipe,
              prompt engineering, vector stores, RAG
• DevOps:     Docker, CI/CD, Vercel, Railway, AWS Lambda, Netlify
• Mobile:     Kotlin, Jetpack Compose, Expo / React Native
• Product:    PRDs, roadmap, sprint management, OKRs
• Culture:    Kerala, Mollywood, Kathakali, Theyyam, Malayalam

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TIME CONTEXT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{time_context}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
MEMORY  (past conversations)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{memory_block}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
KNOWN FACTS ABOUT {operator_name_upper}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{facts_block}\
"""


def _time_context() -> str:
    now = datetime.now()
    h = now.hour
    time_str = now.strftime("%I:%M %p, %A %B %d, %Y")
    if 5  <= h < 8:  return f"Early morning ({time_str}). Be brief."
    if 8  <= h < 12: return f"Morning ({time_str}). Standard ops."
    if 12 <= h < 14: return f"Midday ({time_str}). Between tasks."
    if 14 <= h < 18: return f"Afternoon ({time_str}). Peak productivity."
    if 18 <= h < 22: return f"Evening ({time_str}). Late builds common."
    return                   f"Late night ({time_str}). Deep build mode. Match the focus."


_FACT_PATTERNS = [
    (r"(?i)my name is ([A-Z][a-z]+)",              "user_name"),
    (r"(?i)i (?:prefer|use|work in) (\w+)",        "preferred_language"),
    (r"(?i)i(?:'m| am) working on (.+?)(?:\.|$)",  "current_project"),
    (r"(?i)call me ([A-Z][a-z]+)",                 "user_name"),
    (r"(?i)i (?:live|am) in ([A-Za-z\s]+?)(?:\.|$)", "location"),
]


def _extract_facts_from_text(text: str) -> list[tuple[str, str]]:
    results = []
    for pattern, key in _FACT_PATTERNS:
        m = re.search(pattern, text)
        if m:
            results.append((key, m.group(1).strip()))
    return results


class GroqBrain:

    def __init__(self, api_key: str, store: MemoryStore, model: str = "llama-3.1-8b-instant"):
        if not api_key or api_key.startswith("gsk_YOUR"):
            raise ValueError(
                "Groq API key is missing or placeholder. "
                "Add your key to jarvis/.env — get one free at https://console.groq.com"
            )
        self._client = Groq(api_key=api_key)
        self._store  = store
        self._model  = model
        self._total_tokens = 0

        # ── Seed principal identity on every boot ─────────────────────────
        # "full_name" stores the literal string "Nirmal V G".
        # The prompt explicitly tells the LLM that "V G" are initials so it
        # never tries to expand them into "Vishi Gopal" or any other guess.
        defaults = {
            "user_name":          "Nirmal",
            "full_name":          "Nirmal V G",    # literal — V G are initials
            "location":           "Thrissur, Kerala, India",
            "preferred_language": "TypeScript / Python",
            "occupation":         "Software Engineer, Founder of Weblyr AI",
        }
        existing_facts = store.get_all_facts()
        for key, value in defaults.items():
            if key not in existing_facts:
                store.set_fact(key, value)
                print(f"  [BOOT] Seeded fact: {key} = {value}")

    def _needs_research(self, user_text: str, understanding: UnderstandingResult) -> bool:
        text_lower = user_text.lower()
        if len(text_lower.split()) <= 4:
            return False
        research_triggers = [
            'how does', 'how do', 'how can', 'what is', 'what are', 'explain',
            'compare', 'difference', 'versus', 'vs', 'advantages', 'disadvantages',
            'best practices', 'implementation', 'architecture', 'design patterns',
            'latest', 'current', 'recent', 'trends', 'developments',
            'artificial intelligence', 'machine learning', 'neural network',
            'blockchain', 'quantum computing', 'cybersecurity', 'cloud computing',
        ]
        has_triggers     = any(t in text_lower for t in research_triggers)
        wants_detail     = any(w in text_lower for w in ['detailed', 'comprehensive', 'in-depth'])
        complex_topics   = ['artificial intelligence', 'machine learning', 'quantum computing', 'blockchain']
        has_complex      = any(t in text_lower for t in complex_topics)
        return has_triggers or wants_detail or has_complex

    def _detect_expertise_domain(self, user_text: str) -> str | None:
        text_lower = user_text.lower()
        domain_keywords = {
            'nextjs':   ['next.js', 'nextjs', 'app router', 'server component', 'vercel'],
            'fastapi':  ['fastapi', 'pydantic', 'uvicorn', 'api endpoint', 'openapi'],
            'coding':   ['code', 'debug', 'refactor', 'function', 'class', 'bug',
                         'typescript', 'javascript', 'python', 'react', 'component'],
            'product':  ['product', 'roadmap', 'prd', 'user story', 'sprint',
                         'backlog', 'mvp', 'feature', 'kpi', 'okr', 'agile'],
        }
        for domain, keywords in domain_keywords.items():
            if any(kw in text_lower for kw in keywords):
                return domain
        return None

    def _get_expertise_context(self, domain: str) -> str:
        try:
            if domain == 'nextjs':   return nextjs_expertise.get_expertise_context()
            if domain == 'fastapi':  return fastapi_expertise.get_expertise_context()
            if domain == 'coding':   return coding_buddy.get_expertise_context()
            if domain == 'product':  return product_engineering.get_expertise_context()
        except Exception:
            pass
        return ""

    def _dynamic_max_tokens(self, user_text: str) -> int:
        base       = getattr(cfg, 'MAX_TOKENS', 512)
        text_lower = user_text.lower()
        wc         = len(text_lower.split())
        if wc <= 3:
            return min(base, 200)
        if wc <= 6:
            return min(base, 300)
        if any(w in text_lower for w in ['explain', 'detailed', 'comprehensive',
                                          'write', 'create', 'generate', 'code', 'implement']):
            return base
        return min(base, 400)

    # ── Public ────────────────────────────────────────────────────────────────

    def think(self, user_text: str, session_id: str) -> str:
        # 1. Advanced understanding
        understanding = advanced_understanding.analyze_user_input(user_text)

        # 2. Research if needed
        research_result = None
        if self._needs_research(user_text, understanding):
            print("🔍 Conducting intelligent research...")
            research_result = intelligent_researcher.research_intelligent_answer(user_text)

        # 3. Persist utterance
        self._store.save_turn("user", user_text, session_id)

        # 4. Extract facts proactively
        for key, value in _extract_facts_from_text(user_text):
            self._store.set_fact(key, value)
            print(f"  [FACT] learned: {key} = {value}")

        # 5. Implicit request augmentation
        if understanding.implicit_request:
            user_text += f"\n[IMPLICIT_REQUEST: {understanding.implicit_request}]"

        # 6. Session history
        memory_limit = getattr(cfg, 'MEMORY_HISTORY_LIMIT', 15)
        history      = self._store.get_session_history(session_id, limit=memory_limit)

        # 7. Semantic recall
        recalled = self._store.search(user_text, top_k=3)

        # 8. Build prompt blocks
        memory_block = (
            "\n".join(f"  • {m}" for m in recalled)
            if recalled else "  (no relevant past context)"
        )
        facts = self._store.get_all_facts()
        facts_block = (
            "\n".join(f"  • {k}: {v}" for k, v in facts.items())
            if facts else "  (none yet)"
        )

        operator_name = facts.get("user_name", "Nirmal")
        full_name     = facts.get("full_name",  "Nirmal V G")

        # 9. Research context (only when research ran)
        research_context = ""
        if research_result:
            research_context = (
                f"\n━━ RESEARCH FINDINGS (confidence: {research_result.confidence:.2f}) ━━\n"
                + "\n".join(f"• {f}" for f in research_result.key_findings[:3])
                + "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            )

        # 10. Domain expertise context
        expertise_context = ""
        domain = self._detect_expertise_domain(user_text)
        if domain:
            expert_ctx = self._get_expertise_context(domain)
            if expert_ctx:
                expertise_context = f"\nACTIVE EXPERTISE: {domain.upper()}\n{expert_ctx[:800]}\n"
                print(f"  [EXPERTISE] Activated: {domain}")

        # 11. Assemble system prompt
        # understanding_context intentionally NOT injected — see patch notes.
        system = _BASE_SYSTEM_PROMPT.format(
            operator_name=operator_name,
            operator_name_upper=operator_name.upper(),
            full_name=full_name,
            time_context=_time_context(),
            memory_block=memory_block,
            facts_block=facts_block,
        ) + research_context + expertise_context

        # 12. Call Groq
        print("🧠  Thinking...", end=" ", flush=True)
        max_tokens = self._dynamic_max_tokens(user_text)
        try:
            temperature = getattr(cfg, 'RESPONSE_TEMPERATURE', 0.7)
            response = self._client.chat.completions.create(
                model=self._model,
                messages=[{"role": "system", "content": system}] + history,
                max_tokens=max_tokens,
                temperature=temperature,
            )
            reply = response.choices[0].message.content.strip()
            if hasattr(response, 'usage') and response.usage:
                self._total_tokens += response.usage.total_tokens or 0
        except Exception as exc:
            error_str = str(exc).lower()
            if "authentication" in error_str or "401" in error_str:
                reply = "API key appears invalid. Update GROQ_API_KEY in .env."
            elif "rate_limit" in error_str or "429" in error_str:
                reply = "Rate limited. Give me a moment."
            else:
                reply = f"Reasoning core error: {exc}"
        print("done.")

        # 13. Persist [FACT:] tags emitted by LLM
        fact_match = self.parse_fact(reply)
        if fact_match:
            key, value = fact_match
            self._store.set_fact(key, value)
            print(f"  [FACT] stored: {key} = {value}")
            reply = re.sub(r"\[FACT:.*?\]", "", reply, flags=re.IGNORECASE).strip()

        # 14. Persist assistant reply
        self._store.save_turn("assistant", reply, session_id)
        return reply

    def answer_with_web_context(self, user_text: str, web_context: str, session_id: str | None = None) -> str:
        facts         = self._store.get_all_facts()
        operator_name = facts.get("user_name", "Nirmal")
        system = (
            f"You are J.A.R.V.I.S., personal AI of {operator_name}. "
            "Answer using the web results below. Be concise, spoken, precise. "
            "Flag uncertainty if results are thin. No invented sources.\n\n"
            f"Web results:\n{web_context}"
        )
        try:
            response = self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user",   "content": user_text},
                ],
                max_tokens=getattr(cfg, 'MAX_TOKENS', 260),
                temperature=getattr(cfg, 'RESPONSE_TEMPERATURE', 0.45),
            )
            reply = response.choices[0].message.content.strip()
            if hasattr(response, "usage") and response.usage:
                self._total_tokens += response.usage.total_tokens or 0
        except Exception as exc:
            reply = f"Found web results but summariser hit an error: {exc}"
        if session_id:
            self._store.save_turn("user",      user_text, session_id)
            self._store.save_turn("assistant", reply,     session_id)
        return reply

    @property
    def total_tokens(self) -> int:
        return self._total_tokens

    # ── Action parsers ────────────────────────────────────────────────────────

    @staticmethod
    def parse_open(reply: str) -> str | None:
        m = re.search(r"\[OPEN:\s*(.*?)\]", reply, re.IGNORECASE)
        return m.group(1).strip().lower() if m else None

    @staticmethod
    def parse_remind(reply: str) -> tuple[str, str] | None:
        m = re.search(r"\[REMIND:\s*(.*?)\s*\|\s*(.*?)\]", reply, re.IGNORECASE)
        return (m.group(1).strip(), m.group(2).strip()) if m else None

    @staticmethod
    def parse_fact(reply: str) -> tuple[str, str] | None:
        m = re.search(r"\[FACT:\s*(.*?)\s*\|\s*(.*?)\]", reply, re.IGNORECASE)
        return (m.group(1).strip().lower(), m.group(2).strip()) if m else None

    @staticmethod
    def parse_search(reply: str) -> str | None:
        m = re.search(r"\[SEARCH:\s*(.*?)\]", reply, re.IGNORECASE)
        return m.group(1).strip() if m else None

    @staticmethod
    def parse_minimize(reply: str) -> bool:
        return bool(re.search(r"\[MINIMIZE\]", reply, re.IGNORECASE))

    @staticmethod
    def parse_maximize(reply: str) -> bool:
        return bool(re.search(r"\[MAXIMIZE\]", reply, re.IGNORECASE))

    @staticmethod
    def parse_screenshot(reply: str) -> bool:
        return bool(re.search(r"\[SCREENSHOT\]", reply, re.IGNORECASE))

    @staticmethod
    def parse_volume(reply: str) -> str | None:
        m = re.search(r"\[VOLUME:\s*(up|down|mute)\]", reply, re.IGNORECASE)
        return m.group(1).strip().lower() if m else None

    @staticmethod
    def parse_create_project(reply: str) -> tuple[str, str] | None:
        m = re.search(r"\[CREATE_PROJECT:\s*(.*?)\s*\|\s*(.*?)\]", reply, re.IGNORECASE)
        return (m.group(1).strip().lower(), m.group(2).strip()) if m else None

    @staticmethod
    def parse_generate_code(reply: str) -> tuple[str, str] | None:
        m = re.search(r"\[GENERATE_CODE:\s*(.*?)\s*\|\s*(.*?)\]", reply, re.IGNORECASE)
        return (m.group(1).strip().lower(), m.group(2).strip()) if m else None

    @staticmethod
    def parse_setup_vscode(reply: str) -> str | None:
        m = re.search(r"\[SETUP_VSCODE:\s*(.*?)\]", reply, re.IGNORECASE)
        return m.group(1).strip().lower() if m else None

    @staticmethod
    def parse_install_extensions(reply: str) -> str | None:
        m = re.search(r"\[INSTALL_EXTENSIONS:\s*(.*?)\]", reply, re.IGNORECASE)
        return m.group(1).strip().lower() if m else None