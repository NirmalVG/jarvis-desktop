"""
jarvis/memory/store.py
══════════════════════
Persistent memory: SQLite for structured storage + sentence-transformers
for semantic (meaning-based) similarity search over past conversations.

Why this matters:
  Without memory, Jarvis is goldfish-brained — every conversation starts
  from zero. With this store, Jarvis can say "Last time you asked me to
  open VS Code around this hour — doing the same?" That's the Iron Man feel.

Architecture:
  ┌─────────────────────────────────────────────────────────────┐
  │  sessions  ─── one row per "wake event" (session)          │
  │  turns     ─── every user + assistant message               │
  │  memories  ─── user turns + their 384-dim embedding vector  │
  │  facts     ─── key/value store (user name, preferences)     │
  └─────────────────────────────────────────────────────────────┘

Semantic search (how it works):
  1. Every user utterance is encoded into a 384-dimensional vector
     using all-MiniLM-L6-v2 (~80MB, downloads once on first run).
  2. At query time, the input is also encoded.
  3. We compute cosine similarity between query vector and all stored
     vectors — returns the most semantically similar past memories.
  4. Those get injected into the LLM system prompt as <memory> context.

PRD references: F005, F007
"""

import sqlite3
import uuid
from datetime import datetime
from pathlib import Path

import numpy as np

# DB file lives next to the jarvis/ package root
DB_PATH = Path(__file__).parent.parent / "jarvis_memory.db"


