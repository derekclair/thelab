# Feature Spec: MCP / tool-runtime trust boundary

**Feature ID**: 017-mcp-runtime-trust-boundary
**Status**: Specified. Linux POC exists out of tree. **Not** implemented in
`thelab-langchain`. **Not** wired into `get_agent()`.
**Created**: 2026-08-20
**Owner**: Derek Clair
**Related**: [013-reviewer-quality-gate](../013-reviewer-quality-gate/spec.md),
[015-content-free-telemetry](../015-content-free-telemetry/spec.md),
[014-memory-injection-graph](../014-memory-injection-graph/spec.md)

## Record-keeping note

This spec records a **workstation design**: MCP stdio and other tool
runtimes are a **trust boundary**. A tool process can spawn children, touch
config, set environment variables, and make network calls. Defense in depth
is **runtime monitoring of what that process does**, not a bet that “the
protocol will be patched.”

A Linux proof-of-concept with five detection classes exists **outside this
repository**. This folder distills the boundary and those classes. It does
**not** vendor the POC, copy research-cycle dumps, or import CVE catalogs.

This package has **no** MCP client, **no** host sensors, and **no**
LangGraph node that watches tool processes. `get_agent()` still binds
memory tools only (spec 014). Do not read this folder as “the brain now
monitors MCP.”

Do **not** copy POC source, audit rule files, NVD/KEV JSON, or research-cycle
SUMMARY notes into this tree.

## What this spec refuses to record

The research tree that produced the POC also accumulated CVE lists, CVSS
scores, and cycle stats. Some of those notes are flagged **in that tree** as
unverifiable or hallucinated. This SDD **does not** restate them.

Out of this folder (and out of this git repo) forever:

- CVE identifiers, CVSS numbers, or catalog tables
- Unverifiable counts or “instances affected” figures
- Flaw-chain narratives that the research STATUS already marked unverifiable
- Alert routing to chat products
- Keys, tokens, lab IPs, household identifiers, or private host paths as
  required layout

The design below stands without those claims.

## Overview

On the agent workstation, **tool execution is not a library call with a
pretty schema**. MCP stdio starts a command. That child is a real OS
process. So is any other tool runner that shells out or execs a server.

Once running, that process can:

- spawn further children
- read or rewrite client/server config
- change its environment
- open network connections

Those abilities are the **trust boundary**. Protocol-level review of MCP
messages is useful and is **not** sufficient. A later protocol revision does
not replace host-side observation.

Defense in depth for this desk:

1. **Treat the tool process as untrusted relative to the operator session.**
2. **Watch runtime effects** (children, config, env, new-server network).
3. **Keep alerts content-free** (spec 015).
4. **Do not rubber-stamp** changes that widen this boundary (spec 013).

The five detection classes below are the recorded sensor *ideas*. They are
implemented in an out-of-tree Linux POC. They are **not** shipped here.

```
operator / orchestrator
        │
        ▼
  tool runtime (MCP stdio, or any exec/shell tool)
        │
        ├── children (cmdline, unexpected binaries)
        ├── config files
        ├── environment
        └── network (especially a newly registered server)
                │
                ▼
     host sensors (POC out of tree; not in get_agent())
                │
                ▼
     content-free alerts (015) — no secrets, no transcripts
```

## Goals

- Name MCP stdio / tool execution as a trust boundary on this workstation.
- Record that defense in depth is runtime monitoring, not protocol hope.
- Distill five detection classes without vendoring POC code.
- Stay honest: specified; POC out of tree; this package does not implement
  sensors; `get_agent()` is not wired to them.
- Bind 013 (security-sensitive review) and 015 (alerts must not carry
  secrets or transcripts).

## Non-goals

- Implementing sensors, auditd loaders, eBPF, or an MCP client in
  `thelab-langchain`.
- Wiring a monitor into `get_agent()`, `ToolNode`, or the voice sibling.
- Copying POC source, test suites, or generated audit rules into git.
- A CVE program, KEV tracker, or vulnerability database in this repo.
- Claiming the workstation is “protected” because a POC exists.
- Prevention (kill/quarantine) as a shipped control — the recorded POC is
  **detection**.
- Slack, PagerDuty, or any chat product as an alert sink.
- Changing memory-tool behavior (014) except to note that tool invoke is
  already a boundary, currently HTTP memory rather than MCP stdio.

