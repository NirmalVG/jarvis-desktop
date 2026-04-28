/**
 * src/components/DustField.jsx
 * ─────────────────────────────
 * Canvas-based ambient particle system.
 * Tiny star-like motes drift across the entire viewport
 * with subtle depth variation and no center pull.
 * State-reactive: particles accelerate during THINKING/SPEAKING.
 */

import { useEffect, useRef } from "react"

const PARTICLE_COUNT = 360
const BASE_SPEED = 0.22

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
        vx: (Math.random() * 0.7 + 0.25) * BASE_SPEED,
        vy: (Math.random() - 0.5) * BASE_SPEED * 0.35,
        depth: Math.random() * 0.8 + 0.35,
        size: Math.random() * 1.2 + 0.35,
        alpha: Math.random() * 0.45 + 0.12,
        alphaDir: Math.random() > 0.5 ? 1 : -1,
        r: Math.floor(Math.random() * 55 + 170),
        g: Math.floor(Math.random() * 45 + 205),
        b: Math.floor(Math.random() * 35 + 220),
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

      for (let i = 0; i < particles.length; i++) {
        const p = particles[i]

        p.x += (p.vx + Math.sin(time * 0.22 + p.phase) * 0.015) * spd * p.depth
        p.y += (p.vy + Math.cos(time * 0.18 + p.phase) * 0.01) * spd * p.depth

        // Wrap around edges
        if (p.x < -10) p.x = W + 10
        if (p.x > W + 10) p.x = -10
        if (p.y < -10) p.y = H + 10
        if (p.y > H + 10) p.y = -10

        // Breathing alpha
        p.alpha += p.alphaDir * 0.0015
        if (p.alpha > 0.6) p.alphaDir = -1
        if (p.alpha < 0.08) p.alphaDir = 1

        const twinkle = Math.sin(time * (0.8 + p.depth) + p.phase) * 0.08
        const finalAlpha = Math.max(0.04, Math.min(0.75, p.alpha + twinkle))
        const finalSize = p.size * p.depth

        ctx.beginPath()
        ctx.arc(p.x, p.y, finalSize, 0, Math.PI * 2)
        ctx.fillStyle = `rgba(${p.r},${p.g},${p.b},${finalAlpha})`
        ctx.fill()

        // Tiny star glow for brighter foreground particles
        if (finalSize > 1.0) {
          ctx.beginPath()
          ctx.arc(p.x, p.y, finalSize * 2.2, 0, Math.PI * 2)
          ctx.fillStyle = `rgba(${p.r},${p.g},${p.b},${finalAlpha * 0.08})`
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
