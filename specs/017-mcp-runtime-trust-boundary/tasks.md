# Tasks: MCP / tool-runtime trust boundary (017)

**Feature**: 017-mcp-runtime-trust-boundary
**Spec**: [spec.md](./spec.md) · **Plan**: [plan.md](./plan.md)
**Status**: Specified. Linux POC out of tree. Not wired into `get_agent()`.

Checkboxes are honest. Spec-only work can be marked done. Do not mark
sensors done because a POC exists on another machine. Do not mark
`get_agent()` monitoring done because memory `ToolNode` already runs.

## Phase 0 — Specify the boundary (this folder)

- [x] Write `spec.md` with trust boundary, runtime monitoring as defense
      in depth, five detection classes, honesty about this package
- [x] Write `plan.md` (boundary diagram, class table as ideas, 013/015
      binding, no CVE/POC copy)
- [x] Write `tasks.md` (this file)
- [x] Status: specified; POC out of tree; not a `thelab-langchain` feature
- [x] Cite 013 (no rubber-stamp of tool/exec) and 015 (content-free alerts)
- [x] Refuse CVE tables, unverifiable stats, keys, IPs, chat-product
      routing, and POC source in this tree

## Phase 1 — Linux POC (out of tree; already exists)

Out of tree. Listed so this package does not re-build or vendor it.

- [x] Prototype of five detection classes on Linux:
      shell metacharacters in child cmdline; unexpected subprocess vs
      allow-list; config file integrity; new-server network watch;
      dangerous env var changes
- [x] POC treated as detection, not as production prevention

Do **not** copy POC Python, audit rule files, or test suites into this
repo to “complete” a checkbox.

## Phase 2 — Workstation wiring (not done)

Host-side watcher next to real MCP/tool processes. Not this package.

- [ ] Run sensors beside the workstation tool runtime (outside
      `thelab-langchain`)
- [ ] Content-free alerts (015): rule class, counts/flags, generic names;
      no secrets, transcripts, tool bodies, config dumps, or lab IPs
- [ ] Fail-open: dead sensor does not break the desk loop

Phase 2 is **out of scope for 017 delivery**. Leave unchecked.

## Phase 3 — This package / `get_agent()` (**not done**)

- [ ] MCP client in `thelab_langchain`
- [ ] Sensors or a monitor node in the graph
- [ ] Wiring the out-of-tree POC into `get_agent()`
- [ ] Prevention (kill child, freeze config) as a shipped control

Phase 3 is **out of scope** for 017. Do not implement them under this spec.

## Explicitly not tasks in thelab

Do not open work in this package for:

- Vendoring POC source or research-cycle SUMMARY/JSON dumps
- A CVE / KEV tracker, CVSS tables, or “instances affected” claims
- Slack or any chat product as an alert sink
- Pytest that asserts Hermes MCP process trees
- Changing 014 memory tools in order to look like a monitor
- Adding MCP or shell tools to `ToolNode` without a new spec and 013 review

## Traceability

| Want | Where it lives today |
|------|----------------------|
| Boundary + five classes | This folder |
| Linux POC | Out of tree (not this git repo) |
| Graph / `get_agent()` | Spec 014; memory tools only; **no** sensors |
| Review of tool/exec changes | Spec 013 |
| Alert/telemetry privacy | Spec 015 |
| Sensors in this package | **Not present** |

This tasks file is only the checklist view. It does not claim the brain
monitors MCP.
