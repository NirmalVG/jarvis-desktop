/**
 * src/components/TitleBar.jsx
 * ────────────────────────────
 * Simplified top bar: "J.A.R.V.I.S." branding on the left,
 * settings (gear) and power icons on the right.
 * Matches the design mockup.
 */

import { useState } from "react"

export default function TitleBar({
  onMinimize,
  onToggleClickthrough,
  clickthrough,
  acc = "#00d4ff",
}) {
  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        padding: "0 20px",
        height: 44,
        flexShrink: 0,
        borderBottom: `1px solid rgba(0,212,255,0.06)`,
        background: "rgba(0,0,0,0.7)",
        WebkitAppRegion: "drag",
        position: "relative",
        zIndex: 100,
      }}
    >
      {/* Left: J.A.R.V.I.S. branding */}
      <div style={{ display: "flex", alignItems: "center", gap: 0 }}>
        <span
          style={{
            fontFamily: "'Orbitron', monospace",
            fontSize: 14,
            fontWeight: 900,
            letterSpacing: ".18em",
            color: acc,
            textShadow: `0 0 16px ${acc}88`,
          }}
        >
          J.A.R.V.I.S.
        </span>
      </div>

      {/* Right: control buttons */}
      <div
        style={{
          display: "flex",
          gap: 10,
          alignItems: "center",
          WebkitAppRegion: "no-drag",
        }}
      >
        <IconButton
          icon="⚙"
          title="Settings"
          acc={acc}
          onClick={onToggleClickthrough}
        />
        <IconButton
          icon="⏻"
          title="Power"
          acc={acc}
          onClick={() => window.jarvis?.quit?.()}
          danger
        />
      </div>
    </div>
  )
}

function IconButton({ icon, title, acc, onClick, danger }) {
  const [hover, setHover] = useState(false)
  const color = danger
    ? hover
      ? "#ff4466"
      : `${acc}66`
    : hover
      ? acc
      : `${acc}55`

  return (
    <button
      title={title}
      onClick={onClick}
      onMouseEnter={() => setHover(true)}
      onMouseLeave={() => setHover(false)}
      style={{
        width: 28,
        height: 28,
        background: hover ? `${color}12` : "transparent",
        border: "none",
        borderRadius: 4,
        color,
        fontSize: 15,
        cursor: "pointer",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        transition: "all .2s",
      }}
    >
      {icon}
    </button>
  )
}
