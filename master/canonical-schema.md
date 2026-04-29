# DeployGTM Canonical Schema

This document defines the shape of every JSON artifact produced by the Signal Audit pipeline. These schemas are the contract between stages. If a stage output changes shape, this document changes first, then the producing stage, then the consuming stage.

All changes to scoring weights, field names, or required fields must be reflected here before the code changes.

---

## intake.json

```json
{
  "schema_version": "v1.0",
  "engagement_type": "Signal Audit",
  "client_name": "string",
  "client_slug": "string",
  "domain": "string",
  "target_outcome": "string",
  "offer": "string",
  "constraints": ["string"],
  "current_tools": {
    "crm": "string",
    "outreach": "string"
  },
  "crm_provider": "hubspot | salesforce | attio | none",
  "sequencing_mode": "draft_only | active",
  "crm_scope": "deploygtm_found_leads_tasks_only | full_ingest",
  "managed_sending": "deferred_until_deliverability_controls_exist | active",
  "created_on": "YYYY-MM-DD"
}
```

**Governance defaults (never override without explicit client confirmation):**
- `sequencing_mode: draft_only`
- `crm_scope: deploygtm_found_leads_tasks_only`
- `managed_sending: deferred_until_deliverability_controls_exist`

---

## context_pack.json

```json
{
  "schema_version": "v1.0",
  "client_slug": "string",
  "generated_on": "YYYY-MM-DD",
  "principles": [
    {
      "id": "string",
      "statement": "string",
      "evidence": [
        {
          "source_type": "brain | intake | transcript",
          "source_ref": "brain/icp.md:12",
          "evidence_snippet": "string"
        }
      ]
    }
  ]
}
```

**Required:** every principle must have at least one evidence entry with a `source_ref` that resolves to an actual file path + line number.

---

## icp_strategy.json

```json
{
  "schema_version": "v1.0",
  "client_slug": "string",
  "generated_on": "YYYY-MM-DD",
  "strategy": {
    "market_hypotheses": ["string"],
    "icps": [
      {
        "name": "string",
        "description": "string",
        "fit_criteria": ["string", "string", "string", "string"],
        "personas": [
          {
            "title": "string",
            "problem_ownership_reason": "string"
          }
        ],
        "disqualifiers": ["string"],
        "source_trace": ["context_pack.json principle id"]
      }
    ]
  }
}
```

**Required:** exactly 2 ICPs. Each ICP must have at least 1 disqualifier. `fit_criteria` must have exactly 4 items. `source_trace` must be non-empty.

---

## signal_strategy.json

```json
{
  "schema_version": "v1.1",
  "client_slug": "string",
  "generated_on": "YYYY-MM-DD",
  "signals": [
    {
      "id": "string",
      "display_order": 1,
      "name": "string",
      "category": "capital_event | hiring | leadership | market_motion | technology | pain | market | risk | timing | education | downstream | operations",
      "description": "string",
      "why_it_matters": "string",
      "mapped_icp": "string",
      "bird_dog_query_hint": "string",
      "evidence_required": ["string"],
      "alpha": false,
      "ability_indicator": false,
      "willingness_indicator": false,
      "rationale": "string | null"
    }
  ]
}
```

**New in v1.1:**

| Field | Type | Description |
|---|---|---|
| `alpha` | bool | `true` if this is a client-specific non-generic signal derived from ICP strategy. `false` for standard templates. |
| `ability_indicator` | bool | `true` if this signal provides evidence the account can act (budget, headcount, decision cycle). |
| `willingness_indicator` | bool | `true` if this signal provides evidence the account wants to act (active pain, urgency, stated intent). |
| `rationale` | string or null | Required when `alpha: true`. Explains why this signal is non-generic and how it was derived. Null for template signals. |

**Alpha signal rules:**
- A signal is only `alpha: true` if it was derived from client-specific ICP context, not copied from `SIGNAL_TEMPLATES` as-is.
- Alpha signals should confirm both `ability_indicator` and `willingness_indicator` when possible. A signal that confirms only one is weaker but valid.
- The audit is incomplete if fewer than 2 alpha signals exist per ICP in the final output.
- Generic template signals (funding, hiring, exec change) default to `alpha: false` and should carry explicit `ability_indicator` / `willingness_indicator` values — they are not automatically both.

**Example alpha signal:**
```json
{
  "id": "downstream_customer_consolidation",
  "display_order": 21,
  "name": "Their customer segment is consolidating",
  "category": "downstream",
  "description": "A downstream customer vertical is consolidating — M&A, category contraction, or platform lock-in — forcing the target to re-evaluate their GTM stack before the window closes.",
  "why_it_matters": "Forces urgency without requiring a new budget cycle. The trigger is external and not in their control.",
  "mapped_icp": "Founder-Seller at Series A SaaS",
  "bird_dog_query_hint": "M&A activity in [vertical]. Look for accounts whose top customers are being acquired or exiting.",
  "evidence_required": ["company domain", "acquisition announcement URL", "affected customer name"],
  "alpha": true,
  "ability_indicator": true,
  "willingness_indicator": true,
  "rationale": "Derived from ICP fit criteria: target ICP sells to [vertical]. Consolidation in [vertical] creates a forcing function that activates both urgency and budget authority simultaneously."
}
```

