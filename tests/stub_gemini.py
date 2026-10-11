# SpinDoctor Qwerty 1.1.0 - local scripted stand-in for the Gemini API (host tests only)
# Copyright (C) 2026 RUSSELL PHILIP SMITHSON <russellsmithson77@outlook.com>
# SPDX-License-Identifier: GPL-3.0-or-later
# This program is free software: you can redistribute it and/or modify it under the terms of the GNU General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your
# option) any later version. It is distributed WITHOUT ANY WARRANTY; see the LICENSE file for details.
"""Local stand-in for the Gemini API's generateContent / streamGenerateContent (no model, no network, no key).

  python3 tests/stub_gemini.py PORT LOG.jsonl SCRIPT.json

Gemini CLI talks to it when GOOGLE_GEMINI_BASE_URL=http://127.0.0.1:PORT (its "gateway" auth type). Each agent turn (a request
that declares tools) gets the next scripted step: {"tool": NAME, "args": {...}} -> a functionCall, {"text": ...} -> a reply. Side
requests without tools (JSON-mode routing / next-speaker checks, titles) get a neutral answer and don't advance the script. Every
request is logged: declared tool names, function responses, system text, user text."""
import json, sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
PORT = int(sys.argv[1]); LOG = sys.argv[2]; SCRIPT = json.load(open(sys.argv[3]))
state = {"i": 0}
SIDE_JSON = {"reasoning": "local stand-in", "next_speaker": "user", "model_choice": "flash", "complexity_reasoning": "simple",
             "complexity_score": 1, "is_loop": False, "confidence": 0}


class H(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *a): pass

    def send(self, code, obj, ctype="application/json"):
        b = json.dumps(obj).encode()
        self.send_response(code); self.send_header("Content-Type", ctype); self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b)

    def do_GET(self):
        self.send(200, {"models": [{"name": "models/stub", "supportedGenerationMethods": ["generateContent"]}]})

    def do_POST(self):
        n = int(self.headers.get("Content-Length") or 0); raw = self.rfile.read(n) if n else b"{}"
        try: body = json.loads(raw or b"{}")
        except Exception: body = {}
        if ":countTokens" in self.path:
            self.send(200, {"totalTokens": 1}); return
        if ":embedContent" in self.path or ":batchEmbedContents" in self.path:
            self.send(200, {"embedding": {"values": [0.0] * 8}}); return
        decl = [f.get("name") for t in body.get("tools", []) or [] for f in t.get("functionDeclarations", []) or []]
        gc = body.get("generationConfig") or {}
        json_mode = gc.get("responseMimeType") == "application/json" or "responseSchema" in gc or "responseJsonSchema" in gc
        parts = [(c.get("role"), p) for c in body.get("contents", []) for p in c.get("parts", [])]
        si = body.get("systemInstruction") or {}
        rec = {"path": self.path.split("?")[0], "tools": decl, "json_mode": json_mode,
               "function_responses": [{"name": p["functionResponse"].get("name"), "response": p["functionResponse"].get("response")} for r, p in parts if "functionResponse" in p],
               "user": [p.get("text") for r, p in parts if r == "user" and "text" in p],
               "system": " ".join(p.get("text", "") for p in si.get("parts", [])) if isinstance(si, dict) else str(si)}
        if decl and not json_mode:
            step = SCRIPT[min(state["i"], len(SCRIPT) - 1)]; state["i"] += 1
            part = {"functionCall": {"name": step["tool"], "args": step.get("args", {})}} if "tool" in step else {"text": step["text"]}
        else:
            step = {"side": True}; part = {"text": json.dumps(SIDE_JSON) if json_mode else "SpinDoctor"}
        rec["step"] = step
        with open(LOG, "a") as f: f.write(json.dumps(rec) + "\n")
        resp = {"candidates": [{"content": {"role": "model", "parts": [part]}, "finishReason": "STOP", "index": 0}],
                "usageMetadata": {"promptTokenCount": 1, "candidatesTokenCount": 1, "totalTokenCount": 2}, "modelVersion": "stub"}
        if ":streamGenerateContent" in self.path:
            b = ("data: " + json.dumps(resp) + "\r\n\r\n").encode()
            self.send_response(200); self.send_header("Content-Type", "text/event-stream"); self.send_header("Content-Length", str(len(b))); self.end_headers()
            self.wfile.write(b); self.wfile.flush()
        else:
            self.send(200, resp)


ThreadingHTTPServer(("127.0.0.1", PORT), H).serve_forever()
