#!/usr/bin/env python3
# SpinDoctor Qwerty 1.1.0 - Gemini CLI host check
# Copyright (C) 2026 RUSSELL PHILIP SMITHSON <russellsmithson77@outlook.com>
# SPDX-License-Identifier: GPL-3.0-or-later
"""Run from the repo root:

  python3 tests/gemini_host_check.py                                    # static checks only
  python3 tests/gemini_host_check.py --gemini "$(command -v gemini)" [--out tests/host_check.json]

Static: manifest, TOML commands, skill, context file, and the Node launcher (finds Python, starts the MCP server, clear error).
Real host (--gemini): with a throwaway HOME and workspace, `gemini extensions install <this repo> --consent`, `extensions list`,
`mcp list`, then headless `gemini -p` sessions against tests/stub_gemini.py, a local scripted stand-in for the Gemini API on 127.0.0.1
(GOOGLE_GEMINI_BASE_URL with a placeholder key: no Google account, no sign-in, nothing leaves the machine). Checks which tools are
offered in the default and yolo approval modes, runs the MCP tools, the skill, the shell fallback and a slash command through
Gemini CLI, runs the shared end-to-end suite through the installed launcher, then uninstalls. Standard library only (Python 3.11+
for the TOML check; it is skipped on older Pythons).
"""
import json, os, re, shutil, socket, subprocess, sys, tempfile, time
sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
SK = os.path.join(ROOT, "skills", "spindoctor-qwerty"); LAUNCH = os.path.join(SK, "scripts", "launch_mcp.js")
TOOLS = ["spindoctor_functions", "spindoctor_list_presets", "spindoctor_report", "spindoctor_run_preset", "spindoctor_run_script", "spindoctor_test_theory"]
M = lambda t: "mcp_spindoctor-qwerty_" + t
R = []
OK = lambda s: bool(re.search(r'"ok":\s*true', s or ""))


def T(name, ok, detail=""):
    R.append({"check": name, "pass": bool(ok), "detail": str(detail)[:600]})
    print(("PASS " if ok else "FAIL ") + name + ("" if ok else "  -- " + str(detail)[:500])); sys.stdout.flush()


def mcp_init(cmd, env=None, timeout=60):
    req = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2025-06-18", "capabilities": {}, "clientInfo": {"name": "check", "version": "1"}}}) + "\n"
    p = subprocess.run(cmd, input=req.encode(), stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env, timeout=timeout)
    return p.returncode, p.stdout.decode("utf-8", "replace"), p.stderr.decode("utf-8", "replace")


