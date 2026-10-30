# Rollback runbook: [agent name]

Write this before go-live. On the bad day nobody should be working out the steps.

## When to use it

Any one of these is enough:

- Money moved, or an account changed, that nobody asked for
- The agent did something the last release wasn't supposed to change
- A reviewer, the business owner or on-call asks for it

## Who decides

| Decision | Who | Backup |
|---|---|---|
| Flip the kill switch | on-call | |
| Roll back the release | on-call or the technical owner | |
| Tell the business owner | on-call | |

Flipping the kill switch never needs permission. Stopping first and asking second is the right order.

## Steps

1. Stop the damage. Switch off the tool that's causing it, not the whole agent.
2. Roll back to the last good release.
3. Confirm what's live: the version and its hash.
4. Switch the tool back on once the right release is live.
5. Find who was affected. Search the traces for the bad release's hash.
6. Tell the business owner what happened, who was affected and what's live now.
7. Fix forward later, with a test that fails on the bad release.

## For this repo

```bash
python release.py disable issue_refund   # 1. stop the damage
python release.py rollback               # 2. back to the last good release
python release.py status                 # 3. confirm version and hash
python release.py enable issue_refund    # 4. tool back on
grep -l bc776244da2f traces/*.jsonl      # 5. every conversation v2 touched
```

## Contacts

| Role | Name | How to reach them |
|---|---|---|
| On-call | | |
| Technical owner | | |
| Business owner | | |

## After

Write a short incident note from the traces: which release, which customers, what moved, who approved, when it stopped.
If an approver said yes to the bad action, change what the approval request shows. Don't blame the approver.
