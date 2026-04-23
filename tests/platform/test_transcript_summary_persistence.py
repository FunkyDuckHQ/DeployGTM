from pathlib import Path
import sys
import json

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts import transcript as t


def test_save_project_transcript_summary_writes_json(tmp_path: Path):
    t.PROJECTS_DIR = tmp_path
    (tmp_path / "acme-space").mkdir(parents=True, exist_ok=True)

    summary = {
        "one_line_summary": "Quick sync",
        "what_matters": ["Need ICP strategy"],
        "primary_project": "acme-space",
    }

    out = t.save_project_transcript_summary("acme-space", summary)

    assert out.exists()
    data = json.loads(out.read_text())
    assert data["one_line_summary"] == "Quick sync"
    assert out.parent == tmp_path / "acme-space" / "transcripts"