def static(node):
    m = json.load(open(os.path.join(ROOT, "gemini-extension.json"), encoding="utf-8"))
    s = m.get("mcpServers", {}).get("spindoctor-qwerty", {})
    T("gemini-extension.json: name spindoctor-qwerty (lowercase/dashes), version 1.1.0, description, contextFileName exists, no `trust`",
      m.get("name") == "spindoctor-qwerty" and re.fullmatch(r"[a-z0-9-]+", m["name"]) and m.get("version") == "1.1.0" and m.get("description")
      and os.path.isfile(os.path.join(ROOT, m.get("contextFileName", "?"))) and "trust" not in s, m)
    rel = s.get("args", [""])[0].replace("${extensionPath}", ROOT).replace("${/}", os.sep)
    T("MCP server: node + ${extensionPath}${/}... launcher that exists, cwd ${workspacePath}, 600 s timeout, no secrets/env",
      s.get("command") == "node" and s.get("args", [""])[0].startswith("${extensionPath}${/}") and os.path.abspath(rel) == LAUNCH
      and os.path.isfile(LAUNCH) and s.get("cwd") == "${workspacePath}" and s.get("timeout") == 600000 and "env" not in s, s)
    try:
        import tomllib
        cmds = {}
        for f in sorted(os.listdir(os.path.join(ROOT, "commands", "qwerty"))):
            cmds[f] = tomllib.load(open(os.path.join(ROOT, "commands", "qwerty", f), "rb"))
        T("commands/qwerty/*.toml parse: /qwerty:functions|run|preset|folder|theory, each with description + prompt using {{args}}, no !{shell}",
          sorted(cmds) == ["folder.toml", "functions.toml", "preset.toml", "run.toml", "theory.toml"]
          and all(c.get("description") and "{{args}}" in c.get("prompt", "") and "!{" not in c["prompt"] for c in cmds.values()), list(cmds))
    except ImportError:
        T("commands/qwerty/*.toml (skipped: Python < 3.11 has no tomllib)", True)
    sk = open(os.path.join(SK, "SKILL.md"), encoding="utf-8").read(); fm = sk.split("---")[1]
    gm = open(os.path.join(ROOT, "GEMINI.md"), encoding="utf-8").read()
    T("skill front matter (name, description, license GPL-3.0-or-later) + honest limits in skill and GEMINI.md; no hooks/ folder",
      "name: spindoctor-qwerty" in fm and "description:" in fm and "license: GPL-3.0-or-later" in fm and "not a quantum computer" in sk
      and "never quantum hardware" in gm and not os.path.exists(os.path.join(ROOT, "hooks")))
    rc, out, err = mcp_init([node, LAUNCH])
    T("launcher: finds Python 3.8+ and starts the MCP server (initialize answered, server spindoctor-qwerty 1.1.0)",
      '"spindoctor-qwerty"' in out and '"1.1.0"' in out, (rc, out[:200], err[-300:]))
    env = dict(os.environ, SPINDOCTOR_PYTHON="/nonexistent/python9")
    rc, out, err = mcp_init([node, LAUNCH], env=env)
    T("launcher: a broken SPINDOCTOR_PYTHON falls back to the next candidate", '"spindoctor-qwerty"' in out, (rc, err[-300:]))
    nd = tempfile.mkdtemp(prefix="sdq-nopy-"); os.symlink(node, os.path.join(nd, "node"))
    rc, out, err = mcp_init([os.path.join(nd, "node"), LAUNCH], env={"PATH": nd, "HOME": nd})
    shutil.rmtree(nd, ignore_errors=True)
    T("launcher: without Python on PATH it exits 1 with a clear message", rc == 1 and "Python 3.8 or newer was not found" in err, (rc, err[-300:]))


def free_port():
    s = socket.socket(); s.bind(("127.0.0.1", 0)); p = s.getsockname()[1]; s.close(); return p


