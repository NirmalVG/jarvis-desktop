/**
 * src/components/StateBar.jsx
 * ─────────────────────────────
 * 4-column state indicator strip between the orb and transcript.
 * Clicking a state tab in dev mode simulates a state change.
 */

const STATES = [
  { key: "SLEEPING", icon: "◌ ◌", label: "SLEEP", color: "#4488aa" },
  { key: "LISTENING", icon: "◉ ◉", label: "LISTEN", color: "#00d4ff" },
  { key: "THINKING", icon: "◈ ◈", label: "THINK", color: "#ff9500" },
  { key: "SPEAKING", icon: "◎ ◎", label: "SPEAK", color: "#00ff88" },
]

export default function StateBar({ state, onChange }) {
  return (
    <div
      style={{
        display: "grid",
        gridTemplateColumns: "repeat(4,1fr)",
        borderBottom: "1px solid rgba(0,212,255,0.1)",
        flexShrink: 0,
        position: "relative",
        zIndex: 5,
      }}
    >
      {STATES.map((s, i) => {
        const active = state === s.key
        return (
          <div
            key={s.key}
            onClick={() => onChange?.(s.key)}
            style={{
              padding: "7px 0",
              textAlign: "center",
              borderRight: i < 3 ? "1px solid rgba(0,212,255,0.08)" : "none",
              cursor: "pointer",
              background: active ? `${s.color}0f` : "transparent",
              position: "relative",
              transition: "background 0.22s",
            }}
          >
            {/* Active underline */}
            {active && (
              <div
                style={{
                  position: "absolute",
                  bottom: 0,
                  left: "10%",
                  width: "80%",
                  height: 1.5,
                  background: s.color,
                }}
              />
            )}
            <div
              style={{
                fontFamily: "'Share Tech Mono', monospace",
                fontSize: 7,
                letterSpacing: "0.08em",
                color: s.color,
                opacity: active ? 0.85 : 0.4,
                marginBottom: 2,
              }}
            >
              {s.icon}
            </div>
            <div
              style={{
                fontFamily: "'Orbitron', monospace",
                fontSize: 7,
                fontWeight: 700,
                letterSpacing: "0.16em",
                color: s.color,
                opacity: active ? 0.9 : 0.45,
              }}
            >
              {s.label}
            </div>
          </div>
        )
      })}
    </div>
  )
}
