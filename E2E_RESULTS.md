# E2E results - spindoctor-qwerty-gemini-cli 1.1.0

Host: **real Gemini CLI 0.63.0** (npm package `@google/gemini-cli`, Node 24, Linux x64) with a throwaway HOME and workspace, no Google
account and no sign-in. Model turns come from `tests/stub_gemini.py`, a local scripted stand-in for the Gemini API on 127.0.0.1
(`GOOGLE_GEMINI_BASE_URL`, placeholder key), so tool calls are scripted; everything between the model and the engine (extension
install, context loading, MCP startup through the Node launcher, tool naming and approval modes, skill activation, shell tool, slash
commands) is the real Gemini CLI. Python 3.13.5.

Not tested: a real Gemini model choosing the tools by itself, interactive approval prompts, Windows, macOS.

## Host check: 20/20

| Result | Check |
|---|---|
| PASS | gemini-extension.json: name spindoctor-qwerty (lowercase/dashes), version 1.1.0, description, contextFileName exists, no `trust` |
| PASS | MCP server: node + ${extensionPath}${/}... launcher that exists, cwd ${workspacePath}, 600 s timeout, no secrets/env |
| PASS | commands/qwerty/*.toml parse: /qwerty:functions\|run\|preset\|folder\|theory, each with description + prompt using {{args}}, no !{shell} |
| PASS | skill front matter (name, description, license GPL-3.0-or-later) + honest limits in skill and GEMINI.md; no hooks/ folder |
| PASS | launcher: finds Python 3.8+ and starts the MCP server (initialize answered, server spindoctor-qwerty 1.1.0) |
| PASS | launcher: a broken SPINDOCTOR_PYTHON falls back to the next candidate |
| PASS | launcher: without Python on PATH it exits 1 with a clear message |
| PASS | real gemini 0.63.0 (no account): extensions install <repo> --consent -> copied to ~/.gemini/extensions/spindoctor-qwerty |
| PASS | real gemini: extensions list shows 1.1.0, GEMINI.md context, MCP server spindoctor-qwerty, skill spindoctor-qwerty |
| PASS | real gemini: mcp list starts the extension's server through the Node launcher -> Connected |
| PASS | default approval mode, headless: Gemini CLI offers no MCP tools (they need approval), so headless runs need --approval-mode yolo |
| PASS | yolo approval mode: the 6 MCP tools are offered as mcp_spindoctor-qwerty_<tool>, plus activate_skill; GEMINI.md reaches the model's context and the skill list its system prompt |
| PASS | headless session through Gemini CLI: answer returned, 7 agent turns, stats show 6 tool calls |
| PASS | MCP tools via Gemini CLI: function table, Bell run (ok, PDF report in the workspace), preset qc-001 ok |
| PASS | theory test from the chat via Gemini CLI: verdict supported, 2 excerpts recorded, theory PDF on disk |
| PASS | activate_skill returns the skill instructions and its installed folder as resources |
| PASS | shell fallback from the skill: run_shell_command runs the installed CLI (gate table) |
| PASS | slash command /qwerty:preset qc-002 (headless): Gemini CLI expands the TOML prompt with {{args}}; the preset runs |
| PASS | shared E2E suite through the installed extension's launcher (node launch_mcp.js): SUMMARY 12/12 |
| PASS | real gemini: extensions uninstall removes the extension |

## Shared end-to-end suite through the installed extension: 12/12

Started with the installed extension's own MCP command: `node <extension>/skills/spindoctor-qwerty/scripts/launch_mcp.js`.

| Result | Check |
|---|---|
| PASS | initialize (server spindoctor-qwerty 1.1.0) |
| PASS | tools/list exposes the 6 tools |
| PASS | function table (Markdown, 19 sections, 298-qubit limits listed) |
| PASS | 241 presets listed |
| PASS | one script per command family (16 families, every table example) |
| PASS | 298-qubit circuit with mcx7 (prepared-factor-Born-Z) |
| PASS | q.folder on mixed .txt/.csv/.json/.qasm folder (+ .md skipped) |
| PASS | theory from a file -> supported, TXT+PDF report |
| PASS | theory from a chat summary + quoted excerpts -> supported |
| PASS | theory from an exported chat transcript -> supported |
| PASS | presets qc-001..qc-025 match the updated 3.1.2 reference (20 identical, 5 documented differences) |
| PASS | TXT+PDF reports valid (255 PDFs, 255 TXT twins) |

## Runs

- Clean room (fresh copy of the staged repo, 2026-10-11 PT): host check 20/20 (real Gemini CLI 0.63.0), shared end-to-end 12/12.
