const {
  app,
  BrowserWindow,
  ipcMain,
  Tray,
  Menu,
  nativeImage,
  screen,
  globalShortcut,
} = require("electron")
const path = require("path")

let WebSocket
try {
  WebSocket = require("ws")
} catch (_) {
  console.error("[Electron] 'ws' package not found. Run: npm install ws")
}

const isDev = !app.isPackaged
const WS_PORT = 6789

let mainWindow = null
let tray = null
let wsClient = null
let clickThrough = true

const gotSingleInstanceLock = app.requestSingleInstanceLock()

if (!gotSingleInstanceLock) {
  app.quit()
}

function enableLaunchAtLogin() {
  if (isDev) {
    return
  }

  try {
    app.setLoginItemSettings({
      openAtLogin: true,
      openAsHidden: false,
      name: "Jarvis HUD",
    })
  } catch (error) {
    console.warn("[Electron] Failed to enable launch at login:", error.message)
  }
}

function createWindow() {
  const { width, height } = screen.getPrimaryDisplay().workAreaSize

  mainWindow = new BrowserWindow({
    width,
    height,
    x: 0,
    y: 0,
    transparent: true,
    frame: false,
    alwaysOnTop: true,
    skipTaskbar: false,
    resizable: false,
    hasShadow: false,
    backgroundColor: "#00000000",
    webPreferences: {
      preload: path.join(__dirname, "preload.js"),
      contextIsolation: true,
      nodeIntegration: false,
    },
  })

  mainWindow.maximize()
  mainWindow.setVisibleOnAllWorkspaces(true, { visibleOnFullScreen: true })
  mainWindow.setIgnoreMouseEvents(true, { forward: true })

  if (isDev) {
    mainWindow.loadURL("http://localhost:5173")
  } else {
    mainWindow.loadFile(path.join(__dirname, "../dist/index.html"))
  }

  mainWindow.webContents.on("did-finish-load", () => {
    sendToRenderer("clickthrough-status", { active: clickThrough })
  })

  connectToPythonBridge()
}

function connectToPythonBridge() {
  if (!WebSocket) return

  const tryConnect = () => {
    wsClient = new WebSocket(`ws://localhost:${WS_PORT}`)
    wsClient.on("open", () =>
      sendToRenderer("connection-status", { connected: true }),
    )
    wsClient.on("message", (data) => {
      try {
        const msg = JSON.parse(data.toString())
        if (msg.type === "system_info") {
          sendToRenderer("system-info", msg)
        } else {
          sendToRenderer("jarvis-state", msg)
        }
      } catch (_) {}
    })
    wsClient.on("close", () => {
      sendToRenderer("connection-status", { connected: false })
      setTimeout(tryConnect, 2000)
    })
    wsClient.on("error", () => {})
  }
  tryConnect()
}

function sendToRenderer(channel, data) {
  if (mainWindow && !mainWindow.isDestroyed())
    mainWindow.webContents.send(channel, data)
}

ipcMain.on("toggle-clickthrough", () => {
  clickThrough = !clickThrough
  mainWindow.setIgnoreMouseEvents(clickThrough, { forward: true })
  sendToRenderer("clickthrough-status", { active: clickThrough })
})
ipcMain.on("toggle-fullscreen", () => {
  if (mainWindow.isFullScreen()) {
    mainWindow.setFullScreen(false)
  } else {
    mainWindow.setFullScreen(true)
  }
})
ipcMain.on("minimize-hud", () => mainWindow?.hide())
ipcMain.on("quit", () => app.quit())

// Bidirectional: HUD sends commands to Python bridge via WebSocket
ipcMain.on("send-command", (_, text) => {
  if (wsClient && wsClient.readyState === WebSocket.OPEN) {
    wsClient.send(JSON.stringify({ type: "command", text }))
  }
})

app.on("second-instance", () => {
  if (!mainWindow) return
  if (!mainWindow.isVisible()) mainWindow.show()
  if (mainWindow.isMinimized()) mainWindow.restore()
  mainWindow.focus()
})

app.whenReady().then(() => {
  if (!gotSingleInstanceLock) {
    return
  }

  enableLaunchAtLogin()
  createWindow()

  // Register global shortcut: Ctrl+Shift+J toggles HUD visibility
  try {
    globalShortcut.register("CommandOrControl+Shift+J", () => {
      if (mainWindow?.isVisible()) {
        mainWindow.hide()
      } else {
        mainWindow?.show()
        mainWindow?.focus()
      }
    })
  } catch (e) {
    console.warn("[Electron] Failed to register global shortcut:", e.message)
  }

  const icon = nativeImage.createEmpty()
  tray = new Tray(icon)
  tray.setToolTip("Jarvis HUD")
  tray.setContextMenu(
    Menu.buildFromTemplate([
      { label: "Show HUD", click: () => mainWindow?.show() },
      {
        label: "Toggle click-through",
        click: () => {
          clickThrough = !clickThrough
          mainWindow.setIgnoreMouseEvents(clickThrough, { forward: true })
          sendToRenderer("clickthrough-status", { active: clickThrough })
        },
      },
      { type: "separator" },
      { label: "Quit Jarvis", click: () => app.quit() },
    ]),
  )
  tray.on("double-click", () => mainWindow?.show())
})

app.on("will-quit", () => {
  globalShortcut.unregisterAll()
})

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") app.quit()
})
app.on("activate", () => {
  if (BrowserWindow.getAllWindows().length === 0) createWindow()
})
