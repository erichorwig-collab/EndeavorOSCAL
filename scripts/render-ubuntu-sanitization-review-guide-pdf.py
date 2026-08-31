#!/usr/bin/env python3
"""Render the short Ubuntu 24.04 human-review packet as a local PDF."""

from pathlib import Path

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import KeepTogether, Paragraph, Preformatted, SimpleDocTemplate, Spacer


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "output/pdf/ubuntu-24.04-human-sanitization-review-guide.pdf"


def p(text, style):
    return Paragraph(text.replace("&", "&amp;"), style)


def main():
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    styles = getSampleStyleSheet()
    styles["BodyText"].leading = 14
    code_style = styles["Code"]
    code_style.fontSize = 7.5
    code_style.leading = 9
    story = [
        p("Endeavor Ubuntu 24.04 human sanitization review", styles["Title"]),
        Spacer(1, 0.12 * inch),
        p("Simple reviewer packet. Review only committed sanitized evidence. Never recover or retain raw scan output.", styles["BodyText"]),
    ]
    sections = [
        ("Stop immediately if", "Reject if you find a real hostname, FQDN, address, MAC address, user identifier, package inventory, credential, token, private path, or another unnecessary system characteristic. Also reject if a required CPE, SCAP identifier, reference, rule result, schema version, or hash is missing or changed. When uncertain, reject; do not edit evidence in place.", None),
        ("1. Start from a clean checkout", "Run this on the review host. git status --short must print nothing.", "cd /home/elo/Work/Endeavor\ngit status --short\ngit rev-parse HEAD"),
        ("2. Verify integrity", "Compare the four hashes to the table in PROVENANCE.md. Inspection must show target endeavor-target, identity endeavor-fixture-user, IPv4 127.0.0.1, IPv6 0:0:0:0:0:0:0:1, and MAC 00:00:00:00:00:00.", "C=fixtures/ga-corpus/ubuntu-24.04-x86_64\nsha256sum $C/results.xml $C/results.arf.xml \\\n  $C/results.oscal.json $C/results.arf.oscal.json\npython3 -m endeavor inspect-xccdf --results $C/results.xml\npython3 -m endeavor inspect-arf --results $C/results.arf.xml"),
        ("3. Review SCAP evidence", "Open results.xml and results.arf.xml. Confirm canonical target facts and retain OpenSCAP 1.4.4, SCAP 1.3, XCCDF 1.2, OVAL 5.11.3, CPE 2.3, ARF 1.1, CPE/benchmark/component references, and expected deliberately failing rule outcomes. The /input/ paths are fixed container paths, not host paths.", "rg -n -i 'hostname|fqdn|mac|ip-|identity|token|password|secret|/home/' \\\n  $C/results.xml $C/results.arf.xml"),
        ("4. Verify generated OSCAL", "Both cmp commands must be silent and return status 0.", "M=fixtures/mappings/arf-xccdf-example-v1.json\npython3 -m endeavor convert-xccdf --results $C/results.xml \\\n  --mapping $M --output /tmp/endeavor-ubuntu-xccdf-review.json\npython3 -m endeavor convert-arf-xccdf --results $C/results.arf.xml \\\n  --mapping $M --output /tmp/endeavor-ubuntu-arf-review.json\ncmp /tmp/endeavor-ubuntu-xccdf-review.json $C/results.oscal.json\ncmp /tmp/endeavor-ubuntu-arf-review.json $C/results.arf.oscal.json\nrm -f /tmp/endeavor-ubuntu-xccdf-review.json /tmp/endeavor-ubuntu-arf-review.json"),
        ("5. Record the decision", "In PROVENANCE.md, record reviewer, UTC date, approved/rejected decision, the four files reviewed, hash match, sensitive-data finding, SCAP-preservation finding, and notes. Approval alone does not admit Ubuntu: the Rocky review and version-specific GA record must also complete.", None),
    ]
    for heading, text, command in sections:
        group = [p(heading, styles["Heading1"]), p(text, styles["BodyText"])]
        if command:
            group += [Spacer(1, 0.06 * inch), Preformatted(command, code_style)]
        story += [KeepTogether(group), Spacer(1, 0.07 * inch)]
    SimpleDocTemplate(str(OUTPUT), pagesize=letter, leftMargin=0.7 * inch,
                      rightMargin=0.7 * inch, topMargin=0.65 * inch,
                      bottomMargin=0.65 * inch,
                      title="Ubuntu 24.04 human sanitization review",
                      author="EndeavorOSCAL").build(story)


if __name__ == "__main__":
    main()
