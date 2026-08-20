# Plan: MCP / tool-runtime trust boundary (017)

**Feature**: 017-mcp-runtime-trust-boundary
**Spec**: [spec.md](./spec.md)
**Date**: 2026-08-20
**Status**: Specified. Linux POC out of tree. Not wired into `get_agent()`.

## 1. What this plan is

A map of **where the trust boundary sits** and **what the five detection
classes mean**. It is not a plan to add sensors, an MCP client, or a
security node to `thelab-langchain`.

Success is an honest SDD: the desk treats MCP stdio / tool exec as a
process boundary; defense in depth is runtime watching; the POC stays out
of tree; this package does not pretend to run it.

## 2. Boundary (do not collapse it)

```
desk agent (Hermes, IDE, or future graph tools)
        │
        │  exec / MCP stdio command
        ▼
┌───────────────────────────────────────────┐
│  tool process  ← TRUST BOUNDARY           │
│    children · config · env · network      │
└───────────────────────────────────────────┘
        │
        │  host observations (POC out of tree)
        ▼
  five detection classes → content-free alert (015)
```

`get_agent()` today sits **above** that picture. It compiles a graph with
memory tools (014). It does not launch MCP servers. The voice sibling
calls `get_agent()` (008) and also does not run these sensors.

Collapsing the boundary into “MCP JSON looks fine” or “a future protocol
release will patch it” is a failed design.

## 3. Five classes (distill only)

Implementations stay out of tree. This table is the contract.

| Class | Signal (idea) | Not the signal |
|-------|----------------|----------------|
| Shell metacharacters in child cmdline | Child cmdline of a tool/MCP parent contains shell operators | Full argv dump in git or on the wire |
| Unexpected subprocess vs allow-list | Child binary not on that server’s expected list | A global “malware” catalog in this repo |
| Config file integrity | Watched MCP/tool-host config diverges from a known-good hash | Pasting the new file (secrets) into an alert |
| New-server network watch | Shortly after register/start, outbound peer not on allow-list | Lab IPs, household names, or a full netflow archive |
| Dangerous env var changes | Loader/interpreter-related env changed after snapshot | Dump of the whole environment |

Host techniques the POC *may* use (process table, file watch, connection
table, environ snapshot) are **examples of where to look**. This plan does
not copy scripts, regexes, or audit rule files.

## 4. What already exists vs what does not

| Mechanism | Status |
|-----------|--------|
| This SDD folder | This plan |
| Linux POC (five classes) | Out of tree. Prototype. Detection, not prevention. |
| Workstation MCP processes | Real, outside this package |
| Sensors in `thelab_langchain` | **Not done** |
| MCP client in `get_agent()` | **Not done** (and not this spec’s delivery) |
| Content-free alert path for these classes | Specified via 015; **not** implemented here |
| CVE database / KEV ingest in this repo | **Never** under 017 |

Do not check off “workstation is monitored” because the POC directory
exists on a research machine.

## 5. Sequence (if anyone implements later)

Not a commitment. Default order:

1. **Keep sensors off this package.** Prefer a host-side watcher next to
   the actual MCP/tool processes (workstation runtime), not a LangGraph
   node.
2. **Do not import the POC.** Re-implement against the five classes, or
   keep the POC where it is. Do not vendor it into `src/thelab_langchain/`.
3. **Alerts obey 015.** Rule id + counts/flags + generic names. No
   cmdline-with-args, no config diffs, no transcripts, no keys, no lab IPs.
4. **Fail open.** A dead sensor does not break `get_agent()` or the voice
   loop.
5. **013 before widening the graph.** Adding MCP or shell tools to
   `ToolNode` is a new spec plus reviewer security lens. 017 is not
   permission to add them.

Prevention (kill, freeze config, netns) is a **different** spec with an
operator model. This plan stays detect-and-record.

## 6. Binding 013 and 015

| Spec | Binding |
|------|---------|
| **013** | Tool/exec boundary is security-sensitive. Rubber-stamp is a failed review. Findings: severity, location, fix guidance; no secret dumps. |
| **015** | Sensor alerts are remote/ops data. Tier A only unless a later spec says otherwise. Allow-list fields; ignore unknown keys. No chat-product routing. |

Do not “debug” a class-1 hit by shipping the child cmdline to a collector.
On-host logs, if kept, follow 015’s on-host vs off-host split.

## 7. What we will not do in this plan

- Copy POC Python, tests, or audit rules into this repo.
- Copy research-cycle SUMMARY files, NVD/KEV JSON, or CVE tables.
- Repeat unverifiable stats or flaw chains the research STATUS already
  flagged.
- Claim `thelab_langchain` implements the five classes.
- Wire a monitor into `get_agent()` under 017.
- Put keys, IPs, Slack, or household identifiers in this folder.
- Invent detection rates or coverage percentages.

## 8. Risks

| Risk | Mitigation |
|------|------------|
| Docs imply the brain already watches MCP | Status line on every file in this folder |
| POC copied “for convenience” | FR-7: idea only; no vendor |
| Protocol patch treated as the control | FR-1 / FR-2: process effects + runtime watch |
| Alert contains secrets or transcripts | FR-5 + spec 015 |
| Reviewer skips the boundary on a tool PR | FR-6 + spec 013 |
| Short-lived children missed by polling | Residual risk named; do not claim prevention |
| Unverifiable research stats leak into SDD | Explicit refuse list in the spec |

## 9. Success

- A developer reading this folder can say: tool/MCP exec is a process
  boundary; five classes exist as a POC elsewhere; this package does not
  run them; `get_agent()` is unchanged.
- Git history of `thelab` is not loaded with CVE catalogs, POC source, or
  secret-bearing alert examples.
- Review of later tool-runtime work has a named boundary to tick (013).
