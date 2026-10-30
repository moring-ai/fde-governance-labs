# Deployment pack: [agent name]

This is the document the reviewers sign. Keep it short, keep every claim backed by evidence, and update it with every release.

## What it is

One paragraph: what the agent does, for whom, and which systems it touches.

## Owners

| Role | Name |
|---|---|
| Business owner | |
| Technical owner | |
| Approver(s) for irreversible actions | |
| On-call, holds the kill switch | |
| Data owner | |

## Actions

Paste the action risk sheet: one row per tool, with what it changes, whether it can be undone, the control, the approver and the limit.

## Data

| Question | Answer |
|---|---|
| What it reads | |
| What it writes | |
| What it logs, and which fields are personal data | |
| Where traces are stored, and who can read them | |
| Retention period, and who chose it | |
| Where it runs (account, region) | |
| Which model provider sees which data | |

## Controls

| Control | What it does | Where it lives | The test that proves it |
|---|---|---|---|
| Approvals | | | |
| Scoped access | | | |
| Traces | | | |
| Rollback and kill switch | | | |
| Limits | | | |

## OWASP coverage

List every item on the four lists you checked (LLM, Agentic, Agentic Skills, MCP), each one marked:

| Item | Status | Evidence or reason |
|---|---|---|
| | tested / not applicable / open | |

## Release and rollback

- How a release ships, and who approves it:
- How to roll back, and how long it takes:
- Who holds the kill switch, and how to reach them:
- Last rehearsal date:

## Evidence

Attach these. A reviewer should be able to check each claim above against one of them.

- The test run with controls off (the failures) and on (the passes)
- One replayed trace that shows an approval and a refusal
- The release log, with hashes

## Open risks

| Risk | Why it's accepted for now | Accepted by | Review date |
|---|---|---|---|
| | | | |

## Sign-off

| Reviewer | Role | Date | Decision | Conditions |
|---|---|---|---|---|
| | Security | | | |
| | Data owner | | | |
| | Risk and compliance | | | |
| | Business owner | | | |
