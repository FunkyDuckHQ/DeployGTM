from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.platform.context_pack import build_context_pack


def test_context_pack_has_source_trace_for_deploygtm_own():
    pack = build_context_pack("deploygtm-own")

    assert pack["client_slug"] == "deploygtm-own"
    assert pack["principles"], "expected at least one principle"

    for principle in pack["principles"]:
        assert principle["principle_text"]
        assert principle["confidence"] in {"high", "medium", "low"}
        assert principle["source_trace"], "each principle must have source evidence"
        for ev in principle["source_trace"]:
            assert ev["source_type"] in {"client_context", "transcript_summary", "master_brain", "customer_outcome_intake"}
            assert ev["source_ref"]
            assert ev["evidence_snippet"]
