"""The agent -> driver handoff files: versioned JSON, validated here, stdlib only.

The driver reads these and nothing else from an agent: a missing or invalid file counts as no report.
`report.json`   worker: the ledger checkpoint shape plus `head` (commit sha) and `pr` (URL or null).
`review.json`   reviewer: `verdict` pass|block, `major[]`, `deferred[]`, `commit` reviewed; block iff `major` is not empty.
`findings.json` driver -> fix round: `source`, `attempt` and the blocking `items` verbatim."""

import json

VERSION = 1
LIMIT = 65536
STATUSES = ("PARTIAL", "BLOCKED", "COMPLETE")
SOURCES = ("converge", "review", "ci")
MAJOR_FIELDS = ("id", "file", "line", "problem", "fix")


class ContractError(ValueError):
    """A handoff file is missing or breaks its contract."""


def need(condition, message):
    if not condition:
        raise ContractError(message)


def text(value):
    return isinstance(value, str) and bool(value.strip())


def whole(value, least=0):
    return isinstance(value, int) and not isinstance(value, bool) and value >= least


def versioned(value, what):
    need(isinstance(value, dict), "%s must be a JSON object" % what)
    need(value.get("contract") == VERSION, "%s: contract must be %d" % (what, VERSION))


def validate_report(report):
    versioned(report, "report")
    need(text(report.get("task_id")), "report: task_id is required")
    need(report.get("status") in STATUSES, "report: status must be one of " + ", ".join(STATUSES))
    need(text(report.get("summary")), "report: summary is required")
    need(isinstance(report.get("acceptance_met"), bool), "report: acceptance_met must be true or false")
    for key in ("files", "decisions", "interfaces", "remaining", "checks"):
        need(isinstance(report.get(key), list), "report: %s must be a list" % key)
    need(text(report.get("head")), "report: head (the commit sha) is required")
    need(report.get("pr") is None or text(report["pr"]), "report: pr must be a URL or null")
    return report


def validate_major(item, where):
    need(isinstance(item, dict), "%s: each major item (in items) must be an object" % where)
    for key in MAJOR_FIELDS:
        need(key in item and item[key] not in (None, ""), "%s: major item lacks %s" % (where, key))
    need(text(item["id"]) and text(item["file"]) and text(item["problem"]) and text(item["fix"]),
         "%s: major id, file, problem and fix must be text" % where)
    need(whole(item["line"], 1), "%s: major line must be a positive whole number" % where)


def validate_review(review):
    versioned(review, "review")
    need(review.get("verdict") in ("pass", "block"), "review: verdict must be pass or block")
    need(isinstance(review.get("major"), list), "review: major must be a list")
    need(isinstance(review.get("deferred"), list), "review: deferred must be a list")
    for item in review["major"]:
        validate_major(item, "review")
    for item in review["deferred"]:
        need(isinstance(item, dict) and text(item.get("id")) and text(item.get("note")),
             "review: each deferred item needs an id and a note")
    need(text(review.get("commit")), "review: commit (the sha reviewed) is required")
    need((review["verdict"] == "block") == bool(review["major"]),
         "review: verdict block needs major items, and pass must have none")
    return review


def validate_findings(findings):
    versioned(findings, "findings")
    need(findings.get("source") in SOURCES, "findings: source must be one of " + ", ".join(SOURCES))
    need(whole(findings.get("attempt"), 1), "findings: attempt must be a positive whole number")
    items = findings.get("items")
    need(isinstance(items, list) and items, "findings: items must be a non-empty list")
    if findings["source"] == "review":
        for item in items:
            validate_major(item, "findings")
    else:
        need(all(text(item) for item in items), "findings: items must be non-empty lines of text for " + findings["source"])
    return findings


def make_findings(source, attempt, items):
    return validate_findings({"contract": VERSION, "source": source, "attempt": attempt, "items": list(items)})


def load(path, validate):
    """Read one handoff file and validate it; every failure names the file."""
    try:
        with open(path, encoding="utf-8") as stream:
            raw = stream.read(LIMIT + 1)
    except OSError as error:
        raise ContractError("%s: cannot read (%s)" % (path, error.strerror or error)) from None
    need(len(raw) <= LIMIT, "%s: exceeds 64 KiB; keep the handoff compact" % path)
    try:
        value = json.loads(raw)
    except ValueError as error:
        raise ContractError("%s: not valid JSON (%s)" % (path, error)) from None
    try:
        return validate(value)
    except ContractError as error:
        raise ContractError("%s: %s" % (path, error)) from None
