#!/usr/bin/env node
// SpinDoctor Qwerty 1.1.0 - MCP server launcher for Gemini CLI
// Copyright (C) 2026 RUSSELL PHILIP SMITHSON <russellsmithson77@outlook.com>
// SPDX-License-Identifier: GPL-3.0-or-later
// This program is free software: you can redistribute it and/or modify it under the terms of the GNU General
// Public License as published by the Free Software Foundation, either version 3 of the License, or (at your
// option) any later version. It is distributed WITHOUT ANY WARRANTY; see the LICENSE file for details.
//
// Gemini CLI always has Node, but Python's command name differs by platform (python3 on macOS/Linux; py or python on Windows).
// This finds Python 3.8+ and starts spindoctor_mcp.py next to this file with the same stdin/stdout. No network, no installs.
'use strict'
const { spawn, spawnSync } = require('child_process')
const path = require('path')
const server = path.join(__dirname, 'spindoctor_mcp.py')
const check = 'import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)'
const candidates = []
if (process.env.SPINDOCTOR_PYTHON) candidates.push([process.env.SPINDOCTOR_PYTHON])
if (process.platform === 'win32') candidates.push(['py', '-3'], ['python'], ['python3'])
else candidates.push(['python3'], ['python'])
let found = null
for (const c of candidates) {
  const r = spawnSync(c[0], [...c.slice(1), '-c', check], { stdio: 'ignore', windowsHide: true, timeout: 20000 })
  if (!r.error && r.status === 0) { found = c; break }
}
if (!found) {
  process.stderr.write('spindoctor-qwerty: Python 3.8 or newer was not found (tried ' + candidates.map((c) => c.join(' ')).join(', ') +
    '). Install Python from https://www.python.org and restart Gemini CLI.\n')
  process.exit(1)
}
const env = Object.assign({}, process.env, { PYTHONUTF8: '1', PYTHONDONTWRITEBYTECODE: '1' })
const child = spawn(found[0], [...found.slice(1), server], { stdio: 'inherit', windowsHide: true, env })
for (const s of ['SIGINT', 'SIGTERM']) process.on(s, () => child.kill(s))
child.on('exit', (code, sig) => process.exit(code === null ? 1 : code))
child.on('error', (e) => { process.stderr.write('spindoctor-qwerty: ' + e.message + '\n'); process.exit(1) })
