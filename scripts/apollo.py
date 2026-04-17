"""
DeployGTM — Apollo Contact Enrichment

Finds key contacts at a target company using the Apollo.io API.
Waterfall: Apollo first → manual fallback note if Apollo misses.

Target titles (configurable in config.yaml):
  CEO, Co-Founder, Founder, VP Sales, Head of Sales,
  VP Revenue, Head of Growth, RevOps

Apollo API v1 docs: https://apolloio.github.io/apollo-api-docs/

Standalone:
  python scripts/apollo.py --domain acme.com
  python scripts/apollo.py --domain acme.com --max-contacts 3
"""

from __future__ import annotations

import os
import time
from typing import Optional

import click
import json
import requests
import yaml
from dotenv import load_dotenv

load_dotenv()

APOLLO_BASE = "https://api.apollo.io/v1"


def load_config(config_path: str = "config.yaml") -> dict:
    with open(config_path) as f:
        return yaml.safe_load(f)


def _apollo_headers() -> dict:
    return {
        "Content-Type": "application/json",
        "Cache-Control": "no-cache",
    }


def _apollo_key() -> str:
    key = os.environ.get("APOLLO_API_KEY", "")
    if not key:
        raise EnvironmentError(
            "APOLLO_API_KEY is not set. Add it to your .env file."
        )
    return key


def find_contacts(
    domain: str,
    titles: Optional[list[str]] = None,
    max_contacts: int = 5,
    config: Optional[dict] = None,
) -> list[dict]:
    """
    Find key contacts at a company by domain.

    Returns a list of contact dicts, each with:
      name, title, email, email_status, linkedin_url, confidence, source
    """
    if config is None:
        config = load_config()

    if titles is None:
        titles = config.get("tools", {}).get("apollo", {}).get("target_titles", [
            "CEO", "Co-Founder", "Founder",
            "VP Sales", "Head of Sales",
            "Head of Growth", "RevOps",
        ])

    api_key = _apollo_key()
    contacts = []
    seen_emails = set()

    for title in titles:
        if len(contacts) >= max_contacts:
            break

        payload = {
            "api_key": api_key,
            "q_organization_domains": domain,
            "person_titles": [title],
            "page": 1,
            "per_page": 3,
            "contact_email_status_v2": ["verified", "guessed", "likely"],
        }

        try:
            resp = requests.post(
                f"{APOLLO_BASE}/mixed_people/search",
                json=payload,
                headers=_apollo_headers(),
                timeout=15,
            )
            resp.raise_for_status()
            data = resp.json()
        except requests.RequestException as e:
            click.echo(f"  [apollo] Error searching for '{title}' at {domain}: {e}", err=True)
            time.sleep(1)
            continue

        people = data.get("people") or data.get("contacts") or []

        for person in people:
            if len(contacts) >= max_contacts:
                break

            email = person.get("email") or person.get("sanitized_email")
            if not email or email in seen_emails:
                continue

            seen_emails.add(email)
            contacts.append({
                "name": f"{person.get('first_name', '')} {person.get('last_name', '')}".strip(),
                "title": person.get("title", ""),
                "email": email,
                "email_status": person.get("email_status", "unknown"),
                "linkedin_url": person.get("linkedin_url", ""),
                "phone": person.get("sanitized_phone", ""),
                "confidence": _email_confidence(person.get("email_status")),
                "source": "apollo",
            })

        # Respect Apollo rate limits (free tier: ~300 req/hr)
        time.sleep(0.5)

    if not contacts:
        contacts.append({
            "name": "",
            "title": "Unknown",
            "email": "",
            "email_status": "not_found",
            "linkedin_url": "",
            "phone": "",
            "confidence": "low",
            "source": "apollo_miss — manual LinkedIn lookup needed",
        })

    return contacts


def enrich_company(domain: str) -> dict:
    """
    Fetch firmographic data for a company from Apollo.

    Returns a dict with: name, industry, employee_count, funding_stage,
    linkedin_url, city, country, technologies
    """
    api_key = _apollo_key()

    payload = {
        "api_key": api_key,
        "domain": domain,
    }

    try:
        resp = requests.post(
            f"{APOLLO_BASE}/organizations/enrich",
            json=payload,
            headers=_apollo_headers(),
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as e:
        return {"error": str(e), "source": "apollo", "domain": domain}

    org = data.get("organization", {})
    return {
        "name": org.get("name", ""),
        "domain": domain,
        "industry": org.get("industry", ""),
        "employee_count": org.get("estimated_num_employees"),
        "funding_stage": _normalize_stage(org.get("latest_funding_stage")),
        "funding_total": org.get("total_funding"),
        "linkedin_url": org.get("linkedin_url", ""),
        "city": org.get("city", ""),
        "state": org.get("state", ""),
        "country": org.get("country", ""),
        "technologies": [t.get("name") for t in (org.get("technologies") or [])],
        "source": "apollo",
        "confidence": "high" if org.get("name") else "low",
    }


def _email_confidence(status: Optional[str]) -> str:
    mapping = {
        "verified": "high",
        "likely":   "high",
        "guessed":  "medium",
        "unknown":  "low",
        None:       "low",
    }
    return mapping.get(status, "low")


def _normalize_stage(stage: Optional[str]) -> str:
    if not stage:
        return "unknown"
    s = stage.lower().replace("-", "_").replace(" ", "_")
    if "seed" in s:
        return "seed"
    if "series_a" in s or "series a" in s:
        return "series_a"
    if "series_b" in s:
        return "series_b"
    if "series_c" in s or "series_d" in s or "series_e" in s:
        return "series_c_plus"
    if "bootstrap" in s or "self" in s:
        return "bootstrap"
    return stage


# ─── CLI ──────────────────────────────────────────────────────────────────────

@click.command()
@click.option("--domain", "-d", required=True, help="Company domain (e.g. acme.com)")
@click.option("--max-contacts", "-n", default=5, help="Max contacts to return")
@click.option("--enrich-company/--no-enrich-company", default=True,
              help="Also fetch company firmographics from Apollo")
@click.option("--config", "config_path", default="config.yaml")
@click.option("--output", "-o", default=None, help="Write result to JSON file")
def cli(domain, max_contacts, enrich_company, config_path, output):
    """Find key contacts + company data at a domain via Apollo."""
    config = load_config(config_path)

    result = {}

    if enrich_company:
        click.echo(f"Fetching company data for {domain}...")
        result["company"] = globals()["enrich_company"](domain)
        click.echo(f"  → {result['company'].get('name', 'unknown')} "
                   f"({result['company'].get('employee_count', '?')} employees, "
                   f"{result['company'].get('funding_stage', '?')})")

    click.echo(f"Finding contacts at {domain}...")
    result["contacts"] = find_contacts(domain, max_contacts=max_contacts, config=config)

    for c in result["contacts"]:
        status = "✓" if c["email_status"] in ("verified", "likely") else "~"
        click.echo(f"  {status} {c['name']} — {c['title']} — {c['email'] or 'no email found'}")

    pretty = json.dumps(result, indent=2)
    if output:
        from pathlib import Path
        Path(output).write_text(pretty)
        click.echo(f"\nSaved to {output}")
    else:
        click.echo(f"\n{pretty}")


if __name__ == "__main__":
    cli()
