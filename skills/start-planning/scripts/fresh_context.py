#!/usr/bin/env python3
"""Bounded fresh-context gatherer for start-planning: the Pi path.

Pi has no subagent tool, so the gather step runs the task packet through a separate
`pi --print` session: a fresh session directory, no inherited conversation, a timeout, a
restricted tool set and a strict return schema. Every failure path exits non-zero with a
reason, so the caller stops instead of continuing on evidence the gatherer never produced.

Usage:
    python3 fresh_context.py --packet <packet.md> [--timeout 600] [--output <result.json>]
                             [--pi-bin pi] [--model <id>] [--cwd <dir>] [--allow-bash]
                             [--inherit-env]

Exit codes: 0 ok, 2 usage, 3 pi not found, 4 pi failed, 5 timeout, 6 malformed answer,
7 packet refused.
"""

import argparse
import json
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import sys
import tempfile

OK = 0
USAGE = 2
NO_PI = 3
PI_FAILED = 4
TIMEOUT = 5
MALFORMED = 6
REFUSED = 7

DEFAULT_TIMEOUT = 600.0
DEFAULT_TOOLS = "read,ls,grep,find"

# The keys the gatherer must answer with, exactly: a strict schema, so a malformed answer
# fails the step instead of reaching the plan as prose.
RETURN_KEYS = ("sources", "decisions", "findings", "counts", "edge_cases")

