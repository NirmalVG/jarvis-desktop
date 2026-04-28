/**
 * src/components/SystemPanel.jsx
 * ───────────────────────────────
 * Right-panel system diagnostics with animated usage bars,
 * connection status, session stats, and data throughput.
 */

import { useState, useEffect, useRef } from "react"
import { motion } from "framer-motion"

export default function SystemPanel({ stats, connected, vertical }) {
  const [uptime, setUptime] = useState(0)
  const [cpuUsage, setCpuUsage] = useState(24)
  const [memUsage, setMemUsage] = useState(38)
  const [netThroughput, setNetThroughput] = useState(0)
  const prevTurns = useRef(0)

  useEffect(() => {
    const id = setInterval(() => {
      setUptime((s) => s + 1)
      // Simulate CPU/memory fluctuations (in a real app, we'd use Electron's process.memoryInfo())
      setCpuUsage((prev) => Math.max(8, Math.min(95, prev + (Math.random() - 0.48) * 6)))
      setMemUsage((prev) => Math.max(20, Math.min(85, prev + (Math.random() - 0.5) * 3)))
    }, 1000)
    return () => clearInterval(id)
  }, [])

  // Track data throughput (turns per minute)
  useEffect(() => {
    const turns = stats?.total_turns ?? 0
    if (turns > prevTurns.current) {
      setNetThroughput(turns - prevTurns.current)
      prevTurns.current = turns
    }
    const decay = setInterval(() => setNetThroughput(0), 10000)
    return () => clearInterval(decay)
  }, [stats?.total_turns])

  const m = Math.floor(uptime / 60)
    .toString()
    .padStart(2, "0")
  const h = Math.floor(uptime / 3600)
    .toString()
    .padStart(2, "0")
  const sc = (uptime % 60).toString().padStart(2, "0")

  const cells = [
    {
      label: "SESSION",
      value: stats?.session_id ? stats.session_id.slice(0, 6) + "…" : "A3F9B2…",
    },
    { label: "TURNS", value: stats?.total_turns ?? 0 },
    { label: "MEMORY", value: stats?.memories ?? 0 },
    { label: "UPTIME", value: uptime >= 3600 ? `${h}:${m}:${sc}` : `${m}:${sc}` },
  ]

  return (
    <div style={{ padding: "10px 14px 6px", flexShrink: 0 }}>
      {/* Connection */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 7,
          marginBottom: 10,
        }}
      >
        <motion.div
          animate={{ opacity: connected ? [1, 0.3, 1] : 1 }}
          transition={
            connected ? { duration: 2.5, repeat: Infinity } : { duration: 0.3 }
          }
          style={{
            width: 6,
            height: 6,
            borderRadius: "50%",
            flexShrink: 0,
            background: connected ? "#00ff88" : "#ff3355",
            boxShadow: connected ? "0 0 7px #00ff88" : "0 0 7px #ff3355",
          }}
        />
        <span
          style={{
            fontFamily: "'Orbitron',monospace",
            fontSize: 8,
            letterSpacing: ".18em",
            color: connected ? "#00ff88" : "#ff3355",
          }}
        >
          {connected ? "BRIDGE CONNECTED" : "BRIDGE OFFLINE"}
        </span>
      </div>

      {/* Stats */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: vertical ? "repeat(2,1fr)" : "repeat(4,1fr)",
          gap: 4,
        }}
      >
        {cells.map(({ label, value }) => (
          <div
            key={label}
            style={{
              background: "rgba(0,22,38,.75)",
              border: "1px solid rgba(0,212,255,.14)",
              borderRadius: 3,
              padding: "5px 7px",
              textAlign: "center",
            }}
          >
            <div
              style={{
                fontFamily: "'Orbitron',monospace",
                fontSize: 7,
                letterSpacing: ".13em",
                color: "rgba(0,170,200,.7)",
                marginBottom: 2,
              }}
            >
              {label}
            </div>
            <div
              style={{
                fontFamily: "'Share Tech Mono',monospace",
                fontSize: 12,
                color: "#00d4ff",
              }}
            >
              {value}
            </div>
          </div>
        ))}
      </div>

      {/* Usage bars */}
      <div style={{ marginTop: 10, display: "flex", flexDirection: "column", gap: 6 }}>
        <UsageBar label="CPU" value={cpuUsage} color="#00d4ff" />
        <UsageBar label="MEM" value={memUsage} color="#00ff88" />
        <UsageBar
          label="I/O"
          value={netThroughput > 0 ? Math.min(100, netThroughput * 25) : 3}
          color="#ff9500"
        />
      </div>
    </div>
  )
}

function UsageBar({ label, value, color }) {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
      <span
        style={{
          fontFamily: "'Orbitron',monospace",
          fontSize: 7,
          letterSpacing: ".1em",
          color: `${color}88`,
          minWidth: 22,
          textAlign: "right",
        }}
      >
        {label}
      </span>
      <div
        style={{
          flex: 1,
          height: 4,
          background: `${color}12`,
          borderRadius: 2,
          overflow: "hidden",
          position: "relative",
        }}
      >
        <motion.div
          animate={{ width: `${value}%` }}
          transition={{ duration: 0.6, ease: "easeOut" }}
          style={{
            height: "100%",
            background: `linear-gradient(90deg, ${color}44, ${color})`,
            borderRadius: 2,
            boxShadow: value > 70 ? `0 0 6px ${color}88` : "none",
          }}
        />
      </div>
      <span
        style={{
          fontFamily: "'Share Tech Mono',monospace",
          fontSize: 8,
          color: `${color}88`,
          minWidth: 24,
          textAlign: "right",
        }}
      >
        {Math.round(value)}%
      </span>
    </div>
  )
}
