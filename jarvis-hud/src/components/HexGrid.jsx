/**
 * src/components/HexGrid.jsx
 * ─────────────────────────────
 * Subtle circular vortex / swirl pattern radiating from the centre.
 * Replaces the old hex grid to match the dark Jarvis design.
 * Draws faint concentric circles and radial lines that rotate slowly.
 */

import { useEffect, useRef } from "react"

export default function HexGrid({ state, fullscreen }) {
  const ref = useRef(null)
  const frameRef = useRef(null)
  const timeRef = useRef(0)

  useEffect(() => {
    const cv = ref.current
    if (!cv) return

    const ctx = cv.getContext("2d")

    const draw = () => {
      timeRef.current += 0.003

      const W = fullscreen ? window.innerWidth : 420
      const H = fullscreen ? window.innerHeight : 700

      cv.width = W
      cv.height = H

      const cx = W * 0.55
      const cy = H * 0.5
      const t = timeRef.current

      // Speed factor based on state
      const speedFactor =
        state === "THINKING"
          ? 2.5
          : state === "SPEAKING"
            ? 1.8
            : state === "LISTENING"
              ? 1.3
              : 1

      ctx.clearRect(0, 0, W, H)

      // ── Concentric circles (vortex rings) ─────────────────────────────
      const maxRadius = Math.max(W, H) * 0.7
      const ringCount = 25

      for (let i = 0; i < ringCount; i++) {
        const radius = (i / ringCount) * maxRadius + 30
        const alpha = Math.max(0, 0.02 + (1 - i / ringCount) * 0.04)
        const wobble = Math.sin(t * speedFactor * 2 + i * 0.5) * 3

        ctx.beginPath()
        ctx.arc(cx, cy, radius + wobble, 0, Math.PI * 2)
        ctx.strokeStyle = `rgba(0,180,240,${alpha})`
        ctx.lineWidth = 0.5
        ctx.stroke()
      }

      // ── Radial lines (subtle, rotating) ───────────────────────────────
      const lineCount = 36
      for (let i = 0; i < lineCount; i++) {
        const angle = (i / lineCount) * Math.PI * 2 + t * speedFactor * 0.5
        const innerR = 60
        const outerR = maxRadius * 0.8
        const alpha = 0.015 + Math.sin(t + i * 0.8) * 0.008

        ctx.beginPath()
        ctx.moveTo(cx + Math.cos(angle) * innerR, cy + Math.sin(angle) * innerR)
        ctx.lineTo(cx + Math.cos(angle) * outerR, cy + Math.sin(angle) * outerR)
        ctx.strokeStyle = `rgba(0,180,240,${alpha})`
        ctx.lineWidth = 0.3
        ctx.stroke()
      }

      // ── Spiral arms (very faint) ──────────────────────────────────────
      for (let arm = 0; arm < 3; arm++) {
        const armOffset = (arm / 3) * Math.PI * 2
        ctx.beginPath()
        for (let s = 0; s < 300; s++) {
          const angle = armOffset + s * 0.04 + t * speedFactor * 0.3
          const radius = s * 1.5 + 40
          const x = cx + Math.cos(angle) * radius
          const y = cy + Math.sin(angle) * radius

          if (s === 0) ctx.moveTo(x, y)
          else ctx.lineTo(x, y)
        }
        ctx.strokeStyle = `rgba(0,160,220,0.018)`
        ctx.lineWidth = 1
        ctx.stroke()
      }

      frameRef.current = requestAnimationFrame(draw)
    }

    draw()

    return () => {
      if (frameRef.current) cancelAnimationFrame(frameRef.current)
    }
  }, [state, fullscreen])

  return (
    <canvas
      ref={ref}
      style={{
        position: "fixed",
        inset: 0,
        width: "100%",
        height: "100%",
        pointerEvents: "none",
        zIndex: 0,
      }}
    />
  )
}
