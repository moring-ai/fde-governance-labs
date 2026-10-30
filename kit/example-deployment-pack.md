# Deployment pack: Example Bank support agent

This is the template filled in for the agent in this repo, with every control switched on. Example Bank is made up, and so are the owners.

## What it is

A support agent for Example Bank customers. A signed-in customer can ask for their balance, a refund (up to $100) or to close their account. It touches one system: the customer database, through three tools.

## Owners

| Role | Name |
|---|---|
| Business owner | Head of Customer Support |
| Technical owner | The FDE team |
| Approver(s) for irreversible actions | Support team leads, through the approvals queue |
| On-call, holds the kill switch | Support platform on-call |
| Data owner | Head of Customer Data |

## Actions

| Action | Can it be undone? | Control | Approver | Limit |
|---|---|---|---|---|
| lookup_account | nothing to undo | scoped access | none | own record only |
| issue_refund | no | approval, limit, kill switch | a named team lead | $100; above that it goes to a colleague |
| close_account | only by a person, by hand | approval | a named team lead | none |

## Data

| Question | Answer |
|---|---|
| What it reads | One customer record: name, nickname, email, balance, status |
| What it writes | Balance (refunds) and status (closures) |
| What it logs, and which fields are personal data | Every step: the customer's message, tool input and output, the reply. Names, emails and balances are personal data. |
| Where traces are stored, and who can read them | traces/ in this repo. In production: the bank's log system, read by security and support leads. |
| Retention period, and who chose it | Open: the data owner hasn't chosen one yet |
| Where it runs (account, region) | In this repo, a laptop. In production: the bank's cloud account. |
| Which model provider sees which data | None here (scripted model). With a real model, the provider sees the prompt, the tool schemas and tool output. |

## Controls

| Control | What it does | Where it lives | The test that proves it |
|---|---|---|---|
| Approvals | Refunds and closures wait for a named person's yes, and the request shows what the customer actually said | `_guarded_call` in agent.py, controls/approvals.py | test_irreversible_action_needs_human_approval, test_instructions_in_data_cannot_move_money |
| Scoped access | Each conversation is bound to the signed-in customer; a call about anyone else is refused before an approver is asked | controls/scope.py | test_agent_cannot_read_another_customers_record |
| Traces | One JSONL line per step, with approver and release hash | controls/traces.py | test_every_tool_call_is_traced, test_trace_names_the_approver |
| Rollback and kill switch | Every release kept; one command back; one tool off without a redeploy | controls/rollback.py, release.py | test_bad_update_can_be_rolled_back, test_kill_switch_turns_off_one_tool_without_a_redeploy |
| Limits | Refunds over $100 go to a colleague | releases/v1/tools.json, enforced in tools.py | test_large_refund_goes_to_a_colleague |

## OWASP coverage

| Item | Status | Evidence or reason |
|---|---|---|
| LLM01 Prompt Injection | tested | Lab 2 (typed), Lab 5 (hidden in a nickname) |
| LLM02 Sensitive Information Disclosure | tested | Lab 2 |
| LLM03 Excessive Agency | tested | Lab 1, Lab 4 |
| LLM06 Unbounded Consumption | partly | each message is capped at 5 model steps; no per-customer rate limit yet |
| LLM08 Hidden Context Exposure | tested | rules live in code; Lab 5 shows the limit is readable by attackers |
| ASI01 Agent Goal Hijack | tested | Lab 2, Lab 5 |
| ASI02 Tool Misuse and Exploitation | tested | Lab 1 |
| ASI03 Identity and Privilege Abuse | tested | Lab 2 |
| ASI09 Human-Agent Trust Exploitation | partly | approval requests carry the customer's words; approvers aren't trained yet |
| AST03 Over-Privileged Skills | partly | the scope check covers it; the database layer can still read any record |
| AST07 Update Drift | tested | releases are pinned by hash (Lab 4) |
| AST09 No Governance | tested | traces and release log (Lab 3, Lab 4) |
| MCP02 Privilege Escalation via Scope Creep | tested | the v2 diff shows the limit change (Lab 4) |
| MCP06 Prompt Injection via Contextual Payloads | tested | Lab 5 |
| MCP07 Insufficient Authentication & Authorization | tested | Lab 2 |
| MCP08 Lack of Audit and Telemetry | tested | Lab 3 |
| Model, skill and dependency supply chain (LLM04, ASI04, AST01, AST02, MCP04) | not applicable here | no third-party models, skills or packages at runtime; becomes open when a real model is added |

## Release and rollback

- How a release ships: `python release.py deploy <version>`, after the tests pass against it.
- How to roll back: `python release.py rollback`. Under a second; tested in Lab 4.
- Kill switch: `python release.py disable issue_refund`, held by support platform on-call.
- Last rehearsal: during the session.

## Evidence

- `pytest --controls=off`: 4 failed, 5 passed, 11 skipped. `pytest --controls=on`: 20 passed.
- `python replay.py examples/injection-attempt.jsonl`: a refused refund, with the approver's note.
- `python release.py status`: the release log with hashes (v1 is b604d9faff10).

## Open risks

| Risk | Why it's accepted for now | Accepted by | Review date |
|---|---|---|---|
| The scope check trusts each tool to name its customer in customer_id | Three tools, all checked by test; moving the check into the database layer is planned | Technical owner | before a fourth tool ships |
| Traces hold personal data with no retention period | Needs the data owner's decision | Data owner | before production |
| The approver is a terminal prompt | Fine for the lab; production needs the bank's queue | Business owner | before production |

## Sign-off

| Reviewer | Role | Date | Decision | Conditions |
|---|---|---|---|---|
| | Security | | | |
| | Data owner | | | |
| | Risk and compliance | | | |
| | Business owner | | | |