class MemoryStore:
    """
    Thread-safe SQLite memory store with semantic retrieval.

    Usage:
        store = MemoryStore()
        session = store.new_session()
        store.save_turn("user", "open youtube", session)
        store.save_turn("assistant", "Opening YouTube.", session)
        results = store.search("open browser", top_k=3)
        # → ["open youtube", "launch chrome please", ...]
    """

    def __init__(self, db_path: str | Path = DB_PATH):
        self._db_path = str(db_path)
        # check_same_thread=False: the main loop + HUD bridge run in
        # different threads but take turns — SQLite handles this safely.
        self._conn = sqlite3.connect(self._db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row   # rows behave like dicts
        self._encoder = None                   # lazy-loaded on first search
        self._init_schema()
        self._init_pragmas()
        try:
            print(f"  \U0001f4be  Memory DB: {self._db_path}")
        except UnicodeEncodeError:
            print(f"  [DB]  Memory DB: {self._db_path}")

    # ── Schema ────────────────────────────────────────────────────────────────

    def _init_schema(self) -> None:
        """Create tables if they don't exist yet (idempotent)."""
        self._conn.executescript("""
            CREATE TABLE IF NOT EXISTS sessions (
                id         TEXT PRIMARY KEY,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS turns (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT    NOT NULL,
                role       TEXT    NOT NULL,          -- "user" | "assistant"
                content    TEXT    NOT NULL,
                created_at TEXT    DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES sessions(id)
            );

            -- Memories are user utterances that have been embedded for
            -- semantic search.  We store the raw float32 bytes as a BLOB.
            CREATE TABLE IF NOT EXISTS memories (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                text       TEXT    NOT NULL,
                embedding  BLOB,                      -- numpy float32 bytes
                created_at TEXT    DEFAULT CURRENT_TIMESTAMP
            );

            -- Key/value facts: e.g. ("user_name", "Nirmal")
            CREATE TABLE IF NOT EXISTS facts (
                key        TEXT PRIMARY KEY,
                value      TEXT NOT NULL,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
        """)
        self._conn.commit()

    def _init_pragmas(self) -> None:
        """
        Enable WAL mode for better concurrent read/write performance.
        WAL (Write-Ahead Logging) allows reads while writes are happening —
        important because the HUD bridge thread reads stats while the main
        loop writes turns.
        """
        try:
            self._conn.execute("PRAGMA journal_mode=WAL")
            self._conn.execute("PRAGMA synchronous=NORMAL")
        except Exception:
            pass  # Older SQLite versions may not support WAL

    # ── Sessions ──────────────────────────────────────────────────────────────

    def new_session(self) -> str:
        """Create a new session and return its UUID."""
        session_id = str(uuid.uuid4())
        self._conn.execute("INSERT INTO sessions(id) VALUES (?)", (session_id,))
        self._conn.commit()
        return session_id

    def get_recent_sessions(self, limit: int = 10) -> list[dict]:
        """Return the most recent sessions with their turn counts."""
        rows = self._conn.execute(
            """
            SELECT s.id, s.created_at,
                   COUNT(t.id) as turn_count
            FROM   sessions s
            LEFT JOIN turns t ON t.session_id = s.id
            GROUP  BY s.id
            ORDER  BY s.created_at DESC
            LIMIT  ?
            """,
            (limit,),
        ).fetchall()
        return [
            {
                "id": r["id"],
                "created_at": r["created_at"],
                "turn_count": r["turn_count"],
            }
            for r in rows
        ]

    # ── Turns (conversation history) ──────────────────────────────────────────

    def save_turn(self, role: str, content: str, session_id: str) -> None:
        """
        Persist one dialogue turn and optionally embed it for future recall.

        role    — "user" or "assistant"
        content — the spoken/generated text
        """
        self._conn.execute(
            "INSERT INTO turns(session_id, role, content) VALUES (?, ?, ?)",
            (session_id, role, content),
        )
        self._conn.commit()

        # Only embed meaningful user utterances for semantic search.
        # Short commands ("yes", "ok") and assistant replies are skipped.
        if role == "user" and len(content.strip()) > 12:
            self._embed_and_store(content)

    def get_session_history(self, session_id: str, limit: int = 20) -> list[dict]:
        """
        Return the last `limit` turns as a list of {role, content} dicts.

        The LLM expects messages in chronological order (oldest first),
        so we fetch DESC then reverse.

        Example output:
            [
              {"role": "user",      "content": "open youtube"},
              {"role": "assistant", "content": "[OPEN: youtube]"},
            ]
        """
        rows = self._conn.execute(
            """
            SELECT role, content
            FROM   turns
            WHERE  session_id = ?
            ORDER  BY id DESC
            LIMIT  ?
            """,
            (session_id, limit),
        ).fetchall()

        # Reverse: DB gave us newest-first, LLM wants oldest-first
        return [{"role": r["role"], "content": r["content"]} for r in reversed(rows)]

    def clear_session_history(self, session_id: str) -> int:
        """
        Delete all turns for a given session.
        Returns the number of turns deleted.
        """
        cursor = self._conn.execute(
            "DELETE FROM turns WHERE session_id = ?",
            (session_id,),
        )
        self._conn.commit()
        return cursor.rowcount

    # ── Semantic memory (embedding + recall) ──────────────────────────────────

    def _get_encoder(self):
        """Lazy-load the sentence-transformer model (first call is slow)."""
        if self._encoder is not None:
            return self._encoder
        try:
            from sentence_transformers import SentenceTransformer
            print("  [MEM] Loading sentence-transformer (first run ~10 s)…")
            self._encoder = SentenceTransformer("all-MiniLM-L6-v2")
            print("  [MEM] Encoder ready.")
        except ImportError:
            print("  [MEM] sentence-transformers not installed — semantic search disabled.")
            print("        Run: pip install sentence-transformers")
        return self._encoder

    def _embed_and_store(self, text: str) -> None:
        """Encode text to a float32 vector and store in memories table."""
        encoder = self._get_encoder()
        blob = None
        if encoder is not None:
            vec  = encoder.encode(text)          # shape: (384,)
            blob = vec.astype(np.float32).tobytes()

        self._conn.execute(
            "INSERT INTO memories(text, embedding) VALUES (?, ?)",
            (text, blob),
        )
        self._conn.commit()

    def search(self, query: str, top_k: int = 3) -> list[str]:
        """
        Return the top_k most semantically similar past memories.

        How cosine similarity works (teach moment):
          Two vectors are "similar" if they point in the same direction
          in 384-dimensional space.  "Open YouTube" and "launch browser"
          will be close even though no words are shared.

        Returns list of text snippets (empty list = nothing relevant found).
        """
        encoder = self._get_encoder()

        # Pull last 300 memories (prevents slow linear scan on huge DBs)
        rows = self._conn.execute(
            "SELECT text, embedding FROM memories ORDER BY id DESC LIMIT 300"
        ).fetchall()

        if not rows:
            return []

        if encoder is None:
            # No model — return recency-ordered fallback
            return [r["text"] for r in rows[:top_k]]

        query_vec = encoder.encode(query).astype(np.float32)
        q_norm    = np.linalg.norm(query_vec) + 1e-10

        scored = []
        for row in rows:
            if row["embedding"] is None:
                continue
            mem_vec = np.frombuffer(row["embedding"], dtype=np.float32)
            m_norm  = np.linalg.norm(mem_vec) + 1e-10
            # Cosine similarity ∈ [-1, 1]
            sim = float(np.dot(query_vec, mem_vec) / (q_norm * m_norm))
            scored.append((sim, row["text"]))

        scored.sort(reverse=True, key=lambda x: x[0])

        # Only return genuinely similar results (threshold 0.35)
        return [text for sim, text in scored[:top_k] if sim >= 0.35]

    # ── Facts (long-term key/value knowledge) ─────────────────────────────────

    def set_fact(self, key: str, value: str) -> None:
        """Store or update a user fact (e.g. name, preferred editor)."""
        self._conn.execute(
            """
            INSERT INTO facts(key, value)
            VALUES (?, ?)
            ON CONFLICT(key) DO UPDATE
              SET value = excluded.value,
                  updated_at = CURRENT_TIMESTAMP
            """,
            (key, value),
        )
        self._conn.commit()

    def get_all_facts(self) -> dict[str, str]:
        """Return all stored facts as a flat dict."""
        rows = self._conn.execute("SELECT key, value FROM facts").fetchall()
        return {r["key"]: r["value"] for r in rows}

    def delete_fact(self, key: str) -> bool:
        """Delete a stored fact. Returns True if the fact existed."""
        cursor = self._conn.execute("DELETE FROM facts WHERE key = ?", (key,))
        self._conn.commit()
        return cursor.rowcount > 0

    # ── Stats ─────────────────────────────────────────────────────────────────

    def stats(self) -> dict:
        """Return summary stats shown in the HUD system panel."""
        sessions    = self._conn.execute("SELECT COUNT(*) FROM sessions").fetchone()[0]
        total_turns = self._conn.execute("SELECT COUNT(*) FROM turns").fetchone()[0]
        memories    = self._conn.execute("SELECT COUNT(*) FROM memories").fetchone()[0]
        facts_count = self._conn.execute("SELECT COUNT(*) FROM facts").fetchone()[0]
        return {
            "sessions":    sessions,
            "total_turns": total_turns,
            "memories":    memories,
            "facts":       facts_count,
        }

    # ── Cleanup ───────────────────────────────────────────────────────────────

    def close(self) -> None:
        """Close the DB connection gracefully."""
        self._conn.close()