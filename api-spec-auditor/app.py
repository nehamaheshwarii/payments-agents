import json
from pathlib import Path

import streamlit as st

RUNS_DIR = Path(__file__).parent / "runs"
SEVERITY_ORDER = {"high": 0, "medium": 1, "low": 2}
CATEGORY_LABELS = {
    "ambiguous_field": "Ambiguous field",
    "missing_error_semantics": "Missing error semantics",
    "breaking_change_risk": "Breaking-change risk",
    "integration_blind_spot": "Integration blind spot",
}
SEVERITY_ICON = {"high": "\U0001F534", "medium": "\U0001F7E0", "low": "\U0001F7E1"}


def list_runs() -> list[Path]:
    if not RUNS_DIR.exists():
        return []
    return sorted((p for p in RUNS_DIR.iterdir() if p.is_dir()), reverse=True)


def load_manifest(run_dir: Path) -> dict:
    manifest_path = run_dir / "manifest.json"
    if not manifest_path.exists():
        return {}
    try:
        return json.loads(manifest_path.read_text())
    except json.JSONDecodeError:
        return {}


def load_findings(run_dir: Path) -> list[dict] | None:
    findings_path = run_dir / "findings.json"
    if not findings_path.exists():
        return None
    try:
        data = json.loads(findings_path.read_text())
    except json.JSONDecodeError:
        return []
    return data if isinstance(data, list) else []


def rank_findings(findings: list[dict]) -> list[dict]:
    return sorted(findings, key=lambda f: SEVERITY_ORDER.get(f.get("severity", "low"), 3))


def render_findings(findings: list[dict]) -> None:
    st.subheader(f"{len(findings)} finding(s)")

    counts = {}
    for f in findings:
        sev = f.get("severity", "unknown")
        counts[sev] = counts.get(sev, 0) + 1
    cols = st.columns(3)
    for col, sev in zip(cols, ["high", "medium", "low"]):
        col.metric(sev.title(), counts.get(sev, 0))

    for f in findings:
        sev = f.get("severity", "low")
        icon = SEVERITY_ICON.get(sev, "⚪")
        cat = CATEGORY_LABELS.get(f.get("category"), f.get("category", "finding"))
        endpoint = f.get("endpoint", "")
        with st.expander(f"{icon} [{sev.upper()}] {endpoint} — {cat}"):
            st.markdown(f"**Finding:** {f.get('finding', '')}")
            st.markdown(f"**Why it becomes a support ticket:** {f.get('impact', '')}")
            st.markdown(f"**Suggested fix:** {f.get('suggested_fix', '')}")


def main() -> None:
    st.set_page_config(page_title="API Spec Auditor", page_icon="\U0001F50D", layout="wide")

    st.title("API Spec Auditor")
    st.caption(
        "Catch the ambiguities in your OpenAPI spec before your partners find them in production."
    )

    runs = list_runs()
    if not runs:
        st.info(
            "No runs yet.\n\n"
            "From a terminal:\n\n"
            "```\npython audit.py <spec-url-or-file>\n```\n\n"
            "then follow the printed instructions to have Claude Code complete the "
            "analysis. Come back here once it's written a `findings.json`."
        )
        return

    run_names = [r.name for r in runs]
    selected = st.selectbox("Run", run_names)
    run_dir = RUNS_DIR / selected

    manifest = load_manifest(run_dir)
    if manifest:
        st.caption(
            f"Source: {manifest.get('spec_source', '?')} · "
            f"{manifest.get('endpoint_count', '?')} endpoint(s) · "
            f"{manifest.get('created_at', '?')}"
        )

    findings = load_findings(run_dir)
    if findings is None:
        st.warning(
            f"No `findings.json` yet for this run. Have Claude Code read the files in "
            f"`runs/{selected}/requests/` and write results to `runs/{selected}/findings.json`."
        )
        return

    if not findings:
        st.success("No findings recorded for this run.")
        return

    render_findings(rank_findings(findings))


if __name__ == "__main__":
    main()
