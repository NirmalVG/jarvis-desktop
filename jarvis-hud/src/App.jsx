import { useState, useEffect, useCallback } from "react"
import { useJarvisState } from "./hooks/useJarvisState"
import OrbZone from "./components/OrbZone"
import TranscriptFeed from "./components/TranscriptFeed"
import SystemPanel from "./components/SystemPanel"
import TitleBar from "./components/TitleBar"
import Sidebar from "./components/Sidebar"
import DustField from "./components/DustField"
import HexGrid from "./components/HexGrid"
import CommandPalette from "./components/CommandPalette"
import StateBar from "./components/StateBar"

export default function App() {
  const {
    state,
    transcript,
    reply,
    stats,
    connected,
    commandHistory,
    systemInfo,
    sendCommand,
  } = useJarvisState()

  const [clickthrough, setClickthrough] = useState(true)
  const [paletteOpen, setPaletteOpen] = useState(false)
  const [fullscreen, setFullscreen] = useState(false)
  const [devState, setDevState] = useState(null)

  // Ctrl+K opens command palette
  useEffect(() => {
    const handler = (e) => {
      if ((e.ctrlKey || e.metaKey) && e.key === "k") {
        e.preventDefault()
        setPaletteOpen((o) => !o)
      }
    }
    window.addEventListener("keydown", handler)
    return () => window.removeEventListener("keydown", handler)
  }, [])

  const handleToggleClickthrough = useCallback(() => {
    setClickthrough((c) => !c)
    window.jarvis?.toggleClickthrough?.()
  }, [])

  const handleExecuteCommand = useCallback(
    (cmd) => {
      sendCommand(cmd)
    },
    [sendCommand],
  )

  const activeState = devState || state

  const operatorName = stats?.operator_name ?? "Nirmal"

  return (
    <div
      style={{
        width: "100vw",
        height: "100vh",
        overflow: "hidden",
        position: "relative",
        background: "transparent",
        pointerEvents: clickthrough ? "none" : "auto",
      }}
    >
      {/* Background layers */}
      <HexGrid state={activeState} fullscreen={fullscreen} />
      <DustField state={activeState} />

      {/* UI chrome — always intercept pointer events */}
      <div style={{ pointerEvents: "auto" }}>
        <TitleBar
          onMinimize={() => window.jarvis?.minimizeHud?.()}
          onToggleClickthrough={handleToggleClickthrough}
          clickthrough={clickthrough}
        />
        <Sidebar />
      </div>

      {/* Central orb */}
      <OrbZone state={activeState} />

      {/* Transcript feed — shows NIRMAL / J.A.R.V.I.S. labels */}
      <div style={{ pointerEvents: "auto" }}>
        <TranscriptFeed
          transcript={transcript}
          reply={reply}
          state={activeState}
          operatorName={operatorName}
        />
      </div>

      {/* System panel — top right */}
      <div
        style={{
          position: "fixed",
          top: 54,
          right: 16,
          width: 280,
          zIndex: 70,
          pointerEvents: "auto",
        }}
      >
        <SystemPanel
          stats={stats}
          connected={connected}
          systemInfo={systemInfo}
        />
      </div>

      {/* Dev state bar — bottom centre, hidden in production */}
      {process.env.NODE_ENV === "development" && (
        <div
          style={{
            position: "fixed",
            bottom: 16,
            left: "50%",
            transform: "translateX(-50%)",
            width: 320,
            zIndex: 100,
            pointerEvents: "auto",
          }}
        >
          <StateBar state={activeState} onChange={setDevState} />
        </div>
      )}

      {/* Command palette */}
      <CommandPalette
        visible={paletteOpen}
        onClose={() => setPaletteOpen(false)}
        onExecute={handleExecuteCommand}
      />
    </div>
  )
}
