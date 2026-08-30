"""Accessible static HTML rendering for mapping-coverage reports."""

from __future__ import annotations

from html import escape


def _text(value: object) -> str:
    return escape(str(value), quote=True)


def _cell(value: object) -> str:
    return f"<td>{_text(value)}</td>"


def mapping_report_html(report: dict[str, object]) -> str:
    summary = report["summary"]
    mapping = report["mapping"]
    before = [
        "<!doctype html>",
        '<html lang="en">',
        "<head><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">",
        "<title>Endeavor mapping coverage report</title>",
        "<style>body{max-width:72rem;margin:2rem auto;padding:0 1rem;font:1rem/1.5 system-ui,sans-serif;color:#1b1b1b}table{border-collapse:collapse;width:100%;margin:1rem 0}th,td{border:1px solid #666;padding:.5rem;text-align:left;vertical-align:top}th{background:#eee}caption{text-align:left;font-weight:700;margin:.5rem 0}code{overflow-wrap:anywhere}dt{font-weight:700}dd{margin:0 0 .5rem}</style></head>",
        "<body><main>",
        "<h1>Endeavor mapping coverage report</h1>",
        '<section aria-labelledby="summary"><h2 id="summary">Summary</h2><dl>',
    ]
    for key in ("evaluated", "mapped", "unmapped", "stale-mappings"):
        before.append(f"<dt>{_text(key)}</dt><dd>{_text(summary[key])}</dd>")
    before.extend([
        "</dl>",
        '<p>Mapping: <code>' + _text(mapping["path"]) + "</code> (SHA-256 <code>" + _text(mapping["sha256"]) + "</code>).</p>",
        '<section aria-labelledby="mapped"><h2 id="mapped">Mapped evaluated definitions</h2>',
        "<table><caption>Explicit OVAL-to-OSCAL targets</caption><thead><tr><th scope=\"col\">OVAL definition ID</th><th scope=\"col\">Result</th><th scope=\"col\">Targets</th></tr></thead><tbody>",
    ])
    mapped = report["mapped"]
    if mapped:
        for item in mapped:
            targets = ", ".join(f"{target['type']}: {target['target-id']}" for target in item["targets"])
            before.append("<tr>" + _cell(item["oval-definition-id"]) + _cell(item["result"]) + _cell(targets) + "</tr>")
    else:
        before.append('<tr><td colspan="3">No evaluated definitions have an explicit mapping.</td></tr>')
    before.extend([
        "</tbody></table></section>",
        '<section aria-labelledby="unmapped"><h2 id="unmapped">Unmapped evaluated definitions</h2>',
        "<table><caption>Definitions requiring mapping review</caption><thead><tr><th scope=\"col\">OVAL definition ID</th><th scope=\"col\">Result</th><th scope=\"col\">Title</th><th scope=\"col\">Class</th></tr></thead><tbody>",
    ])
    unmapped = report["unmapped"]
    if unmapped:
        for item in unmapped:
            before.append("<tr>" + _cell(item["oval-definition-id"]) + _cell(item["result"]) + _cell(item["title"]) + _cell(item["class"]) + "</tr>")
    else:
        before.append('<tr><td colspan="4">All evaluated definitions have an explicit mapping.</td></tr>')
    before.extend(["</tbody></table></section>", '<section aria-labelledby="stale"><h2 id="stale">Stale mapping identifiers</h2>'])
    stale = report["stale-mappings"]
    if stale:
        before.append("<ul>" + "".join(f"<li><code>{_text(identifier)}</code></li>" for identifier in stale) + "</ul>")
    else:
        before.append("<p>No stale mapping identifiers.</p>")
    before.append("</section></main></body></html>\n")
    return "".join(before)
