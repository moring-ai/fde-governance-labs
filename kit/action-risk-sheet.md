# Action risk sheet

List every action the agent can take. One row per tool.
This sheet decides where a human has to say yes, so fill it in before you write the approval code.

## Template

| Action | What it changes | Can it be undone? | Worst case | Who can ask for it | Control | Approver | Limit |
|---|---|---|---|---|---|---|---|
| | | | | | | | |

How to fill it in:

- What it changes: the record, the money or the message, in plain words.
- Can it be undone: yes, no, or "only by a person, by hand". Treat anything that moves money, sends a message, deletes or closes as no until someone proves otherwise.
- Worst case: picture the agent doing this to the wrong customer, or ten times in a row.
- Who can ask for it: who the agent acts for. Usually the signed-in customer, about their own record.
- Control: what stops it going wrong. Name the check, not the prompt line.
- Approver: a role or a named person, not "a human".
- Limit: the number above which a person takes over. Say who owns that number.

## Filled in for this repo's agent

| Action | What it changes | Can it be undone? | Worst case | Who can ask for it | Control | Approver | Limit |
|---|---|---|---|---|---|---|---|
| lookup_account | nothing; it reads one record | nothing to undo | another customer's name, email and balance go to the wrong person | the signed-in customer, for their own record | scoped access (Lab 2) | none | own record only |
| issue_refund | moves money into the account | no | money goes out with no reason, or a lot of it | the signed-in customer | approval (Lab 1), limit, kill switch (Lab 4) | a named person at the bank | $100 per refund; above that it goes to a colleague |
| close_account | closes the account | only by a person, by hand | a customer is locked out of their money | the signed-in customer | approval (Lab 1) | a named person at the bank | none |

## Rules we keep

- The irreversible flag lives in code next to the tool (tools.py), not in config that ships with a prompt edit.
- Limits live in versioned release config, so a change shows up in the release history and the diff.
- A tool nobody can name an approver for doesn't ship.
