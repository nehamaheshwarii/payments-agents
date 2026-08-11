#!/usr/bin/env python3
"""Prepare an API spec audit: parse the spec, chunk its endpoints, and write
self-contained analysis requests for Claude Code to pick up.

This script never calls an API. It writes request files under
runs/<timestamp>/requests/ and prints instructions for having Claude Code
read them, run the analysis described in prompts/, and write the combined
result to runs/<timestamp>/findings.json.
"""

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests
import yaml

CHUNK_SIZE = 4
CORE_FLOW_ENDPOINT_LIMIT = 12
PROMPTS_DIR = Path(__file__).parent / "prompts"
RUNS_DIR = Path(__file__).parent / "runs"


def parse_spec_text(text: str) -> dict:
    text = text.strip()
    if text.startswith("{"):
        return json.loads(text)
    return yaml.safe_load(text)


def load_spec(source: str) -> dict:
    if re.match(r"^https?://", source):
        resp = requests.get(source, timeout=20)
        resp.raise_for_status()
        return parse_spec_text(resp.text)
    return parse_spec_text(Path(source).read_text())


def resolve_refs(node, root, seen=None, depth=0, max_depth=6):
    if seen is None:
        seen = set()
    if depth > max_depth:
        return node
    if isinstance(node, dict):
        ref = node.get("$ref")
        if isinstance(ref, str) and ref.startswith("#/"):
            if ref in seen:
                return {"$ref": ref}
            target = root
            for part in ref.lstrip("#/").split("/"):
                target = target.get(part, {}) if isinstance(target, dict) else {}
            return resolve_refs(target, root, seen | {ref}, depth + 1, max_depth)
        return {k: resolve_refs(v, root, seen, depth + 1, max_depth) for k, v in node.items()}
    if isinstance(node, list):
        return [resolve_refs(item, root, seen, depth + 1, max_depth) for item in node]
    return node


def extract_endpoints(spec: dict) -> list[dict]:
    methods = {"get", "post", "put", "patch", "delete"}
    endpoints = []
    for path, path_item in (spec.get("paths") or {}).items():
        if not isinstance(path_item, dict):
            continue
        shared_params = path_item.get("parameters", [])
        for method, operation in path_item.items():
            if method.lower() not in methods or not isinstance(operation, dict):
                continue
            op = dict(operation)
            if shared_params:
                op["parameters"] = shared_params + op.get("parameters", [])
            endpoints.append(
                {
                    "path": path,
                    "method": method.upper(),
                    "operation": resolve_refs(op, spec),
                }
            )
    return endpoints


def chunk_list(items, size):
    for i in range(0, len(items), size):
        yield items[i : i + size]


def build_endpoint_requests(endpoints: list[dict]) -> list[str]:
    prompt = (PROMPTS_DIR / "endpoint_analysis.md").read_text()
    files = []
    for chunk in chunk_list(endpoints, CHUNK_SIZE):
        payload = json.dumps(chunk, indent=2, default=str)
        files.append(
            f"{prompt}\n\n---\n\n## Endpoints to analyze\n\n```json\n{payload}\n```\n"
        )
    return files


def build_consumer_request(spec: dict, endpoints: list[dict]) -> str:
    prompt = (PROMPTS_DIR / "consumer_simulation.md").read_text()
    overview = {
        "info": spec.get("info", {}),
        "paths": [
            {
                "path": e["path"],
                "method": e["method"],
                "summary": e["operation"].get("summary"),
                "description": e["operation"].get("description"),
            }
            for e in endpoints
        ],
        "core_flow_detail": endpoints[:CORE_FLOW_ENDPOINT_LIMIT],
    }
    payload = json.dumps(overview, indent=2, default=str)
    return f"{prompt}\n\n---\n\n## Spec overview\n\n```json\n{payload}\n```\n"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Parse an OpenAPI spec and prepare an audit for Claude Code."
    )
    parser.add_argument("source", help="Spec URL or local file path (YAML or JSON)")
    args = parser.parse_args()

    try:
        spec = load_spec(args.source)
    except Exception as e:
        print(f"Couldn't load the spec: {e}", file=sys.stderr)
        sys.exit(1)

    endpoints = extract_endpoints(spec)
    if not endpoints:
        print("No endpoints found in this spec.", file=sys.stderr)
        sys.exit(1)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    run_dir = RUNS_DIR / timestamp
    requests_dir = run_dir / "requests"
    requests_dir.mkdir(parents=True, exist_ok=True)

    request_files = []

    for i, content in enumerate(build_endpoint_requests(endpoints), start=1):
        name = f"endpoint_analysis_{i:02d}.md"
        (requests_dir / name).write_text(content)
        request_files.append(f"requests/{name}")

    consumer_name = "consumer_simulation.md"
    (requests_dir / consumer_name).write_text(build_consumer_request(spec, endpoints))
    request_files.append(f"requests/{consumer_name}")

    findings_path = run_dir / "findings.json"
    manifest = {
        "spec_source": args.source,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "endpoint_count": len(endpoints),
        "requests": request_files,
        "output": "findings.json",
    }
    (run_dir / "manifest.json").write_text(json.dumps(manifest, indent=2))

    print(f"Parsed {len(endpoints)} endpoint(s).")
    print(f"Wrote {len(request_files)} request file(s) to {requests_dir}/\n")
    print("Next steps:")
    print("  1. In Claude Code, ask it to read every file in that requests/ directory")
    print("     and follow each file's instructions.")
    print("  2. Have it combine all the resulting JSON arrays into one and write it to")
    print(f"     {findings_path}")
    print(f"  3. Run `streamlit run app.py` and select run \"{timestamp}\" to view results.\n")
    print("Suggested prompt for Claude Code:")
    print(
        f'  Read every file in {requests_dir}/, follow each file\'s instructions, and '
        f'write a single JSON array combining all findings to {findings_path}'
    )


if __name__ == "__main__":
    main()
