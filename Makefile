# DeployGTM — Common commands
# Usage: make <target>

.DEFAULT_GOAL := help

# ─── Setup ────────────────────────────────────────────────────────────────────

install:  ## Install Python dependencies
	pip install -r requirements.txt

env:  ## Copy .env.example to .env (won't overwrite existing)
	@if [ -f .env ]; then echo ".env already exists — edit it directly."; \
	else cp .env.example .env && echo "Created .env — fill in your API keys."; fi

setup-hubspot:  ## Create DeployGTM custom properties in HubSpot (run once)
	python scripts/pipeline.py setup-hubspot

setup: install env  ## Full setup: install deps + create .env
	@echo "\nSetup complete. Fill in .env, then run: make run-one"

# ─── Pipeline ─────────────────────────────────────────────────────────────────

run-one:  ## Run pipeline on one account (prompts for input)
	@echo "Usage: python scripts/pipeline.py run --company NAME --domain DOMAIN --signal TYPE --signal-date YYYY-MM-DD"

batch:  ## Run batch pipeline on data/signals_intake.csv
	python scripts/batch.py run --input data/signals_intake.csv

batch-yc:  ## Run batch pipeline on data/yc_w26_targets.csv
	python scripts/batch.py run --input data/yc_w26_targets.csv

batch-resume:  ## Resume interrupted batch (skips already-processed domains)
	python scripts/batch.py run --input data/yc_w26_targets.csv --resume

# ─── Export & CRM ─────────────────────────────────────────────────────────────

export:  ## Export output/ to HubSpot import CSVs (priority ≥ 8)
	python scripts/export.py run --min-priority 8

push-hubspot:  ## Push output/ directly to HubSpot via API (requires confirmation)
	python scripts/export.py run --push-to-hubspot --min-priority 8

# ─── Reports ──────────────────────────────────────────────────────────────────

report:  ## Generate weekly signal report from output/
	python scripts/report.py generate

report-hs:  ## Weekly report with live HubSpot stage data
	python scripts/report.py generate --include-hubspot

# ─── BirdDog ──────────────────────────────────────────────────────────────────

signals:  ## Find signals from Apollo (hiring + funded) → signals_intake.csv
	python scripts/signals.py all --output data/signals_intake.csv

signals-hiring:  ## Find companies posting sales roles via Apollo
	python scripts/signals.py apollo-hiring --output data/signals_intake.csv

signals-funded:  ## Find recently funded B2B SaaS companies via Apollo
	python scripts/signals.py apollo-funded --output data/signals_intake.csv

signals-yc:  ## Fetch YC W26 companies from public YC directory
	python scripts/signals.py yc-batch --batch W26 --output data/yc_w26_targets.csv

birddog-status:  ## Check BirdDog connection and monitored account count
	python scripts/birddog.py status

birddog-pull:  ## Pull signals from BirdDog (last 7 days)
	python scripts/birddog.py pull-signals

birddog-run:  ## Pull BirdDog signals and run pipeline on them
	python scripts/birddog.py pull-signals --run-pipeline

# ─── Transcripts ──────────────────────────────────────────────────────────────

transcript:  ## Process a voice memo transcript (set FILE=path/to/file.txt)
	python scripts/transcript.py process --file $(FILE) --update-project

# ─── Signal Audit (client engagements) ───────────────────────────────────────

new-client:  ## Start a new Signal Audit client (set CLIENT=slug DOMAIN=domain.com)
	python scripts/pipeline.py new-client --client $(CLIENT) --domain $(DOMAIN)

audit-week1:  ## Run Week 1 workflow for a client (set CLIENT=slug)
	python scripts/signal_audit.py week1 --client $(CLIENT)

audit-week2:  ## Run Week 2 enrichment for a client (set CLIENT=slug)
	python scripts/signal_audit.py week2 --client $(CLIENT)

audit-deliverable:  ## Compile final deliverable package (set CLIENT=slug)
	python scripts/signal_audit.py deliverable --client $(CLIENT)

audit-status:  ## Show Signal Audit engagement status (set CLIENT=slug)
	python scripts/signal_audit.py status --client $(CLIENT)

# ─── Git ──────────────────────────────────────────────────────────────────────

push:  ## Commit staged changes and push to current branch
	@read -p "Commit message: " msg; \
	git commit -m "$$msg" && git push

# ─── Help ─────────────────────────────────────────────────────────────────────

help:  ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
	| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'
