# Changelog

## 1.1.0 - 2026-10-11

- Engine 1.1.0 at parity with the updated SpinDoctor 3.1.2: 1-298 logical qubits (59 per entangled factor), the `mcx7` gate,
  wide-register Born-Z sampling, `q.folder` with 3.1.2 semantics, CSV report copies and measurement-CSV fitting equations. All 241
  presets replayed. Tools `spindoctor_functions` (function table, now marked read-only) and `spindoctor_test_theory` (theory testing
  from a file, pasted text or the chat, with TXT+JSON+PDF theory reports).
- **Works on Windows.** 1.0 started the MCP server with `python3`, which the python.org installer doesn't provide on Windows. The server
  now starts through a small Node launcher (`skills/spindoctor-qwerty/scripts/launch_mcp.js`; Gemini CLI always has Node) that finds
  Python 3.8+ (`python3`/`python` on macOS and Linux; `py -3`, `python`, `python3` on Windows) and prints a clear message if none is
  found.
- **Relative paths resolve in your project.** 1.0 started the server in the extension folder (`cwd: ${extensionPath}`), so a relative
  file or folder path pointed inside the installed extension. It now starts in `${workspacePath}`. MCP timeout raised to 600 s for long
  runs.
- The repo root is now the extension root, so `gemini extensions install https://github.com/LKVexa/spindoctor-qwerty-gemini-cli` works
  directly (1.0 had it in a `spindoctor-qwerty/` subfolder). New command `/qwerty:folder`; GEMINI.md, the commands and the skill are
  updated for 3.1.2 and Gemini CLI's tool names and shell fallback.
- Tests: `tests/gemini_host_check.py` (static checks, launcher tests, and the real Gemini CLI: install, list, `mcp list`, headless
  sessions against a local stand-in for the Gemini API, a slash command, the shared end-to-end suite, uninstall).
- License changed from MIT to GPL-3.0-or-later. Author RUSSELL PHILIP SMITHSON. README, NOTICE, COPYRIGHT and SPDX headers added.

## 1.0.0

- First release: `spindoctor-qwerty/` with `gemini-extension.json`, GEMINI.md, skill, four TOML commands and a `python3` MCP server.
