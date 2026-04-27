#!/usr/bin/env node
/**
 * Start both backend and frontend with one command
 * Runs: Backend on 8000 + Frontend on 3000
 * Everything accessible from http://localhost:3000
 */

const { spawn } = require('child_process');
const path = require('path');
const os = require('os');

const isWindows = os.platform() === 'win32';

console.log(`
╔════════════════════════════════════════════════════════════╗
║   Document Intelligence System - Starting                  ║
║   Backend: http://localhost:8000                          ║
║   Frontend: http://localhost:3000 (opens in browser)      ║
╚════════════════════════════════════════════════════════════╝
`);

// Backend process
const backendProcess = spawn(
  isWindows ? 'python' : 'python3',
  ['app.py'],
  {
    cwd: path.join(__dirname, 'backend'),
    stdio: 'inherit',
    shell: isWindows
  }
);

// Give backend time to start
setTimeout(() => {
  // Frontend process
  const frontendProcess = spawn(
    isWindows ? 'npm.cmd' : 'npm',
    ['run', 'dev'],
    {
      cwd: path.join(__dirname, 'frontend'),
      stdio: 'inherit',
      shell: isWindows
    }
  );

  // Handle termination
  process.on('SIGINT', () => {
    console.log('\nShutting down...');
    backendProcess.kill('SIGTERM');
    frontendProcess.kill('SIGTERM');
    process.exit(0);
  });
}, 3000);

// Error handling
backendProcess.on('error', (err) => {
  console.error('Failed to start backend:', err);
  process.exit(1);
});
