# SpinDoctor Qwerty for Gemini CLI

A [Gemini CLI extension](https://geminicli.com/docs/extensions/reference/) that runs the **SpinDoctor 3.1.2 quantum-circuit
simulator** on your computer: `q.*` circuit scripts (1-298 logical qubits), the 241 built-in presets, folders of command files
(`q.folder`), and theory tests from a file, pasted text or the chat itself, each with TXT, PDF, JSON and CSV reports.

> **Honest limits.** SpinDoctor is a classical FP64 simulator. It is not a quantum computer, does not connect to quantum hardware,
> and gives no quantum speed-up or advantage. One entangled group is limited to 59 qubits and dense groups are limited by memory
> (2^n x 16 bytes). Registers wider than 29 qubits sample in basis Z only. Histograms are seeded Born samples.

Version 1.1.0 - engine 1.1.0 (SpinDoctor 3.1.2 parity) - tested with Gemini CLI 0.63.0 - Python 3.8+, standard library only - no
network, no extra account, no keys for the extension itself.

## Install

```bash
gemini extensions install https://github.com/LKVexa/spindoctor-qwerty-gemini-cli
```

Gemini CLI shows a security notice and asks whether to trust the source; then restart Gemini CLI. `gemini extensions list` should
show `spindoctor-qwerty (1.1.0)` and `gemini mcp list` should show `spindoctor-qwerty ... Connected`. From a local clone:
`gemini extensions install ./spindoctor-qwerty-gemini-cli` (Gemini copies it; run `gemini extensions update spindoctor-qwerty` after
you change the clone) or `gemini extensions link ./spindoctor-qwerty-gemini-cli` while developing.

Requirements: Python 3.8 or newer (any of `python3`, `python`, or on Windows `py`). No packages to install. The MCP server starts
through `skills/spindoctor-qwerty/scripts/launch_mcp.js`, a short Node script (Gemini CLI already runs on Node) that finds Python and
starts the server; it tries `python3` then `python` on macOS/Linux, and `py -3`, `python`, `python3` on Windows.

## What's in the repo

| Path | What it is |
|---|---|
| `gemini-extension.json` | Extension manifest: name, version, `GEMINI.md` context, MCP server `spindoctor-qwerty` (6 tools) |
| `GEMINI.md` | Context loaded into every session: when to use which tool, theory-test steps, honest limits |
| `commands/qwerty/` | `/qwerty:functions`, `/qwerty:run`, `/qwerty:preset`, `/qwerty:folder`, `/qwerty:theory` |
| `skills/spindoctor-qwerty/` | Agent skill (`SKILL.md`), the bundled engine (`spindoctor/`), CLI, MCP server and launcher (`scripts/`), examples |
| `FUNCTIONS.md` | The full function table with a runnable example for every command |
| `tests/` | Host check, shared end-to-end suite, local Gemini API stand-in, reference outputs |

No hooks and no policies: the extension never runs anything on its own.

## Using it

- Ask in plain language ("show the SpinDoctor functions", "run a 3-qubit GHZ circuit") or use the slash commands.
- Gemini CLI names the tools `mcp_spindoctor-qwerty_spindoctor_functions` and so on. It asks before each MCP tool call unless you
  allow it; in headless mode (`gemini -p`) tools that need approval aren't offered at all, so use `--approval-mode yolo` there (only in
  folders you trust). `spindoctor_functions` is marked read-only (it writes nothing).
- The server runs in your current workspace folder, so relative paths resolve there. Reports and state go to `~/spindoctor-workspace`
  unless a tool call passes `workspace`. Gemini CLI doesn't pass your shell's environment variables to extensions, so
  `SPINDOCTOR_WORKSPACE` in your shell has no effect here.
- If the tools aren't available, the skill tells the model to run the CLI with the shell tool:
  `python3 "<skill folder>/scripts/spindoctor_cli.py" functions`.

## SpinDoctor Qwerty - plugin tools

| Function | What it does | Command to type |
|---|---|---|
| Function table (spindoctor_functions) | Show this table in chat | `/qwerty:functions` or ask: "show the SpinDoctor functions" |
| Run a script (spindoctor_run_script) | Run any q.* lines above; returns results + TXT/JSON/CSV/PDF report paths | Ask: "run q.circuit new bell 2 / q.circuit add h 0 / ..." |
| Run a preset (spindoctor_run_preset) | Run qc-001..qc-241 with overrides | `/qwerty:preset qc-067 shots=64` |
| List presets (spindoctor_list_presets) | Search the 241 presets | Ask: "list presets about Grover" |
| Read a report (spindoctor_report) | List/read TXT reports (PDF/JSON paths alongside) | Ask: "show the newest SpinDoctor report" |
| Test a theory from a file (spindoctor_test_theory source=file) | Read a .txt/.md/.pdf/.py/.json/.csv/.q attachment, then hypothesis -> prediction -> q.* script -> run -> verdict + TXT/PDF theory report | Ask: "test the theory in C:/notes/theory.md" (the host must pass the file path/content) |
| Test a theory from text (spindoctor_test_theory source=text) | Same pipeline for pasted text | Ask: "test this theory: a Hadamard on \|0> gives 50/50" |
| Test the theory we discussed (spindoctor_test_theory source=chat) | The AI summarises the theory from the conversation (claims, assumptions, variables, prediction), you confirm, then it is tested; quoted excerpts go in the report under 'Source: chat history'. An exported chat transcript (.txt/.md/.json/.html) also works | `/qwerty:theory we discussed`, ask: "test the theory we discussed" or "test the theory in my exported chat C:/chats/conversation.json" |

