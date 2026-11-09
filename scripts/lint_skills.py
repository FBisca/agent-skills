#!/usr/bin/env python3
"""Lint the frontmatter of every SKILL.md under a directory: the YAML every harness must read.

A harness (Claude Code, Codex, Pi) reads a skill's frontmatter as YAML. A frontmatter that
YAML cannot parse, or that YAML reads as something other than what the author wrote, is not a
skill with an error: one harness skips the skill, another keeps it with a description cut in
half, and nothing says so.

Two plain-scalar hazards cause it, and both are invisible in the source:

- a colon in an unquoted value ("into the vault: tasks") is read as a nested mapping, so the
  whole frontmatter fails to parse and the skill disappears;
- a "#" in an unquoted value ("his #heritage-updates reply") starts a comment, so the value is
  silently cut at that word.

Both are fixed by quoting the value. This linter finds them without a YAML dependency, so it
runs in CI on a bare Python, and it names the file, the line and the reason.

The rule it enforces is the one every harness agrees on: the value a harness reads is the text
the author wrote. YAML 1.1 (PyYAML) and YAML 1.2 (the "yaml" npm package Pi uses) disagree on
plain scalars like "yes", "12:30" and "2026-11-07" - one reads a boolean, the other a string -
so a value is only accepted when every dialect reads the same text back.

A quoted value, a flow collection and a block scalar are checked too: a quote that is never
closed, an escape YAML does not define, text after the closing quote, a bracket that closes
another bracket, a collection that is never closed - none of them is text a harness can read,
and every one of them is named with the file, the line and the reason.

Usage: python3 scripts/lint_skills.py [DIR ...]     (no DIR = this repo's skills/)
Exit code: 0 when every skill is clean, 1 when any skill is not, 2 when a path is not a folder.
"""

from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]

# The frontmatter a skill must carry: a name that matches its folder and a description the
# harness routes on. Both must be text, never a boolean, a number or a date.
NAME_KEY = "name"
DESCRIPTION_KEY = "description"
STRING_KEYS = (NAME_KEY, DESCRIPTION_KEY)

# The longest description a harness takes (Claude Code and Pi both cap it at 1024).
MAX_DESCRIPTION = 1024

# A key line: "key:" or "key: value".
KEY_LINE = re.compile(r"^([A-Za-z_][A-Za-z0-9_.-]*):(.*)$")

# A plain scalar may not contain a colon followed by a space, and may not end with a colon:
# YAML reads both as a nested mapping and the whole frontmatter fails to parse.
COLON_IN_PLAIN = re.compile(r":(\s|$)")

# A plain scalar may not contain a "#" preceded by a space: YAML starts a comment there and
# cuts the value.
COMMENT_IN_PLAIN = re.compile(r"\s#")

# Characters YAML reserves at the start of a plain scalar. Each one either fails to parse
# ("%", "@", "`"), starts a structure (",", "[", "]", "{", "}"), or names an anchor, an alias or
# a tag ("&", "*", "!"). A value that starts with a flow indicator ("[", "{", "]", "}") is
# checked as a flow value instead, and a quote is checked as a quoted value.
RESERVED_START = set(",[]{}#&*!|>'\"%@`")

# A plain scalar may not start with these when a space follows: YAML reads a sequence entry,
# a mapping key or a nested mapping.
STRUCTURE_START = ("- ", "? ", ": ")

# The escapes a double-quoted scalar may carry.
DOUBLE_ESCAPES = set('"\\/ntrbf0aev \tN_LPxuU')

# The scalars YAML reads as something other than text. YAML 1.1 reads "yes", "no", "on" and
# "off" as booleans and "12:30" as a number; YAML 1.2 reads them as text. A value either
# dialect reads differently is refused, because the harnesses use different dialects.
NULL_SCALAR = re.compile(r"^(~|null|Null|NULL|)$")
BOOL_1_1 = re.compile(r"^(y|Y|yes|Yes|YES|n|N|no|No|NO|true|True|TRUE|false|False|FALSE|on|On|ON|off|Off|OFF)$")
BOOL_1_2 = re.compile(r"^(true|True|TRUE|false|False|FALSE)$")
NUMBER = re.compile(r"^[-+]?(\d[\d_]*(\.[\d_]*)?([eE][-+]?\d+)?|\.[\d_]+([eE][-+]?\d+)?)$")
HEX_OCTAL = re.compile(r"^[-+]?(0x[0-9a-fA-F_]+|0o[0-7_]+|0b[01_]+)$")
SEXAGESIMAL = re.compile(r"^[-+]?\d[\d_]*(:[0-5]?\d)+$")
INFINITY = re.compile(r"^[-+]?\.(inf|Inf|INF|nan|NaN|NAN)$")
# A timestamp is only a timestamp when the whole scalar is one: "2026-11-07" and
# "2026-11-07T10:00:00Z" are dates, "2026-11-07 and more" is text.
TIMESTAMP = re.compile(
    r"^\d{4}-\d{2}-\d{2}"
    r"([Tt ]\d{2}:\d{2}:\d{2}(\.\d+)?([Zz]|[+-]\d{2}:\d{2})?)?$")


