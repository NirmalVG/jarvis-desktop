/**
 * src/components/CommandPalette.jsx
 * ───────────────────────────────────
 * Quick-action command palette overlay.
 * Triggered by Ctrl+K / Cmd+K — shows frequent commands.
 * HUD-styled with search and keyboard navigation.
 */

import { useState, useEffect, useRef, useCallback } from "react"
import { motion, AnimatePresence } from "framer-motion"

const QUICK_ACTIONS = [
  { label: "Open YouTube", command: "open youtube", icon: "▶" },
  { label: "Open VS Code", command: "open vs code", icon: "⟨⟩" },
  { label: "Open GitHub", command: "open github", icon: "◈" },
  { label: "Open Gmail", command: "open gmail", icon: "✉" },
  { label: "Open Spotify", command: "open spotify", icon: "♫" },
  { label: "Take Screenshot", command: "screenshot", icon: "📷" },
  { label: "Volume Up", command: "volume up", icon: "🔊" },
  { label: "Volume Down", command: "volume down", icon: "🔉" },
  { label: "Mute", command: "mute", icon: "🔇" },
  { label: "Minimize Window", command: "minimize window", icon: "⊟" },
  { label: "Maximize Window", command: "maximize window", icon: "⊞" },
  { label: "Open Calculator", command: "open calculator", icon: "∑" },
  { label: "Open Terminal", command: "open terminal", icon: "⊳" },
  { label: "Open Notepad", command: "open notepad", icon: "📝" },
  { label: "Open ChatGPT", command: "open chatgpt", icon: "⬡" },
]

export default function CommandPalette({ visible, onClose, onExecute, acc = "#00d4ff" }) {
  const [search, setSearch] = useState("")
  const [selected, setSelected] = useState(0)
  const inputRef = useRef(null)

  const filtered = QUICK_ACTIONS.filter(
    (a) =>
      a.label.toLowerCase().includes(search.toLowerCase()) ||
      a.command.toLowerCase().includes(search.toLowerCase()),
  )

  useEffect(() => {
    if (visible) {
      setSearch("")
      setSelected(0)
      setTimeout(() => inputRef.current?.focus(), 100)
    }
  }, [visible])

  const handleKey = useCallback(
    (e) => {
      if (e.key === "Escape") {
        onClose?.()
      } else if (e.key === "ArrowDown") {
        e.preventDefault()
        setSelected((s) => Math.min(s + 1, filtered.length - 1))
      } else if (e.key === "ArrowUp") {
        e.preventDefault()
        setSelected((s) => Math.max(s - 1, 0))
      } else if (e.key === "Enter" && filtered[selected]) {
        onExecute?.(filtered[selected].command)
        onClose?.()
      }
    },
    [filtered, selected, onClose],
  )

  if (!visible) return null

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        transition={{ duration: 0.15 }}
        onClick={onClose}
        style={{
          position: "fixed",
          inset: 0,
          zIndex: 9999,
          background: "rgba(0,0,0,0.5)",
          display: "flex",
          alignItems: "flex-start",
          justifyContent: "center",
          paddingTop: 120,
        }}
      >
        <motion.div
          initial={{ opacity: 0, y: -10, scale: 0.96 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          exit={{ opacity: 0, y: -10, scale: 0.96 }}
          transition={{ duration: 0.18, ease: "easeOut" }}
          onClick={(e) => e.stopPropagation()}
          style={{
            width: 420,
            maxHeight: 460,
            background: "rgba(2,8,18,0.96)",
            border: `1px solid ${acc}30`,
            borderRadius: 8,
            boxShadow: `0 0 40px ${acc}15, 0 8px 32px rgba(0,0,0,0.6)`,
            overflow: "hidden",
            backdropFilter: "blur(12px)",
          }}
        >
          {/* Search input */}
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: 10,
              padding: "12px 16px",
              borderBottom: `1px solid ${acc}18`,
            }}
          >
            <span
              style={{
                fontFamily: "'Orbitron', monospace",
                fontSize: 10,
                color: `${acc}66`,
                letterSpacing: ".12em",
              }}
            >
              ⌘
            </span>
            <input
              ref={inputRef}
              value={search}
              onChange={(e) => {
                setSearch(e.target.value)
                setSelected(0)
              }}
              onKeyDown={handleKey}
              placeholder="Search commands..."
              style={{
                flex: 1,
                background: "transparent",
                border: "none",
                outline: "none",
                fontFamily: "'Rajdhani', sans-serif",
                fontSize: 15,
                fontWeight: 500,
                color: `${acc}dd`,
                letterSpacing: ".02em",
              }}
            />
            <span
              style={{
                fontFamily: "'Share Tech Mono', monospace",
                fontSize: 8,
                color: `${acc}33`,
                letterSpacing: ".1em",
                padding: "2px 6px",
                border: `1px solid ${acc}22`,
                borderRadius: 3,
              }}
            >
              ESC
            </span>
          </div>

          {/* Results */}
          <div
            style={{
              maxHeight: 360,
              overflowY: "auto",
              padding: "6px 6px",
            }}
          >
            {filtered.length === 0 && (
              <div
                style={{
                  padding: "20px 16px",
                  textAlign: "center",
                  fontFamily: "'Share Tech Mono', monospace",
                  fontSize: 11,
                  color: `${acc}33`,
                  letterSpacing: ".12em",
                }}
              >
                NO MATCHING COMMANDS
              </div>
            )}
            {filtered.map((action, i) => (
              <div
                key={action.command}
                onMouseEnter={() => setSelected(i)}
                onClick={() => {
                  onExecute?.(action.command)
                  onClose?.()
                }}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 12,
                  padding: "8px 12px",
                  borderRadius: 4,
                  cursor: "pointer",
                  background:
                    i === selected ? `${acc}12` : "transparent",
                  border:
                    i === selected
                      ? `1px solid ${acc}25`
                      : "1px solid transparent",
                  transition: "all 0.12s",
                }}
              >
                <span
                  style={{
                    fontSize: 14,
                    width: 22,
                    textAlign: "center",
                    opacity: 0.7,
                  }}
                >
                  {action.icon}
                </span>
                <div style={{ flex: 1 }}>
                  <div
                    style={{
                      fontFamily: "'Rajdhani', sans-serif",
                      fontSize: 14,
                      fontWeight: 600,
                      color:
                        i === selected
                          ? `${acc}`
                          : `${acc}aa`,
                    }}
                  >
                    {action.label}
                  </div>
                  <div
                    style={{
                      fontFamily: "'Share Tech Mono', monospace",
                      fontSize: 9,
                      color: `${acc}44`,
                      letterSpacing: ".06em",
                    }}
                  >
                    {action.command}
                  </div>
                </div>
                {i === selected && (
                  <span
                    style={{
                      fontFamily: "'Share Tech Mono', monospace",
                      fontSize: 8,
                      color: `${acc}44`,
                      padding: "1px 5px",
                      border: `1px solid ${acc}22`,
                      borderRadius: 2,
                    }}
                  >
                    ENTER
                  </span>
                )}
              </div>
            ))}
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  )
}
