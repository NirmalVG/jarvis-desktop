/**
 * src/components/UltimateOrb.jsx  (v2 — audio-reactive)
 * ───────────────────────────────────────────────────────
 * Same shader architecture as before, now with:
 *   • uAudio uniform: mic amplitude [0, 1] → extra surface distortion
 *     when the operator speaks, the orb physically reacts to their voice
 *   • uAudio drives bloom intensity and distort additively
 *
 * Usage: just drop in and the hook handles everything.
 *   <UltimateOrb state="SPEAKING" />
 */

import { useRef, useMemo } from "react"
import { Canvas, useFrame, extend } from "@react-three/fiber"
import { shaderMaterial } from "@react-three/drei"
import * as THREE from "three"
import { AnimatePresence, motion } from "framer-motion"
import { useAudioReactive } from "../hooks/useAudioReactive"

// ─── Simplex noise GLSL (unchanged) ──────────────────────────────────────────
const SIMPLEX_3D = /* glsl */ `
vec3 mod289v3(vec3 x){return x-floor(x*(1./289.))*289.;}
vec4 mod289v4(vec4 x){return x-floor(x*(1./289.))*289.;}
vec4 permute4(vec4 x){return mod289v4(((x*34.)+1.)*x);}
vec4 taylorInvSqrt(vec4 r){return 1.7928429-0.8537347*r;}
float snoise(vec3 v){
  const vec2 C=vec2(1./6.,1./3.);
  const vec4 D=vec4(0.,.5,1.,2.);
  vec3 i=floor(v+dot(v,C.yyy));
  vec3 x0=v-i+dot(i,C.xxx);
  vec3 g=step(x0.yzx,x0.xyz);
  vec3 l=1.-g;
  vec3 i1=min(g.xyz,l.zxy);
  vec3 i2=max(g.xyz,l.zxy);
  vec3 x1=x0-i1+C.xxx;
  vec3 x2=x0-i2+C.yyy;
  vec3 x3=x0-D.yyy;
  i=mod289v3(i);
  vec4 p=permute4(permute4(permute4(
    i.z+vec4(0.,i1.z,i2.z,1.))
    +i.y+vec4(0.,i1.y,i2.y,1.))
    +i.x+vec4(0.,i1.x,i2.x,1.));
  float n_=.142857142857;
  vec3 ns=n_*D.wyz-D.xzx;
  vec4 j=p-49.*floor(p*ns.z*ns.z);
  vec4 x_=floor(j*ns.z);
  vec4 y_=floor(j-7.*x_);
  vec4 x=x_*ns.x+ns.yyyy;
  vec4 y=y_*ns.x+ns.yyyy;
  vec4 h=1.-abs(x)-abs(y);
  vec4 b0=vec4(x.xy,y.xy);
  vec4 b1=vec4(x.zw,y.zw);
  vec4 s0=floor(b0)*2.+1.;
  vec4 s1=floor(b1)*2.+1.;
  vec4 sh=-step(h,vec4(0.));
  vec4 a0=b0.xzyw+s0.xzyw*sh.xxyy;
  vec4 a1=b1.xzyw+s1.xzyw*sh.zzww;
  vec3 p0=vec3(a0.xy,h.x);
  vec3 p1=vec3(a0.zw,h.y);
  vec3 p2=vec3(a1.xy,h.z);
  vec3 p3=vec3(a1.zw,h.w);
  vec4 norm=taylorInvSqrt(vec4(dot(p0,p0),dot(p1,p1),dot(p2,p2),dot(p3,p3)));
  p0*=norm.x;p1*=norm.y;p2*=norm.z;p3*=norm.w;
  vec4 m=max(.6-vec4(dot(x0,x0),dot(x1,x1),dot(x2,x2),dot(x3,x3)),0.);
  m=m*m;
  return 42.*dot(m*m,vec4(dot(p0,x0),dot(p1,x1),dot(p2,x2),dot(p3,x3)));
}`