# Credentials never belong in a packet: it travels to a subprocess. These patterns refuse
# the packet instead of leaking it.
SECRET_PATTERNS = (
    re.compile(r"\bsk-[A-Za-z0-9_-]{16,}"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{16,}"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"\b[A-Za-z0-9_]*(?:API_KEY|SECRET|PASSWORD|ACCESS_TOKEN)[A-Za-z0-9_]*\s*[=:]\s*\S{8,}"),
)

# The environment the gatherer needs to run pi: paths, home (pi's own config lives there),
# proxies and the provider credentials. Everything else in the parent environment is dropped.
ENV_KEEP = {
    "PATH", "HOME", "TMPDIR", "TEMP", "TMP", "LANG", "LC_ALL", "LC_CTYPE", "TERM", "SHELL",
    "USER", "LOGNAME", "SSH_AUTH_SOCK", "HTTP_PROXY", "HTTPS_PROXY", "NO_PROXY",
    "http_proxy", "https_proxy", "no_proxy", "SSL_CERT_FILE", "SSL_CERT_DIR",
}
ENV_PREFIX = ("PI_",)
ENV_SUFFIX = ("_API_KEY", "_API_BASE", "_BASE_URL", "_TOKEN")

RETURN_FORMAT = """
## Return format

Answer with one JSON object and nothing else: no prose before it, no code fences.

{"sources": [{"source": "<link or repo-relative path>", "settles": "<what it settles>"}],
 "decisions": [{"decision": "<what the source settles>", "source": "<source>", "status": "settled|open"}],
 "findings": ["<fact read from the code or a source>"],
 "counts": {"<population>": <integer>},
 "edge_cases": ["<empty set, conflict, departed or archived owner>"]}

`sources` lists every source you read, with what it settles. `decisions` lists the
decisions the sources settle (status `settled`) and the ones they leave open (status
`open`). `counts` and `edge_cases` carry what the data shows; leave a key out when there is
no data to count.
""".strip()


class GatherError(Exception):
    """A gatherer failure the caller must see: it carries the exit code and the reason."""

    def __init__(self, code, reason):
        super().__init__(reason)
        self.code = code
        self.reason = reason


# ---- the packet ----------------------------------------------------------------------------

def read_packet(path):
    """The packet text, or a refusal when it is missing or carries a secret."""
    packet = Path(path)
    if not packet.is_file():
        raise GatherError(USAGE, "packet not found: %s" % packet)
    text = packet.read_text(encoding="utf-8")
    for pattern in SECRET_PATTERNS:
        match = pattern.search(text)
        if match:
            line = text[: match.start()].count("\n") + 1
            raise GatherError(REFUSED,
                              "the packet carries a secret-looking string at line %d (%s); "
                              "a packet holds references and allowed paths, never credentials"
                              % (line, match.group(0)[:12]))
    return text


# ---- the subprocess ------------------------------------------------------------------------

def build_argv(pi_bin, prompt, session_dir, model=None, tools=DEFAULT_TOOLS):
    """The argv of the isolated gatherer session: no parent session, no extensions, no MCP."""
    argv = [pi_bin, "--print", "--no-session", "--session-dir", str(session_dir),
            "--no-extensions", "--no-mcp", "--tools", tools]
    if model:
        argv += ["--model", model]
    argv.append(prompt)
    return argv


def build_env(inherit=False):
    """The environment of the gatherer: what pi needs to run, not what the parent holds."""
    if inherit:
        return dict(os.environ)
    env = {name: value for name, value in os.environ.items()
           if name in ENV_KEEP or name.startswith(ENV_PREFIX) or name.endswith(ENV_SUFFIX)}
    env.setdefault("PATH", os.defpath)
    return env


def pi_process(argv, cwd, env, timeout):
    """Run the gatherer's pi subprocess. The seam the tests answer.

    Returns (returncode, stdout, stderr). Raises subprocess.TimeoutExpired on a timeout.
    """
    proc = subprocess.Popen(argv, cwd=cwd, env=env, stdin=subprocess.DEVNULL,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                            start_new_session=True)
    try:
        out, err = proc.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
        except OSError:
            pass
        proc.communicate()
        raise
    return proc.returncode, out, err


# ---- the answer ----------------------------------------------------------------------------

def extract_json(text):
    """The JSON object in the answer, or None when there is none."""
    text = (text or "").strip()
    if not text:
        return None
    fenced = re.match(r"^```[A-Za-z]*\s*\n(.*?)\n?```\s*$", text, re.S)
    if fenced:
        text = fenced.group(1).strip()
    try:
        parsed = json.loads(text)
    except ValueError:
        parsed = None
    if isinstance(parsed, dict):
        return parsed
    return _scan_object(text)


def _scan_object(text):
    """The first balanced JSON object in the text, string-aware."""
    depth = 0
    start = -1
    in_string = False
    escaped = False
    for index, char in enumerate(text):
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
        elif char == "{":
            if depth == 0:
                start = index
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0 and start >= 0:
                try:
                    parsed = json.loads(text[start:index + 1])
                except ValueError:
                    start = -1
                    continue
                if isinstance(parsed, dict):
                    return parsed
    return None


def _strings(value, path, problems):
    if not isinstance(value, list):
        problems.append("%s must be a list" % path)
        return
    for index, item in enumerate(value):
        if not isinstance(item, str):
            problems.append("%s[%d] must be a string" % (path, index))


def validate(obj):
    """The reasons the answer is not a valid gather result; empty means valid."""
    problems = []
    if not isinstance(obj, dict):
        return ["the answer is not a JSON object"]
    missing = [key for key in RETURN_KEYS if key not in obj]
    if missing:
        problems.append("missing keys: %s" % ", ".join(missing))
    unknown = [key for key in obj if key not in RETURN_KEYS]
    if unknown:
        problems.append("unknown keys: %s" % ", ".join(sorted(unknown)))
    if missing or unknown:
        return problems

    sources = obj["sources"]
    if not isinstance(sources, list):
        problems.append("sources must be a list")
    elif not sources:
        problems.append("sources is empty: every source read must be listed")
    else:
        for index, source in enumerate(sources):
            if not isinstance(source, dict):
                problems.append("sources[%d] must be an object" % index)
                continue
            for key in ("source", "settles"):
                if not isinstance(source.get(key), str) or not source[key].strip():
                    problems.append("sources[%d].%s must be a non-empty string" % (index, key))

    decisions = obj["decisions"]
    if not isinstance(decisions, list):
        problems.append("decisions must be a list")
    else:
        for index, decision in enumerate(decisions):
            if not isinstance(decision, dict):
                problems.append("decisions[%d] must be an object" % index)
                continue
            for key in ("decision", "source"):
                if not isinstance(decision.get(key), str) or not decision[key].strip():
                    problems.append("decisions[%d].%s must be a non-empty string" % (index, key))
            if decision.get("status") not in ("settled", "open"):
                problems.append('decisions[%d].status must be "settled" or "open"' % index)

    _strings(obj["findings"], "findings", problems)
    _strings(obj["edge_cases"], "edge_cases", problems)

    counts = obj["counts"]
    if not isinstance(counts, dict):
        problems.append("counts must be an object")
    else:
        for key, value in counts.items():
            if not isinstance(value, int) or isinstance(value, bool):
                problems.append("counts[%s] must be an integer" % key)
    return problems


# ---- the run -------------------------------------------------------------------------------

def gather(packet_path, timeout=DEFAULT_TIMEOUT, pi_bin="pi", model=None, cwd=None,
           allow_bash=False, inherit_env=False, runner=None):
    """Run the gatherer and return the validated result object.

    Raises GatherError on every failure: missing packet, missing pi, a failed or timed-out
    subprocess, a malformed answer or a refused packet.
    """
    packet = read_packet(packet_path)
    cwd = str(cwd or os.getcwd())
    if os.path.sep in pi_bin:
        pi_path = pi_bin if os.access(pi_bin, os.X_OK) else None
    else:
        pi_path = shutil.which(pi_bin)
    if not pi_path:
        raise GatherError(NO_PI,
                          "pi not found (%s): install Pi, or gather with the harness's own "
                          "fresh-context path" % pi_bin)
    prompt = packet + "\n\n" + RETURN_FORMAT
    tools = DEFAULT_TOOLS + (",bash" if allow_bash else "")
    session_dir = tempfile.mkdtemp(prefix="start-planning-gather-")
    try:
        argv = build_argv(pi_path, prompt, session_dir, model=model, tools=tools)
        env = build_env(inherit=inherit_env)
        runner = runner or pi_process
        try:
            code, out, err = runner(argv, cwd, env, timeout)
        except subprocess.TimeoutExpired:
            raise GatherError(TIMEOUT, "the gatherer timed out after %gs" % timeout)
        if code != 0:
            raise GatherError(PI_FAILED, "pi exited %s: %s" % (code, (err or out or "").strip()[-500:]))
    finally:
        shutil.rmtree(session_dir, ignore_errors=True)

    answer = extract_json(out)
    if answer is None:
        raise GatherError(MALFORMED, "the gatherer answered with no JSON object: %s"
                          % (out or "").strip()[-500:])
    problems = validate(answer)
    if problems:
        raise GatherError(MALFORMED, "the gatherer answered with an invalid result: %s"
                          % "; ".join(problems))
    return answer


def main(argv=None):
    parser = argparse.ArgumentParser(description="Run a start-planning gather packet in a fresh Pi session.")
    parser.add_argument("--packet", required=True, help="the gather packet (see references/gather-packet.md)")
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT, help="seconds before the gatherer fails")
    parser.add_argument("--output", help="write the validated result here as JSON")
    parser.add_argument("--pi-bin", default="pi", help="the pi executable (default: pi)")
    parser.add_argument("--model", help="model id for the gatherer session")
    parser.add_argument("--cwd", help="directory the gatherer runs in (default: the current one)")
    parser.add_argument("--allow-bash", action="store_true",
                        help="give the gatherer the bash tool too, for read-only queries")
    parser.add_argument("--inherit-env", action="store_true",
                        help="pass the whole parent environment to the gatherer")
    args = parser.parse_args(argv)

    try:
        answer = gather(args.packet, timeout=args.timeout, pi_bin=args.pi_bin, model=args.model,
                        cwd=args.cwd, allow_bash=args.allow_bash, inherit_env=args.inherit_env)
    except GatherError as error:
        print("GATHER FAILED: %s" % error.reason, file=sys.stderr)
        return error.code

    text = json.dumps(answer, indent=2, ensure_ascii=False)
    print(text)
    if args.output:
        Path(args.output).write_text(text + "\n", encoding="utf-8")
    return OK


if __name__ == "__main__":
    sys.exit(main())
