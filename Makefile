# DeployGTM — Common commands
# Usage: make <target>

PYTHON := $(shell command -v python3 2>/dev/null || command -v python 2>/dev/null)
.DEFAULT_GOAL := help

# ─── Setup ────────────────────────────────────────────────────────────────────

install:  ## Install Python dependencies
	$(PYTHON) -m pip install -r requirements.txt

env:  ## Copy .env.example to .env (won't overwrite existing)
	@if [ -f .env ]; then echo ".env already exists — edit it directly."; \
	else cp .env.example .env && echo "Created .env — fill in your API keys."; fi

api-test:  ## Validate API connections (HubSpot + external). Run before first batch.
	$(PYTHON) scripts/local_api_harness.py validate-env && \
	$(PYTHON) scripts/local_api_harness.py hubspot-read && \
	$(PYTHON) scripts/local_api_harness.py one-second-read

test:  ## Run offline unit tests (no API keys needed)
	$(PYTHON) -m pytest tests/ -v

setup-hubspot:  ## Create DeployGTM custom properties in HubSpot (run once)
	$(PYTHON) scripts/pipeline.py setup-hubspot

generate-sequences:  ## Generate HubSpot sequence step templates → master/hubspot_sequences.md
	$(PYTHON) scripts/sequence_builder.py generate

setup: install env  ## Full setup: install deps + create .env
	@echo "\nSetup complete. Fill in .env, then run: make run-one"

ui:  ## Launch pipeline dashboard in browser (streamlit)
	streamlit run ui/app.py

# ─── Daily Ops ────────────────────────────────────────────────────────────────

daily:  ## Morning briefing — follow-ups due, project status, pipeline activity
	$(PYTHON) scripts/daily.py

intake:  ## Start working with a new prospect (set COMPANY="Name" DOMAIN=domain.com)
	$(PYTHON) scripts/intake.py "$(COMPANY)" $(DOMAIN)

precall:  ## Pre-call brief before a discovery/close call (set DOMAIN=acme.com CONTACT="Name")
	$(PYTHON) scripts/precall.py --domain $(DOMAIN) $(if $(CONTACT),--contact "$(CONTACT)",)

# ─── Pipeline ─────────────────────────────────────────────────────────────────

run-one:  ## Run pipeline on one account (prompts for input)
	@echo "Usage: python scripts/pipeline.py run --company NAME --domain DOMAIN --signal TYPE --signal-date YYYY-MM-DD"

qualify:  ## Quick ICP qualifier for inbound leads (set COMPANY=name DOMAIN=domain.com)
	$(PYTHON) scripts/qualify.py run --company "$(COMPANY)" --domain $(DOMAIN)

qualify-context:  ## Qualify with context (set COMPANY DOMAIN CONTEXT="reply text...")
	$(PYTHON) scripts/qualify.py run --company "$(COMPANY)" --domain $(DOMAIN) --context "$(CONTEXT)"

batch:  ## Run batch pipeline on data/signals_intake.csv
	$(PYTHON) scripts/batch.py run --input data/signals_intake.csv

batch-yc:  ## Run batch pipeline on data/yc_w26_targets.csv
	$(PYTHON) scripts/batch.py run --input data/yc_w26_targets.csv

batch-resume:  ## Resume interrupted batch (skips already-processed domains)
	$(PYTHON) scripts/batch.py run --input data/yc_w26_targets.csv --resume

# ─── Export & CRM ─────────────────────────────────────────────────────────────

export:  ## Export output/ to HubSpot import CSVs (priority ≥ 8)
	$(PYTHON) scripts/export.py run --min-priority 8

audit:  ## Scan output/ for data quality issues before pushing to HubSpot
	$(PYTHON) scripts/crm_audit.py scan

audit-summary:  ## Pipeline summary across all output files
	$(PYTHON) scripts/crm_audit.py summary

push-hubspot:  ## Push output/ directly to HubSpot via API (requires confirmation)
	$(PYTHON) scripts/export.py run --push-to-hubspot --min-priority 8

deal:  ## Create/update a HubSpot deal (set COMPANY="Name" STAGE=replied AMOUNT=3500)
	$(PYTHON) scripts/hubspot.py create-deal --company "$(COMPANY)" $(if $(STAGE),--stage $(STAGE),) $(if $(AMOUNT),--amount $(AMOUNT),)

advance-deal:  ## Advance a deal stage (set COMPANY="Name" STAGE=meeting_booked)
	$(PYTHON) scripts/hubspot.py advance-deal --company "$(COMPANY)" --stage $(STAGE)

# ─── Reports ──────────────────────────────────────────────────────────────────

report:  ## Generate weekly signal report from output/
	$(PYTHON) scripts/report.py generate

report-hs:  ## Weekly report with live HubSpot stage data
	$(PYTHON) scripts/report.py generate --include-hubspot

# ─── Signals & BirdDog ────────────────────────────────────────────────────────

signals:  ## Find signals from Apollo (hiring + funded) → signals_intake.csv
	$(PYTHON) scripts/signals.py all --output data/signals_intake.csv

signals-hiring:  ## Find companies posting sales roles via Apollo
	$(PYTHON) scripts/signals.py apollo-hiring --output data/signals_intake.csv

signals-funded:  ## Find recently funded B2B SaaS companies via Apollo
	$(PYTHON) scripts/signals.py apollo-funded --output data/signals_intake.csv

