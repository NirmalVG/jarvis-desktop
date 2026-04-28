/**
 * electron/preload.js
 * Exposes a safe, typed API from main process to renderer via contextBridge.
 */

const { contextBridge, ipcRenderer } = require("electron")

contextBridge.exposeInMainWorld("jarvis", {
  // Renderer → Main
  toggleClickthrough: () => ipcRenderer.send("toggle-clickthrough"),
  toggleFullscreen: () => ipcRenderer.send("toggle-fullscreen"),
  minimizeHud: () => ipcRenderer.send("minimize-hud"),
  quit: () => ipcRenderer.send("quit"),

  // Main → Renderer (event subscriptions)
  onState: (cb) => ipcRenderer.on("jarvis-state", (_, d) => cb(d)),
  onConnection: (cb) => ipcRenderer.on("connection-status", (_, d) => cb(d)),
  onClickthrough: (cb) =>
    ipcRenderer.on("clickthrough-status", (_, d) => cb(d)),

  // Cleanup
  removeAllListeners: (channel) => ipcRenderer.removeAllListeners(channel),
})
