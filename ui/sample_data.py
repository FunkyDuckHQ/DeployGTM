"""Sample output files for UI preview when output/ is empty.

Uses the canonical pipeline schema:
  outreach[email] = {
    persona, primary: {subject, body, channel},
    followup_1: {send_on_day, body, channel},
    followup_2: {send_on_day, body, channel},
    linkedin_connection_note, pain_used, signal_used, notes
  }
"""

SAMPLE_ACCOUNTS = [
    {
        "company": "Acme AI",
        "domain": "acme.ai",
        "signal": {
            "type": "funding",
            "date": "2026-03-24",
            "summary": "YC W26 — raised $3M Seed, building AI agent infrastructure for sales teams. Founder doing all sales."
        },
        "research": {
            "summary": "Acme AI builds AI sales agents that auto-research prospects and draft personalized outreach. 8 employees, San Francisco. Founder-led sales, no SDR yet.",
            "pain_hypothesis": "Evan is doing everything manually — researching prospects, writing emails, updating HubSpot. His AE hire starts in 6 weeks and he has nothing set up for them to inherit.",
            "icp_verdict": "qualified",
            "confidence": "high",
            "run_date": "2026-04-15"
        },
        "score": {
            "icp_fit": 5,
            "signal_strength": 3,
            "priority": 15,
            "action": "reach out immediately",
            "rationale": "Perfect ICP fit — founder-led sales, YC W26, just raised, technical product. Signal is funding + imminent AE hire."
        },
        "contacts": [
            {
                "name": "Evan Park",
                "title": "CEO & Co-Founder",
                "email": "evan@acme.ai",
                "email_status": "verified",
                "linkedin_url": "https://linkedin.com/in/evanpark",
                "confidence": "high",
                "source": "apollo"
            }
        ],
        "outreach": {
            "evan@acme.ai": {
                "persona": "founder_seller",
                "primary": {
                    "subject": "pipeline before your AE starts",
                    "body": "Evan — congrats on the W26 raise.\n\nYou've got ~6 weeks before your AE is in the door. Right now that's all upside — but only if there's a system underneath them when they arrive.\n\nI build that system. Signal detection, enrichment, HubSpot setup, outreach sequences. Two weeks, $3,500, you walk away with infrastructure your AE can actually run.\n\nWorth a 20-minute call this week?",
                    "channel": "email"
                },
                "followup_1": {
                    "send_on_day": 3,
                    "body": "Evan — following up on the pipeline note. If the timing's off, just say so. If there's interest, happy to share what the first two weeks look like.",
                    "channel": "email"
                },
                "followup_2": {
                    "send_on_day": 7,
                    "body": "Still relevant? Happy to park this if the focus is elsewhere right now.",
                    "channel": "email"
                },
                "linkedin_connection_note": "Evan — congrats on YC W26. I build outbound pipeline infrastructure for founders who are still running sales themselves. Worth a quick conversation?",
                "pain_used": "AE starting in 6 weeks with nothing set up to hand them",
                "signal_used": "YC W26 funding announcement",
                "notes": "Strong fit. Lead with the AE timeline — it's concrete and urgent."
            }
        },
        "follow_up_log": {
            "evan@acme.ai": {
                "touches_sent": 1,
                "last_touch_date": "2026-04-15",
                "last_touch_number": 1,
                "next_touch_due": "2026-04-18",
                "status": "active"
            }
        },
        "meta": {"run_date": "2026-04-15", "version": "1.0"}
    },
    {
        "company": "Terzo",
        "domain": "terzo.com",
        "signal": {
            "type": "hiring",
            "date": "2026-04-10",
            "summary": "Posted VP Sales and 2 AE roles — investing in sales but infrastructure may not exist yet."
        },
        "research": {
            "summary": "Terzo builds contract intelligence for enterprise procurement teams. 22 employees, Series A. Strong product-market fit signals, recently expanded sales motion.",
            "pain_hypothesis": "Brodie just got hired as VP Sales and inherited nothing. No sequences, no scoring, no signal layer. He needs to show quick pipeline wins but has no infrastructure to build on.",
            "icp_verdict": "qualified",
            "confidence": "high",
            "run_date": "2026-04-12"
        },
        "score": {
            "icp_fit": 4,
            "signal_strength": 2,
            "priority": 8,
            "action": "reach out this week",
            "rationale": "Strong fit — new VP Sales with nothing inherited. Signal is hiring, not funding, so slightly lower urgency."
        },
        "contacts": [
            {
                "name": "Brodie Walsh",
                "title": "VP Sales",
                "email": "brodie@terzo.com",
                "email_status": "likely",
                "linkedin_url": "https://linkedin.com/in/brodiewalsh",
                "confidence": "high",
                "source": "apollo"
            }
        ],
        "outreach": {
            "brodie@terzo.com": {
                "persona": "first_sales_leader",
                "primary": {
                    "subject": "you were hired to close, not build a stack",
                    "body": "Brodie — saw Terzo posted VP Sales + two AEs recently.\n\nMost people in your seat get hired, then spend the first 90 days duct-taping tools together instead of selling. CRM hygiene, sequences, signal detection — none of it exists yet.\n\nI build that infrastructure. Two weeks, you have a working system underneath you. Signal Audit: $3,500.\n\nWorth a call?",
                    "channel": "email"
                },
                "followup_1": {
                    "send_on_day": 3,
                    "body": "Brodie — any traction on the pipeline infrastructure question? Happy to share what week one looks like if that's useful.",
                    "channel": "email"
                },
                "followup_2": {
                    "send_on_day": 7,
                    "body": "Still on the radar? If the timing's off I'll circle back next quarter.",
                    "channel": "email"
                },
                "linkedin_connection_note": "Brodie — saw you just joined Terzo as VP Sales. I help new sales leaders build the infrastructure layer before it becomes a bottleneck. Worth connecting?",
                "pain_used": "Inherited nothing — no CRM hygiene, no sequences, no signal detection",
                "signal_used": "VP Sales + AE hiring signal",
                "notes": "If Brodie is brand new (<30 days in seat), urgency is high — they're in the 'trying to understand what they have' phase."
            }
        },
        "follow_up_log": {},
        "meta": {"run_date": "2026-04-12", "version": "1.0"}
    },
    {
        "company": "Mindra",
        "domain": "mindra.io",
        "signal": {
            "type": "gtm_struggle",
            "date": "2026-04-01",
            "summary": "Founder posted on LinkedIn about outbound challenges and inconsistent pipeline."
        },
        "research": {
            "summary": "Mindra builds employee engagement and performance tooling for mid-market HR teams. 14 employees, Seed. Deniz is the founder and still running all sales.",
            "pain_hypothesis": "Deniz is burning 3 hours a day on manual prospecting — LinkedIn, Apollo, writing emails. No signal detection, no enrichment, no scoring. Has the tools but not the system.",
            "icp_verdict": "qualified",
            "confidence": "medium",
            "run_date": "2026-04-03"
        },
        "score": {
            "icp_fit": 4,
            "signal_strength": 3,
            "priority": 12,
            "action": "reach out immediately",
            "rationale": "Founder directly signaled pipeline pain on LinkedIn. Strong ICP fit. High signal strength because the pain is public and self-identified."
        },
        "contacts": [
            {
                "name": "Deniz Aydin",
                "title": "CEO & Founder",
                "email": "deniz@mindra.io",
                "email_status": "verified",
                "linkedin_url": "https://linkedin.com/in/denizaydin",
                "confidence": "high",
                "source": "apollo"
            }
        ],
        "outreach": {
            "deniz@mindra.io": {
                "persona": "founder_seller",
                "primary": {
                    "subject": "the outbound infrastructure question",
                    "body": "Deniz — saw your post about inconsistent pipeline.\n\nThat's almost always an infrastructure problem, not a messaging problem. No signal layer, no scoring, no enrichment running automatically. So it's all manual and it shows.\n\nI build the engine. Signal detection, enrichment, HubSpot setup, outreach sequences — two weeks, working system. $3,500.\n\nHappy to walk you through what it looks like if that's useful.",
                    "channel": "email"
                },
                "followup_1": {
                    "send_on_day": 3,
                    "body": "Deniz — still thinking about the pipeline infrastructure question. If the LinkedIn post was a moment of frustration and not an active problem, no worries. But if it's still real, worth 20 minutes.",
                    "channel": "email"
                },
                "followup_2": {
                    "send_on_day": 7,
                    "body": "Last note on this — happy to park it if the timing isn't right.",
                    "channel": "email"
                },
                "linkedin_connection_note": "Deniz — saw your post on pipeline consistency. That's an infrastructure problem more than a messaging one. I build the engine. Worth connecting?",
                "pain_used": "Manual prospecting 3+ hours/day, inconsistent results despite having the tools",
                "signal_used": "LinkedIn post about outbound challenges",
                "notes": "Lead with the LinkedIn post reference immediately — she signaled the pain publicly."
            }
        },
        "follow_up_log": {
            "deniz@mindra.io": {
                "touches_sent": 2,
                "last_touch_date": "2026-04-10",
                "last_touch_number": 2,
                "next_touch_due": "2026-04-17",
                "status": "active"
            }
        },
        "meta": {"run_date": "2026-04-03", "version": "1.0"}
    },
    {
        "company": "Rex",
        "domain": "rex.run",
        "signal": {
            "type": "agency_churn",
            "date": "2026-03-28",
            "summary": "Former agency connection — intro call scheduled, signal is they've tried the advice route and it didn't work."
        },
        "research": {
            "summary": "Rex builds developer workflow automation. 11 employees, just closed Seed. Technical founder still doing all sales. Recently ended engagement with fractional CRO.",
            "pain_hypothesis": "Josh got advice but no infrastructure. The fractional CRO built a strategy deck and left. Pipeline is still manual and inconsistent.",
            "icp_verdict": "qualified",
            "confidence": "medium",
            "run_date": "2026-03-29"
        },
        "score": {
            "icp_fit": 4,
            "signal_strength": 2,
            "priority": 8,
            "action": "reach out this week",
            "rationale": "Agency churn is a strong signal — they already know they need help. ICP fit is solid. Discovery call is the next step."
        },
        "contacts": [
            {
                "name": "Josh Kim",
                "title": "CEO",
                "email": "josh@rex.run",
                "email_status": "verified",
                "linkedin_url": "https://linkedin.com/in/joshkim",
                "confidence": "high",
                "source": "apollo"
            }
        ],
        "outreach": {
            "josh@rex.run": {
                "persona": "founder_seller",
                "primary": {
                    "subject": "after the fractional CRO",
                    "body": "Josh — heard you wrapped up with the fractional CRO engagement.\n\nThat's usually the moment where founders realize: advice isn't the gap. Infrastructure is.\n\nI build the pipeline engine — signal detection, enrichment, HubSpot setup, outreach sequences. You walk away with a working system, not a playbook.\n\nAlready have an intro call scheduled — just want to make sure I'm coming in with the right context.",
                    "channel": "email"
                },
                "followup_1": {
                    "send_on_day": 3,
                    "body": "Following up ahead of our call — any context you'd want to share beforehand?",
                    "channel": "email"
                },
                "followup_2": {
                    "send_on_day": 7,
                    "body": "Still good for the intro call? Happy to reschedule if timing shifted.",
                    "channel": "email"
                },
                "linkedin_connection_note": "Josh — I build outbound pipeline infrastructure for technical founders doing sales themselves. Heard you recently ended a fractional CRO engagement — I take the opposite approach. Worth connecting.",
                "pain_used": "Got strategy, not infrastructure — the fractional CRO left them with a deck, not a working system",
                "signal_used": "Agency/fractional CRO churn",
                "notes": "Intro call already scheduled — focus on confirming the right framing, not selling."
            }
        },
        "follow_up_log": {
            "josh@rex.run": {
                "touches_sent": 0,
                "last_touch_date": None,
                "last_touch_number": 0,
                "next_touch_due": "2026-04-17",
                "status": "active"
            }
        },
        "meta": {"run_date": "2026-03-29", "version": "1.0"}
    },
    {
        "company": "Fibinaci",
        "domain": "fibinaci.com",
        "signal": {
            "type": "manual",
            "date": "2026-04-05",
            "summary": "Inbound inquiry — founder reached out about advisory relationship."
        },
        "research": {
            "summary": "Fibinaci builds financial modeling tools for startup CFOs. 7 employees, pre-Series A. Strong product but narrow ICP, potential GTM infrastructure gaps.",
            "pain_hypothesis": "Alex wants advisory help, but the economics and scope aren't defined. May not be a good fit if they want strategy instead of infrastructure.",
            "icp_verdict": "pending",
            "confidence": "low",
            "run_date": "2026-04-06"
        },
        "score": {
            "icp_fit": 3,
            "signal_strength": 2,
            "priority": 6,
            "action": "nurture / monitor",
            "rationale": "Inbound is a good signal but advisory isn't our primary motion. Need NDA + demo before committing to anything."
        },
        "contacts": [
            {
                "name": "Alex Chen",
                "title": "CEO",
                "email": "alex@fibinaci.com",
                "email_status": "verified",
                "linkedin_url": "https://linkedin.com/in/alexchen",
                "confidence": "high",
                "source": "manual"
            }
        ],
        "outreach": {
            "alex@fibinaci.com": {
                "persona": "founder_seller",
                "primary": {
                    "subject": "Re: Advisory conversation",
                    "body": "Alex — happy to continue the advisory conversation. Before we go further, want to make sure we're aligned on scope and economics.\n\nTwo things that would help: a quick NDA so I can give you the full picture, and a product demo so I understand what you're selling and to whom.\n\nOnce I have that context, I can tell you whether I'm the right fit for what you need.",
                    "channel": "email"
                },
                "followup_1": {
                    "send_on_day": 5,
                    "body": "Alex — just following up on the NDA + demo step. Happy to proceed whenever you're ready.",
                    "channel": "email"
                },
                "followup_2": {
                    "send_on_day": 12,
                    "body": "Still interested in the advisory conversation? No pressure either way.",
                    "channel": "email"
                },
                "linkedin_connection_note": "",
                "pain_used": "Wants advisory but scope and economics are undefined — need to qualify before engaging",
                "signal_used": "Inbound inquiry",
                "notes": "Don't over-invest until NDA is signed and you've seen the product. Treat as warm inbound, not hot lead."
            }
        },
        "follow_up_log": {},
        "meta": {"run_date": "2026-04-06", "version": "1.0"}
    },
]
