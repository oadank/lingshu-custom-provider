const { app, BrowserWindow, shell, Menu, Tray, dialog, ipcMain } = require('electron')
const { spawn } = require('child_process')
const path = require('path')
const http = require('http')
const fs = require('fs')

const API_PORT = Number(process.env.NOVA_PORT || 18765)
const API_HOST = '127.0.0.1'
const isDev = process.argv.includes('--dev') || !app.isPackaged

let mainWindow = null
let apiProcess = null
let shuttingDown = false
let activePort = API_PORT
let tray = null
let quitting = false

function appIconPath() {
  const png = path.join(__dirname, 'build', 'icon.png')
  if (fs.existsSync(png)) return png
  return undefined
}

function installAppMenu() {
  if (isDev) return
  Menu.setApplicationMenu(null)
}

function userDataDir() {
  return path.join(app.getPath('userData'), 'data')
}

function webDir() {
  if (isDev) {
    const local = path.join(__dirname, '..', 'web', 'dist')
    if (fs.existsSync(path.join(local, 'index.html'))) return local
    return null
  }
  const packaged = path.join(process.resourcesPath, 'web')
  if (fs.existsSync(path.join(packaged, 'index.html'))) return packaged
  return null
}

function apiBinaryPath() {
  if (isDev) {
    const local = path.join(__dirname, 'sidecars', 'nova-api', 'nova-api.exe')
    if (fs.existsSync(local)) return local
    const legacy = path.join(__dirname, 'sidecars', 'nova-api.exe')
    if (fs.existsSync(legacy)) return legacy
    return null
  }
  const onedir = path.join(process.resourcesPath, 'nova-api', 'nova-api.exe')
  if (fs.existsSync(onedir)) return onedir
  return path.join(process.resourcesPath, 'nova-api.exe')
}

function apiCwd() {
  const bin = apiBinaryPath()
  return bin ? path.dirname(bin) : undefined
}

function pythonDevCommand(port) {
  const apiRoot = path.join(__dirname, '..', 'api')
  const venvPy = path.join(apiRoot, '.venv', 'Scripts', 'python.exe')
  const py = fs.existsSync(venvPy) ? venvPy : 'py'
  const args = fs.existsSync(venvPy)
    ? ['-m', 'uvicorn', 'app.main:app', '--host', API_HOST, '--port', String(port)]
    : ['-3.12', '-m', 'uvicorn', 'app.main:app', '--host', API_HOST, '--port', String(port)]
  return {
    cmd: py,
    args,
    cwd: apiRoot,
  }
}

function httpGetJson(port, urlPath, timeoutMs = 3000) {
  return new Promise((resolve, reject) => {
    const req = http.get(`http://${API_HOST}:${port}${urlPath}`, (res) => {
      let data = ''
      res.on('data', (chunk) => {
        data += chunk
      })
      res.on('end', () => {
        try {
          resolve({ status: res.statusCode, body: JSON.parse(data) })
        } catch {
          resolve({ status: res.statusCode, body: data })
        }
      })
    })
    req.on('error', reject)
    req.setTimeout(timeoutMs, () => {
      req.destroy()
      reject(new Error('timeout'))
    })
  })
}

function waitForOurApi(port, timeoutMs = 30000) {
  const started = Date.now()
  return new Promise((resolve, reject) => {
    const tick = async () => {
      try {
        const res = await httpGetJson(port, '/api/health', 800)
        if (res.status === 200 && res.body?.ok && res.body?.desktop) {
          resolve()
          return
        }
      } catch {
        /* retry */
      }
      if (Date.now() - started > timeoutMs) {
        reject(new Error(`API health timeout on port ${port}`))
      } else {
        setTimeout(tick, 120)
      }
    }
    tick()
  })
}

async function pickApiPort() {
  for (let port = API_PORT; port < API_PORT + 10; port++) {
    try {
      const res = await httpGetJson(port, '/api/health', 400)
      if (res.status === 200 && res.body?.desktop) return port
      if (res.status === 200 && !res.body?.desktop) continue
    } catch {
      return port
    }
  }
  return API_PORT
}

function stopApiProcess() {
  if (!apiProcess) return
  try {
    if (process.platform === 'win32') {
      spawn('taskkill', ['/pid', String(apiProcess.pid), '/f', '/t'], {
        stdio: 'ignore',
        windowsHide: true,
      })
    } else {
      apiProcess.kill('SIGTERM')
    }
  } catch {
    /* ignore */
  }
  apiProcess = null
}

async function startApiOnPort(port) {
  const dataDir = userDataDir()
  fs.mkdirSync(dataDir, { recursive: true })
  const web = webDir()
  const bin = apiBinaryPath()
  const cwd = apiCwd()
  const env = {
    ...process.env,
    NOVA_DATA_DIR: dataDir,
    NOVA_HOST: API_HOST,
    NOVA_PORT: String(port),
    NOVA_DESKTOP: '1',
  }
  if (web) env.NOVA_WEB_DIR = web

  if (bin && fs.existsSync(bin)) {
    apiProcess = spawn(bin, [], {
      env,
      cwd,
      stdio: 'ignore',
      windowsHide: true,
    })
  } else {
    const { cmd, args, cwd: pyCwd } = pythonDevCommand(port)
    apiProcess = spawn(cmd, args, {
      env,
      cwd: pyCwd,
      stdio: 'ignore',
      windowsHide: true,
    })
  }

  apiProcess.on('exit', (code) => {
    if (!shuttingDown && code && code !== 0) {
      console.error('API process exited', code)
    }
  })
  await waitForOurApi(port)
}

function stopApi() {
  if (!apiProcess) return
  shuttingDown = true
  stopApiProcess()
}

