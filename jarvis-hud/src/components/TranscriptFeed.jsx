/**
 * src/components/TranscriptFeed.jsx  (patched)
 * ─────────────────────────────────────────────
 * Changes from original:
 *   • Accepts `operatorName` prop (default "Nirmal") — replaces the
 *     hardcoded "You" label that was showing for every user message.
 *   • UserLabel now renders the actual operator name with the same
 *     badge treatment as the J.A.R.V.I.S. label.
 *   • operatorName flows through from App.jsx via stats.user_name
 *     (which is seeded from the facts store on boot).
 */
import { useEffect, useRef, useState } from "react"
import { motion, AnimatePresence } from "framer-motion"

const MAX = 14

export default function TranscriptFeed({
  transcript,
  reply,
  state,
  operatorName = "Nirmal",
}) {
  const [entries, setEntries] = useState([])
  const bottomRef = useRef(null)

  useEffect(() => {
    if (!transcript || transcript.trim().length < 2) return
    setEntries((prev) => {
      const last = prev[prev.length - 1]
      if (last?.role === "user" && last.text === transcript) return prev
      return [
        ...prev,
        { id: Date.now(), role: "user", text: transcript },
      ].slice(-MAX)
    })
  }, [transcript])

  useEffect(() => {
    if (!reply || reply.trim().length < 2) return
    setEntries((prev) => {
      const last = prev[prev.length - 1]
      if (last?.role === "jarvis" && last.text === reply) return prev
      return [
        ...prev,
        { id: Date.now() + 1, role: "jarvis", text: reply },
      ].slice(-MAX)
    })
  }, [reply])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [entries])

  const isThinking = state === "THINKING"

  return (
    <div
      style={{
        position: "absolute",
        left: 20,
        top: 60,
        bottom: 20,
        width: 380,
        zIndex: 60,
        display: "flex",
        flexDirection: "column",
        pointerEvents: "auto",
      }}
    >
      {/* Glass container */}
      <div
        style={{
          flex: 1,
          display: "flex",
          flexDirection: "column",
          background: "rgba(0,8,16,0.55)",
          border: "1px solid rgba(0,212,255,0.12)",
          borderRadius: 2,
          backdropFilter: "blur(8px)",
          overflow: "hidden",
          boxShadow:
            "0 0 30px rgba(0,212,255,0.03), inset 0 0 30px rgba(0,0,0,0.3)",
        }}
      >
        {/* Top edge glow */}
        <div
          style={{
            height: 1,
            background:
              "linear-gradient(90deg, transparent, rgba(0,212,255,0.3), rgba(0,212,255,0.5), rgba(0,212,255,0.3), transparent)",
            flexShrink: 0,
          }}
        />

        {/* System status header */}
        <div style={{ padding: "14px 18px 10px", flexShrink: 0 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <div
              style={{
                width: 6,
                height: 6,
                borderRadius: "50%",
                background: "#00ff88",
                boxShadow: "0 0 6px #00ff88",
                animation: "status-glow 2s ease-in-out infinite",
                flexShrink: 0,
              }}
            />
            <span
              style={{
                fontFamily: "'Share Tech Mono', monospace",
                fontSize: 12,
                color: "#00ff88",
                letterSpacing: ".1em",
              }}
            >
              {">"} SYS_STATUS: ACTIVE
            </span>
          </div>
        </div>

        {/* Messages area */}
        <div
          style={{
            flex: 1,
            overflowY: "auto",
            overflowX: "hidden",
            padding: "4px 18px 8px",
            display: "flex",
            flexDirection: "column",
            gap: 12,
          }}
        >
          {entries.length === 0 && (
            <div
              style={{
                fontFamily: "'Share Tech Mono', monospace",
                fontSize: 11,
                color: "rgba(0,212,255,0.15)",
                textAlign: "center",
                letterSpacing: "0.14em",
                paddingTop: 30,
              }}
            >
              — NO ACTIVE DIALOGUE —
            </div>
          )}

          <AnimatePresence initial={false}>
            {entries.map((entry) => (
              <ChatMessage
                key={entry.id}
                entry={entry}
                operatorName={operatorName}
              />
            ))}
          </AnimatePresence>

          {/* Thinking indicator */}
          {isThinking && (
            <motion.div
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              style={{ paddingLeft: 2 }}
            >
              <JarvisLabel />
              <div
                style={{
                  display: "flex",
                  gap: 4,
                  alignItems: "center",
                  paddingTop: 6,
                  paddingLeft: 4,
                }}
              >
                {[0, 1, 2].map((i) => (
                  <motion.div
                    key={i}
                    animate={{ opacity: [0.2, 1, 0.2] }}
                    transition={{
                      duration: 0.8,
                      repeat: Infinity,
                      delay: i * 0.2,
                    }}
                    style={{
                      width: 5,
                      height: 5,
                      borderRadius: "50%",
                      background: "#00d4ff",
                    }}
                  />
                ))}
              </div>
            </motion.div>
          )}

          <div ref={bottomRef} />
        </div>

        {/* Bottom input prompt */}
        <div
          style={{
            padding: "10px 18px 14px",
            borderTop: "1px solid rgba(0,212,255,0.08)",
            flexShrink: 0,
          }}
        >
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: 8,
              padding: "8px 12px",
              background: "rgba(0,212,255,0.04)",
              border: "1px solid rgba(0,212,255,0.15)",
              borderRadius: 2,
            }}
          >
            <span
              style={{
                fontFamily: "'Share Tech Mono', monospace",
                fontSize: 12,
                color: "rgba(0,212,255,0.5)",
              }}
            >
              {">"}
            </span>
            <span
              style={{
                fontFamily: "'Share Tech Mono', monospace",
                fontSize: 11,
                color: "rgba(0,212,255,0.35)",
                letterSpacing: ".08em",
                flex: 1,
              }}
            >
              AWAITING INPUT...
            </span>
            <span
              style={{
                width: 7,
                height: 14,
                background: "rgba(0,212,255,0.5)",
                animation: "blink-cursor 1s step-end infinite",
              }}
            />
          </div>
        </div>

        {/* Bottom edge glow */}
        <div
          style={{
            height: 1,
            background:
              "linear-gradient(90deg, transparent, rgba(0,212,255,0.2), rgba(0,212,255,0.3), rgba(0,212,255,0.2), transparent)",
            flexShrink: 0,
          }}
        />
      </div>
    </div>
  )
}

