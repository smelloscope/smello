# Debug Stripe with Smello

Stripe's Python SDK makes HTTP calls to `api.stripe.com` using the `requests` library. When charges fail, webhooks misbehave, or idempotency keys cause confusion, you need to see the raw API traffic. Smello captures every Stripe API call automatically.

## Setup

```bash
pip install smello smello-server
smello-server  # start the dashboard
```

Then run your script with `smello run`:

```bash
smello run my_stripe_app.py
```

Stripe's Python SDK uses `requests` under the hood (via `urllib3`). Smello captures all API calls automatically. No code changes needed.

## Scenario: debugging a payment that silently fails

A customer reports their payment didn't go through, but your code didn't raise an exception. What happened?

```python
stripe.api_key = "sk_test_..."

charge = stripe.Charge.create(
    amount=2000,
    currency="usd",
    source=token,
    description="Order #1234",
)
# charge.status is "succeeded" but the customer wasn't charged?
```

### Debug in the dashboard

Open the Smello dashboard and filter to `api.stripe.com`:

- **Request body**: see the exact parameters sent to Stripe. Is the `amount` correct? Is the `source` token valid?
- **Response body**: Stripe returns detailed charge objects. Check `status`, `paid`, `failure_code`, and `failure_message`. A charge can return 200 but still have `status: "failed"`.
- **Multiple API calls**: creating a charge might trigger additional calls (customer lookup, payment method validation). You'll see all of them in sequence.

### Debug with an AI agent

If you use [Claude Code](https://claude.ai/code) or another AI coding tool, the `/smello-debugger` skill can query captured events and cross-reference them with your source code. Install it once:

```bash
npx skills add smelloscope/smello --skill smello-debugger
```

Then ask your agent:

```
/smello-debugger
My Stripe charge returns 200 but the customer wasn't charged
```

The skill is also invoked automatically when your agent recognizes a debugging question, but calling `/smello-debugger` explicitly gives the best results. See [AI Agent Skills](../ai-skills.md) for compatible tools.

## Tips

- **Webhook debugging**: If you're using Smello's FastAPI middleware to capture incoming requests, you'll see Stripe webhook `POST` deliveries in the timeline alongside your outgoing API calls. This gives you both sides of the conversation.
- **Idempotency keys**: Stripe's `Idempotency-Key` header is visible in the request headers. If you're seeing unexpected behavior with retries, check that your idempotency keys are unique where they should be and stable where they should be.
- **Stripe-Request-Id**: Every Stripe response includes a `Request-Id` header. When contacting Stripe support, you can grab this directly from the Smello dashboard.
- **Test vs. live keys**: The request URL is the same for test and live mode. Check the API key prefix in the `Authorization` header (redacted by default: un-redact if debugging key issues) or look for `Stripe-Account` headers in Connect scenarios.
- **Pagination**: Stripe list endpoints use cursor-based pagination. You'll see each page request separately in the timeline.

--8<-- "includes/guide-next-steps.md"
