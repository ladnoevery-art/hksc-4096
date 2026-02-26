const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const { spawn } = require('child_process');

let pythonProcess;
let mainWindow;

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1600,
    height: 1000,
    minWidth: 1200,
    minHeight: 800,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      nodeIntegration: false,
      contextIsolation: true,
      enableRemoteModule: false
    },
    titleBarStyle: 'hiddenInset',
    show: false
  });

  mainWindow.loadFile('index.html');
  
  // Show window when ready
  mainWindow.once('ready-to-show', () => {
    mainWindow.show();
    // Open DevTools in development
    // mainWindow.webContents.openDevTools();
  });

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

app.whenReady().then(() => {
  createWindow();
  
  // Start Python Flask backend
  const pythonPath = process.platform === 'win32' ? 'python' : 'python3';
  pythonProcess = spawn(pythonPath, ['../hksc-python/hksc_4096.py', '--flask'], {
    cwd: __dirname,
    stdio: 'pipe'
  });

  pythonProcess.stdout.on('data', (data) => {
    console.log(`Python: ${data}`);
  });

  pythonProcess.stderr.on('data', (data) => {
    console.error(`Python Error: ${data}`);
  });

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

app.on('before-quit', () => {
  if (pythonProcess) {
    pythonProcess.kill();
    console.log('Python backend stopped');
  }
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

// IPC handlers for communication with renderer
ipcMain.handle('get-app-version', () => {
  return app.getVersion();
});