/* ── J.A.R.V.I.S. label badge ──────────────────────────────────────────── */
function JarvisLabel() {
  return (
    <span
      style={{
        fontFamily: "'Orbitron', monospace",
        fontSize: 9,
        fontWeight: 700,
        letterSpacing: ".16em",
        color: "#00d4ff",
        background: "rgba(0,212,255,0.08)",
        border: "1px solid rgba(0,212,255,0.2)",
        padding: "3px 10px",
        borderRadius: 2,
        display: "inline-block",
        textShadow: "0 0 8px rgba(0,212,255,0.5)",
      }}
    >
      J.A.R.V.I.S.
    </span>
  )
}

/* ── Operator label badge — shows the real name, not "You" ─────────────── */
function OperatorLabel({ name }) {
  return (
    <span
      style={{
        fontFamily: "'Orbitron', monospace",
        fontSize: 9,
        fontWeight: 700,
        letterSpacing: ".16em",
        color: "#00ff88",
        background: "rgba(0,255,136,0.08)",
        border: "1px solid rgba(0,255,136,0.2)",
        padding: "3px 10px",
        borderRadius: 2,
        display: "inline-block",
        textShadow: "0 0 8px rgba(0,255,136,0.5)",
      }}
    >
      {name.toUpperCase()}
    </span>
  )
}

/* ── Individual chat message ────────────────────────────────────────────── */
function ChatMessage({ entry, operatorName }) {
  const isUser = entry.role === "user"

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -6 }}
      transition={{ duration: 0.25, ease: "easeOut" }}
    >
      {isUser ? <OperatorLabel name={operatorName} /> : <JarvisLabel />}
      <div style={{ marginTop: 6 }}>
        {isUser ? (
          /* Operator messages: plain floating text */
          <div
            style={{
              fontFamily: "'Rajdhani', sans-serif",
              fontSize: 14,
              fontWeight: 500,
              lineHeight: 1.5,
              color: "rgba(180,220,240,0.85)",
              paddingLeft: 4,
            }}
          >
            {entry.text}
          </div>
        ) : (
          /* Jarvis replies: bordered translucent box */
          <div
            style={{
              fontFamily: "'Rajdhani', sans-serif",
              fontSize: 14,
              fontWeight: 500,
              lineHeight: 1.5,
              color: "rgba(180,220,240,0.85)",
              padding: "10px 14px",
              background: "rgba(0,212,255,0.03)",
              border: "1px solid rgba(0,212,255,0.12)",
              borderRadius: 2,
              borderLeft: "2px solid rgba(0,212,255,0.3)",
            }}
          >
            {entry.text}
          </div>
        )}
      </div>
    </motion.div>
  )
}
