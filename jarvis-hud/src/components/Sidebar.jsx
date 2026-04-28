/**
 * src/components/Sidebar.jsx
 * ──────────────────────────
 * Thin vertical navigation bar on the far left edge.
 * Matches the Jarvis design with icon buttons and active states.
 */

import { useState } from "react"

const NAV_ITEMS = [
  { id: "home", icon: "✦", label: "Home", active: true },
  { id: "ai", icon: "⬡", label: "AI Core" },
  { id: "target", icon: "◎", label: "Systems" },
  { id: "shield", icon: "◈", label: "Security" },
]

export default function Sidebar({ acc = "#00d4ff" }) {
  const [activeId, setActiveId] = useState("home")

  return (
    <div
      style={{
        position: "fixed",
        left: 0,
        top: 44,
        bottom: 0,
        width: 52,
        background: "rgba(2,5,12,0.85)",
        borderRight: `1px solid ${acc}12`,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        paddingTop: 16,
        paddingBottom: 16,
        zIndex: 80,
        backdropFilter: "blur(6px)",
      }}
    >
      {/* Nav icons */}
      <div
        style={{
          display: "flex",
          flexDirection: "column",
          gap: 6,
          flex: 1,
        }}
      >
        {NAV_ITEMS.map((item) => {
          const isActive = activeId === item.id
          return (
            <SidebarIcon
              key={item.id}
              icon={item.icon}
              label={item.label}
              active={isActive}
              acc={acc}
              onClick={() => setActiveId(item.id)}
            />
          )
        })}
      </div>

      {/* Bottom exit icon */}
      <SidebarIcon
        icon="⊳"
        label="Exit"
        acc={acc}
        active={false}
        onClick={() => window.jarvis?.quit?.()}
        bottom
      />
    </div>
  )
}

function SidebarIcon({ icon, label, active, acc, onClick, bottom }) {
  const [hover, setHover] = useState(false)

  return (
    <button
      title={label}
      onClick={onClick}
      onMouseEnter={() => setHover(true)}
      onMouseLeave={() => setHover(false)}
      style={{
        width: 36,
        height: 36,
        background: active
          ? `${acc}18`
          : hover
            ? `${acc}0a`
            : "transparent",
        border: active
          ? `1px solid ${acc}44`
          : `1px solid transparent`,
        borderRadius: 8,
        color: active ? acc : hover ? `${acc}88` : `${acc}44`,
        fontSize: 16,
        cursor: "pointer",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        fontFamily: "'Share Tech Mono', monospace",
        transition: "all .2s ease",
        boxShadow: active ? `0 0 12px ${acc}22, inset 0 0 8px ${acc}08` : "none",
        position: "relative",
      }}
    >
      {/* Active indicator bar */}
      {active && (
        <div
          style={{
            position: "absolute",
            left: -8,
            top: "50%",
            transform: "translateY(-50%)",
            width: 3,
            height: 20,
            borderRadius: "0 2px 2px 0",
            background: acc,
            boxShadow: `0 0 8px ${acc}`,
          }}
        />
      )}
      {icon}
    </button>
  )
}