class Problem:
    """One thing wrong with one skill: where it is and why it matters."""

    def __init__(self, path, line, message):
        self.path = path
        self.line = line
        self.message = message

    def __str__(self):
        return "%s:%s: %s" % (self.path, self.line, self.message)


def _unquote(value):
    """The text a quoted scalar carries, or None when the quoting does not hold."""
    if len(value) >= 2 and value[0] == '"' and value[-1] == '"':
        body = value[1:-1]
        out, index = [], 0
        while index < len(body):
            char = body[index]
            if char == "\\":
                if index + 1 >= len(body) or body[index + 1] not in DOUBLE_ESCAPES:
                    return None
                out.append(body[index + 1])
                index += 2
                continue
            out.append(char)
            index += 1
        return "".join(out)
    if len(value) >= 2 and value[0] == "'" and value[-1] == "'":
        body = value[1:-1]
        if re.search(r"(?<!')'(?!')", body):
            return None
        return body.replace("''", "'")
    return None


def _is_text(value):
    """True when every YAML dialect reads this plain scalar as the text it is."""
    if value != value.strip():
        return False  # YAML strips the surrounding spaces, so the harness reads less than written
    if NULL_SCALAR.match(value) or BOOL_1_1.match(value) or BOOL_1_2.match(value):
        return False
    if NUMBER.match(value) or HEX_OCTAL.match(value) or SEXAGESIMAL.match(value) or INFINITY.match(value):
        return False
    if TIMESTAMP.match(value):
        return False
    return True


def _quoted_problem(value, line_no, path):
    """The problem with a quoted value, or None when the quoting holds."""
    quote = value[0]
    if len(value) < 2:
        return Problem(path, line_no, "the quoted value is not closed")
    body = value[1:]
    index = 0
    while index < len(body):
        char = body[index]
        if quote == '"' and char == "\\":
            if index + 1 >= len(body) or body[index + 1] not in DOUBLE_ESCAPES:
                return Problem(path, line_no, "the value carries an escape YAML does not define")
            index += 2
            continue
        if char == quote:
            if quote == "'" and body[index + 1:index + 2] == "'":
                index += 2
                continue
            trailing = body[index + 1:].strip()
            if trailing and not trailing.startswith("#"):
                return Problem(path, line_no, "something follows the closing quote of the value")
            return None
        index += 1
    return Problem(path, line_no, "the quoted value is not closed")


def _flow_problem(value, line_no, path):
    """The problem with a flow collection, or None when it holds together."""
    depth = 0
    quote = None
    opened = []
    end = -1
    for index, char in enumerate(value):
        if end != -1:
            break  # the flow value ended: whatever follows is trailing text
        if depth == 0:
            if char in "[{":
                depth = 1
                opened.append(char)
            elif char in "]}":
                return Problem(path, line_no, "the flow value closes a bracket it never opened")
            continue
        if quote:
            if char == quote:
                quote = None
            continue
        if char in "\"'":
            quote = char
        elif char in "[{":
            depth += 1
            opened.append(char)
        elif char in "]}":
            if opened[-1] != ("[" if char == "]" else "{"):
                return Problem(path, line_no, "the flow value closes a bracket it did not open")
            opened.pop()
            depth -= 1
            if depth == 0:
                end = index
    if quote:
        return Problem(path, line_no, "the flow value carries an unclosed quote")
    if depth:
        return Problem(path, line_no, "the flow value is not closed")
    trailing = value[end + 1:].strip()
    if trailing:
        # YAML 1.1 reads the comment and moves on; YAML 1.2 refuses the line. The dialects
        # disagree, so the value must be the whole value.
        return Problem(path, line_no, "something follows the flow value, which YAML cannot read")
    return None


