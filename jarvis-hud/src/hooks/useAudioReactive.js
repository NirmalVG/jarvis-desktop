/**
 * src/hooks/useAudioReactive.js
 * ──────────────────────────────
 * Reads the microphone via Web Audio API and returns a normalised
 * amplitude value [0, 1] each animation frame.
 *
 * This value is passed as a shader uniform so the orb BREATHES with
 * the operator's voice — exactly like in the Iron Man films.
 *
 * TEACH: Web Audio API overview
 * ─────────────────────────────
 * The browser gives us a low-level audio graph:
 *
 *   Microphone → MediaStream → AudioContext → AnalyserNode
 *                                                  ↓
 *                                          getByteTimeDomainData()
 *                                          → 256 uint8 samples each call
 *                                          → average RMS = "loudness"
 *
 * We don't record anything — we just read the amplitude.
 * The data is never sent anywhere; it stays on the GPU as a uniform.
 *
 * Usage:
 *   const amplitude = useAudioReactive(state)
 *   // amplitude ∈ [0, 1], updates at animation frame rate
 *
 * Returns 0 when mic is unavailable or permission is denied.
 */

import { useEffect, useRef, useState } from "react"

// FFT size: 256 gives us 128 frequency bins.
// Larger = more detail but more CPU. 256 is ideal for a smooth amplitude.
const FFT_SIZE = 256

export function useAudioReactive(state) {
  const [amplitude, setAmplitude] = useState(0)
  const rafRef = useRef(null)
  const analyserRef = useRef(null)
  const streamRef = useRef(null)
  const contextRef = useRef(null)
  const dataRef = useRef(new Uint8Array(FFT_SIZE))

  useEffect(() => {
    // Only spin up the microphone in states where we're listening
    // or speaking (voice is active).  Sleep mode = mic off.
    const shouldListen = state === "LISTENING" || state === "SPEAKING"

    if (!shouldListen) {
      // Clean up if we were running
      cleanup()
      setAmplitude(0)
      return
    }

    let mounted = true

    const init = async () => {
      try {
        // Request microphone permission
        const stream = await navigator.mediaDevices.getUserMedia({
          audio: { echoCancellation: true, noiseSuppression: true },
          video: false,
        })

        if (!mounted) {
          stream.getTracks().forEach((t) => t.stop())
          return
        }

        streamRef.current = stream

        // Build the audio graph
        const ctx = new (window.AudioContext || window.webkitAudioContext)()
        contextRef.current = ctx

        const source = ctx.createMediaStreamSource(stream)
        const analyser = ctx.createAnalyser()
        analyser.fftSize = FFT_SIZE
        analyser.smoothingTimeConstant = 0.75 // smooths rapid amplitude spikes

        source.connect(analyser)
        analyserRef.current = analyser
        dataRef.current = new Uint8Array(analyser.frequencyBinCount)

        // Animation loop — reads amplitude every frame
        const tick = () => {
          if (!analyserRef.current || !mounted) return
          rafRef.current = requestAnimationFrame(tick)

          analyserRef.current.getByteTimeDomainData(dataRef.current)

          // RMS (Root Mean Square) is the perceptually correct loudness measure
          // TEACH: RMS = √( Σ(sample²) / N )
          // uint8 samples are centred at 128 (silence = 128, not 0)
          let sumSq = 0
          const buf = dataRef.current
          for (let i = 0; i < buf.length; i++) {
            const norm = (buf[i] - 128) / 128 // → [-1, 1]
            sumSq += norm * norm
          }
          const rms = Math.sqrt(sumSq / buf.length)

          // Amplify and clamp — raw RMS from speech is typically 0.01–0.15
          const amp = Math.min(1, rms * 6)

          if (mounted) setAmplitude(amp)
        }

        tick()
      } catch (err) {
        // Permission denied or no mic — silently degrade
        console.warn("[AudioReactive] Mic unavailable:", err.message)
        if (mounted) setAmplitude(0)
      }
    }

    init()

    return () => {
      mounted = false
      cleanup()
    }
  }, [state])

  const cleanup = () => {
    if (rafRef.current) {
      cancelAnimationFrame(rafRef.current)
      rafRef.current = null
    }
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((t) => t.stop())
      streamRef.current = null
    }
    if (contextRef.current) {
      contextRef.current.close().catch(() => {})
      contextRef.current = null
    }
    analyserRef.current = null
  }

  return amplitude
}
