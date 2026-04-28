/**
 * src/components/DustField.jsx
 * ─────────────────────────────
 * Canvas-based ambient particle system.
 * ~200 tiny dust motes drift slowly across a pure-black background
 * with soft blue tinting and subtle fade in/out.
 * State-reactive: particles accelerate during THINKING/SPEAKING.
 */

import { useEffect, useRef } from "react"

const PARTICLE_COUNT = 220
const BASE_SPEED = 0.15

export default function DustField({ state = "SLEEPING" }) {
  const canvasRef = useRef(null)
  const particlesRef = useRef(null)
  const frameRef = useRef(null)

  // Initialize particles once
  useEffect(() => {
    const particles = []
    for (let i = 0; i < PARTICLE_COUNT; i++) {
      particles.push({
        x: Math.random() * window.innerWidth,
        y: Math.random() * window.innerHeight,
        vx: (Math.random() - 0.5) * BASE_SPEED,
        vy: (Math.random() - 0.5) * BASE_SPEED,
        size: Math.random() * 1.8 + 0.3,
        alpha: Math.random() * 0.4 + 0.05,
        alphaDir: Math.random() > 0.5 ? 1 : -1,
        // Blue tint variations
        r: Math.floor(Math.random() * 40 + 20),
        g: Math.floor(Math.random() * 80 + 160),
        b: Math.floor(Math.random() * 55 + 200),
        phase: Math.random() * Math.PI * 2,
      })
    }
    particlesRef.current = particles
  }, [])

  useEffect(() => {
    const cv = canvasRef.current
    if (!cv) return

    const ctx = cv.getContext("2d")
    let W = window.innerWidth
    let H = window.innerHeight

    const resize = () => {
      W = window.innerWidth
      H = window.innerHeight
      cv.width = W
      cv.height = H
    }
    resize()
    window.addEventListener("resize", resize)

    const speedMultiplier = () => {
      switch (state) {
        case "THINKING":
          return 3.2
        case "SPEAKING":
          return 2.4
        case "LISTENING":
          return 1.6
        default:
          return 1
      }
    }

    let time = 0

    const draw = () => {
      frameRef.current = requestAnimationFrame(draw)
      time += 0.016

      const particles = particlesRef.current
      if (!particles) return

      ctx.clearRect(0, 0, W, H)

      const spd = speedMultiplier()
      const cx = W / 2
      const cy = H / 2

      for (let i = 0; i < particles.length; i++) {
        const p = particles[i]

        // Drift towards center subtly
        const dx = cx - p.x
        const dy = cy - p.y
        const dist = Math.sqrt(dx * dx + dy * dy)
        const pull = 0.00003 * spd

        p.vx += dx * pull + Math.sin(time * 0.3 + p.phase) * 0.002
        p.vy += dy * pull + Math.cos(time * 0.4 + p.phase) * 0.002

        p.x += p.vx * spd
        p.y += p.vy * spd

        // Dampen
        p.vx *= 0.998
        p.vy *= 0.998

        // Wrap around edges
        if (p.x < -10) p.x = W + 10
        if (p.x > W + 10) p.x = -10
        if (p.y < -10) p.y = H + 10
        if (p.y > H + 10) p.y = -10

        // Breathing alpha
        p.alpha += p.alphaDir * 0.002
        if (p.alpha > 0.5) p.alphaDir = -1
        if (p.alpha < 0.03) p.alphaDir = 1

        // Glow near center
        const centerGlow =
          dist < 300 ? (1 - dist / 300) * 0.3 : 0

        const finalAlpha = Math.min(1, p.alpha + centerGlow)

        ctx.beginPath()
        ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2)
        ctx.fillStyle = `rgba(${p.r},${p.g},${p.b},${finalAlpha})`
        ctx.fill()

        // Tiny glow for larger particles
        if (p.size > 1.2) {
          ctx.beginPath()
          ctx.arc(p.x, p.y, p.size * 2.5, 0, Math.PI * 2)
          ctx.fillStyle = `rgba(${p.r},${p.g},${p.b},${finalAlpha * 0.1})`
          ctx.fill()
        }
      }
    }

    draw()

    return () => {
      if (frameRef.current) cancelAnimationFrame(frameRef.current)
      window.removeEventListener("resize", resize)
    }
  }, [state])

  return (
    <canvas
      ref={canvasRef}
      style={{
        position: "fixed",
        inset: 0,
        width: "100%",
        height: "100%",
        pointerEvents: "none",
        zIndex: 1,
      }}
    />
  )
}
