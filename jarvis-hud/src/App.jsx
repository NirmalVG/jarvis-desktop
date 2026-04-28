/**
 * src/App.jsx
 * ─────────────
 * Main HUD application shell — Jarvis design.
 * 
 * Layout: Full-screen black background with layered elements:
 *   1. Full-screen ambient dust particles (DustField)
 *   2. Blue-glowing particle orb (OrbZone) — centered
 *   3. Floating chat panel (TranscriptFeed) — left side
 *   4. TitleBar — top
 *   5. Stats overlay — top right corner
 *   6. Status indicator — bottom right corner
 *   7. Command palette (Ctrl+K)
 */

import { useState, useEffect, useCallback } from "react"
import { useJarvisState } from "./hooks/useJarvisState"
import TitleBar from "./components/TitleBar"
import OrbZone from "./components/OrbZone"
import TranscriptFeed from "./components/TranscriptFeed"
import DustField from "./components/DustField"
import StateBar from "./components/StateBar"
import CommandPalette from "./components/CommandPalette"

const ACC = "#00d4ff"

export default function App() {
  const {
    state: liveState,
    transcript,
    reply,
    stats,
    connected,
    commandHistory,
  } = useJarvisState()
  const [clickthrough, setClickthrough] = useState(true)
  const [devOverride, setDevOverride] = useState(null)
  const [paletteOpen, setPaletteOpen] = useState(false)

  const state = devOverride || liveState

  useEffect(() => {
    if (connected && liveState !== "SLEEPING") setDevOverride(null)
  }, [liveState, connected])

  useEffect(() => {
    window.jarvis?.onClickthrough((d) => setClickthrough(d.active))
  }, [])

  // Global keyboard shortcut: Ctrl+K / Cmd+K for command palette
  const handleKeyDown = useCallback(
    (e) => {
      if ((e.ctrlKey || e.metaKey) && e.key === "k") {
        e.preventDefault()
        setPaletteOpen((prev) => !prev)
      }
      if (e.key === "Escape" && paletteOpen) {
        setPaletteOpen(false)
      }
    },
    [paletteOpen],
  )

  useEffect(() => {
    window.addEventListener("keydown", handleKeyDown)
    return () => window.removeEventListener("keydown", handleKeyDown)
  }, [handleKeyDown])

  const isDevMode = !connected

  return (
    <div
      style={{
        width: "100vw",
        height: "100vh",
        background: "#000000",
        position: "relative",
        overflow: "hidden",
        fontFamily: "'Rajdhani', sans-serif",
      }}
    >
      {/* Layer 0: Full-screen ambient dust particles */}
      <DustField state={state} />

      {/* Layer 2: Top bar */}
      <TitleBar
        onMinimize={() => window.jarvis?.minimizeHud()}
        onToggleClickthrough={() => window.jarvis?.toggleClickthrough()}
        clickthrough={clickthrough}
        acc={ACC}
      />

      {/* Dev mode state switcher */}
      {isDevMode && (
        <div style={{ position: "relative", zIndex: 90 }}>
          <StateBar state={state} onChange={(s) => setDevOverride(s)} />
        </div>
      )}

      {/* Layer 4: Central orb — positioned absolutely */}
      <OrbZone state={state} />

      {/* Layer 5: Floating chat panel on the left */}
      <TranscriptFeed transcript={transcript} reply={reply} state={state} />

      {/* Layer 6: Stats overlay — top right */}
      <StatsOverlay stats={stats} connected={connected} />

      {/* Layer 7: Status indicator — bottom right */}
      <StatusDot state={state} connected={connected} />

      {/* Command Palette */}
      <CommandPalette
        visible={paletteOpen}
        onClose={() => setPaletteOpen(false)}
        acc={ACC}
      />

      {/* Shortcut hint */}
      {!paletteOpen && (
        <div
          style={{
            position: "fixed",
            bottom: 12,
            right: 16,
            fontFamily: "'Share Tech Mono', monospace",
            fontSize: 8,
            color: "rgba(0,212,255,0.1)",
            letterSpacing: ".1em",
            zIndex: 40,
            pointerEvents: "none",
          }}
        >
          CTRL+K COMMAND PALETTE
        </div>
      )}
    </div>
  )
}

// ─── Stats Overlay (top-right corner) ────────────────────────────────────────
function StatsOverlay({ stats, connected }) {
  const [coord, setCoord] = useState({ x: 45.912, y: 8 })

  useEffect(() => {
    const id = setInterval(() => {
      setCoord({
        x: (45 + Math.random() * 2).toFixed(3),
        y: Math.floor(Math.random() * 10),
      })
    }, 3000)
    return () => clearInterval(id)
  }, [])

  return (
    <div
      style={{
        position: "fixed",
        top: 58,
        right: 20,
        zIndex: 70,
        pointerEvents: "none",
        textAlign: "right",
      }}
    >
      {/* Coordinates */}
      <div
        style={{
          fontFamily: "'Share Tech Mono', monospace",
          fontSize: 10,
          color: "rgba(0,212,255,0.45)",
          letterSpacing: ".06em",
          lineHeight: 1.6,
        }}
      >
        <div>COORD: {coord.x} X{coord.y}</div>
        <div>SYNC: {connected ? "99.8" : "0.0"}%</div>
      </div>

      {/* Sync progress bar */}
      <div
        style={{
          marginTop: 6,
          width: 120,
          height: 3,
          background: "rgba(0,212,255,0.08)",
          borderRadius: 1,
          overflow: "hidden",
          marginLeft: "auto",
        }}
      >
        <div
          style={{
            width: connected ? "85%" : "0%",
            height: "100%",
            background: "linear-gradient(90deg, rgba(0,212,255,0.3), #00d4ff)",
            borderRadius: 1,
            transition: "width 1s ease",
            boxShadow: "0 0 6px rgba(0,212,255,0.4)",
          }}
        />
      </div>

      {/* Memory stats (subtle) */}
      {stats?.memories > 0 && (
        <div
          style={{
            fontFamily: "'Share Tech Mono', monospace",
            fontSize: 8,
            color: "rgba(0,212,255,0.2)",
            letterSpacing: ".08em",
            marginTop: 8,
          }}
        >
          MEM: {stats.memories} · TURNS: {stats.total_turns ?? 0}
        </div>
      )}
    </div>
  )
}

// ─── Status Dot (bottom-right corner) ────────────────────────────────────────
function StatusDot({ state, connected }) {
  const isActive = state !== "SLEEPING"

  return (
    <div
      style={{
        position: "fixed",
        bottom: 24,
        right: 24,
        zIndex: 70,
        pointerEvents: "none",
      }}
    >
      <div
        style={{
          width: 36,
          height: 36,
          borderRadius: "50%",
          border: `1px solid rgba(0,212,255,${isActive ? 0.3 : 0.12})`,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          background: "rgba(0,4,10,0.6)",
          transition: "all 0.5s ease",
          boxShadow: isActive
            ? "0 0 16px rgba(0,212,255,0.1)"
            : "none",
        }}
      >
        <div
          style={{
            width: 8,
            height: 8,
            borderRadius: "50%",
            background: connected ? "#00d4ff" : "rgba(0,212,255,0.2)",
            boxShadow: connected
              ? "0 0 8px rgba(0,212,255,0.6)"
              : "none",
            transition: "all 0.5s ease",
          }}
        />
      </div>
    </div>
  )
}
