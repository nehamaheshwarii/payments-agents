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


---

## Spec overview

```json
{
  "info": {
    "title": "Sample Payments API",
    "version": "1.0",
    "description": "A minimal payments API used to demonstrate the API Spec Auditor."
  },
  "paths": [
    {
      "path": "/payments",
      "method": "POST",
      "summary": "Create a payment",
      "description": null
    },
    {
      "path": "/payments/{id}",
      "method": "GET",
      "summary": "Retrieve a payment",
      "description": null
    }
  ],
  "core_flow_detail": [
    {
      "path": "/payments",
      "method": "POST",
      "operation": {
        "summary": "Create a payment",
        "operationId": "createPayment",
        "requestBody": {
          "required": true,
          "content": {
            "application/json": {
              "schema": {
                "type": "object",
                "required": [
                  "amount",
                  "currency",
                  "merchant_id"
                ],
                "properties": {
                  "amount": {
                    "type": "integer",
                    "description": "Amount in the smallest currency unit."
                  },
                  "currency": {
                    "type": "string",
                    "example": "usd"
                  },
                  "merchant_id": {
                    "type": "string"
                  },
                  "idempotency_key": {
                    "type": "string"
                  },
                  "metadata": {
                    "type": "object",
                    "additionalProperties": true
                  }
                }
              }
            }
          }
        },
        "responses": {
          "201": {
            "description": "Payment created",
            "content": {
              "application/json": {
                "schema": {
                  "type": "object",
                  "properties": {
                    "id": {
                      "type": "string"
                    },
                    "amount": {
                      "type": "integer"
                    },
                    "currency": {
                      "type": "string"
                    },
                    "status": {
                      "type": "string",
                      "enum": [
                        "pending",
                        "processing",
                        "succeeded",
                        "failed",
                        "requires_action"
                      ]
                    },
                    "merchant_id": {
                      "type": "string"
                    },
                    "created_at": {
                      "type": "string",
                      "format": "date-time"
                    },
                    "expires_at": {
                      "type": "string",
                      "format": "date-time"
                    }
                  }
                }
              }
            }
          },
          "402": {
            "description": "Payment failed"
          },
          "409": {
            "description": "Conflict"
          }
        }
      }
    },
    {
      "path": "/payments/{id}",
      "method": "GET",
      "operation": {
        "summary": "Retrieve a payment",
        "operationId": "getPayment",
        "parameters": [
          {
            "name": "id",
            "in": "path",
            "required": true,
            "schema": {
              "type": "string"
            }
          }
        ],
        "responses": {
          "200": {
            "description": "Payment found",
            "content": {
              "application/json": {
                "schema": {
                  "type": "object",
                  "properties": {
                    "id": {
                      "type": "string"
                    },
                    "amount": {
                      "type": "integer"
                    },
                    "currency": {
                      "type": "string"
                    },
                    "status": {
                      "type": "string",
                      "enum": [
                        "pending",
                        "processing",
                        "succeeded",
                        "failed",
                        "requires_action"
                      ]
                    },
                    "merchant_id": {
                      "type": "string"
                    },
                    "created_at": {
                      "type": "string",
                      "format": "date-time"
                    },
                    "expires_at": {
                      "type": "string",
                      "format": "date-time"
                    }
                  }
                }
              }
            }
          },
          "404": {
            "description": "Not found"
          }
        }
      }
    }
  ]
}
```
