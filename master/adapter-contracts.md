# DeployGTM Adapter Contracts

All external integrations are adapters. Adapters satisfy abstract base classes. Business logic in `scripts/platform/` calls adapters through their contracts, never through provider-specific APIs directly.

---

## CRMAdapter

File: `scripts/platform/adapters/base.py`

```python
class CRMAdapter(ABC):
    provider: str                          # "hubspot", "salesforce", "attio", etc.

    def setup(self, *, dry_run: bool = False) -> list[dict]:
        """Provision DeployGTM custom fields/properties in the CRM."""

    def upsert_company(self, company: CompanyRecord, *, dry_run: bool = False) -> Optional[str]:
        """Create or update company. Returns provider company ID."""

    def upsert_contact(
        self,
        contact: ContactRecord,
        context: CRMContext,
        *,
        company_id: Optional[str] = None,
        dry_run: bool = False,
    ) -> Optional[str]:
        """Create or update contact. Returns provider contact ID."""

    def sync(
        self,
        company: CompanyRecord,
        contacts: Iterable[ContactRecord],
        context: CRMContext,
        *,
        dry_run: bool = False,
    ) -> SyncResult:
        """Default orchestrator: upsert company, then each contact."""
```

**Rules:**
- `dry_run=True` must always be the safe default in calling code.
- `setup()` must be idempotent: calling it twice must not duplicate fields.
- Never write to a production CRM without explicit `--confirm` flag at the CLI layer.
- DeployGTM-prefixed properties (`deploygtm_activation_priority`, etc.) are the only properties this system owns in a client CRM. Do not touch other properties.

**Current implementations:**
- `scripts/hubspot.py` (legacy direct; wrap in adapter before new CRM work)
- `scripts/platform/adapters/hubspot.py` (canonical — target implementation)

**Canonical types:** `CompanyRecord`, `ContactRecord`, `CRMContext`, `SyncResult` in `adapters/types.py`.

---

## MessagingAdapter

File: `scripts/platform/adapters/messaging.py` (to be created)

The messaging brain is a data source, not the operating system. Any implementation that can return calibrated outreach copy for a given account + ICP + signal context satisfies this contract.

```python
class MessagingAdapter(ABC):
    provider: str                          # "local_brain", "octave", "custom", etc.

    def get_icp_context(self, icp_name: str) -> dict:
        """Return ICP definition: description, fit_criteria, disqualifiers, personas."""

    def get_persona_context(self, persona_name: str) -> dict:
        """Return persona: pain points, language, objections, buying triggers."""

    def get_tone_guidelines(self) -> dict:
        """Return tone and style rules: what to avoid, what to lead with."""

    def generate_opener(
        self,
        company: CompanyRecord,
        signal: dict,
        icp_name: str,
        persona_name: str,
    ) -> str:
        """Generate a first-line opener tied to the signal, not the product."""

    def generate_outreach(
        self,
        company: CompanyRecord,
        signal: dict,
        icp_name: str,
        persona_name: str,
    ) -> dict:
        """Return full outreach object: opener, body, cta, follow_up_variants."""
```

**Rules:**
- The opener must lead with the signal or the pain hypothesis, never the product.
- `generate_outreach()` must return at least 2 follow-up variants.
- No AI-sounding language. No "I hope this finds you well." The output must pass a native speaker test.
- Any implementation must be testable without a live API: use fixture responses in tests.

**Current implementations:**
- `LocalBrainAdapter`: reads `brain/` markdown files. The default and only current implementation.
- `OctaveAdapter`: deferred. Wire once Octave API access is confirmed. Must satisfy this contract exactly — no pipeline changes required.

**Switching adapters:**
Change `config.yaml: messaging.provider` from `local_brain` to `octave`. No code changes to the pipeline.

---

## SignalAdapter

File: `scripts/platform/adapters/signal.py` (to be created)

Signal adapters surface account signals from external monitoring systems. They do not determine signal meaning or ICP fit — that is business logic in `account_matrix.py`.

```python
class SignalAdapter(ABC):
    provider: str                          # "birddog", "apollo", "manual", etc.

    def pull_signals(
        self,
        manifest: list[dict],              # birddog_signal_manifest.json entries
        *,
        dry_run: bool = False,
    ) -> list[dict]:
        """Fetch signals matching the manifest. Returns list of signal events."""

    def push_manifest(
        self,
        manifest: list[dict],
        *,
        dry_run: bool = False,
    ) -> dict:
        """Register signal definitions with the provider. Returns provider response."""

    def get_status(self) -> dict:
        """Return provider connectivity and quota status."""
```

**Signal event shape (returned by `pull_signals`):**
```json
{
  "domain": "acme.com",
  "signal_id": "sales_hiring",
  "signal_date": "2026-04-15",
  "signal_source": "birddog",
  "signal_summary": "Posted VP Sales role on LinkedIn",
  "birddog_score": 78,
  "alpha": false,
  "ability_indicator": false,
  "willingness_indicator": true,
  "raw": {}
}
```

**Rules:**
- `alpha`, `ability_indicator`, `willingness_indicator` are required fields on every signal event.
- Generic signals (`funding_recent`, `sales_hiring`) default `alpha: false`.
- Client-specific signals derived from ICP strategy must explicitly declare `alpha: true`.
- `dry_run=True` must not push to external systems; return a mock response envelope.

**Current implementations:**
- `ManualSignalAdapter`: reads `data/signals_intake.csv`. Current default.
- `BirddogAdapter`: calls BirdDog API. Status: `enabled: false` in `config.yaml` until API write capability confirmed.
- `ApolloSignalAdapter`: uses Apollo for hiring/funding signals. Active for legacy pipeline.

---

## EnrichmentAdapter (existing, informal)

Currently implemented in `scripts/apollo.py` without an ABC. Future state:

```python
class EnrichmentAdapter(ABC):
    provider: str                          # "apollo", "clay", "clearbit", etc.

    def enrich_company(self, domain: str) -> dict:
        """Return firmographic data for domain."""

    def find_contacts(self, domain: str, titles: list[str]) -> list[dict]:
        """Return contacts at domain matching titles."""
```

Formalizing this ABC is deferred until the demo-quality build loop is stable. Do not block Signal Audit work on this.

---

## Adapter registration

`config.yaml` controls which adapter implementation is active for each category:

```yaml
adapters:
  crm: hubspot                     # hubspot | salesforce | attio | dry_run
  messaging: local_brain           # local_brain | octave
  signal: manual                   # manual | birddog | apollo
  enrichment: apollo               # apollo | clay
```

Pipeline code reads this config and instantiates the correct adapter. Adding a new provider means: implement the ABC, add to the registry, add the config key. No pipeline changes.

---

## What adapters must never do

- Contain scoring logic (that is `account_matrix.py`)
- Contain ICP derivation logic (that is `icp_strategy.py`)
- Write to production systems without a `dry_run` parameter
- Depend on each other directly (adapters are independently swappable)
- Return provider-specific IDs or data structures in the return type — always map to canonical types
