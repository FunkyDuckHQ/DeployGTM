"""
DeployGTM — HubSpot CRM Sync

Pushes enriched accounts and contacts to HubSpot.
ALWAYS requires explicit confirmation before writing to production CRM.

Custom properties created by this script (run setup_properties() once):
  Signal Source, Signal Type, Signal Date, Signal Summary,
  ICP Fit Score, Signal Strength, Priority Score,
  Pain Hypothesis, Enrichment Confidence, Outreach Angle

HubSpot API v3: https://developers.hubspot.com/docs/api/crm/contacts

Standalone:
  python scripts/hubspot.py setup-properties
  python scripts/hubspot.py push --pipeline-output output/acme_2024-03-15.json
  python scripts/hubspot.py push --pipeline-output output/acme_2024-03-15.json --dry-run
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Optional

import click
import requests
import yaml
from dotenv import load_dotenv

load_dotenv()

HS_BASE = "https://api.hubapi.com"


def load_config(config_path: str = "config.yaml") -> dict:
    with open(config_path) as f:
        return yaml.safe_load(f)


def _headers() -> dict:
    token = os.environ.get("HUBSPOT_ACCESS_TOKEN", "")
    if not token:
        raise EnvironmentError(
            "HUBSPOT_ACCESS_TOKEN is not set. Add it to your .env file.\n"
            "Create a private app at: HubSpot → Settings → Integrations → Private Apps\n"
            "Scopes: crm.objects.contacts.write, crm.objects.companies.write, "
            "crm.schemas.contacts.write"
        )
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }


# ─── Custom property definitions ─────────────────────────────────────────────

CUSTOM_CONTACT_PROPERTIES = [
    {
        "name": "deploygtm_signal_source",
        "label": "Signal Source",
        "type": "string",
        "fieldType": "text",
        "groupName": "contactinformation",
        "description": "Where the buying signal was detected (e.g. BirdDog, LinkedIn, Crunchbase)",
    },
    {
        "name": "deploygtm_signal_type",
        "label": "Signal Type",
        "type": "enumeration",
        "fieldType": "select",
        "groupName": "contactinformation",
        "description": "Type of buying signal",
        "options": [
            {"label": "Funding", "value": "funding", "displayOrder": 1},
            {"label": "Hiring (Sales)", "value": "hiring", "displayOrder": 2},
            {"label": "GTM Struggle Post", "value": "gtm_struggle", "displayOrder": 3},
            {"label": "Agency Churn", "value": "agency_churn", "displayOrder": 4},
            {"label": "Tool Adoption", "value": "tool_adoption", "displayOrder": 5},
            {"label": "Manual / ICP Match", "value": "manual", "displayOrder": 6},
        ],
    },
    {
        "name": "deploygtm_signal_date",
        "label": "Signal Date",
        "type": "date",
        "fieldType": "date",
        "groupName": "contactinformation",
        "description": "Date the buying signal was detected",
    },
    {
        "name": "deploygtm_signal_summary",
        "label": "Signal Summary",
        "type": "string",
        "fieldType": "textarea",
        "groupName": "contactinformation",
        "description": "Free-text description of the signal",
    },
    {
        "name": "deploygtm_icp_fit_score",
        "label": "ICP Fit Score",
        "type": "number",
        "fieldType": "number",
        "groupName": "contactinformation",
        "description": "ICP fit score 1–5 (5 = perfect fit)",
    },
    {
        "name": "deploygtm_signal_strength",
        "label": "Signal Strength",
        "type": "number",
        "fieldType": "number",
        "groupName": "contactinformation",
        "description": "Signal strength score 1–3 (3 = active signal < 30 days)",
    },
    {
        "name": "deploygtm_priority_score",
        "label": "Priority Score",
        "type": "number",
        "fieldType": "number",
        "groupName": "contactinformation",
        "description": "Priority = ICP Fit × Signal Strength (max 15). ≥12 = reach out immediately.",
    },
    {
        "name": "deploygtm_urgency_score",
        "label": "Urgency Score",
        "type": "number",
        "fieldType": "number",
        "groupName": "contactinformation",
        "description": "0-100 current urgency score from signal strength, BirdDog alerts, and recency decay",
    },
    {
        "name": "deploygtm_engagement_score",
        "label": "Engagement Score",
        "type": "number",
        "fieldType": "number",
        "groupName": "contactinformation",
        "description": "0-100 score from email/CRM engagement; defaults to 0 before tests begin",
    },
    {
        "name": "deploygtm_confidence_score",
        "label": "Confidence Score",
        "type": "number",
        "fieldType": "number",
        "groupName": "contactinformation",
        "description": "0-100 confidence score based on source quality and enrichment completeness",
    },
    {
        "name": "deploygtm_activation_priority",
        "label": "Activation Priority",
        "type": "number",
        "fieldType": "number",
        "groupName": "contactinformation",
        "description": "0-100 action ordering score; ICP fit and urgency remain separate fields",
    },
    {
        "name": "deploygtm_score_decay",
        "label": "Score Decay",
        "type": "string",
        "fieldType": "textarea",
        "groupName": "contactinformation",
        "description": "JSON/rationale for signal recency decay used in urgency scoring",
    },
    {
        "name": "deploygtm_pain_hypothesis",
        "label": "Pain Hypothesis",
        "type": "string",
        "fieldType": "textarea",
        "groupName": "contactinformation",
        "description": "Claude-generated hypothesis about the contact's GTM pain",
    },
    {
        "name": "deploygtm_enrichment_confidence",
        "label": "Enrichment Confidence",
        "type": "enumeration",
        "fieldType": "select",
        "groupName": "contactinformation",
        "description": "Confidence level of research data",
        "options": [
            {"label": "High", "value": "high", "displayOrder": 1},
            {"label": "Medium", "value": "medium", "displayOrder": 2},
            {"label": "Low", "value": "low", "displayOrder": 3},
        ],
    },
    {
        "name": "deploygtm_outreach_angle",
        "label": "Outreach Angle",
        "type": "enumeration",
        "fieldType": "select",
        "groupName": "contactinformation",
        "description": "Which messaging persona was used for outreach",
        "options": [
            {"label": "Founder-Seller", "value": "founder_seller", "displayOrder": 1},
            {"label": "First Sales Leader", "value": "first_sales_leader", "displayOrder": 2},
            {"label": "RevOps / Growth", "value": "revops_growth", "displayOrder": 3},
        ],
    },
]


def setup_properties(dry_run: bool = False) -> list[dict]:
    """
    Create all DeployGTM custom contact properties in HubSpot.
    Safe to run multiple times — skips existing properties.
    """
    results = []
    for prop in CUSTOM_CONTACT_PROPERTIES:
        if dry_run:
            click.echo(f"  [dry-run] Would create property: {prop['name']}")
            results.append({"property": prop["name"], "status": "dry_run"})
            continue

        resp = requests.post(
            f"{HS_BASE}/crm/v3/properties/contacts",
            headers=_headers(),
            json=prop,
            timeout=15,
        )

        if resp.status_code == 409:
            results.append({"property": prop["name"], "status": "already_exists"})
            click.echo(f"  ✓ {prop['name']} (already exists)")
        elif resp.status_code in (200, 201):
            results.append({"property": prop["name"], "status": "created"})
            click.echo(f"  + {prop['name']} (created)")
        else:
            results.append({"property": prop["name"], "status": "error", "detail": resp.text})
            click.echo(f"  ✗ {prop['name']} — {resp.status_code}: {resp.text}", err=True)

    return results


# ─── Upsert helpers ───────────────────────────────────────────────────────────

def upsert_company(company_data: dict, dry_run: bool = False) -> Optional[str]:
    """
    Create or update a company record. Returns the HubSpot company ID.
    Matches by domain.
    """
    domain = company_data.get("domain", "")
    if not domain:
        return None

    props = {
        "name": company_data.get("name") or company_data.get("company", ""),
        "domain": domain,
        "numberofemployees": str(company_data.get("employee_count") or ""),
        "industry": company_data.get("industry", ""),
        "city": company_data.get("city", ""),
        "state": company_data.get("state", ""),
    }
    props = {k: v for k, v in props.items() if v}

    if dry_run:
        click.echo(f"  [dry-run] Would upsert company: {props.get('name', domain)}")
        return "dry_run_company_id"

    resp = requests.post(
        f"{HS_BASE}/crm/v3/objects/companies",
        headers=_headers(),
        json={"properties": props},
        timeout=15,
    )

    if resp.status_code in (200, 201):
        return resp.json()["id"]

    # Try to find existing by domain
    search = requests.post(
        f"{HS_BASE}/crm/v3/objects/companies/search",
        headers=_headers(),
        json={
            "filterGroups": [{"filters": [
                {"propertyName": "domain", "operator": "EQ", "value": domain}
            ]}],
            "limit": 1,
        },
        timeout=15,
    )
    results = search.json().get("results", [])
    if results:
        company_id = results[0]["id"]
        # Update existing
        requests.patch(
            f"{HS_BASE}/crm/v3/objects/companies/{company_id}",
            headers=_headers(),
            json={"properties": props},
            timeout=15,
        )
        return company_id

    click.echo(f"  ✗ Could not upsert company {domain}: {resp.status_code}", err=True)
    return None


def upsert_contact(
    contact: dict,
    score: dict,
    outreach: Optional[dict],
    signal: dict,
    research: dict,
    company_id: Optional[str],
    dry_run: bool = False,
) -> Optional[str]:
    """
    Create or update a contact record with all DeployGTM enrichment data.
    Returns the HubSpot contact ID.
    """
    email = contact.get("email", "")
    if not email:
        click.echo(f"  ~ Skipping {contact.get('name', 'unknown')} — no email", err=True)
        return None

    props = {
        "email": email,
        "firstname": (contact.get("name", "") or "").split()[0] if contact.get("name") else "",
        "lastname": " ".join((contact.get("name", "") or "").split()[1:]) if contact.get("name") else "",
        "jobtitle": contact.get("title", ""),
        "hs_linkedin_bio": contact.get("linkedin_url", ""),
        "phone": contact.get("phone", ""),
        # DeployGTM custom properties
        "deploygtm_signal_type": signal.get("type", ""),
        "deploygtm_signal_source": signal.get("source", "manual"),
        "deploygtm_signal_summary": signal.get("summary", ""),
        "deploygtm_icp_fit_score": str(score.get("icp_fit_score") or score.get("icp_fit", "")),
        "deploygtm_signal_strength": str(score.get("signal_strength", "")),
        "deploygtm_priority_score": str(score.get("priority", "")),
        "deploygtm_urgency_score": str(score.get("urgency_score", "")),
        "deploygtm_engagement_score": str(score.get("engagement_score", "")),
        "deploygtm_confidence_score": str(score.get("confidence_score", "")),
        "deploygtm_activation_priority": str(score.get("activation_priority", "")),
        "deploygtm_score_decay": json.dumps(score.get("decay", {})) if score.get("decay") else "",
        "deploygtm_pain_hypothesis": research.get("pain_hypothesis", ""),
        "deploygtm_enrichment_confidence": research.get("confidence", "low"),
    }

    if outreach:
        props["deploygtm_outreach_angle"] = outreach.get("persona", "")

    if signal.get("date"):
        # HubSpot date fields expect Unix ms timestamp at midnight UTC
        from datetime import datetime
        try:
            dt = datetime.strptime(signal["date"], "%Y-%m-%d")
            props["deploygtm_signal_date"] = str(int(dt.timestamp() * 1000))
        except ValueError:
            pass

    props = {k: v for k, v in props.items() if v}

    if dry_run:
        click.echo(f"  [dry-run] Would upsert contact: {email}")
        return "dry_run_contact_id"

    resp = requests.post(
        f"{HS_BASE}/crm/v3/objects/contacts",
        headers=_headers(),
        json={"properties": props},
        timeout=15,
    )

    if resp.status_code in (200, 201):
        contact_id = resp.json()["id"]
    elif resp.status_code == 409:
        # Contact exists — find and update
        existing = requests.post(
            f"{HS_BASE}/crm/v3/objects/contacts/search",
            headers=_headers(),
            json={
                "filterGroups": [{"filters": [
                    {"propertyName": "email", "operator": "EQ", "value": email}
                ]}],
                "limit": 1,
            },
            timeout=15,
        )
        results = existing.json().get("results", [])
        if not results:
            return None
        contact_id = results[0]["id"]
        requests.patch(
            f"{HS_BASE}/crm/v3/objects/contacts/{contact_id}",
            headers=_headers(),
            json={"properties": props},
            timeout=15,
        )
    else:
        click.echo(f"  ✗ Could not upsert {email}: {resp.status_code} {resp.text}", err=True)
        return None

    # Associate contact → company
    if company_id and company_id != "dry_run_company_id":
        requests.put(
            f"{HS_BASE}/crm/v3/objects/contacts/{contact_id}"
            f"/associations/companies/{company_id}/contact_to_company",
            headers=_headers(),
            timeout=15,
        )

    return contact_id


# ─── Main push function ───────────────────────────────────────────────────────

def push_pipeline_output(pipeline_output: dict, dry_run: bool = False) -> dict:
    """
    Push a complete pipeline.py output record to HubSpot.

    pipeline_output structure (from pipeline.py):
      company, contacts, research, score, outreach, signal
    """
    results = {"company_id": None, "contact_ids": [], "deal_id": None, "errors": []}

    company_name = pipeline_output.get("company", "")
    company_data = pipeline_output.get("company") or pipeline_output.get("research", {})
    signal = pipeline_output.get("signal", {})
    score = pipeline_output.get("score", {})
    research = pipeline_output.get("research", {})
    contacts = pipeline_output.get("contacts", [])
    outreach_map = pipeline_output.get("outreach", {})

    # 1. Upsert company
    company_id = upsert_company(company_data, dry_run=dry_run)
    results["company_id"] = company_id
    if company_id:
        click.echo(f"  Company → {company_id}")

    # 2. Upsert each contact
    for contact in contacts:
        email = contact.get("email", "")
        contact_outreach = outreach_map.get(email)

        contact_id = upsert_contact(
            contact=contact,
            score=score,
            outreach=contact_outreach,
            signal=signal,
            research=research,
            company_id=company_id,
            dry_run=dry_run,
        )

        if contact_id:
            results["contact_ids"].append(contact_id)
            name = contact.get("name", email)
            click.echo(f"  Contact → {name} ({contact_id})")

    # 3. Create deal at outreach_sent stage
    if company_name and outreach_map:
        try:
            deal_id = create_or_update_deal(
                company_name=company_name,
                stage="outreach_sent",
                company_id=company_id,
                contact_ids=results["contact_ids"],
                dry_run=dry_run,
            )
            results["deal_id"] = deal_id
        except Exception as e:
            results["errors"].append(f"Deal creation failed: {e}")

    return results


# ─── Deal management ──────────────────────────────────────────────────────────

DEAL_STAGES = {
    "outreach_sent":   "appointmentscheduled",   # closest default: "Appointment Scheduled"
    "replied":         "qualifiedtobuy",          # "Qualified to Buy"
    "meeting_booked":  "presentationscheduled",   # "Presentation Scheduled"
    "proposal_sent":   "decisionmakerboughtin",   # "Decision Maker Bought-In"
    "closed_won":      "closedwon",
    "closed_lost":     "closedlost",
}

DEAL_STAGE_LABELS = {v: k for k, v in DEAL_STAGES.items()}


def create_or_update_deal(
    company_name: str,
    stage: str = "outreach_sent",
    amount: Optional[int] = None,
    deal_name: Optional[str] = None,
    close_date: Optional[str] = None,
    company_id: Optional[str] = None,
    contact_ids: Optional[list] = None,
    pipeline_id: str = "default",
    dry_run: bool = False,
) -> Optional[str]:
    """
    Create a deal in HubSpot, or update if one already exists for this company.

    stage: one of outreach_sent | replied | meeting_booked | proposal_sent | closed_won | closed_lost
    amount: deal value in dollars (7500 for retainer, 3500 for Signal Audit)
    Returns deal ID or None.
    """
    hs_stage = DEAL_STAGES.get(stage, DEAL_STAGES["outreach_sent"])
    name = deal_name or f"{company_name} — DeployGTM"

    properties = {
        "dealname": name,
        "dealstage": hs_stage,
        "pipeline": pipeline_id,
    }
    if amount:
        properties["amount"] = str(amount)
    if close_date:
        properties["closedate"] = close_date

    if dry_run:
        click.echo(f"  [dry-run] Would create deal: {name} → stage: {stage} / ${amount or '?'}")
        return "dry-run-deal-id"

    headers = _headers()

    # Search for existing deal with this name
    search_resp = requests.post(
        f"{HS_BASE}/crm/v3/objects/deals/search",
        headers=headers,
        json={
            "filterGroups": [{
                "filters": [{"propertyName": "dealname", "operator": "EQ", "value": name}]
            }],
            "properties": ["dealname", "dealstage"],
            "limit": 1,
        },
        timeout=15,
    )

    deal_id = None
    if search_resp.ok:
        results = search_resp.json().get("results", [])
        if results:
            deal_id = results[0]["id"]

    if deal_id:
        # Update existing deal
        resp = requests.patch(
            f"{HS_BASE}/crm/v3/objects/deals/{deal_id}",
            headers=headers,
            json={"properties": properties},
            timeout=15,
        )
        resp.raise_for_status()
        click.echo(f"  Deal updated → {name} ({stage})")
    else:
        # Create new deal
        resp = requests.post(
            f"{HS_BASE}/crm/v3/objects/deals",
            headers=headers,
            json={"properties": properties},
            timeout=15,
        )
        resp.raise_for_status()
        deal_id = resp.json()["id"]
        click.echo(f"  Deal created → {name} ({stage}) [{deal_id}]")

    # Associate with company
    if company_id and deal_id and deal_id != "dry-run-deal-id":
        try:
            requests.put(
                f"{HS_BASE}/crm/v3/objects/deals/{deal_id}/associations/companies/{company_id}/deal_to_company",
                headers=headers, timeout=10,
            )
        except requests.RequestException:
            pass

    # Associate with contacts
    for cid in (contact_ids or []):
        if cid and deal_id != "dry-run-deal-id":
            try:
                requests.put(
                    f"{HS_BASE}/crm/v3/objects/deals/{deal_id}/associations/contacts/{cid}/deal_to_contact",
                    headers=headers, timeout=10,
                )
            except requests.RequestException:
                pass

    return deal_id


# ─── CLI ──────────────────────────────────────────────────────────────────────

@click.group()
def cli():
    """HubSpot CRM sync for DeployGTM."""
    pass


@cli.command("setup-properties")
@click.option("--dry-run", is_flag=True, help="Preview without writing")
def cmd_setup(dry_run):
    """Create all DeployGTM custom contact properties in HubSpot (run once)."""
    if not dry_run:
        click.echo("\n⚠️  This will create custom properties in your HubSpot account.")
        click.confirm("Continue?", abort=True)

    click.echo("\nCreating custom properties...")
    setup_properties(dry_run=dry_run)
    click.echo("\nDone. Run this command once per HubSpot account.")


@cli.command("push")
@click.option("--pipeline-output", "-f", required=True,
              help="Path to JSON file from pipeline.py")
@click.option("--dry-run", is_flag=True,
              help="Preview what would be pushed without writing to HubSpot")
@click.option("--config", "config_path", default="config.yaml")
def cmd_push(pipeline_output, dry_run, config_path):
    """Push a pipeline.py output file to HubSpot."""
    config = load_config(config_path)

    if config.get("tools", {}).get("hubspot", {}).get("require_confirmation") and not dry_run:
        click.echo(f"\nAbout to push to HubSpot CRM: {pipeline_output}")
        click.confirm("Confirm push to production CRM?", abort=True)

    data = json.loads(Path(pipeline_output).read_text())
    click.echo(f"\nPushing {pipeline_output}...")

    results = push_pipeline_output(data, dry_run=dry_run)

    click.echo(f"\n{'[DRY RUN] ' if dry_run else ''}Push complete.")
    click.echo(f"  Company ID:   {results['company_id']}")
    click.echo(f"  Contact IDs:  {results['contact_ids']}")
    if results["errors"]:
        click.echo(f"  Errors:       {results['errors']}", err=True)


# ─── Sequence enrollment ──────────────────────────────────────────────────────

def enroll_in_sequence(
    contact_id: str,
    sequence_id: str,
    from_email: str,
    dry_run: bool = False,
) -> dict:
    """
    Enroll a contact in a HubSpot sequence.

    Requires Sales Hub Starter or above.
    sequence_id: found in HubSpot → Sequences → [sequence] → URL
    from_email:  the sender email address (must be connected to HubSpot)
    """
    if dry_run:
        return {"status": "dry_run", "contact_id": contact_id, "sequence_id": sequence_id}

    resp = requests.post(
        f"{HS_BASE}/automation/v4/sequences/enrollments",
        headers=_headers(),
        json={
            "sequenceId": int(sequence_id),
            "contactId": int(contact_id),
            "fromUserId": None,       # HubSpot resolves from fromEmail
            "fromEmail": from_email,
            "startingStepNumber": 1,
        },
        timeout=15,
    )

    if resp.status_code in (200, 201):
        return {"status": "enrolled", "contact_id": contact_id, "data": resp.json()}
    elif resp.status_code == 409:
        return {"status": "already_enrolled", "contact_id": contact_id}
    else:
        return {"status": "error", "contact_id": contact_id,
                "code": resp.status_code, "detail": resp.text}


def enroll_contacts_from_output(
    pipeline_output: dict,
    persona_sequence_map: dict[str, str],
    from_email: str,
    contact_ids: list[str],
    dry_run: bool = False,
) -> list[dict]:
    """
    Enroll contacts from a pipeline output into persona-matched HubSpot sequences.

    persona_sequence_map: {persona_slug: hubspot_sequence_id}
      e.g. {"founder_seller": "123456", "first_sales_leader": "123457"}
    """
    outreach_map = pipeline_output.get("outreach", {})
    contacts = pipeline_output.get("contacts", [])
    results = []

    for contact, contact_id in zip(contacts, contact_ids):
        email = contact.get("email", "")
        outreach = outreach_map.get(email, {})
        persona = outreach.get("persona", "founder_seller")
        sequence_id = persona_sequence_map.get(persona)

        if not sequence_id:
            results.append({"status": "no_sequence_configured", "email": email, "persona": persona})
            continue

        result = enroll_in_sequence(contact_id, sequence_id, from_email, dry_run=dry_run)
        result["email"] = email
        result["persona"] = persona
        results.append(result)

    return results


@cli.command("enroll")
@click.option("--pipeline-output", "-f", required=True,
              help="Path to pipeline.py JSON output file")
@click.option("--from-email", required=True,
              help="Sender email address (must be connected in HubSpot)")
@click.option("--dry-run", is_flag=True)
@click.option("--config", "config_path", default="config.yaml")
def cmd_enroll(pipeline_output, from_email, dry_run, config_path):
    """
    Enroll contacts from a pipeline output into HubSpot sequences.

    Sequences are mapped by persona in config.yaml:
      tools.hubspot.sequences.founder_seller: "SEQUENCE_ID"
      tools.hubspot.sequences.first_sales_leader: "SEQUENCE_ID"
      tools.hubspot.sequences.revops_growth: "SEQUENCE_ID"

    Get sequence IDs from HubSpot → Sales → Sequences → [sequence] → URL bar.
    Requires Sales Hub Starter or above.
    """
    config = load_config(config_path)
    sequences = config.get("tools", {}).get("hubspot", {}).get("sequences", {})

    if not sequences:
        click.echo(
            "\nNo sequences configured. Add to config.yaml:\n\n"
            "  tools:\n"
            "    hubspot:\n"
            "      sequences:\n"
            "        founder_seller: \"123456\"\n"
            "        first_sales_leader: \"123457\"\n"
            "        revops_growth: \"123458\"\n\n"
            "Find sequence IDs in HubSpot → Sales → Sequences → open sequence → URL.",
            err=True,
        )
        return

    if not dry_run:
        click.echo(f"\nAbout to enroll contacts into HubSpot sequences from {from_email}")
        click.confirm("Confirm?", abort=True)

    data = json.loads(Path(pipeline_output).read_text())

    # First push to get contact IDs (or they may already be pushed)
    click.echo("\nPushing contacts to CRM first...")
    push_results = push_pipeline_output(data, dry_run=dry_run)
    contact_ids = push_results.get("contact_ids", [])

    if not contact_ids:
        click.echo("No contact IDs returned from push. Cannot enroll.", err=True)
        return

    click.echo(f"\nEnrolling {len(contact_ids)} contacts into sequences...")
    enroll_results = enroll_contacts_from_output(
        pipeline_output=data,
        persona_sequence_map=sequences,
        from_email=from_email,
        contact_ids=contact_ids,
        dry_run=dry_run,
    )

    for r in enroll_results:
        status = r.get("status", "?")
        email = r.get("email", "?")
        persona = r.get("persona", "?")
        seq = sequences.get(persona, "—")
        icon = "✓" if status == "enrolled" else ("~" if status in ("already_enrolled", "dry_run") else "✗")
        click.echo(f"  {icon} {email} [{persona}] → sequence {seq} ({status})")


@cli.command("create-deal")
@click.option("--company", "-c", required=True, help="Company name")
@click.option("--stage", "-s",
              type=click.Choice(list(DEAL_STAGES.keys())),
              default="outreach_sent", show_default=True,
              help="Deal stage")
@click.option("--amount", "-a", type=int, default=None,
              help="Deal value in dollars (3500 for Signal Audit, 7500 for Retainer)")
@click.option("--deal-name", default=None, help="Override default deal name")
@click.option("--dry-run", is_flag=True)
def cmd_create_deal(company: str, stage: str, amount: Optional[int], deal_name: Optional[str], dry_run: bool):
    """Create or update a HubSpot deal for a company."""
    deal_id = create_or_update_deal(
        company_name=company,
        stage=stage,
        amount=amount,
        deal_name=deal_name,
        dry_run=dry_run,
    )
    if deal_id and not dry_run:
        click.echo(f"\nDeal ID: {deal_id}")
        click.echo(f"View at: https://app.hubspot.com/contacts/deals/{deal_id}")


@cli.command("advance-deal")
@click.option("--company", "-c", required=True, help="Company name (matches deal name)")
@click.option("--stage", "-s",
              type=click.Choice(list(DEAL_STAGES.keys())),
              required=True,
              help="New stage to advance to")
@click.option("--amount", "-a", type=int, default=None, help="Update deal value if known")
@click.option("--dry-run", is_flag=True)
def cmd_advance_deal(company: str, stage: str, amount: Optional[int], dry_run: bool):
    """Advance a deal to a new stage (e.g. outreach_sent → replied → meeting_booked)."""
    create_or_update_deal(
        company_name=company,
        stage=stage,
        amount=amount,
        dry_run=dry_run,
    )


if __name__ == "__main__":
    cli()
