/**
 * src/hooks/useJarvisState.js
 * ────────────────────────────
 * Subscribes to Jarvis state events from the Python bridge.
 * NOW BIDIRECTIONAL — can send commands back to Python.
 *
 * In Electron: uses window.jarvis IPC (via preload contextBridge).
 * In browser dev mode: opens a raw WebSocket to ws://localhost:6789.
 *
 * Returns: { state, transcript, reply, stats, connected, commandHistory, systemInfo, sendCommand }
 */

import { useEffect, useState, useRef, useCallback } from "react"

const INITIAL = {
  state: "SLEEPING",
  transcript: "",
  reply: "",
  stats: { sessions: 0, total_turns: 0, memories: 0, session_id: "—" },
  connected: false,
  commandHistory: [],
  systemInfo: {
    cpu_percent: 0,
    memory_percent: 0,
    memory_used_gb: 0,
    memory_total_gb: 0,
    disk_percent: 0,
    uptime_hours: 0,
    platform: "—",
  },
}

const MAX_HISTORY = 50

export function useJarvisState() {
  const [data, setData] = useState(INITIAL)
  const wsRef = useRef(null)
  const historyRef = useRef([])

  const addToHistory = useCallback((transcript, reply, state) => {
    if (!transcript || transcript.trim().length < 2) return
    const entry = {
      id: Date.now(),
      transcript,
      reply: reply || "",
      state,
      timestamp: new Date().toISOString(),
    }
    historyRef.current = [...historyRef.current, entry].slice(-MAX_HISTORY)
    setData((prev) => ({ ...prev, commandHistory: historyRef.current }))
  }, [])

  // Send a command to the Python backend via WebSocket
  const sendCommand = useCallback((text) => {
    if (!text || text.trim().length < 1) return

    const isElectron = typeof window !== "undefined" && !!window.jarvis
    if (isElectron) {
      // Electron IPC path
      window.jarvis.sendCommand?.(text)
    } else {
      // Direct WebSocket path
      const ws = wsRef.current
      if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: "command", text }))
      }
    }
  }, [])

  useEffect(() => {
    const isElectron = typeof window !== "undefined" && !!window.jarvis

    if (isElectron) {
      // ── Electron IPC path ─────────────────────────────────────────────────
      window.jarvis.onState((msg) => {
        setData((prev) => ({ ...prev, ...msg, connected: true }))
        if (msg.transcript && msg.state === "SPEAKING") {
          addToHistory(msg.transcript, msg.reply, msg.state)
        }
      })
      window.jarvis.onConnection((msg) => {
        setData((prev) => ({ ...prev, connected: msg.connected }))
      })
      // Listen for system info updates
      window.jarvis.onSystemInfo?.((info) => {
        setData((prev) => ({ ...prev, systemInfo: { ...prev.systemInfo, ...info } }))
      })

      return () => {
        window.jarvis.removeAllListeners("jarvis-state")
        window.jarvis.removeAllListeners("connection-status")
        window.jarvis.removeAllListeners("system-info")
      }
    } else {
      // ── Browser dev path: direct WebSocket ───────────────────────────────
      const connect = () => {
        const ws = new WebSocket("ws://localhost:6789")
        wsRef.current = ws

        ws.onopen = () => {
          setData((prev) => ({ ...prev, connected: true }))
        }
        ws.onmessage = (evt) => {
          try {
            const msg = JSON.parse(evt.data)

            // Handle command_history bulk message from bridge
            if (msg.type === "command_history" && msg.history) {
              historyRef.current = msg.history.map((h, i) => ({
                id: Date.now() + i,
                ...h,
              }))
              setData((prev) => ({
                ...prev,
                commandHistory: historyRef.current,
              }))
              return
            }

            // Handle system_info messages
            if (msg.type === "system_info") {
              setData((prev) => ({
                ...prev,
                systemInfo: { ...prev.systemInfo, ...msg },
              }))
              return
            }

            setData((prev) => ({ ...prev, ...msg, connected: true }))
            if (msg.transcript && msg.state === "SPEAKING") {
              addToHistory(msg.transcript, msg.reply, msg.state)
            }
          } catch (_) {}
        }
        ws.onclose = () => {
          setData((prev) => ({ ...prev, connected: false }))
          setTimeout(connect, 2000)
        }
        ws.onerror = () => {}
      }
      connect()

      return () => wsRef.current?.close()
    }
  }, [addToHistory])

  return { ...data, sendCommand }
}