---

## accounts.json

```json
{
  "client": {
    "client_name": "string",
    "client_slug": "string",
    "crm_provider": "string",
    "generated_on": "YYYY-MM-DD"
  },
  "accounts": [
    {
      "company": "string",
      "domain": "string",
      "signals": [
        {
          "type": "string",
          "date": "YYYY-MM-DD",
          "source": "birddog | apollo | manual | supersend",
          "summary": "string",
          "birddog_score": null,
          "alpha": false,
          "ability_indicator": false,
          "willingness_indicator": true
        }
      ],
      "contacts": [
        {
          "email": "string",
          "name": "string",
          "title": "string",
          "linkedin_url": "string | null",
          "metadata": {}
        }
      ],
      "scores": {
        "icp_fit_score": 0,
        "urgency_score": 0,
        "engagement_score": 0,
        "confidence_score": 0,
        "activation_priority": 0,
        "rationale": ["string"]
      },
      "engagement": {
        "status": "active | bounced | unsubscribed | cold",
        "open_count": 0,
        "click_count": 0,
        "reply_count": 0,
        "bounce_count": 0,
        "unsubscribe_count": 0,
        "events": [
          {
            "type": "open | click | reply | bounce | unsubscribe",
            "timestamp": "ISO8601"
          }
        ]
      },
      "copy": {
        "opener": "string",
        "reason": "string"
      }
    }
  ]
}
```

**Signal fields on account signals (v1.1 addition):**
The `alpha`, `ability_indicator`, and `willingness_indicator` fields from `signal_strategy.json` carry forward to the account-level signal objects. When `account_matrix.py` populates signals, it should inherit these values from the matched signal strategy entry.

**Scoring invariant:**
```
activation_priority = round(
    0.45 * icp_fit_score
  + 0.35 * urgency_score
  + 0.10 * engagement_score
  + 0.10 * confidence_score
)
```

Do not compute `activation_priority` any other way. If the formula changes, change this document first.

---

## crm_push_plan.json

```json
{
  "schema_version": "v1.0",
  "client_slug": "string",
  "generated_on": "YYYY-MM-DD",
  "dry_run": true,
  "writes_enabled": false,
  "requires_explicit_approval": true,
  "crm_provider": "string",
  "scope": "deploygtm_found_leads_tasks_only",
  "min_activation_priority": 60,
  "planned_records": [
    {
      "company": {
        "name": "string",
        "domain": "string",
        "properties": {
          "deploygtm_activation_priority": 0,
          "deploygtm_icp_fit_score": 0,
          "deploygtm_urgency_score": 0,
          "deploygtm_confidence_score": 0
        }
      },
      "contacts": [],
      "tasks": [
        {
          "type": "sales_follow_up",
          "subject": "string",
          "body": "string"
        }
      ],
      "notes": [
        {
          "body": "string"
        }
      ],
      "deal": {
        "name": "string",
        "stage": "outreach_ready",
        "source": "DeployGTM Signal Audit"
      },
      "copy": {
        "opener": "string",
        "reason": "string"
      }
    }
  ],
  "deferred_records": [],
  "guardrails": [
    "Do not ingest or modify the entire client CRM.",
    "Do not send email from this plan.",
    "Do not write to production CRM without explicit confirmation.",
    "Only push DeployGTM-found accounts, contacts, notes, tasks, and deals."
  ]
}
```

**Required guardrails array must be present and non-empty.** Any code that strips the guardrails array is a bug.

---

## birddog_signal_manifest.json

Derived from `signal_strategy.json`. Used to configure BirdDog monitoring or for manual export.

```json
{
  "client_slug": "string",
  "generated_on": "YYYY-MM-DD",
  "signals": [
    {
      "id": "string",
      "name": "string",
      "query_hint": "string",
      "mapped_icp": "string",
      "alpha": false,
      "ability_indicator": false,
      "willingness_indicator": false
    }
  ]
}
```

Alpha signals and their indicators carry through from `signal_strategy.json`. BirdDog integration should prioritize alpha signals when configuring monitoring rules.

---

## Schema versioning

When a field is added, increment the minor version (v1.0 → v1.1). When a field is removed or renamed, increment the major version (v1.x → v2.0) and add a migration note here.

**v1.1 changes (2026-04-29):**
- `signal_strategy.json`: added `alpha`, `ability_indicator`, `willingness_indicator`, `rationale` to each signal object.
- `accounts.json`: added `alpha`, `ability_indicator`, `willingness_indicator` to each signal object within the `signals` array.
- `birddog_signal_manifest.json`: added `alpha`, `ability_indicator`, `willingness_indicator` to each signal entry.
