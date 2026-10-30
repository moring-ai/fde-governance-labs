# Controls map

Every control has a part in your code and a part in the customer's world. Plan both on day one.

| Control | In your code | In the cloud account | In the customer's systems |
|---|---|---|---|
| Approvals | The gate before every irreversible call (`_guarded_call` in agent.py) | Where pending requests wait | The approver: their staff, in their queue, ticket or chat tool |
| Scoped access | The check that the call names the bound customer | The agent's own identity, with access only to what it needs | The sign-in that binds the customer, and the data owner's access rules |
| Traces | One record per step: input, output, approver, release | Storage, encryption and retention for the trace files | Their audit or SIEM tooling, and the people allowed to read it |
| Rollback | Every release kept, with a hash | The config store that holds the history | The change process that decides when to roll back |
| Kill switch | Read on every tool call, so it works without a redeploy | Who has permission to flip it | The on-call person who holds it out of hours |
| Limits | Enforced in the tool, read from versioned config | | The policy owner who sets the number |

OWASP's Agent Control Standard (version 0.1, donated in September 2026) names the same pattern: policy enforcement points at runtime, agents you can inspect and trace, and an Agent Bill of Materials.
`_guarded_call` is a policy enforcement point.

## Why not your own AWS account

It's the fastest way to get a demo running, and it fails review for reasons that have nothing to do with your code.

- The customer can't see it. Their security team can't watch logs they don't own.
- They can't audit it. Who changed the prompt last Tuesday? The answer sits in your account.
- They can't switch it off. Stopping it means calling you at 2am.
- Their data leaves their boundary. Every customer record the agent reads crosses into an account their contracts don't cover.

So the agent runs in the customer's account, on their identity, writing traces to their log system, with the kill switch held by their on-call.
Build it that way from the first demo, even if the first demo runs in a sandbox account that looks like theirs.
