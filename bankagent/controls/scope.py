"""Lab 2: the agent can only touch the record of the customer bound to the conversation.

The bound customer comes from the session (who signed in), set when the
conversation starts. Nothing the customer types and nothing the model decides
can change it. The prompt also tells the model to stay on one customer, but a
prompt is a request. This is a check.
"""


def in_scope(args: dict, bound_customer_id: str) -> bool:
    """True only if the tool call names the bound customer. A missing id is out of scope."""
    return args.get("customer_id") == bound_customer_id