// ─── Vertex shader (now with uAudio) ─────────────────────────────────────────
const vertexShader = /* glsl */ `
  ${SIMPLEX_3D}
  uniform float uTime;
  uniform float uDistort;
  uniform float uSpeed;
  uniform float uAudio;   // NEW: mic amplitude [0,1]

  varying vec3 vNormal;
  varying vec3 vPosition;
  varying vec3 vWorldPos;

  void main() {
    vNormal = normalize(normalMatrix * normal);
    float t  = uTime * uSpeed;
    float n1 = snoise(position * 1.4 + t * 0.35);
    float n2 = snoise(position * 3.2 - t * 0.25);
    float n3 = snoise(position * 7.0 + t * 0.60);

    // Audio reactivity: mic amplitude adds extra surface chaos
    // TEACH: uAudio is 0 at silence, ~0.5 at normal speech, ~1.0 at shouting
    // We add it to distort so the surface literally ripples with your voice.
    float audioBoost = uAudio * 0.35;
    float displacement = (n1 * 0.55 + n2 * 0.30 + n3 * 0.15) * (uDistort + audioBoost);

    // High-frequency audio spike: sharp surface pops when a consonant fires
    float spike = snoise(position * 18.0 + t * 4.0) * uAudio * 0.12;
    displacement += spike;

    vec3 displaced = position + normal * displacement;
    vPosition = displaced;
    vWorldPos = (modelMatrix * vec4(displaced, 1.0)).xyz;
    gl_Position = projectionMatrix * modelViewMatrix * vec4(displaced, 1.0);
  }
`

// ─── Fragment shader (audio brightens energy veins) ───────────────────────────
const fragmentShader = /* glsl */ `
  ${SIMPLEX_3D}
  uniform float uTime;
  uniform float uSpeed;
  uniform vec3  uColorA;
  uniform vec3  uColorB;
  uniform float uIntensity;
  uniform float uAudio;

  varying vec3 vNormal;
  varying vec3 vPosition;
  varying vec3 vWorldPos;

  void main() {
    vec3 viewDir = normalize(cameraPosition - vWorldPos);
    float NdotV  = max(dot(normalize(vNormal), viewDir), 0.0);
    float fresnel = pow(1.0 - NdotV, 3.0);

    float t  = uTime * uSpeed;
    float p1 = snoise(vPosition * 1.8 + t * 0.45) * 0.5 + 0.5;
    float p2 = snoise(vPosition * 4.5 - t * 0.55) * 0.5 + 0.5;
    float p3 = snoise(vPosition * 9.0 + t * 1.10) * 0.5 + 0.5;
    float plasma = p1 * 0.50 + p2 * 0.32 + p3 * 0.18;

    // Audio amplifies the energy veins — voice makes the orb "crack" with light
    float veins = pow(p2, 5.0) * (4.0 + uAudio * 6.0);

    vec3 col = mix(uColorA, uColorB, plasma);
    col += uColorB * fresnel * 3.5 * (uIntensity + uAudio * 0.8);
    col += uColorB * veins   * 1.2 *  uIntensity;

    float core = 1.0 - clamp(length(vPosition) * 0.9, 0.0, 1.0);
    col += uColorB * core * (0.25 + uAudio * 0.4) * uIntensity;

    float alpha = 0.88 + fresnel * 0.12;
    gl_FragColor = vec4(col, alpha);
  }
`

const PlasmaMaterial = shaderMaterial(
  {
    uTime: 0,
    uDistort: 0.08,
    uSpeed: 0.3,
    uColorA: new THREE.Color("#040d18"),
    uColorB: new THREE.Color("#00d4ff"),
    uIntensity: 0.5,
    uAudio: 0, // NEW
  },
  vertexShader,
  fragmentShader,
)

extend({ PlasmaMaterial })

// ─── State config ─────────────────────────────────────────────────────────────
// All states use blue palette to match the Jarvis design.
// Speed/intensity/distort still vary per state for dynamism.
const S = {
  SLEEPING: {
    colorA: "#030b16",
    colorB: "#00c8f0",
    ring: "#1a4466",
    label: "STANDBY",
    speed: 0.22,
    distort: 0.055,
    intensity: 0.38,
    bloom: 0.7,
    aberration: 0.0008,
    particleSpd: 0.12,
    particleAlpha: 0.25,
    ringSpd: 0.004,
  },
  LISTENING: {
    colorA: "#002040",
    colorB: "#00d4ff",
    ring: "#00b8e0",
    label: "LISTENING",
    speed: 1.6,
    distort: 0.24,
    intensity: 0.9,
    bloom: 1.5,
    aberration: 0.0016,
    particleSpd: 0.85,
    particleAlpha: 0.65,
    ringSpd: 0.01,
  },
  THINKING: {
    colorA: "#001830",
    colorB: "#00aaff",
    ring: "#0088cc",
    label: "PROCESSING",
    speed: 3.2,
    distort: 0.42,
    intensity: 1.25,
    bloom: 2.2,
    aberration: 0.003,
    particleSpd: 2.1,
    particleAlpha: 0.85,
    ringSpd: 0.022,
  },
  SPEAKING: {
    colorA: "#001428",
    colorB: "#00eeff",
    ring: "#00ccee",
    label: "RESPONDING",
    speed: 4.5,
    distort: 0.52,
    intensity: 1.45,
    bloom: 2.8,
    aberration: 0.0014,
    particleSpd: 2.8,
    particleAlpha: 1.0,
    ringSpd: 0.018,
  },
}