## Domain terms (define once)

| Term | Meaning |
|------|---------|
| **Trust boundary** | The line where the agent (or MCP client) starts a process whose OS effects are no longer “just a function return.” Children, config, env, and network on the other side are in scope. |
| **Tool runtime** | Anything that execs or shells a tool: MCP stdio servers, LangGraph `ToolNode`, CLI tool hosts. This spec is about that runtime, not about a particular vendor product. |
| **MCP stdio** | MCP transport that launches a server as a child command and talks over stdio. The child is a host process. |
| **Detection class** | One kind of runtime check. Five are recorded here. Not a CVE. |
| **Allow-list** | Expected child executables (or expected endpoints) for a given server. Unknown is alert-worthy. |
| **Sensor** | Host-side watcher that implements a detection class. Lives out of tree today. |
| **Content-free alert** | A signal that a class fired, with low-cardinality labels (rule id, generic process name, path *class*). No secrets, transcripts, tool argument bodies, or config diffs that may contain tokens (015). |
| **Out of tree** | Not in this git repository. The Linux POC is research/workspace code, not a `thelab` module. |

Do not call a protocol changelog “the fix.” Do not call the POC “production
monitoring.” Do not call `get_agent()` an MCP host — it is not.

## Detection classes (ideas, not source)

Five classes. Names are the design. Do not paste POC implementations.

| # | Class | What to watch |
|---|--------|----------------|
| 1 | **Shell metacharacters in child cmdline** | A child of a tool/MCP process whose command line contains shell operators that look like injection (for example `;`, `\|`, `&&`, backticks, `$(…)`). |
| 2 | **Unexpected subprocess vs allow-list** | A child executable that is not on the server’s expected list. |
| 3 | **Config file integrity** | MCP (or tool-host) config files changing away from a known-good baseline, especially from a process that is not a known editor. |
| 4 | **New-server network watch** | Shortly after a server is registered or first started, outbound connections that are not on an allow-list (unknown peers, not loopback). |
| 5 | **Dangerous env var changes** | After a baseline snapshot, changes to process environment that alter loader or interpreter behavior (class examples: `LD_PRELOAD`, `LD_LIBRARY_PATH`, `PYTHONPATH`, `NODE_PATH`). |

These are **host observations**. They do not parse MCP JSON-RPC as the
primary control. They do not require a CVE id to fire.

Residual limits (name them; do not hide them):

- Detection is not prevention. A short-lived child can exit before a poll.
- Allow-lists can be wrong or incomplete.
- Config watch without a baseline is noise.
- Class 4 is a **new-server window**, not a full network IDS.

## Honest current state

| Surface | Today |
|---------|--------|
| This spec folder | Contract and distillation |
| Linux POC | Out of tree. Five classes as a prototype. Not a product. |
| `thelab_langchain` | **No** sensors. **No** MCP stdio client. |
| `get_agent()` | Memory tools + `ToolNode` only (014). **Not** wired to the POC. |
| Workstation MCP (Hermes and similar) | Real tool processes on the desk. Outside this package. The boundary still applies there. |

`get_agent()` tool invoke is already a **smaller** boundary: memory tools
talk to a network store and fail open (014). That is not MCP stdio, and this
spec does not add monitoring around it.

## Functional requirements

### FR-1 Boundary is process effects

- MCP stdio and any exec/shell tool runtime **MUST** be treated as a trust
  boundary: children, config, environment, and network are in scope.
- Reviewers and architects **MUST NOT** treat “the protocol will be patched”
  as the only control.

### FR-2 Runtime monitoring is the defense-in-depth layer

- The recorded control is **watching runtime effects**, not a protocol
  patch, not a prompt filter, and not a CVE chase.
- Sensors, when they exist, run **beside** the tool process (host), not as
  a required step inside `get_agent()`.

### FR-3 Five classes

- The distilled class list is the five rows above.
- A later implementation **MAY** refine signals. It **MUST NOT** drop a
  class silently without a spec change.
- This package **MUST NOT** claim those sensors are present until they live
  in a named, accepted follow-up and actually run.

### FR-4 Honesty of this package

- Docs **MUST NOT** claim `thelab-langchain` monitors MCP or tool processes.
- `get_agent()` **MUST NOT** grow an MCP client or sensor loop under this
  spec.
- Do not vendor POC source into `src/` “as a port.”