signals-yc:  ## Fetch YC W26 companies from public YC directory
	$(PYTHON) scripts/signals.py yc-batch --batch W26 --output data/yc_w26_targets.csv

birddog-status:  ## Check BirdDog connection and monitored account count
	$(PYTHON) scripts/birddog.py status

birddog-pull:  ## Pull signals from BirdDog (last 7 days)
	$(PYTHON) scripts/birddog.py pull-signals

birddog-run:  ## Pull BirdDog signals and run pipeline on them
	$(PYTHON) scripts/birddog.py pull-signals --run-pipeline

# ─── Follow-Up Cadence ────────────────────────────────────────────────────────

followup-due:  ## List all contacts with follow-up touches due
	$(PYTHON) scripts/follow_up.py due

followup-generate:  ## Generate follow-up message (set FILE=output/x.json EMAIL=e TOUCH=1)
	$(PYTHON) scripts/follow_up.py generate --file $(FILE) --email $(EMAIL) --touch $(TOUCH) --save

followup-log:  ## Log a follow-up as sent (set FILE EMAIL TOUCH, optional DATE STATUS)
	$(PYTHON) scripts/follow_up.py log --file $(FILE) --email $(EMAIL) --touch $(TOUCH)

followup-status:  ## Show follow-up status for one account (set FILE=output/x.json)
	$(PYTHON) scripts/follow_up.py status --file $(FILE)

followup-tasks:  ## Create HubSpot tasks for all due follow-ups
	$(PYTHON) scripts/follow_up.py create-tasks

followup-respond:  ## Generate response to a prospect reply (set FILE EMAIL REPLY="they said...")
	$(PYTHON) scripts/follow_up.py respond --file $(FILE) --email $(EMAIL) --reply-summary "$(REPLY)" --save

# ─── Transcripts ──────────────────────────────────────────────────────────────

transcript:  ## Process a voice memo transcript (set FILE=path/to/file.txt)
	$(PYTHON) scripts/transcript.py process --file $(FILE) --update-project

# ─── Signal Audit (client engagements) ───────────────────────────────────────

new-client:  ## Start a new Signal Audit client (set CLIENT=slug DOMAIN=domain.com)
	$(PYTHON) scripts/pipeline.py new-client --client $(CLIENT) --domain $(DOMAIN)

audit-week1:  ## Run Week 1 workflow for a client (set CLIENT=slug)
	$(PYTHON) scripts/signal_audit.py week1 --client $(CLIENT)

audit-week2:  ## Run Week 2 enrichment for a client (set CLIENT=slug)
	$(PYTHON) scripts/signal_audit.py week2 --client $(CLIENT)

audit-deliverable:  ## Compile final deliverable package (set CLIENT=slug)
	$(PYTHON) scripts/signal_audit.py deliverable --client $(CLIENT)

audit-status:  ## Show Signal Audit engagement status (set CLIENT=slug)
	$(PYTHON) scripts/signal_audit.py status --client $(CLIENT)

# ─── Account Matrix (client-agnostic artifacts) ──────────────────────────────

init-matrix:  ## Scaffold a new client account matrix stub (set CLIENT=slug)
	$(PYTHON) projects/deploygtm-own/scripts/init_matrix.py --client $(CLIENT)

outreach-variants:  ## Generate 3 outreach variants (set CLIENT=slug COMPANY="Name" [LOG=1|2|3])
	$(PYTHON) projects/deploygtm-own/scripts/generate_outreach.py --client $(CLIENT) --company "$(COMPANY)" $(if $(LOG),--log-variant $(LOG),)

batch-outreach:  ## Generate variants across a tier filter (set CLIENT=slug [TIER=1 or 1,2] [LIMIT=n] [LOG=1|2|3])
	$(PYTHON) projects/deploygtm-own/scripts/batch_outreach.py --client $(CLIENT) $(if $(TIER),--tier $(TIER),) $(if $(LIMIT),--limit $(LIMIT),) $(if $(LOG),--log-variant $(LOG),)

verify-signals:  ## Audit which accounts are ready vs. blocked on signal gaps (set CLIENT=slug)
	$(PYTHON) projects/deploygtm-own/scripts/verify_signals.py --client $(CLIENT)

variant-respond:  ## Record a response to a tracked variant (set ID=n SENTIMENT=positive|neutral|negative)
	$(PYTHON) projects/deploygtm-own/scripts/variant_tracker.py respond --id $(ID) --sentiment $(SENTIMENT)

variant-list:  ## List logged variants (optional CLIENT=slug)
	$(PYTHON) projects/deploygtm-own/scripts/variant_tracker.py list $(if $(CLIENT),--client $(CLIENT),)

variant-report:  ## Weekly variant performance by angle (set CLIENT=slug)
	$(PYTHON) projects/deploygtm-own/scripts/variant_tracker.py report --client $(CLIENT)

weekly-report:  ## Weekly signal report for a client (set CLIENT=slug)
	$(PYTHON) projects/deploygtm-own/scripts/weekly_signal_report.py --client $(CLIENT)

# ─── Git ──────────────────────────────────────────────────────────────────────

push:  ## Commit staged changes and push to current branch
	@read -p "Commit message: " msg; \
	git commit -m "$$msg" && git push

# ─── Help ─────────────────────────────────────────────────────────────────────

help:  ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
	| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'
