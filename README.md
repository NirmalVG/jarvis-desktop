# Jarvis Desktop

Jarvis Desktop is a local AI desktop assistant with a Python voice backend and a React/Electron HUD. It wakes by clap or wake word, listens through speech recognition, answers through Groq, speaks with Edge neural TTS, and shows an ambient orb interface.

## Project Structure

```text
jarvis-desktop/
  jarvis/       Python backend: wake, STT, brain, TTS, actions, memory, web search
  jarvis-hud/   React/Electron HUD
  launcher.bat  Windows launcher
  launcher.sh   Linux/macOS launcher
```

## Setup

Create `jarvis/.env` and add your Groq API key:

```env
GROQ_API_KEY=your_groq_key_here
```

Install backend dependencies:

```powershell
cd jarvis
pip install -r requirements.txt
```

Install HUD dependencies:

```powershell
cd ../jarvis-hud
npm install
```

## Run

From the project root:

```powershell
.\launcher.bat
```

For backend-only development:

```powershell
cd jarvis
python main.py --no-wake
```

For HUD development:

```powershell
cd jarvis-hud
npm run dev
```

## Notes

- `jarvis/.env` is ignored by Git and must not be committed.
- The HUD connects to the backend WebSocket bridge on `ws://localhost:6789`.
- The wake briefing uses live web results, so internet access is needed for current technology headlines.