def real(gemini, node):
    tmp = tempfile.mkdtemp(prefix="sdq-gemini-"); home = os.path.join(tmp, "home"); work = os.path.join(tmp, "work"); ws = os.path.join(tmp, "ws")
    os.makedirs(os.path.join(home, ".gemini")); os.makedirs(work)
    port = free_port(); log = os.path.join(tmp, "stub.jsonl"); script = os.path.join(tmp, "script.json")
    env = {k: v for k, v in os.environ.items() if not k.startswith(("GEMINI", "GOOGLE", "SPINDOCTOR"))}
    env.update(HOME=home, USERPROFILE=home, PATH=os.path.dirname(node) + os.pathsep + os.environ.get("PATH", ""), NO_COLOR="1",
               GOOGLE_GEMINI_BASE_URL="http://127.0.0.1:%d" % port, GEMINI_API_KEY="local-stub", GEMINI_CLI_DISABLE_AUTO_UPDATE="true")
    # Gemini CLI 0.63 picks its "gateway" auth for GOOGLE_GEMINI_BASE_URL but then rejects it in validation, so select API-key auth
    # explicitly; the Gemini SDK still sends every request to GOOGLE_GEMINI_BASE_URL.
    json.dump({"security": {"auth": {"selectedType": "gemini-api-key"}}, "privacy": {"usageStatisticsEnabled": False},
               "general": {"disableAutoUpdate": True}}, open(os.path.join(home, ".gemini", "settings.json"), "w"))
    run = lambda args, inp=None, t=300: subprocess.run([gemini] + args, cwd=work, env=env, input=inp, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=t)
    stub = None
    try:
        v = run(["--version"], t=60).stdout.decode().strip()
        r = run(["extensions", "install", ROOT, "--consent"], inp=b"y\n")
        o = r.stdout.decode("utf-8", "replace"); inst = os.path.join(home, ".gemini", "extensions", "spindoctor-qwerty")
        T("real gemini %s (no account): extensions install <repo> --consent -> copied to ~/.gemini/extensions/spindoctor-qwerty" % v,
          r.returncode == 0 and "installed successfully" in o and os.path.isfile(os.path.join(inst, "gemini-extension.json")), o[-400:])
        o = run(["extensions", "list"], t=120).stdout.decode("utf-8", "replace")
        T("real gemini: extensions list shows 1.1.0, GEMINI.md context, MCP server spindoctor-qwerty, skill spindoctor-qwerty",
          "spindoctor-qwerty (1.1.0)" in o and "GEMINI.md" in o and "MCP servers:" in o and "Agent skills:" in o, o[-500:])
        o = run(["mcp", "list"], t=120).stdout.decode("utf-8", "replace")
        T("real gemini: mcp list starts the extension's server through the Node launcher -> Connected",
          "spindoctor-qwerty" in o and "launch_mcp.js" in o and "Connected" in o, o[-400:])

        def session(steps, prompt, extra):
            json.dump(steps, open(script, "w")); open(log, "w").close()
            nonlocal stub
            if stub: stub.kill(); stub.wait()
            stub = subprocess.Popen([sys.executable, os.path.join(HERE, "stub_gemini.py"), str(port), log, script], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            time.sleep(1)
            r = run(["-p", prompt, "--output-format", "json"] + extra, t=900)
            o = r.stdout.decode("utf-8", "replace")
            try: res = json.loads(o[o.index("{"):])
            except Exception: res = {}
            recs = [json.loads(l) for l in open(log)]
            agent = [x for x in recs if x["tools"] and not x["json_mode"]]
            fr = {}
            for x in agent[-1:]:
                for f in x["function_responses"]: fr.setdefault(f["name"], []).append(json.dumps(f["response"]))
            return r.returncode, res, agent, fr, o

        rc, res, agent, fr, o = session([{"text": "ok"}], "hello", [])
        offered = set(agent[0]["tools"]) if agent else set()
        T("default approval mode, headless: Gemini CLI offers no MCP tools (they need approval), so headless runs need --approval-mode yolo",
          agent and not any(t.startswith("mcp_") for t in offered) and rc == 0, sorted(offered))
        thy = {"source": "chat", "text": "Theory: H then CX makes a Bell state; only 00 and 11, about half each.",
               "excerpts": ["User: does H then CX entangle two qubits?", "Assistant: yes, a Bell state."], "hypothesis": "H(0) then CX(0,1) prepares a Bell state",
               "prediction": "P(00)=P(11)=0.5", "script": "q.circuit new th 2\nq.circuit add h 0\nq.circuit add cx 0 1\nq.circuit run shots 4000 basis z",
               "checks": [{"kind": "probability", "outcome": x, "expected": 0.5, "tolerance": 0.05} for x in ("00", "11")], "workspace": ws}
        cli = os.path.join(inst, "skills", "spindoctor-qwerty", "scripts", "spindoctor_cli.py")
        steps = [{"tool": M("spindoctor_functions"), "args": {}},
                 {"tool": M("spindoctor_run_script"), "args": {"script": "q.circuit new bell 2\nq.circuit add h 0\nq.circuit add cx 0 1\nq.circuit run shots 1000 basis z", "workspace": ws}},
                 {"tool": M("spindoctor_run_preset"), "args": {"preset_id": "qc-001", "workspace": ws}},
                 {"tool": M("spindoctor_test_theory"), "args": thy},
                 {"tool": "activate_skill", "args": {"name": "spindoctor-qwerty"}},
                 {"tool": "run_shell_command", "args": {"command": 'python3 "%s" functions gates' % cli, "description": "SpinDoctor gate table via the CLI"}},
                 {"text": "Done. SpinDoctor is a classical simulation, not quantum hardware."}]
        rc, res, agent, fr, o = session(steps, "Show the SpinDoctor functions, run a Bell circuit and preset qc-001, and test the Bell theory we discussed.", ["--approval-mode", "yolo"])
        offered = set(agent[0]["tools"]) if agent else set()
        ctx = (agent[0]["system"] + " " + " ".join(u or "" for u in agent[0]["user"])) if agent else ""
        T("yolo approval mode: the 6 MCP tools are offered as mcp_spindoctor-qwerty_<tool>, plus activate_skill; GEMINI.md reaches the model's context and the skill list its system prompt",
          all(M(t) in offered for t in TOOLS) and "activate_skill" in offered and agent and "SpinDoctor Qwerty (Gemini CLI extension)" in ctx and "spindoctor-qwerty" in agent[0]["system"],
          {"tools": sorted(offered), "context_in_system": "SpinDoctor Qwerty (Gemini CLI extension)" in (agent[0]["system"] if agent else "")})
        g = lambda n: (fr.get(n) or [""])[0]
        T("headless session through Gemini CLI: answer returned, %d agent turns, stats show 6 tool calls" % len(agent),
          rc == 0 and "classical simulation" in str(res.get("response", "")) and len(agent) == len(steps)
          and res.get("stats", {}).get("tools", {}).get("totalCalls") == 6, str(res.get("response", o[-300:]))[:300])
        T("MCP tools via Gemini CLI: function table, Bell run (ok, PDF report in the workspace), preset qc-001 ok",
          "| Function |" in g(M("spindoctor_functions")) and OK(g(M("spindoctor_run_script")).replace('\\"', '"')) and ".pdf" in g(M("spindoctor_run_script"))
          and ws in g(M("spindoctor_run_script")) and "qc-001" in g(M("spindoctor_run_preset")), {k: v[0][:160] for k, v in fr.items()})
        th = g(M("spindoctor_test_theory")).replace('\\"', '"'); pdfs = re.findall(r'"([^"]+\.pdf)', th)
        T("theory test from the chat via Gemini CLI: verdict supported, 2 excerpts recorded, theory PDF on disk",
          re.search(r'"verdict":\s*"supported"', th) and re.search(r'"excerptsRecorded":\s*2', th) and pdfs and os.path.isfile(pdfs[0].replace("\\\\", "\\")), th[:300])
        sk = g("activate_skill")
        T("activate_skill returns the skill instructions and its installed folder as resources",
          "activated_skill" in sk and "q.circuit" in sk and "launch_mcp.js" in sk or ("activated_skill" in sk and "spindoctor_cli.py" in sk), sk[:300])
        T("shell fallback from the skill: run_shell_command runs the installed CLI (gate table)", "Gate set" in g("run_shell_command"), g("run_shell_command")[:300])
        rc, res, agent, fr, o = session([{"tool": M("spindoctor_run_preset"), "args": {"preset_id": "qc-002", "workspace": ws}}, {"text": "Preset done (classical simulation)."}],
                                        "/qwerty:preset qc-002", ["--approval-mode", "yolo"])
        ut = " ".join(u or "" for u in (agent[0]["user"] if agent else []))
        T("slash command /qwerty:preset qc-002 (headless): Gemini CLI expands the TOML prompt with {{args}}; the preset runs",
          "Use the spindoctor_run_preset tool to run SpinDoctor preset qc-002" in ut and "qc-002" in g(M("spindoctor_run_preset")) and rc == 0, ut[:300])
        e2e = os.path.join(HERE, "e2e_results.json")
        r = subprocess.run([sys.executable, os.path.join(HERE, "e2e_mcp.py"), "--server", node, os.path.join(inst, "skills", "spindoctor-qwerty", "scripts", "launch_mcp.js"),
                            "--examples", os.path.join(SK, "examples", "theory"), "--out", e2e], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=3600, cwd=work)
        t = r.stdout.decode("utf-8", "replace"); mm = re.search(r"SUMMARY (\d+)/(\d+)", t)
        T("shared E2E suite through the installed extension's launcher (node launch_mcp.js): %s" % (mm.group(0) if mm else "?"),
          r.returncode == 0 and mm and mm.group(1) == mm.group(2), "\n".join(l for l in t.splitlines() if l.startswith("FAIL"))[-500:])
        r = run(["extensions", "uninstall", "spindoctor-qwerty"], t=120)
        T("real gemini: extensions uninstall removes the extension", not os.path.exists(inst), r.stdout.decode()[-300:])
    finally:
        if stub: stub.kill()
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    a = sys.argv[1:]; opt = dict(zip(a[::2], a[1::2]))
    node = opt.get("--node") or shutil.which("node") or "node"
    static(node)
    if opt.get("--gemini"): real(os.path.abspath(opt["--gemini"]), node)
    outp = opt.get("--out", os.path.join(HERE, "host_check.json"))
    json.dump({"passed": sum(r["pass"] for r in R), "total": len(R), "python": sys.version.split()[0], "checks": R}, open(outp, "w"), indent=1)
    print("HOST CHECK %d/%d passed" % (sum(r["pass"] for r in R), len(R)))
    return 0 if all(r["pass"] for r in R) else 1


if __name__ == "__main__":
    sys.exit(main())
