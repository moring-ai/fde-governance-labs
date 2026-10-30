# OWASP cheat sheet

OWASP keeps a top 10 for each layer of an agent system. Your customer's security team uses them to ask where yours breaks.

| Layer | List | Status |
|---|---|---|
| The model | Top 10 for LLM Applications | 2026 edition, released August 2026 |
| The agent | Top 10 for Agentic Applications | 2026 edition, published December 2025 |
| The agent's skills | Agentic Skills Top 10 | 2026 edition, still in development |
| The agent's tools | MCP Top 10 | 2025 edition, in beta |

Names on the last two can still change. Check reading-list.md before you quote one in a review.

## Today's labs, by OWASP item

| Lab | What breaks | LLM 2026 | Agentic 2026 | Skills | MCP | The control |
|---|---|---|---|---|---|---|
| 1 | closes an account, nobody approved | LLM03 | ASI02 | | | approvals |
| 2 | reads another customer's record | LLM01, LLM02 | ASI01, ASI03 | AST03 | MCP07 | scoped access |
| 3 | nobody can say what happened | | | AST09 | MCP08 | traces |
| 4 | a "tone" release raises the refund limit 100x | LLM03 | | AST07 | MCP02 | rollback, kill switch |
| 5 | an account nickname tells it to refund $95 | LLM01, LLM08 | ASI01 | | MCP06 | approvals, with context |

In a review, answer with the control and the test, not the definition.
"How do you handle LLM03?" gets: "Refunds and closures wait for a named approver. Here's the test that fails when they don't."

## Top 10 for LLM Applications (2026)

| ID | Name | In plain words | In the labs |
|---|---|---|---|
| LLM01 | Prompt Injection | Untrusted input changes what the model does, typed in directly or hidden in content it reads. | Lab 2 (typed), Lab 5 (hidden in data) |
| LLM02 | Sensitive Information Disclosure | Confidential data leaks out through answers or context. | Lab 2 |
| LLM03 | Excessive Agency | The model takes real actions through tools with too little access control. | Lab 1, Lab 4 |
| LLM04 | Supply Chain | A model, dependency or data source you pulled in is compromised. | |
| LLM05 | Data and Model Poisoning | Training or fine-tuning data is tampered with to change behaviour. | |
| LLM06 | Unbounded Consumption | Crafted requests burn disproportionate compute and money. | agent.py caps each message at 5 model steps |
| LLM07 | Misinformation | Confident, wrong output that people or systems act on. | |
| LLM08 | Hidden Context Exposure | System prompts, tool schemas and other hidden context leak. Assume they're discoverable. | Lab 5: Chen kept his refund under the limit he could read |
| LLM09 | Vector and Embedding Weaknesses | Retrieval stores leak across users or get poisoned. | |
| LLM10 | Improper Output Handling | Model output reaches a terminal, browser or system without checks. | |

LLM08 replaced 2025's LLM07 System Prompt Leakage.
OWASP's 2025 entry put the principle plainly: a system prompt "should not be considered a secret, nor should it be used as a security control."
That's why the labs keep the irreversible flag and the scope check in code.

## Top 10 for Agentic Applications (2026)

| ID | Name | In plain words | In the labs |
|---|---|---|---|
| ASI01 | Agent Goal Hijack | Text the agent reads redirects what it's trying to do. | Lab 2, Lab 5 |
| ASI02 | Tool Misuse and Exploitation | The agent uses a legitimate tool in an unsafe way. | Lab 1 |
| ASI03 | Identity and Privilege Abuse | The agent acts with more privilege than the person it serves. | Lab 2 |
| ASI04 | Agentic Supply Chain Vulnerabilities | Tools, prompts, models or agents pulled in at runtime are compromised. | |
| ASI05 | Unexpected Code Execution | The agent writes or runs code it shouldn't. | |
| ASI06 | Memory and Context Poisoning | Stored memory or context gets corrupted to steer later runs. | |
| ASI07 | Insecure Inter-Agent Communication | Messages between agents are spoofed or tampered with. | |
| ASI08 | Cascading Failures | One fault spreads across agents and systems. | |
| ASI09 | Human-Agent Trust Exploitation | People trust the agent too much and approve what they shouldn't. | Lab 3 (an auto-approver), Lab 5 (what the approver sees) |
| ASI10 | Rogue Agents | An agent drifts outside what it was built to do. | |

## Agentic Skills Top 10 (2026, in development)

| ID | Name | In plain words | In the labs |
|---|---|---|---|
| AST01 | Malicious Skills | A skill from a registry steals data or runs unauthorized actions. | |
| AST02 | Supply Chain Compromise | A skill's dependencies have no provenance and get tampered with unnoticed. | |
| AST03 | Over-Privileged Skills | A skill has more permission than its job needs. | Lab 2: lookup can read any record |
| AST04 | Insecure Metadata | Skill config is parsed unsafely, so a payload can run. | |
| AST05 | Untrusted External Instructions | A skill pulls instructions from a source that can change under you. | |
| AST06 | Weak Isolation | Skills share a host with no sandbox, so one compromise spreads. | |
| AST07 | Update Drift | A skill floats on a version range instead of a pinned hash and pulls a bad update. | Lab 4: releases carry a hash |
| AST08 | Poor Scanning | Pattern-matching scanners miss natural-language attacks. | |
| AST09 | No Governance | No inventory, no approval workflow, no audit log. | Lab 3 |
| AST10 | Cross-Platform Reuse | A malicious skill is ported across registries, using format differences. | |

## MCP Top 10 (2025, beta)

| ID | Name | In plain words | In the labs |
|---|---|---|---|
| MCP01 | Token Mismanagement & Secret Exposure | Hard-coded or long-lived credentials, secrets in logs or model memory. | |
| MCP02 | Privilege Escalation via Scope Creep | Permissions grow over time until the agent can do too much. | Lab 4: the limit went from $100 to $10,000 |
| MCP03 | Tool Poisoning | A tool, plugin or its output is compromised. | |
| MCP04 | Software Supply Chain Attacks & Dependency Tampering | A compromised dependency changes what the agent does. | |
| MCP05 | Command Injection & Execution | The agent builds and runs commands from untrusted input. | |
| MCP06 | Prompt Injection via Contextual Payloads | The payload is text in the context; the model is the interpreter. | Lab 5 |
| MCP07 | Insufficient Authentication & Authorization | Servers, tools or agents don't check who's asking. | Lab 2 |
| MCP08 | Lack of Audit and Telemetry | Too little logging to investigate an incident. | Lab 3 |
| MCP09 | Shadow MCP Servers | MCP servers running outside the organization's governance. | |
| MCP10 | Context Injection & Over-Sharing | Data from one task or user leaks into another through shared context. | |

## Where the rest fit

Most blank rows above are about what you pull in (models, skills, servers, dependencies) or how you run it (sandboxing, isolation).
Those belong in the deployment pack under "OWASP coverage", each one marked tested, not applicable (say why) or open.