### FR-5 Alerts follow 015

If sensors emit (out of tree or in a later spec):

- **MUST NOT** include transcripts, prompts, completions, tool argument or
  result bodies, API keys, tokens, `.env` values, or config file contents
  that may hold secrets.
- **MUST NOT** include lab IPs or household identifiers (015 FR-2).
- **MAY** include: rule class id, generic process name, boolean/count, path
  *class* (for example “mcp-config”), not a dump of the file.
- Unknown payload keys are ignored. Allow-list, not redaction.
- Do not route those alerts to a chat product from this spec.

### FR-6 Review (013)

- Tool/exec boundaries are **security-sensitive**.
- A spec or PR that adds MCP, shell tools, or a wider `ToolNode` **MUST NOT**
  be rubber-stamped. Reviewer applies the security and privacy lenses (013).
- Findings **MUST NOT** paste secrets or cmdline dumps that contain secrets.

### FR-7 Out-of-tree POC is not this repo

- Point at the **idea** of the five classes.
- Do not copy POC Python, audit rule files, or demo transcripts into git.
- Do not make a private research path required layout for this package.

## Non-functional requirements

- No keys, IPs, Slack, household identifiers, or CVE dump tables in this
  spec, plan, or tasks.
- No invented detection rates, false-positive percentages, or “instances
  protected.”
- Sensors, if later built, must fail open relative to the voice loop and
  `get_agent()`: a down monitor does not break the turn (same fail-open
  spirit as 015 / 014).
- SDD in this folder stays human prose. Do not vendor skill bodies.

## User stories

1. As the person at the desk, I know a tool/MCP child is a real process, not
   a sandboxed RPC.
2. As an operator, I know defense in depth is watching children, config,
   env, and new-server network — not waiting for a protocol patch.
3. As a developer of this package, I know `get_agent()` does not host MCP
   and does not run those sensors.
4. As a reviewer (013), I do not approve a wider tool/exec boundary without
   the security lens.
5. As an operator of telemetry (015), an alert that a class fired does not
   ship my conversation or my keys.

## Acceptance criteria (for this SDD record)

- [x] This folder contains `spec.md`, `plan.md`, and `tasks.md` that name
      the trust boundary, runtime monitoring as defense in depth, and the
      five detection classes.
- [x] Status is specified; POC out of tree; not a `thelab-langchain`
      feature; not wired into `get_agent()`.
- [x] Related specs 013 and 015 are cited (no rubber-stamp; content-free
      alerts).
- [x] No CVE tables, CVSS scores, unverifiable stats, POC source, keys,
      IPs, or chat-product routing in this folder.
- [ ] Sensors in this package — **not done**.
- [ ] Wiring into `get_agent()` — **not done** (out of scope for 017).

## Seams this package must keep stable

| Seam | Contract |
|------|----------|
| `get_agent(user_id)` | Unchanged. No MCP client. No sensor side-effect. |
| `ToolNode` / memory tools | Still 014: profile, recall, store; fail-open invoke. Not an MCP host. |
| Workstation MCP | Outside this package. Boundary still applies. |
| Sensor process | Out of tree. Not imported by this package. |
| Alert payload | 015 allow-list if anything is exported. |

## Relationship to other specs

- **013** — Tool/exec boundaries are security-sensitive. Reviewer does not
  rubber-stamp them. This spec is *what* the boundary is; 013 is *how*
  review treats it.
- **015** — Telemetry and alerts are content-free. Sensor output is not a
  transcript archive and not a secrets store.
- **014** — Shipped graph. Memory `ToolNode` is the only tool runtime in
  this package today. 017 does not add tools.
- **010** — Secrets stay off the board; same classes stay out of findings
  and alerts.
- **012** — Fleet dispatch. This spec does not add a “security scanner”
  roster slot or a dispatcher in this package.
- **008** — Voice I/O calls `get_agent()`. I/O does not become the MCP
  monitor.

## Open questions

- Whether a later spec should run host sensors next to Hermes (workstation)
  rather than inside this Python package. Default: **workstation / out of
  tree, not `get_agent()`.**
- Whether a later spec should add MCP tools to the graph at all. Default:
  **not in 017.** If it happens, 013 + this boundary apply first.
- Prevention (kill child, freeze config) vs detect-and-alert. Default:
  **detection only**, until a later spec with an explicit operator model.
