#!/usr/bin/env python3
"""Verify deterministic accessibility invariants of an Endeavor static HTML report.

This is a structural check, not a browser, layout, contrast, keyboard, or
screen-reader emulator.  Those require separate human release review.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import stat
import sys


VOID_ELEMENTS = frozenset({"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"})
HEADING = re.compile(r"h[1-6]")


@dataclass
class Node:
    tag: str
    attributes: dict[str, str]
    children: list["Node"] = field(default_factory=list)
    text: list[str] = field(default_factory=list)


class ReportParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.root = Node("document", {})
        self.stack = [self.root]
        self.errors: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        node = Node(tag, {key.lower(): value or "" for key, value in attrs})
        self.stack[-1].children.append(node)
        if tag not in VOID_ELEMENTS:
            self.stack.append(node)

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.handle_starttag(tag, attrs)
        if tag.lower() not in VOID_ELEMENTS:
            self.handle_endtag(tag)

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if len(self.stack) == 1 or self.stack[-1].tag != tag:
            self.errors.append(f"mismatched closing tag: {tag}")
            return
        self.stack.pop()

    def handle_data(self, data: str) -> None:
        self.stack[-1].text.append(data)


def _nodes(node: Node, tag: str | None = None) -> list[Node]:
    found: list[Node] = []
    for child in node.children:
        if tag is None or child.tag == tag:
            found.append(child)
        found.extend(_nodes(child, tag))
    return found


def _text(node: Node) -> str:
    return "".join([*node.text, *(_text(child) for child in node.children)]).strip()


def _descendants(node: Node, tag: str) -> list[Node]:
    return _nodes(node, tag)


def _violation(condition: bool, message: str, violations: list[str]) -> None:
    if not condition:
        violations.append(message)


def validate(path: Path) -> dict[str, object]:
    try:
        metadata = path.lstat()
    except OSError as exc:
        raise ValueError("report does not exist") from exc
    if not stat.S_ISREG(metadata.st_mode) or stat.S_ISLNK(metadata.st_mode):
        raise ValueError("report must be a regular non-symlink file")
    try:
        source = path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError("report is not UTF-8") from exc
    parser = ReportParser()
    parser.feed(source)
    parser.close()
    violations = list(parser.errors)
    _violation(source.lstrip().lower().startswith("<!doctype html>"), "missing HTML doctype", violations)
    _violation(len(parser.stack) == 1, "unclosed HTML element", violations)

    html = _nodes(parser.root, "html")
    head = _nodes(parser.root, "head")
    body = _nodes(parser.root, "body")
    main = _nodes(parser.root, "main")
    _violation(len(html) == 1 and bool(html[0].attributes.get("lang", "").strip()), "document must have one html element with lang", violations)
    _violation(len(head) == 1, "document must have one head element", violations)
    _violation(len(body) == 1, "document must have one body element", violations)
    _violation(len(main) == 1, "document must have one main landmark", violations)

    titles = _nodes(parser.root, "title")
    _violation(len(titles) == 1 and bool(_text(titles[0])), "document must have one non-empty title", violations)
    charsets = [node for node in _nodes(parser.root, "meta") if node.attributes.get("charset", "").lower() == "utf-8"]
    viewports = [node for node in _nodes(parser.root, "meta") if node.attributes.get("name", "").lower() == "viewport" and bool(node.attributes.get("content", "").strip())]
    _violation(bool(charsets), "document must declare UTF-8", violations)
    _violation(bool(viewports), "document must declare a viewport", violations)

    headings = [node for node in _nodes(parser.root) if HEADING.fullmatch(node.tag)]
    heading_levels = [int(node.tag[1]) for node in headings]
    _violation(heading_levels.count(1) == 1, "document must have exactly one h1", violations)
    _violation(heading_levels[:1] == [1], "first heading must be h1", violations)
    _violation(all(current <= previous + 1 for previous, current in zip(heading_levels, heading_levels[1:])), "heading levels must not skip", violations)
    _violation(all(bool(_text(node)) for node in headings), "headings must not be empty", violations)

    identifiers: dict[str, Node] = {}
    for node in _nodes(parser.root):
        identifier = node.attributes.get("id")
        if identifier:
            if identifier in identifiers:
                violations.append(f"duplicate id: {identifier}")
            identifiers[identifier] = node
    for section in _nodes(parser.root, "section"):
        labelledby = section.attributes.get("aria-labelledby", "").strip()
        _violation(bool(labelledby), "section must have aria-labelledby", violations)
        if labelledby:
            label = identifiers.get(labelledby)
            _violation(label is not None and HEADING.fullmatch(label.tag) is not None and bool(_text(label)), f"section label is not a non-empty heading: {labelledby}", violations)

    for table in _nodes(parser.root, "table"):
        captions = _descendants(table, "caption")
        headers = _descendants(table, "th")
        _violation(len(captions) == 1 and bool(_text(captions[0])), "table must have one non-empty caption", violations)
        _violation(bool(headers), "table must have headers", violations)
        _violation(all(header.attributes.get("scope") in {"col", "row", "colgroup", "rowgroup"} for header in headers), "table headers must declare scope", violations)
        _violation(len(_descendants(table, "thead")) == 1 and len(_descendants(table, "tbody")) == 1, "table must have thead and tbody", violations)

    for image in _nodes(parser.root, "img"):
        _violation("alt" in image.attributes, "image must declare alt text", violations)
    for anchor in _nodes(parser.root, "a"):
        _violation(bool(_text(anchor)) or bool(anchor.attributes.get("aria-label", "").strip()), "link must have an accessible name", violations)
    for node in _nodes(parser.root):
        _violation("autofocus" not in node.attributes, "autofocus is not allowed", violations)
        _violation(not (node.attributes.get("tabindex", "") and node.attributes["tabindex"] not in {"-1", "0"}), "positive tabindex is not allowed", violations)
        _violation(not any(name.startswith("on") for name in node.attributes), "inline event handlers are not allowed", violations)

    return {
        "format": "endeavor-report-accessibility-validation",
        "version": "1.0.0",
        "report": path.name,
        "status": "passed" if not violations else "failed",
        "checks": [
            "document-language-and-metadata",
            "landmarks-and-heading-hierarchy",
            "section-labels",
            "semantic-table-labels",
            "accessible-image-and-link-names",
            "keyboard-risk-markup",
        ],
        "violations": violations,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        payload = validate(args.report)
    except ValueError as exc:
        payload = {
            "format": "endeavor-report-accessibility-validation",
            "version": "1.0.0",
            "report": args.report.name or "report",
            "status": "failed",
            "checks": [],
            "violations": [str(exc)],
        }
    destination = sys.stdout if payload["status"] == "passed" else sys.stderr
    print(json.dumps(payload, sort_keys=True), file=destination)
    return 0 if payload["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
