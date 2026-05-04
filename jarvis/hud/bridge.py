"""
jarvis/hud/bridge.py
════════════════════
WebSocket server that broadcasts Jarvis state to the Electron HUD.
Now supports BIDIRECTIONAL communication — HUD can send commands back.

The main loop calls bridge.emit(event) whenever state changes.
Electron connects on ws://localhost:6789 and receives JSON messages.

Message schema (Server → Client)
──────────────
{
  "type":       "state_change" | "transcript" | "reply" | "stats" | "system_info",
  "state":      "SLEEPING" | "LISTENING" | "THINKING" | "SPEAKING",
  "transcript": "what the user said",
  "reply":      "what Jarvis replied",
  "stats":      { ... },
  "system_info": { "cpu_percent": 12, "memory_percent": 45, ... }
}

Message schema (Client → Server)
──────────────
{
  "type":    "command",
  "text":    "open youtube"
}
"""

import asyncio
import json
import threading
import queue
from datetime import datetime

WS_PORT = 6789


class HUDBridge:
    """
    Runs an asyncio WebSocket server in a background thread.
    Thread-safe: emit() can be called from the main Python thread.

    Now supports:
      • Bidirectional messaging — clients can send commands
      • Command queue — main.py polls for HUD-originated commands
      • System info broadcasting — periodic CPU/mem/uptime

    Usage
    ─────
        bridge = HUDBridge()
        bridge.start()

        bridge.emit("LISTENING")
        bridge.emit("THINKING", transcript="Open YouTube")
        bridge.emit("SPEAKING",  reply="Opening YouTube.")
        bridge.emit("SLEEPING")

        # Poll for HUD commands (non-blocking):
        cmd = bridge.get_pending_command()
        if cmd:
            handle_command(cmd, ...)

        # On shutdown:
        bridge.stop()
    """

    def __init__(self, port: int = WS_PORT):
        self._port    = port
        self._clients: set = set()
        self._loop:   asyncio.AbstractEventLoop | None = None
        self._thread: threading.Thread | None = None
        self._server  = None
        self._stop_future: asyncio.Future | None = None

        # Command queue: HUD → Python backend
        self._command_queue: queue.Queue = queue.Queue()

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

        # System info broadcasting
        self._system_info_task: asyncio.Task | None = None

    # ── Public (called from main thread) ─────────────────────────────────────

    def start(self) -> None:
        """Start the WebSocket server in a daemon background thread."""
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        print(f"  🖥   HUD bridge listening on ws://localhost:{self._port}")

    def stop(self) -> None:
        """Gracefully shut down the WebSocket server and close all clients."""
        if self._loop and not self._loop.is_closed():
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
    
    def has_clients(self) -> bool:
        """Check if any HUD clients are currently connected."""
        return len(self._clients) > 0

    def get_pending_command(self) -> str | None:
        """
        Non-blocking poll for commands sent from HUD.
        Returns the command text, or None if queue is empty.
        Called by main.py between listen cycles.
        """
        try:
            return self._command_queue.get_nowait()
        except queue.Empty:
            return None

    def emit_system_info(self, info: dict) -> None:
        """Broadcast system diagnostics to all HUD clients."""
        payload = {
            "type": "system_info",
            **info,
            "timestamp": datetime.now().isoformat(),
        }
        if self._loop and not self._loop.is_closed():
            asyncio.run_coroutine_threadsafe(
                self._broadcast(json.dumps(payload)),
                self._loop,
            )

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
            self._server = await websockets.serve(
                self._handler, "127.0.0.1", self._port
            )
            # Start periodic system info broadcast
            self._system_info_task = asyncio.ensure_future(self._broadcast_system_info_loop())
            self._stop_future = self._loop.create_future()
            await self._stop_future
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
        # Cancel system info task
        if self._system_info_task and not self._system_info_task.done():
            self._system_info_task.cancel()

        for ws in list(self._clients):
            try:
                await ws.close()
            except Exception:
                pass
        self._clients.clear()

        if self._server:
            self._server.close()
            await self._server.wait_closed()

        if self._stop_future and not self._stop_future.done():
            self._stop_future.set_result(True)

    async def _handler(self, websocket) -> None:
        self._clients.add(websocket)
        print(f"  [HUD] Client connected ({len(self._clients)} total)")

        # Send current state to new client immediately
        try:
            await websocket.send(json.dumps(self._last_payload))
            if self._command_history:
                await websocket.send(json.dumps({
                    "type": "command_history",
                    "history": self._command_history[-20:],
                }))
        except Exception:
            pass

        try:
            # BIDIRECTIONAL: listen for incoming messages from HUD
            async for raw_msg in websocket:
                try:
                    msg = json.loads(raw_msg)
                    if msg.get("type") == "command" and msg.get("text"):
                        cmd_text = msg["text"].strip()
                        if len(cmd_text) > 1:
                            self._command_queue.put(cmd_text)
                            print(f"  [HUD] Command received: {cmd_text}")
                except (json.JSONDecodeError, KeyError):
                    pass
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

    async def _broadcast_system_info_loop(self) -> None:
        """Periodically broadcast system info to HUD clients (every 5 seconds)."""
        while True:
            try:
                await asyncio.sleep(5)
                if not self._clients:
                    continue
                try:
                    from services.diagnostics import get_system_info
                    info = get_system_info()
                    payload = json.dumps({
                        "type": "system_info",
                        **info,
                        "timestamp": datetime.now().isoformat(),
                    })
                    await self._broadcast(payload)
                except ImportError:
                    pass  # diagnostics module not available
                except Exception:
                    pass
            except asyncio.CancelledError:
                break
            except Exception:
                await asyncio.sleep(10)


# ── Singleton ─────────────────────────────────────────────────────────────────
_bridge: HUDBridge | None = None


def get_bridge() -> HUDBridge:
    global _bridge
    if _bridge is None:
        _bridge = HUDBridge()
        _bridge.start()
    return _bridge