const lerp = (a, b, t) => a + (b - a) * t

// ─── PlasmaSphere ─────────────────────────────────────────────────────────────
function PlasmaSphere({ state, amplitude }) {
  const matRef = useRef()
  const vals = useRef({
    speed: S.SLEEPING.speed,
    distort: S.SLEEPING.distort,
    intensity: S.SLEEPING.intensity,
    colorA: new THREE.Color(S.SLEEPING.colorA),
    colorB: new THREE.Color(S.SLEEPING.colorB),
  })

  useFrame(({ clock }) => {
    if (!matRef.current) return
    const cfg = S[state] || S.SLEEPING
    const v = vals.current

    v.speed = lerp(v.speed, cfg.speed, 0.035)
    v.distort = lerp(v.distort, cfg.distort, 0.035)
    v.intensity = lerp(v.intensity, cfg.intensity, 0.04)
    v.colorA.lerp(new THREE.Color(cfg.colorA), 0.035)
    v.colorB.lerp(new THREE.Color(cfg.colorB), 0.04)

    const m = matRef.current
    m.uTime = clock.getElapsedTime()
    m.uSpeed = v.speed
    m.uDistort = v.distort
    m.uIntensity = v.intensity
    m.uColorA.copy(v.colorA)
    m.uColorB.copy(v.colorB)
    m.uAudio = amplitude // ← live mic amplitude every frame
  })

  return (
    <mesh>
      <sphereGeometry args={[1, 128, 128]} />
      <plasmaMaterial
        ref={matRef}
        transparent
        depthWrite={false}
        side={THREE.FrontSide}
      />
    </mesh>
  )
}

// ─── InnerCore ────────────────────────────────────────────────────────────────
function InnerCore({ state, amplitude }) {
  const ref = useRef()
  const col = useRef(new THREE.Color(S.SLEEPING.colorB))

  useFrame(({ clock }) => {
    if (!ref.current) return
    const t = clock.getElapsedTime()
    const cfg = S[state] || S.SLEEPING

    col.current.lerp(new THREE.Color(cfg.colorB), 0.05)
    ref.current.material.color.copy(col.current)
    ref.current.material.emissive.copy(col.current)

    const freq = cfg.speed * 0.6
    const amp = state === "SLEEPING" ? 0.04 : 0.14
    // Audio makes the core "jump" with each word spoken
    const audioScale = amplitude * 0.25
    const s = 0.32 + Math.sin(t * freq) * amp + audioScale
    ref.current.scale.setScalar(s)

    const emi =
      state === "SLEEPING"
        ? 0.6
        : 1.8 + Math.sin(t * freq * 1.5) * 0.8 + amplitude * 1.5
    ref.current.material.emissiveIntensity = emi
  })

  return (
    <mesh ref={ref}>
      <sphereGeometry args={[1, 24, 24]} />
      <meshStandardMaterial
        color={S.SLEEPING.colorB}
        emissive={S.SLEEPING.colorB}
        emissiveIntensity={0.8}
        roughness={0}
        metalness={0.3}
        transparent
        opacity={0.9}
      />
    </mesh>
  )
}

// ─── WireShell ────────────────────────────────────────────────────────────────
function WireShell({ state }) {
  const ref = useRef()
  const col = useRef(new THREE.Color(S.SLEEPING.ring))

  useFrame(({ clock }) => {
    if (!ref.current) return
    const t = clock.getElapsedTime()
    const cfg = S[state] || S.SLEEPING

    col.current.lerp(new THREE.Color(cfg.ring), 0.04)
    ref.current.material.color.copy(col.current)

    const dir = state === "THINKING" ? -1 : 1
    ref.current.rotation.y += 0.004 * dir * (cfg.speed / 3.2)
    ref.current.rotation.x += 0.002

    ref.current.material.opacity =
      state === "SLEEPING"
        ? 0.04 + Math.sin(t * 0.6) * 0.015
        : 0.09 + Math.sin(t * cfg.speed * 0.4) * 0.04
  })

  return (
    <mesh ref={ref}>
      <icosahedronGeometry args={[1.08, 2]} />
      <meshBasicMaterial wireframe transparent opacity={0.06} />
    </mesh>
  )
}