Every command family is listed with a runnable example in **[FUNCTIONS.md](FUNCTIONS.md)** (the exact table the tool shows):
circuits (`q.circuit`, including 298-qubit wide registers and the `mcx7` gate), queries (`q.query`), the tranche register
(`q.tranche`), the procedural grid, presets and sequences, resource planning, math calculators, physics models, lessons, noise, error
correction, compilation, algorithms, inputs/folders/history (`q.input`, `q.folder`, `q.history`) and the cartridge commands.

## Theory testing

`spindoctor_test_theory` turns a claim into a test: hypothesis -> measurable prediction -> `q.*` script -> run -> compare -> a TXT +
JSON + PDF **theory test report** with the hypothesis, script, raw results, verdict (*supported*, *not supported* or *inconclusive*)
and limits.

- **From a file:** .txt, .md, .pdf, .py, .json, .csv or .q. In Gemini CLI, give the file's absolute path on your computer (or paste the text).
- **From pasted text.**
- **From the chat history:** say *"test the theory we discussed"*. The model writes a short summary (claims, assumptions, variables,
  measurable prediction), shows it to you to confirm or correct, then passes it with optional quoted excerpts; the report records them
  under *Source: chat history*. Exported chat transcripts (.txt/.md/.json/.html from ChatGPT, Claude and others) also work.
- The plugin cannot read your conversation or attachments by itself: only the model sees them, and very long conversations may already
  be truncated by the context window.

Sample theory files and chat transcripts are in `skills/spindoctor-qwerty/examples/theory/`. The two sample
PDFs are stored as text; run `python3 skills/spindoctor-qwerty/examples/theory/make_sample_pdfs.py` to
recreate them.

## Folder ingestion (`q.folder`)

`q.folder run path="<folder>"` runs every supported file at the top level of a folder (.txt, .csv, .json, .qasm, .qasm2, .circuit,
.pdf) in ordinal name order: 1-128 supported files, at most 4 MiB per file, 1-128 commands per file and 4096 characters per command,
strict UTF-8. Other files (for example .md) are skipped and listed. The first failing file stops the job.


## Testing

| Test | Command |
|---|---|
| Static checks + launcher | `python3 tests/gemini_host_check.py` |
| Real Gemini CLI | `python3 tests/gemini_host_check.py --gemini "$(command -v gemini)"` |

**Real host, scripted model.** The host check uses the real Gemini CLI (0.63.0 from npm) with a throwaway HOME and workspace and no
Google account: it installs this repo as an extension, checks `extensions list` and `mcp list`, then runs headless `gemini -p`
sessions against `tests/stub_gemini.py`, a local scripted stand-in for the Gemini API on 127.0.0.1 (`GOOGLE_GEMINI_BASE_URL` with a
placeholder key). Through Gemini CLI's own MCP client it shows the function table, runs a Bell circuit and preset qc-001, tests a
theory from the chat (verdict *supported*, PDF written), activates the skill, runs the CLI fallback through the shell tool and expands
`/qwerty:preset`. Then it runs the shared end-to-end suite through the installed launcher and uninstalls. Gemini CLI 0.63 picks a
"gateway" sign-in type when `GOOGLE_GEMINI_BASE_URL` is set and then rejects it, so the check selects API-key sign-in in the throwaway
settings file; requests still go only to the local stand-in. Not tested: a real Gemini model choosing the tools, interactive approval
prompts, Windows, macOS. Results: [E2E_RESULTS.md](E2E_RESULTS.md).

## Author and license

Author: **RUSSELL PHILIP SMITHSON** <russellsmithson77@outlook.com>

Copyright (C) 2026 RUSSELL PHILIP SMITHSON. Licensed under the GNU General Public License v3.0 or later (`GPL-3.0-or-later`): see
[LICENSE](LICENSE), [NOTICE](NOTICE) and [COPYRIGHT](COPYRIGHT). Gemini is a trademark of Google LLC; this project is not affiliated
with Google.
