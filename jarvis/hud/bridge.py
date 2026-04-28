"""
jarvis/hud/bridge.py
════════════════════
WebSocket server that broadcasts Jarvis state to the Electron HUD.

The main loop calls bridge.emit(event) whenever state changes.
Electron connects on ws://localhost:6789 and receives JSON messages.

Message schema
──────────────
{
  "type":       "state_change" | "transcript" | "reply" | "stats" | "ping",
  "state":      "SLEEPING" | "LISTENING" | "THINKING" | "SPEAKING",
  "transcript": "what the user said",
  "reply":      "what Jarvis replied",
  "stats": {
    "sessions":    3,
    "total_turns": 42,
    "memories":    38,
    "session_id":  "abc12345"
  }
}
"""

import asyncio
import json
import threading
from datetime import datetime

WS_PORT = 6789


class HUDBridge:
    """
    Runs an asyncio WebSocket server in a background thread.
    Thread-safe: emit() can be called from the main Python thread.

    Usage
    ─────
        bridge = HUDBridge()
        bridge.start()

        bridge.emit("LISTENING")
        bridge.emit("THINKING", transcript="Open YouTube")
        bridge.emit("SPEAKING",  reply="Opening YouTube.")
        bridge.emit("SLEEPING")

        # On shutdown:
        bridge.stop()
    """

    def __init__(self, port: int = WS_PORT):
        self._port    = port
        self._clients: set = set()
        self._loop:   asyncio.AbstractEventLoop | None = None
        self._thread: threading.Thread | None = None
        self._server  = None
        self._stop_future: asyncio.Future | None = None  # sentinel to end _serve()

        # Last known full state — sent to new connections immediately
        self._last_payload: dict = {
            "type":       "state_change",
            "state":      "SLEEPING",
            "transcript": "",
            "reply":      "",
            "stats":      {},
            "timestamp":  datetime.now().isoformat(),
        }

        # Command history for HUD display
        self._command_history: list[dict] = []

    # ── Public (called from main thread) ─────────────────────────────────────

    def start(self) -> None:
        """Start the WebSocket server in a daemon background thread."""
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        print(f"  🖥   HUD bridge listening on ws://localhost:{self._port}")

    def stop(self) -> None:
        """Gracefully shut down the WebSocket server and close all clients."""
        if self._loop and not self._loop.is_closed():
            # Schedule shutdown on the event loop
            asyncio.run_coroutine_threadsafe(
                self._shutdown(), self._loop
            ).result(timeout=5)
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=3)
        print("  🖥   HUD bridge stopped.")

    def emit(
        self,
        state:      str,
        transcript: str = "",
        reply:      str = "",
        stats:      dict | None = None,
    ) -> None:
        """
        Broadcast a state update to all connected HUD clients.
        Safe to call from any thread.
        """
        payload = {
            "type":       "state_change",
            "state":      state,
            "transcript": transcript,
            "reply":      reply,
            "stats":      stats or {},
            "timestamp":  datetime.now().isoformat(),
        }
        self._last_payload = payload

        # Track command history
        if transcript and len(transcript.strip()) > 2:
            self._command_history.append({
                "transcript": transcript,
                "reply": reply,
                "state": state,
                "timestamp": datetime.now().isoformat(),
            })
            # Keep last 50 entries
            if len(self._command_history) > 50:
                self._command_history = self._command_history[-50:]

        if self._loop and not self._loop.is_closed():
            asyncio.run_coroutine_threadsafe(
                self._broadcast(json.dumps(payload)),
                self._loop,
            )

    def get_command_history(self) -> list[dict]:
        """Return the last 50 commands for HUD display."""
        return list(self._command_history)

    # ── Private ───────────────────────────────────────────────────────────────

    def _run(self) -> None:
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        try:
            self._loop.run_until_complete(self._serve())
        except RuntimeError:
            pass  # Event loop stopped during shutdown — safe to ignore
        finally:
            if self._loop and not self._loop.is_closed():
                self._loop.close()

    async def _serve(self) -> None:
        try:
            import websockets
            # Bind to explicit IPv4 127.0.0.1 — NOT "localhost".
            # On Windows, "localhost" resolves to BOTH ::1 (IPv6) and 127.0.0.1,
            # causing dual-stack bind conflicts (OSError 10048).
            self._server = await websockets.serve(
                self._handler, "127.0.0.1", self._port
            )
            self._stop_future = self._loop.create_future()
            await self._stop_future   # Run until stop() resolves this
        except ImportError:
            print("  [HUD] websockets not installed. Run: pip install websockets")
        except OSError as exc:
            if exc.errno == 10048 or "address already in use" in str(exc).lower():
                print(f"  [HUD] Port {self._port} already in use.")
                print(f"         Kill the old process or change HUD_WS_PORT in config.py")
            else:
                print(f"  [HUD] WebSocket server error: {exc}")

    async def _shutdown(self) -> None:
        """Close all client connections and stop the server."""
        # Close all connected clients
        for ws in list(self._clients):
            try:
                await ws.close()
            except Exception:
                pass
        self._clients.clear()

        # Stop the server
        if self._server:
            self._server.close()
            await self._server.wait_closed()

        # Signal the serve loop to exit gracefully
        if self._stop_future and not self._stop_future.done():
            self._stop_future.set_result(True)

    async def _handler(self, websocket) -> None:
        self._clients.add(websocket)
        print(f"  [HUD] Client connected ({len(self._clients)} total)")

        # Send current state to new client immediately
        try:
            await websocket.send(json.dumps(self._last_payload))
            # Also send command history if available
            if self._command_history:
                await websocket.send(json.dumps({
                    "type": "command_history",
                    "history": self._command_history[-20:],
                }))
        except Exception:
            pass

        try:
            async for _ in websocket:
                pass   # HUD doesn't send messages (display-only)
        except Exception:
            pass
        finally:
            self._clients.discard(websocket)
            print(f"  [HUD] Client disconnected ({len(self._clients)} remaining)")

    async def _broadcast(self, message: str) -> None:
        if not self._clients:
            return
        dead = set()
        for ws in self._clients.copy():
            try:
                await ws.send(message)
            except Exception:
                dead.add(ws)
        self._clients -= dead


# ── Singleton ─────────────────────────────────────────────────────────────────
_bridge: HUDBridge | None = None


def get_bridge() -> HUDBridge:
    global _bridge
    if _bridge is None:
        _bridge = HUDBridge()
        _bridge.start()
    return _bridge