function showMainWindow() {
  if (!mainWindow || mainWindow.isDestroyed()) {
    createWindow()
    return
  }
  if (mainWindow.isMinimized()) mainWindow.restore()
  mainWindow.show()
  mainWindow.focus()
}

function createTray() {
  const icon = appIconPath()
  if (!icon) return
  try {
    tray = new Tray(icon)
  } catch {
    return
  }
  tray.setToolTip('灵枢3.0 — 已缩到托盘，仍在后台运行')
  const menu = Menu.buildFromTemplate([
    { label: '显示主界面', click: () => showMainWindow() },
    { type: 'separator' },
    {
      label: '退出',
      click: () => {
        quitting = true
        app.quit()
      },
    },
  ])
  tray.setContextMenu(menu)
  tray.on('click', () => showMainWindow())
  tray.on('double-click', () => showMainWindow())
}

async function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1280,
    height: 840,
    minWidth: 960,
    minHeight: 640,
    title: '灵枢3.0',
    icon: appIconPath(),
    autoHideMenuBar: !isDev,
    backgroundColor: '#F3F1EC',
    webPreferences: {
      preload: path.join(__dirname, 'preload.cjs'),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true,
      // 正式包禁用 DevTools，降低前端源码/网络面板被直接查看的风险
      devTools: isDev,
    },
    show: false,
  })

  mainWindow.once('ready-to-show', () => mainWindow?.show())

  // 点关闭：隐藏到托盘，后台继续运行；真正退出走托盘菜单「退出」
  mainWindow.on('close', (event) => {
    if (!quitting) {
      event.preventDefault()
      mainWindow?.hide()
    }
  })

  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url)
    return { action: 'deny' }
  })

  if (!isDev) {
    mainWindow.webContents.on('devtools-opened', () => {
      mainWindow?.webContents.closeDevTools()
    })
    mainWindow.webContents.on('before-input-event', (event, input) => {
      const key = String(input.key || '').toLowerCase()
      if (key === 'f12') {
        event.preventDefault()
        return
      }
      if (input.control && input.shift && ['i', 'j', 'c'].includes(key)) {
        event.preventDefault()
      }
    })
  }

  if (isDev) {
    try {
      await new Promise((resolve, reject) => {
        const req = http.get('http://127.0.0.1:5173', (res) => {
          res.resume()
          resolve()
        })
        req.on('error', reject)
        req.setTimeout(800, () => {
          req.destroy()
          reject(new Error('vite down'))
        })
      })
      await mainWindow.loadURL('http://127.0.0.1:5173')
      mainWindow.webContents.openDevTools({ mode: 'detach' })
      return
    } catch {
      /* fall through */
    }
  }

  const web = webDir()
  if (web) {
    await mainWindow.loadFile(path.join(web, 'index.html'), { hash: '/' })
    return
  }

  await mainWindow.loadURL(`http://${API_HOST}:${activePort}/`)
}

function registerIpc() {
  ipcMain.handle('pick-import-folder', async () => {
    const win = BrowserWindow.getFocusedWindow() || mainWindow
    const result = await dialog.showOpenDialog(win ?? undefined, {
      title: '选择作品文件夹',
      properties: ['openDirectory'],
    })
    if (result.canceled || !result.filePaths[0]) return null

    const folder = result.filePaths[0]
    const title = path.basename(folder)
    let names = []
    try {
      names = fs.readdirSync(folder)
    } catch (err) {
      throw new Error(`无法读取文件夹：${err instanceof Error ? err.message : String(err)}`)
    }

    const files = []
    for (const name of names) {
      if (!name.toLowerCase().endsWith('.txt')) continue
      if (name.startsWith('.')) continue
      const full = path.join(folder, name)
      let st
      try {
        st = fs.statSync(full)
      } catch {
        continue
      }
      if (!st.isFile()) continue
      if (st.size > 5 * 1024 * 1024) continue
      const buf = fs.readFileSync(full)
      files.push({ name, data: Uint8Array.from(buf) })
    }
    return { title, files }
  })

  ipcMain.handle('pick-import-book-file', async () => {
    const win = BrowserWindow.getFocusedWindow() || mainWindow
    const result = await dialog.showOpenDialog(win ?? undefined, {
      title: '选择整本小说文件',
      properties: ['openFile'],
      filters: [
        { name: '小说文本', extensions: ['txt', 'text', 'md', 'markdown', 'docx'] },
        { name: '所有文件', extensions: ['*'] },
      ],
    })
    if (result.canceled || !result.filePaths[0]) return null
    const full = result.filePaths[0]
    const name = path.basename(full)
    let st
    try {
      st = fs.statSync(full)
    } catch (err) {
      throw new Error(`无法读取文件：${err instanceof Error ? err.message : String(err)}`)
    }
    if (!st.isFile()) throw new Error('请选择文件')
    if (st.size > 60 * 1024 * 1024) throw new Error('文件过大（超过 60MB）')
    const buf = fs.readFileSync(full)
    const title = name.replace(/\.(txt|text|md|markdown|docx)$/i, '').trim() || '未命名作品'
    return { title, files: [{ name, data: Uint8Array.from(buf) }] }
  })
}

app.whenReady().then(async () => {
  try {
    installAppMenu()
    registerIpc()
    activePort = await pickApiPort()
    process.env.NOVA_ACTUAL_PORT = String(activePort)
    await startApiOnPort(activePort)
    await createWindow()
    createTray()
  } catch (err) {
    console.error(err)
    app.quit()
  }
})

app.on('window-all-closed', () => {
  stopApi()
  if (process.platform !== 'darwin') app.quit()
})

app.on('before-quit', () => {
  quitting = true
  stopApi()
})

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) createWindow()
})
