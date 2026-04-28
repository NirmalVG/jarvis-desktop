/**
 * src/components/OrbZone.jsx
 * ────────────────────────────
 * Container for the central orb. Positioned absolutely in the centre
 * of the viewport. Large, free-floating with no brackets.
 */

import UltimateOrb from "./UltimateOrb"

export default function OrbZone({ state }) {
  return (
    <div
      style={{
        position: "fixed",
        inset: 0,
        width: "100vw",
        height: "100vh",
        zIndex: 10,
        pointerEvents: "none",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
      }}
    >
      <UltimateOrb state={state} size="min(62vmin, 560px)" />
    </div>
  )
}
