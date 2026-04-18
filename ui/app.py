"""
DeployGTM — Pipeline Dashboard

Visual interface for the DeployGTM outbound pipeline.
Reads output/ JSON files. Falls back to sample data for preview.

Run:
  streamlit run ui/app.py
  make ui
"""

from __future__ import annotations

import json
import sys
from datetime import date, timedelta
from pathlib import Path
from typing import Optional

import streamlit as st

# ─── Path setup ───────────────────────────────────────────────────────────────

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
OUTPUT_DIR = ROOT / "output"

# ─── Page config ──────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="DeployGTM",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Styles ───────────────────────────────────────────────────────────────────

st.markdown("""
<style>
    .block-container { padding-top: 1.5rem; }
    .metric-label { font-size: 0.85rem; color: #888; }
    .priority-high { color: #e74c3c; font-weight: 700; }
    .priority-med { color: #f39c12; font-weight: 600; }
    .priority-low { color: #95a5a6; }
    .badge-qualified { background: #27ae60; color: white; padding: 2px 8px; border-radius: 12px; font-size: 0.75rem; }
    .badge-pending { background: #f39c12; color: white; padding: 2px 8px; border-radius: 12px; font-size: 0.75rem; }
    .badge-disqualified { background: #e74c3c; color: white; padding: 2px 8px; border-radius: 12px; font-size: 0.75rem; }
    .outreach-box { background: #f8f9fa; border-left: 3px solid #3498db; padding: 1rem; font-family: monospace; font-size: 0.85rem; white-space: pre-wrap; }
    .touch-due { color: #e74c3c; font-weight: 600; }
</style>
""", unsafe_allow_html=True)

# ─── Data loading ─────────────────────────────────────────────────────────────