def _plain_problem(value, line_no, path):
    """The problem with a plain scalar, or None when every dialect reads it faithfully."""
    if COLON_IN_PLAIN.search(value):
        return Problem(path, line_no,
                       "the value is not quoted and holds a colon, so YAML reads it as a nested "
                       "mapping and the whole frontmatter fails to parse; quote the value")
    if COMMENT_IN_PLAIN.search(value):
        return Problem(path, line_no,
                       "the value is not quoted and holds a '#', so YAML cuts it at that word; "
                       "quote the value")
    if value[0] in RESERVED_START:
        return Problem(path, line_no,
                       "the value starts with '%s', which YAML reserves; quote the value" % value[0])
    if value.startswith(STRUCTURE_START):
        return Problem(path, line_no,
                       "the value starts with '%s', which YAML reads as a structure; quote the value"
                       % value[:2].strip())
    return None


def _split_fields(lines, path, problems):
    """The frontmatter as (key, value, line number) triples, with the problems found.

    A value is None when it is a block scalar: its text is the indented lines below, which
    YAML folds or keeps, and no harness reads it the way a plain value is read.
    """
    fields = []
    index = 0
    while index < len(lines):
        raw = lines[index]
        line_no = index + 2  # the frontmatter opens on line 1
        index += 1
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        indentation = raw[:len(raw) - len(raw.lstrip())]
        if "\t" in indentation:
            # YAML cannot indent with a tab.
            problems.append(Problem(path, line_no, "the frontmatter holds a tab, which YAML cannot read"))
            continue
        if "\t" in raw[len(indentation):]:
            # A tab anywhere else lands inside the value, and YAML cannot read it there either.
            problems.append(Problem(path, line_no, "the value holds a tab, which YAML cannot read"))
            continue
        match = KEY_LINE.match(raw)
        if not match:
            problems.append(Problem(path, line_no, "the line is not a 'key: value' frontmatter line"))
            continue
        key, rest = match.group(1), match.group(2)
        if rest.startswith(" "):
            rest = rest[1:]
        value = rest.strip()
        if value[:1] in ("|", ">"):
            while index < len(lines) and (not lines[index].strip() or lines[index].startswith((" ", "\t"))):
                index += 1
            fields.append((key, None, line_no))
            continue
        fields.append((key, value, line_no))
    return fields


def _value_text(value):
    """The text a harness reads from a value, or None when it is not text."""
    if value is None:
        return None
    if value[:1] in ("'", '"'):
        return _unquote(value)
    if value[:1] in ("[", "{"):
        return None
    return value


def _flow_is_text(value):
    """True when a flow collection holds nothing but text."""
    return not value.startswith(("[", "{"))


HARDCODED_SKILL_PATH = re.compile(r"~/\.(claude|agents)/skills/")
INVOCATION_SYNTAX = re.compile(r"/skill:|Invoke it as")
ABSOLUTE_USER_PATH = re.compile(r"/(Users|home)/[A-Za-z0-9._-]+/")
TEXT_SUFFIXES = (".md", ".py", ".json", ".sh", ".yml", ".yaml", ".toml")
NOTICE = "NOTICE.md"
UPSTREAM_URL = re.compile(r"https?://\S+")
LICENCE_NAME = re.compile(r"licen[cs]e", re.IGNORECASE)


def _hygiene_lines(path, pattern, message):
    """One problem per line of the file that the pattern matches, naming that line."""
    problems = []
    text = path.read_text(encoding="utf-8", errors="ignore")
    for line_no, line in enumerate(text.splitlines(), 1):
        if pattern.search(line):
            problems.append(Problem(path, line_no, message))
    return problems


def hygiene_problems(path):
    """The hygiene problems of the skill folder that holds one SKILL.md.

    A skill is copied, not linked; it names no install path and no invocation syntax, since the
    harness's own discovery provides both; it holds no absolute user path; and a copied skill
    names its upstream and its licence in its NOTICE.
    """
    problems = []
    folder = path.parent
    if folder.is_symlink():
        return [Problem(path, 1, "the skill folder is a symlink; a skill is copied, not linked")]
    for item in sorted(folder.rglob("*")):
        if item.is_symlink():
            problems.append(Problem(item, 1, "the path is a symlink; a skill is copied, not linked"))
        elif item.is_file() and item.suffix in TEXT_SUFFIXES:
            problems.extend(_hygiene_lines(item, ABSOLUTE_USER_PATH,
                                           "the file holds an absolute user path; name it relative "
                                           "to the skill"))
    problems.extend(_hygiene_lines(path, HARDCODED_SKILL_PATH,
                                   "the skill hardcodes a skill path; name the skill, not its "
                                   "install folder"))
    problems.extend(_hygiene_lines(path, INVOCATION_SYNTAX,
                                   "the skill carries an invocation syntax; the harness's own "
                                   "discovery states the invocation"))
    notice = folder / NOTICE
    if notice.is_file() and not notice.is_symlink():
        text = notice.read_text(encoding="utf-8", errors="ignore")
        if not UPSTREAM_URL.search(text):
            problems.append(Problem(notice, 1, "NOTICE.md does not name its upstream; give the URL "
                                               "it was copied from"))
        if not LICENCE_NAME.search(text):
            problems.append(Problem(notice, 1, "NOTICE.md does not name its licence"))
    return problems