// ─── EnergyRings ─────────────────────────────────────────────────────────────
const RING_DEFS = [
  { radius: 1.38, tube: 0.008, rotX: 0.45, rotY: 0.0, rotZ: 0.0, spinDir: 1 },
  { radius: 1.62, tube: 0.006, rotX: 1.4, rotY: 0.9, rotZ: 0.0, spinDir: -1 },
  { radius: 1.85, tube: 0.005, rotX: 2.3, rotY: 0.0, rotZ: 0.6, spinDir: 1 },
  { radius: 2.1, tube: 0.004, rotX: 0.2, rotY: 1.55, rotZ: 1.1, spinDir: -1 },
]

function SingleRing({ state, radius, tube, rotX, rotY, rotZ, spinDir }) {
  const ref = useRef()
  const col = useRef(new THREE.Color(S.SLEEPING.ring))

  useFrame(({ clock }) => {
    if (!ref.current) return
    const t = clock.getElapsedTime()
    const cfg = S[state] || S.SLEEPING

    col.current.lerp(new THREE.Color(cfg.ring), 0.04)
    ref.current.material.color.copy(col.current)
    ref.current.rotation.z += spinDir * cfg.ringSpd

    if (state === "LISTENING") {
      const s = 1 + Math.abs(Math.sin(t * 2.2)) * 0.06
      ref.current.scale.setScalar(s)
    } else {
      ref.current.scale.setScalar(1)
    }

    const baseAlpha = state === "SLEEPING" ? 0.2 : 0.55
    ref.current.material.opacity = baseAlpha + Math.sin(t * 1.4) * 0.1
  })

  return (
    <mesh ref={ref} rotation={[rotX, rotY, rotZ]}>
      <torusGeometry args={[radius, tube, 8, 180]} />
      <meshBasicMaterial transparent opacity={0.35} />
    </mesh>
  )
}

function EnergyRings({ state }) {
  return (
    <>
      {RING_DEFS.map((r, i) => (
        <SingleRing key={i} state={state} {...r} />
      ))}
    </>
  )
}

// ─── ParticleField ────────────────────────────────────────────────────────────
const PARTICLE_COUNT = 2500

function ParticleField({ state, amplitude }) {
  const ref = useRef()
  const col = useRef(new THREE.Color(S.SLEEPING.ring))

  const { positions } = useMemo(() => {
    const pos = new Float32Array(PARTICLE_COUNT * 3)
    for (let i = 0; i < PARTICLE_COUNT; i++) {
      const r = 1.5 + Math.random() * 2.2
      const theta = Math.random() * Math.PI * 2
      const phi = Math.acos(2 * Math.random() - 1)
      pos[i * 3] = r * Math.sin(phi) * Math.cos(theta)
      pos[i * 3 + 1] = r * Math.sin(phi) * Math.sin(theta)
      pos[i * 3 + 2] = r * Math.cos(phi)
    }
    return { positions: pos }
  }, [])

  useFrame(({ clock }) => {
    if (!ref.current) return
    const t = clock.getElapsedTime()
    const cfg = S[state] || S.SLEEPING

    col.current.lerp(new THREE.Color(cfg.ring), 0.04)
    ref.current.material.color.copy(col.current)

    // Audio makes particles speed up with the voice
    const spd = cfg.particleSpd + amplitude * 3.0
    ref.current.rotation.y += 0.0015 * spd
    ref.current.rotation.x += 0.0004 * spd

    ref.current.material.opacity =
      cfg.particleAlpha * (0.6 + Math.sin(t * 0.8) * 0.2)
    ref.current.material.size =
      state === "SPEAKING"
        ? 0.03 + Math.sin(t * 7) * 0.008 + amplitude * 0.015
        : state === "THINKING"
          ? 0.025
          : 0.02
  })

  return (
    <points ref={ref}>
      <bufferGeometry>
        {/* FIXED: correct R3F v8 bufferAttribute API */}
        <bufferAttribute attach="attributes-position" args={[positions, 3]} />
      </bufferGeometry>
      <pointsMaterial
        size={0.02}
        transparent
        opacity={0.25}
        sizeAttenuation
        depthWrite={false}
      />
    </points>
  )
}