@st.cache_data(ttl=30)
def load_accounts() -> list[dict]:
    """Load all output/ JSON files. Falls back to sample data if empty."""
    files = sorted(OUTPUT_DIR.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    accounts = []
    for fpath in files:
        try:
            data = json.loads(fpath.read_text())
            data["_file"] = fpath.name
            accounts.append(data)
        except Exception:
            continue

    if not accounts:
        from sample_data import SAMPLE_ACCOUNTS
        for i, a in enumerate(SAMPLE_ACCOUNTS):
            a["_file"] = f"sample_{a['domain'].replace('.', '_')}.json"
            a["_is_sample"] = True
        return SAMPLE_ACCOUNTS

    return accounts


def days_since(date_str: Optional[str]) -> Optional[int]:
    if not date_str:
        return None
    try:
        return (date.today() - date.fromisoformat(date_str)).days
    except ValueError:
        return None


def touch_is_due(entry: dict) -> bool:
    due = entry.get("next_touch_due")
    if not due or entry.get("status") in ("booked", "paused", "opted_out"):
        return False
    return due <= date.today().isoformat()


def priority_color(p: int) -> str:
    if p >= 12:
        return "🔴"
    if p >= 8:
        return "🟡"
    if p >= 5:
        return "🟢"
    return "⚪"


# ─── Sidebar ──────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("## 🎯 DeployGTM")
    st.markdown("*Pipeline dashboard*")
    st.divider()

    page = st.radio(
        "Navigate",
        ["Dashboard", "Accounts", "Follow-ups", "Outreach"],
        label_visibility="collapsed",
    )

    st.divider()

    accounts = load_accounts()
    is_sample = any(a.get("_is_sample") for a in accounts)
    if is_sample:
        st.info("**Preview mode** — showing sample data. Run `make batch` to populate with real accounts.", icon="ℹ️")
    else:
        st.success(f"**{len(accounts)} accounts** in pipeline", icon="✅")

    st.divider()
    st.markdown("**Quick actions**")
    st.code("make daily", language="bash")
    st.code("make signals", language="bash")
    st.code("make batch", language="bash")
    st.code("make followup-due", language="bash")


# ─── Dashboard ────────────────────────────────────────────────────────────────

if page == "Dashboard":
    st.title("Morning briefing")

    # Top metrics
    all_accts = accounts
    priority_high = [a for a in all_accts if a.get("score", {}).get("priority", 0) >= 12]
    priority_med = [a for a in all_accts if 8 <= a.get("score", {}).get("priority", 0) < 12]
    qualified = [a for a in all_accts if a.get("research", {}).get("icp_verdict") == "qualified"]

    due_count = 0
    for a in all_accts:
        for entry in a.get("follow_up_log", {}).values():
            if touch_is_due(entry):
                due_count += 1

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Total accounts", len(all_accts))
    col2.metric("🔴 Reach out now", len(priority_high))
    col3.metric("🟡 This week", len(priority_med))
    col4.metric("Qualified ICP", len(qualified))
    col5.metric("Follow-ups due", due_count, delta=f"{due_count} today" if due_count else None,
                delta_color="inverse" if due_count else "off")

    st.divider()
    col_left, col_right = st.columns([1.4, 1])

    with col_left:
        st.subheader("Priority accounts")
        sorted_accts = sorted(all_accts, key=lambda a: a.get("score", {}).get("priority", 0), reverse=True)
        for a in sorted_accts[:8]:
            p = a.get("score", {}).get("priority", 0)
            signal_type = a.get("signal", {}).get("type", "")
            verdict = a.get("research", {}).get("icp_verdict", "")
            contacts = a.get("contacts", [])
            email_count = sum(1 for c in contacts if c.get("email"))
            outreach_count = len(a.get("outreach", {}))
            action = a.get("score", {}).get("action", "")

            with st.container():
                c1, c2, c3 = st.columns([2.5, 1, 1])
                c1.markdown(f"**{priority_color(p)} {a['company']}** &nbsp; `{a.get('domain','')}`")
                c2.markdown(f"`{signal_type}`")
                c3.markdown(f"Priority **{p}**")
                st.caption(f"{action} · {email_count} contacts · {'outreach ready' if outreach_count else 'no outreach yet'} · {verdict}")
                st.markdown("---")

    with col_right:
        st.subheader("Follow-ups due today")
        found_any = False
        for a in all_accts:
            for email, entry in a.get("follow_up_log", {}).items():
                if not touch_is_due(entry):
                    continue
                found_any = True
                touch_num = (entry.get("touches_sent", 0) or 0) + 1
                st.markdown(f"**{a['company']}** — {email}")
                st.caption(f"Touch {touch_num} due · status: {entry.get('status', 'active')}")
                st.code(
                    f"make followup-generate \\\n"
                    f"  FILE=output/{a['_file']} \\\n"
                    f"  EMAIL={email} TOUCH={touch_num}",
                    language="bash"
                )
        if not found_any:
            st.success("Nothing due — inbox clear.")

        st.divider()
        st.subheader("Signal breakdown")
        from collections import Counter
        signal_counts = Counter(a.get("signal", {}).get("type", "unknown") for a in all_accts)
        for sig, count in signal_counts.most_common():
            st.markdown(f"- **{sig}**: {count}")


# ─── Accounts ─────────────────────────────────────────────────────────────────

elif page == "Accounts":
    st.title("All accounts")

    # Filters
    col1, col2, col3 = st.columns(3)
    with col1:
        min_priority = st.slider("Min priority", 0, 15, 0)
    with col2:
        signal_options = list({a.get("signal", {}).get("type", "unknown") for a in accounts})
        selected_signal = st.multiselect("Signal type", signal_options, default=signal_options)
    with col3:
        verdict_options = list({a.get("research", {}).get("icp_verdict", "unknown") for a in accounts})
        selected_verdict = st.multiselect("ICP verdict", verdict_options, default=verdict_options)

    filtered = [
        a for a in accounts
        if a.get("score", {}).get("priority", 0) >= min_priority
        and a.get("signal", {}).get("type", "unknown") in selected_signal
        and a.get("research", {}).get("icp_verdict", "unknown") in selected_verdict
    ]
    filtered = sorted(filtered, key=lambda a: a.get("score", {}).get("priority", 0), reverse=True)

    st.caption(f"Showing {len(filtered)} of {len(accounts)} accounts")
    st.divider()

    for a in filtered:
        p = a.get("score", {}).get("priority", 0)
        score = a.get("score", {})
        research = a.get("research", {})
        contacts = a.get("contacts", [])
        signal = a.get("signal", {})
        outreach = a.get("outreach", {})

        verdict = research.get("icp_verdict", "unknown")
        verdict_badge = {
            "qualified": "🟢",
            "pending": "🟡",
            "disqualified": "🔴",
        }.get(verdict, "⚪")

        with st.expander(
            f"{priority_color(p)}  **{a['company']}** — {a.get('domain','')}  ·  Priority {p}  ·  {verdict_badge} {verdict}",
            expanded=(p >= 12)
        ):
            left, right = st.columns([1, 1])

            with left:
                st.markdown("**Signal**")
                st.markdown(f"- Type: `{signal.get('type', '')}`")
                st.markdown(f"- Date: {signal.get('date', '')}")
                st.markdown(f"- {signal.get('summary', '')}")

                st.markdown("**Research**")
                st.markdown(research.get("summary", "—"))
                st.markdown(f"*Pain hypothesis:* {research.get('pain_hypothesis', '—')}")
                st.caption(f"Confidence: {research.get('confidence', '?')} · Run: {research.get('run_date', '?')}")

            with right:
                st.markdown("**Score**")
                st.markdown(f"- ICP Fit: {score.get('icp_fit', '?')} / 5")
                st.markdown(f"- Signal Strength: {score.get('signal_strength', '?')} / 3")
                st.markdown(f"- Priority: **{p}**")
                st.markdown(f"- Action: *{score.get('action', '?')}*")
                st.caption(score.get("rationale", ""))

                st.markdown("**Contacts**")
                for c in contacts:
                    email_icon = "✉️" if c.get("email") else "❌"
                    status = c.get("email_status", "?")
                    st.markdown(f"- {email_icon} **{c.get('name','?')}** · {c.get('title','')} · {c.get('email','no email')} · `{status}`")

                if outreach:
                    st.markdown(f"**Outreach** — {len(outreach)} message(s) generated ✓")
                else:
                    st.warning("No outreach generated yet")


# ─── Follow-ups ───────────────────────────────────────────────────────────────

elif page == "Follow-ups":
    st.title("Follow-up queue")

    today = date.today().isoformat()

    # Collect all follow-up entries
    due: list[dict] = []
    upcoming: list[dict] = []
    completed: list[dict] = []

    for a in accounts:
        for email, entry in a.get("follow_up_log", {}).items():
            status = entry.get("status", "active")
            next_due = entry.get("next_touch_due") or ""
            touches = entry.get("touches_sent", 0) or 0

            row = {
                "company": a["company"],
                "domain": a.get("domain", ""),
                "email": email,
                "priority": a.get("score", {}).get("priority", 0),
                "status": status,
                "touches_sent": touches,
                "next_due": next_due,
                "last_touch_date": entry.get("last_touch_date", ""),
                "_file": a["_file"],
            }

            if status in ("booked", "paused", "opted_out", "replied"):
                completed.append(row)
            elif next_due and next_due <= today:
                due.append(row)
            else:
                upcoming.append(row)

    due.sort(key=lambda r: (r["next_due"], -r["priority"]))
    upcoming.sort(key=lambda r: (r["next_due"], -r["priority"]))

    col1, col2, col3 = st.columns(3)
    col1.metric("Due now", len(due))
    col2.metric("Upcoming", len(upcoming))
    col3.metric("Closed / paused", len(completed))

    st.divider()

    # Due now
    if due:
        st.subheader(f"🔴 Due now ({len(due)})")
        for r in due:
            touch_num = (r["touches_sent"] or 0) + 1
            with st.container():
                c1, c2, c3 = st.columns([2, 1.5, 1])
                c1.markdown(f"**{r['company']}** — {r['email']}")
                c2.markdown(f"Touch {touch_num} · {r['next_due']}")
                c3.markdown(f"Priority {r['priority']}")
                with st.expander("Show commands"):
                    st.code(
                        f"# Generate message\n"
                        f"make followup-generate \\\n"
                        f"  FILE=output/{r['_file']} \\\n"
                        f"  EMAIL={r['email']} TOUCH={touch_num}\n\n"
                        f"# Log as sent\n"
                        f"python scripts/follow_up.py log \\\n"
                        f"  --file output/{r['_file']} \\\n"
                        f"  --email {r['email']} --touch {touch_num}",
                        language="bash",
                    )
        st.divider()
    else:
        st.success("No follow-ups due right now.")

    # Upcoming
    if upcoming:
        st.subheader(f"🟡 Coming up ({len(upcoming)})")
        for r in upcoming:
            touch_num = (r["touches_sent"] or 0) + 1
            days_until = (date.fromisoformat(r["next_due"]) - date.today()).days if r["next_due"] else "?"
            c1, c2, c3 = st.columns([2, 1.5, 1])
            c1.markdown(f"{r['company']} — {r['email']}")
            c2.markdown(f"Touch {touch_num} in {days_until}d · {r['next_due']}")
            c3.markdown(f"Priority {r['priority']}")

    # Closed
    if completed:
        with st.expander(f"Closed / paused ({len(completed)})"):
            for r in completed:
                st.markdown(f"- **{r['company']}** ({r['email']}) · {r['status']} · {r['touches_sent']} touches sent")


# ─── Outreach ─────────────────────────────────────────────────────────────────

elif page == "Outreach":
    st.title("Outreach copy")

    # Account selector
    account_names = [
        f"{a['company']} — {a.get('domain', '')} (Priority {a.get('score', {}).get('priority', '?')})"
        for a in sorted(accounts, key=lambda a: a.get("score", {}).get("priority", 0), reverse=True)
    ]
    selected_idx = st.selectbox("Select account", range(len(account_names)), format_func=lambda i: account_names[i])
    a = sorted(accounts, key=lambda a: a.get("score", {}).get("priority", 0), reverse=True)[selected_idx]

    st.divider()

    outreach = a.get("outreach", {})
    contacts = a.get("contacts", [])

    if not outreach:
        st.warning("No outreach generated for this account. Run the pipeline to generate it.")
        st.code(
            f"python scripts/pipeline.py run \\\n"
            f"  --company \"{a['company']}\" --domain {a.get('domain','')} \\\n"
            f"  --signal {a.get('signal',{}).get('type','manual')} \\\n"
            f"  --signal-date {a.get('signal',{}).get('date',date.today().isoformat())} \\\n"
            f"  --signal-summary \"{a.get('signal',{}).get('summary','')}\"",
            language="bash",
        )
    else:
        for email, msgs in outreach.items():
            contact = next((c for c in contacts if c.get("email") == email), {})
            name = contact.get("name", email)
            title = contact.get("title", "")
            email_status = contact.get("email_status", "?")
            linkedin_url = contact.get("linkedin_url", "")

            # Support both schema versions:
            # New: {primary: {subject, body}, followup_1: {body}, followup_2: {body}, linkedin_connection_note, ...}
            # Old flat: {subject, body, follow_up_1, follow_up_2}
            primary = msgs.get("primary") or {}
            subj = primary.get("subject") or msgs.get("subject", "")
            body = primary.get("body") or msgs.get("body", "")
            fu1_obj = msgs.get("followup_1") or {}
            fu1 = fu1_obj.get("body") if fu1_obj else msgs.get("follow_up_1", "")
            fu2_obj = msgs.get("followup_2") or {}
            fu2 = fu2_obj.get("body") if fu2_obj else msgs.get("follow_up_2", "")
            linkedin_note = msgs.get("linkedin_connection_note", "")
            pain_used = msgs.get("pain_used", "")
            signal_used = msgs.get("signal_used", "")
            notes = msgs.get("notes", "")
            persona = msgs.get("persona", "")

            header_parts = [f"**{name}**", title, email]
            if persona:
                header_parts.append(f"persona: *{persona}*")
            st.subheader(name)
            st.caption(f"{title} · {email} · email: {email_status}" + (f" · [LinkedIn]({linkedin_url})" if linkedin_url else ""))

            tabs = ["Touch 1", "Touch 2 (day 3)", "Touch 3 (day 7)"]
            if linkedin_note:
                tabs.append("LinkedIn")
            tab_objects = st.tabs(tabs)

            with tab_objects[0]:
                if subj:
                    st.markdown(f"**Subject:** {subj}")
                st.text_area("Body", value=body, height=200, key=f"body_{email}", label_visibility="collapsed")
                if pain_used or signal_used:
                    with st.expander("What this message is built on"):
                        if signal_used:
                            st.markdown(f"**Signal used:** {signal_used}")
                        if pain_used:
                            st.markdown(f"**Pain used:** {pain_used}")
                        if notes:
                            st.markdown(f"**Notes:** {notes}")

            with tab_objects[1]:
                if fu1:
                    day = fu1_obj.get("send_on_day", 3) if fu1_obj else 3
                    st.caption(f"Send ~day {day} after touch 1")
                    st.text_area("Follow-up 1", value=fu1, height=120, key=f"fu1_{email}", label_visibility="collapsed")
                else:
                    st.info("Not yet generated.")
                    st.code(
                        f"python scripts/follow_up.py generate \\\n"
                        f"  --file output/{a['_file']} \\\n"
                        f"  --email {email} --touch 1",
                        language="bash",
                    )

            with tab_objects[2]:
                if fu2:
                    day = fu2_obj.get("send_on_day", 7) if fu2_obj else 7
                    st.caption(f"Send ~day {day} after touch 1")
                    st.text_area("Follow-up 2", value=fu2, height=100, key=f"fu2_{email}", label_visibility="collapsed")
                else:
                    st.info("Not yet generated.")
                    st.code(
                        f"python scripts/follow_up.py generate \\\n"
                        f"  --file output/{a['_file']} \\\n"
                        f"  --email {email} --touch 2",
                        language="bash",
                    )

            if linkedin_note and len(tabs) > 3:
                with tab_objects[3]:
                    char_count = len(linkedin_note)
                    color = "🔴" if char_count > 300 else "🟢"
                    st.caption(f"{color} {char_count}/300 chars (connection note limit)")
                    st.text_area(
                        "LinkedIn connection note",
                        value=linkedin_note,
                        height=100,
                        key=f"li_{email}",
                        label_visibility="collapsed",
                    )
                    if linkedin_url:
                        st.markdown(f"[Open LinkedIn profile]({linkedin_url})")

            # Follow-up log
            log_entry = a.get("follow_up_log", {}).get(email)
            if log_entry:
                status_icon = {"booked": "📅", "paused": "⏸", "replied": "💬", "active": "🟢"}.get(
                    log_entry.get("status", "active"), "⚪"
                )
                st.caption(
                    f"{status_icon} {log_entry.get('touches_sent', 0)} touch(es) sent · "
                    f"last: {log_entry.get('last_touch_date', 'never')} · "
                    f"status: {log_entry.get('status', 'active')} · "
                    f"next due: {log_entry.get('next_touch_due', '—')}"
                )

            st.divider()

        # After reviewing, push options
        st.subheader("Actions")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Audit before pushing:**")
            st.code(f"make audit", language="bash")
        with col2:
            st.markdown("**Push to HubSpot:**")
            st.code(
                f"python scripts/hubspot.py push \\\n"
                f"  --file output/{a['_file']}",
                language="bash",
            )
