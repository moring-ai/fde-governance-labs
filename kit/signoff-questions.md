# Sign-off questions

Four people usually have to say yes before an agent touches a customer's production systems. Each one asks different questions, and the FDE in the room tends to answer all of them.

A good answer shows something working. "We told the model not to" isn't an answer. A failing test that passes with the control on is one.

## Security

| They ask | A good answer shows | In the labs |
|---|---|---|
| What can it do without a person saying yes? | The action risk sheet, and approvals on every irreversible tool | Lab 1 |
| What stops someone talking it into another customer's data? | A scope bound at sign-in, checked in code on every call | Lab 2 |
| What if text in your own data tells it to do something? | Controls on the tool call, which don't care where the instruction came from | Lab 5 |
| Where do its credentials live, and who else can use them? | Its own identity in our account, short-lived, nothing shared | controls-map.md |
| How do we turn it off at 2am? | A kill switch that works without a redeploy, and the name of whoever holds it | Lab 4 |

## Data owner

| They ask | A good answer shows | In the labs |
|---|---|---|
| Which records can it read, and on whose behalf? | One customer per conversation, the one who signed in | Lab 2 |
| What does it write down, and who can read that? | The trace format, what's in it (names, emails, balances) and who has access | Lab 3 |
| How long do you keep it? | A retention period the data owner chose | deployment pack, Data |
| Does our data leave our environment? | Where the agent runs, which model provider sees what, which region | controls-map.md |

## Risk and compliance

| They ask | A good answer shows | In the labs |
|---|---|---|
| Who approved this refund, and when? | A trace line with the approver's name, their answer and a timestamp | Lab 3 |
| What changed between Tuesday and today? | Release history with a hash for every version that ran | Lab 4 |
| Can you show me it working? | The test run: failures with controls off, passes with them on | every lab |
| Which OWASP items did you test? | The coverage table: tested, not applicable and open | owasp-cheatsheet.md |
| What's still open? | A short list of known gaps, each one accepted by a named person | deployment pack, Open risks |

## Business owner

| They ask | A good answer shows | In the labs |
|---|---|---|
| What will it do for customers, and what won't it? | The tool list and its limits, in plain words | action-risk-sheet.md |
| What's the worst it can do on a bad day? | The irreversible actions, and the most money it can move at once | action-risk-sheet.md |
| How fast can we stop it? | Kill switch and rollback, timed in a rehearsal | Lab 4 |
| When does a person take over? | The handoff rules, for example refunds over $100 go to a colleague | Lab 4 |
| Who gets paged? | The runbook, with names | rollback-runbook.md |

## Questions to ask them back

- Who is the approver, and where do they want approval requests to show up?
- Who holds the kill switch out of hours?
- Which log system should traces go to, and who can read it?
- What's the refund limit, or any money limit, and who owns that number?
