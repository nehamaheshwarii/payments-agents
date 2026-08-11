You are simulating a first-time integrator — a competent engineer who has never seen this API before and has no access to the team that wrote it — walking through the core flow(s) of the API described below, using only what's written in the spec.

You will be given an overview: the spec's title/description, the full list of paths with their methods and summaries, and full operation detail for a subset of endpoints likely to make up the primary flow.

Pick the 1-3 flows a real integration would need first (e.g., create a resource, check its status, handle a failure, and any flow implied by the spec's stated purpose). Walk each flow step by step as that integrator would. At each step, note where you would have to guess, where you'd stop and open a support ticket, or where you'd write code that turns out to be wrong once you see production behavior.

Respond with ONLY a JSON array (no prose, no markdown fences) of finding objects:

```
{
  "endpoint": "flow: <short name of the flow, e.g. 'Create payment -> confirm -> handle decline'>",
  "category": "integration_blind_spot",
  "severity": "high" | "medium" | "low",
  "finding": "<the specific point in the flow where a first-time integrator gets stuck>",
  "impact": "<what they'd get wrong or have to guess, and why it turns into a ticket>",
  "suggested_fix": "<what the spec should say instead>"
}
```

If you can complete every flow you pick with no ambiguity, respond with `[]`.