def lint_skill(path):
    """The problems of one SKILL.md: its frontmatter and its folder's hygiene."""
    return hygiene_problems(path) + _frontmatter_problems(path)


def _frontmatter_problems(path):
    """The frontmatter problems of one SKILL.md."""
    problems = []
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        return [Problem(path, 1, "the file cannot be read: %s" % exc)]
    if not text.startswith("---\n"):
        return [Problem(path, 1, "the file has no frontmatter")]
    end = text.find("\n---\n", 3)
    if end == -1:
        return [Problem(path, 1, "the frontmatter is not closed")]
    block = text[4:end + 1].splitlines()
    fields = _split_fields(block, path, problems)

    seen = {}
    for key, value, line_no in fields:
        seen.setdefault(key, (value, line_no))
        if value is None:
            if key in STRING_KEYS:
                problems.append(Problem(path, line_no,
                                        "the '%s' is a block scalar; write it as one quoted line"
                                        % key))
            continue
        if value == "":
            if key in STRING_KEYS:
                problems.append(Problem(path, line_no, "the '%s' is empty" % key))
            continue
        if value[:1] in ("'", '"'):
            problem = _quoted_problem(value, line_no, path)
        elif value[:1] in ("[", "{", "]", "}"):
            problem = _flow_problem(value, line_no, path)
        else:
            problem = _plain_problem(value, line_no, path)
        if problem:
            problems.append(problem)
        elif key in STRING_KEYS and not _flow_is_text(value):
            problems.append(Problem(path, line_no,
                                    "the '%s' is a list or a mapping, but a harness reads it as "
                                    "text; quote the value" % key))
        elif key in STRING_KEYS and not _is_text(value):
            problems.append(Problem(path, line_no,
                                    "the '%s' is not quoted and YAML reads it as something other "
                                    "than text; quote the value" % key))

    if NAME_KEY not in seen:
        problems.append(Problem(path, 1, "the frontmatter has no '%s'" % NAME_KEY))
    else:
        name, line_no = seen[NAME_KEY]
        if name is None or name == "":
            pass  # already reported: a block scalar or an empty name
        else:
            text_name = _value_text(name)
            if text_name is None:
                text_name = name
            if text_name != path.parent.name:
                problems.append(Problem(path, line_no,
                                        "the '%s' is '%s' but the folder is '%s'"
                                        % (NAME_KEY, text_name, path.parent.name)))

    if DESCRIPTION_KEY not in seen:
        problems.append(Problem(path, 1, "the frontmatter has no '%s'" % DESCRIPTION_KEY))
    else:
        description, line_no = seen[DESCRIPTION_KEY]
        if description is None or description == "":
            pass  # already reported: a block scalar or an empty description
        else:
            text_description = _value_text(description)
            if text_description is None:
                pass  # already reported: a flow collection
            elif not text_description.strip():
                problems.append(Problem(path, line_no, "the '%s' is empty" % DESCRIPTION_KEY))
            elif len(text_description) > MAX_DESCRIPTION:
                problems.append(Problem(path, line_no,
                                        "the '%s' is %d characters, over the %d a harness takes"
                                        % (DESCRIPTION_KEY, len(text_description), MAX_DESCRIPTION)))
    return problems


def lint_dir(directory):
    """The problems of every SKILL.md under a directory."""
    problems = []
    for skill in sorted(Path(directory).glob("*/SKILL.md")):
        problems.extend(lint_skill(skill))
    return problems


def main(argv):
    directories = argv[1:] or [str(ROOT / "skills")]
    problems = []
    for directory in directories:
        path = Path(directory)
        if not path.is_dir():
            print("not a directory: %s" % path, file=sys.stderr)
            return 2
        problems.extend(lint_dir(path))
    for problem in problems:
        print(problem)
    if problems:
        print("%d problem(s) in %d skill(s)"
              % (len(problems), len({str(problem.path) for problem in problems})), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