// ─── ScanBeam ─────────────────────────────────────────────────────────────────
function ScanBeam({ state }) {
  const ref = useRef()
  const active = state === "LISTENING" || state === "THINKING"

  useFrame(({ clock }) => {
    if (!ref.current) return
    const t = clock.getElapsedTime()
    ref.current.position.y = Math.sin(t * 1.3) * 1.2
    ref.current.material.opacity = active ? 0.18 + Math.sin(t * 3) * 0.06 : 0
  })

  return (
    <mesh ref={ref} rotation={[Math.PI / 2, 0, 0]}>
      <cylinderGeometry args={[1.8, 1.8, 0.012, 64, 1, true]} />
      <meshBasicMaterial
        color={state === "THINKING" ? "#ff9500" : "#00d4ff"}
        transparent
        opacity={0}
        side={THREE.DoubleSide}
        depthWrite={false}
      />
    </mesh>
  )
}

// ─── Lighting ─────────────────────────────────────────────────────────────────
function Lighting({ state }) {
  const cfg = S[state] || S.SLEEPING
  return (
    <>
      <ambientLight color="#08192a" intensity={1.0} />
      <pointLight
        color={cfg.colorB}
        intensity={3.5}
        position={[2, 2, 3]}
        distance={14}
      />
      <pointLight
        color="#ff6600"
        intensity={0.6}
        position={[-2, -1.5, -2]}
        distance={10}
      />
      <pointLight
        color={cfg.ring}
        intensity={0.8}
        position={[0, -3, 1]}
        distance={8}
      />
    </>
  )
}

// ─── Scene ────────────────────────────────────────────────────────────────────
function SceneContent({ state, amplitude }) {
  return (
    <>
      <Lighting state={state} />
      <InnerCore state={state} amplitude={amplitude} />
      <PlasmaSphere state={state} amplitude={amplitude} />
      <WireShell state={state} />
      <EnergyRings state={state} />
      <ParticleField state={state} amplitude={amplitude} />
      <ScanBeam state={state} />
    </>
  )
}

// ─── State label ──────────────────────────────────────────────────────────────
function StateLabel({ state }) {
  const cfg = S[state] || S.SLEEPING
  return (
    <AnimatePresence mode="wait">
      <motion.div
        key={state}
        initial={{ opacity: 0, y: 5, letterSpacing: "0.4em" }}
        animate={{ opacity: 1, y: 0, letterSpacing: "0.24em" }}
        exit={{ opacity: 0, y: -5 }}
        transition={{ duration: 0.3 }}
        style={{
          position: "absolute",
          bottom: 4,
          left: "50%",
          transform: "translateX(-50%)",
          fontFamily: "'Orbitron', monospace",
          fontSize: 10,
          fontWeight: 700,
          letterSpacing: "0.24em",
          color: cfg.ring,
          whiteSpace: "nowrap",
          textShadow: `0 0 16px ${cfg.ring}cc, 0 0 32px ${cfg.ring}66`,
        }}
      >
        {cfg.label}
      </motion.div>
    </AnimatePresence>
  )
}

// ─── Public component ─────────────────────────────────────────────────────────
export default function UltimateOrb({ state = "SLEEPING", size = 300 }) {
  // useAudioReactive hooks into the mic and returns normalised amplitude.
  // It's zero when mic is off or permission denied — orb just uses shader defaults.
  const amplitude = useAudioReactive(state)

  return (
    <div
      style={{
        position: "relative",
        width: size,
        height: size,
        flexShrink: 0,
        overflow: "visible",
      }}
    >
      <Canvas
        style={{ width: "100%", height: "100%", background: "transparent" }}
        camera={{ position: [0, 0, 4.8], fov: 48 }}
        gl={{
          antialias: true,
          alpha: true,
          premultipliedAlpha: false,
          toneMapping: THREE.ACESFilmicToneMapping,
          toneMappingExposure: 1.2,
        }}
        onCreated={({ gl }) => gl.setClearAlpha(0)}
        dpr={[1, 2]}
      >
        <SceneContent state={state} amplitude={amplitude} />
      </Canvas>

      <StateLabel state={state} />
    </div>
  )
}
