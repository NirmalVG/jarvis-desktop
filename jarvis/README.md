# Jarvis Desktop

> Offline-first AI desktop assistant. Clap to wake. Speak to act. HUD overlay.

## Project Structure

```
jarvis-desktop/
├── launcher.bat               ← One-click: starts backend + HUD
│
├── jarvis/                    ← Python backend
│   ├── config.py              ← All settings (edit this)
│   ├── main.py                ← Entry point + state machine + HUD bridge
│   ├── .env.example           ← API key template
│   │
│   ├── wake/
│   │   ├── clap_detector.py   ← ML double-clap wake (offline, no API key)
│   │   └── keyword_detector.py← openwakeword "Hey Mycroft" wake
│   │
│   ├── memory/
│   │   └── store.py           ← SQLite + sentence embeddings for recall
│   │
│   ├── voice/
│   │   ├── stt.py             ← WebRTC VAD recording + Whisper transcription
│   │   └── tts.py             ← Edge Neural TTS (online) + pyttsx3 fallback
│   │
│   ├── brain/
│   │   └── groq_brain.py      ← Groq LLM with memory-augmented prompting
│   │
│   ├── actuation/
│   │   └── actions.py         ← Cross-platform app launch, reminders, window control
│   │
│   ├── hud/
│   │   └── bridge.py          ← WebSocket server → pushes state to Electron HUD
│   │
│   └── vision/                ← M3 scaffold
│       └── camera.py          ← Webcam, YOLO, BLIP, QR scanning stubs
│
└── jarvis-hud/                ← Electron + React HUD overlay
    ├── electron/
    │   ├── main.js            ← Electron main process (transparent, always-on-top)
    │   └── preload.js         ← Secure IPC bridge
    └── src/
        ├── App.jsx            ← 3-column cockpit layout
        ├── hooks/
        │   └── useJarvisState.js  ← WebSocket / IPC state subscription
        └── components/
            ├── StateOrb3D.jsx ← 3D breathing orb (React Three Fiber)
            ├── OrbCanvas.jsx  ← 2D canvas fallback orb
            ├── OrbZone.jsx    ← Orb container with corner brackets
            ├── HexGrid.jsx    ← Background hex pattern
            ├── TitleBar.jsx   ← Top bar with clock, mode, controls
            ├── TranscriptFeed.jsx ← Scrolling dialogue log
            ├── SystemPanel.jsx    ← Memory stats, bridge status
            └── Statebar.jsx       ← Dev-mode state switcher
```

## Quick Start

### 1. Install Python dependencies

```bash
cd jarvis
pip install -r requirements.txt
```

### 2. Install HUD dependencies

```bash
cd jarvis-hud
npm install
```

### 3. Configure

Edit `jarvis/config.py` — add your Groq API key (free at [console.groq.com](https://console.groq.com)).
Or copy `.env.example` to `.env` and set `GROQ_API_KEY` there.

### 4. Launch

**Windows (one-click):**
```bash
launcher.bat
```

**Manual (any OS):**
```bash
# Terminal 1: Python backend
cd jarvis && python main.py

# Terminal 2: HUD
cd jarvis-hud && npm run dev
```

## Wake Modes

| Mode      | How to trigger   | Requires              |
| --------- | ---------------- | --------------------- |
| `clap`    | Double clap      | Nothing (offline)     |
| `keyword` | Say "Hey Mycroft"| openwakeword (offline) |

## Commands

| Say                                    | What Jarvis does             |
| -------------------------------------- | ---------------------------- |
| "Open YouTube"                         | Opens youtube.com in browser |
| "Open VS Code"                         | Launches VS Code             |
| "Remind me in 10 minutes to call Maya" | Speaks reminder after 10m    |
| "What did I ask you earlier?"          | Semantic memory search       |
| "Shut down" / "Goodbye"                | Graceful exit                |
| Anything else                          | Groq LLM response            |

## Architecture

```
  ┌─────────────────────────────────────────────────────────┐
  │              ELECTRON HUD (React + Three.js)            │
  │  ┌───────────┐  ┌───────────┐  ┌────────────────────┐  │
  │  │ Transcript │  │  3D Orb   │  │ System / Subsystem │  │
  │  │   Feed     │  │  State    │  │   Panels           │  │
  │  └───────────┘  └───────────┘  └────────────────────┘  │
  └──────────────────────┬──────────────────────────────────┘
                         │ WebSocket (ws://localhost:6789)
  ┌──────────────────────┴──────────────────────────────────┐
  │               PYTHON BACKEND                            │
  │                                                         │
  │  SLEEPING → wake gesture → LISTENING                    │
  │  LISTENING → VAD silence → THINKING                     │
  │  THINKING → Groq reply → ACTING / SPEAKING              │
  │  SPEAKING → done → SLEEPING (loop)                      │
  │                                                         │
  │  ┌─────┐  ┌─────┐  ┌──────┐  ┌────────┐  ┌──────────┐ │
  │  │Wake │  │ STT │  │Brain │  │Actuator│  │  Memory  │ │
  │  │Clap │  │Whisp│  │ Groq │  │OS Acts │  │  SQLite  │ │
  │  └─────┘  └─────┘  └──────┘  └────────┘  └──────────┘ │
  └─────────────────────────────────────────────────────────┘
```

Memory persists at `~/.jarvis/memory.db` — conversation history, semantic
embeddings, and user facts survive across restarts.

## HUD Features

- **3D Animated Orb** — breathing, distorting sphere that changes color per state
- **State Transitions** — STANDBY (cyan) → LISTENING (cyan pulse) → PROCESSING (amber) → RESPONDING (green)
- **Live Transcript** — scrolling dialogue feed with user/Jarvis messages
- **System Metrics** — session ID, turn count, memory count, uptime
- **Subsystem Status** — green/red indicators for all 8 subsystems
- **Click-Through Mode** — HUD is transparent and click-through by default
- **Dev Mode** — when backend is disconnected, state bar appears for UI testing

## Roadmap (PRD phases)

| Phase | Status  | Description                            |
| ----- | ------- | -------------------------------------- |
| M1    | ✅ Done | Audio pipeline, LLM, STT, TTS          |
| M2    | ✅ Done | Voice dialogue, persistent memory      |
| M3    | 🔜 Scaffold | Vision (YOLO/CLIP) stubs ready     |
| M4    | ⏳      | RL planner, context graph              |
| M5    | ✅ Done | HUD overlay (Electron + React)         |
| M6    | ⏳      | Security hardening, sandboxing         |

## Cross-Platform Support

| Feature        | Windows | macOS | Linux |
| -------------- | ------- | ----- | ----- |
| Clap detection | ✅      | ✅    | ✅    |
| Voice (STT/TTS)| ✅      | ✅    | ✅    |
| App launching  | ✅      | ✅    | ✅    |
| Window control | ✅      | ⏳    | ⏳    |
| HUD overlay    | ✅      | ✅    | ✅    |
