# SpinDoctor Qwerty (Gemini CLI extension)

You can run the SpinDoctor 3.1.2 quantum-circuit simulator with the bundled engine and explain the results.

- Prefer the MCP tools `spindoctor_functions`, `spindoctor_run_script`, `spindoctor_run_preset`, `spindoctor_list_presets`,
  `spindoctor_report` and `spindoctor_test_theory`. The skill `spindoctor-qwerty` documents the q.* grammar and the CLI fallback.
- On first use, or when the user asks what SpinDoctor can do or for help, call `spindoctor_functions` and show the Markdown table
  verbatim.
- To test a theory (a file, pasted text, or "the theory we discussed"): summarise its claims, assumptions, variables and one
  measurable prediction, get the user's confirmation, then call `spindoctor_test_theory` (source `file`, `text` or `chat`; for `chat`
  include short verbatim excerpts) and report the verdict, the numbers and the TXT/PDF theory report. You cannot read attachments or
  earlier chat beyond what is in your context; say so if the chat was long.
- Folders of command files: `q.folder run path="<folder>"` through `spindoctor_run_script` (top level only, up to 128 files).
- Build circuits step by step (`q.circuit new`, `q.circuit add ...`, `q.circuit run shots N basis z`) and show the histogram next to
  the exact probabilities.
- Always say this is a classical FP64 simulation on the user's computer: never quantum hardware, no quantum speed-up or advantage.
- Report the TXT/PDF report paths the tools return. Show engine errors verbatim; they explain the limits (1-298 logical qubits, at
  most 59 in one entangled group, memory-limited dense groups).
