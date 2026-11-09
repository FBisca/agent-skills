"""The skill frontmatter contract: every SKILL.md must be readable by every harness.

A harness (Claude Code, Codex, Pi) reads a skill's frontmatter as YAML. Frontmatter that YAML
cannot parse makes the skill disappear; frontmatter that YAML reads as something other than the
text the author wrote makes the harness route on a description the author never wrote. Neither
is loud, so the gate checks it here.

`scripts/lint_skills.py` holds the rules and names the file, the line and the reason. This test
runs it over the skills of this repo, over a set of frontmatter that must be refused, and over
the exit codes the gate reads. The refusals are read out of the lint itself, so a rule the lint
grows without a test fails here.
"""

import ast
import contextlib
import io
import pytest
from pathlib import Path
import importlib.util
import os
import re
import sys
import tempfile
import unittest


pytestmark = pytest.mark.unit

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "skills"


def load_linter():
    """The linter module, loaded from the script the gate runs."""
    path = ROOT / "scripts" / "lint_skills.py"
    spec = importlib.util.spec_from_file_location("lint_skills", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["lint_skills"] = module
    spec.loader.exec_module(module)
    return module


LINTER = load_linter()


def write_skill(body, root):
    """A SKILL.md with the given frontmatter, in a folder under `root`."""
    directory = Path(root) / "probe"
    directory.mkdir()
    skill = directory / "SKILL.md"
    skill.write_text(body, encoding="utf-8")
    return skill


# Every defect the lint names, with the message it must refuse it by. The lint can only be
# trusted where it refuses: a rule nobody exercises is a rule nobody knows.
DEFECTS = [
    ("an unclosed double quote",
     '---\nname: probe\ndescription: "An unclosed quote\n---\n\nbody\n',
     "the quoted value is not closed"),
    ("an unclosed single quote",
     "---\nname: probe\ndescription: 'An unclosed quote\n---\n\nbody\n",
     "the quoted value is not closed"),
    ("an escape YAML does not define",
     '---\nname: probe\ndescription: "A bad \\q escape."\n---\n\nbody\n',
     "the value carries an escape YAML does not define"),
    ("text after the closing quote",
     '---\nname: probe\ndescription: "A value." and more\n---\n\nbody\n',
     "something follows the closing quote of the value"),
    ("a flow value that closes a bracket it never opened",
     '---\nname: probe\ndescription: ]\n---\n\nbody\n',
     "the flow value closes a bracket it never opened"),
    ("a flow value that closes the wrong bracket",
     '---\nname: probe\ndescription: [a, b}\n---\n\nbody\n',
     "the flow value closes a bracket it did not open"),
    ("a flow value that is not closed",
     '---\nname: probe\ndescription: [a, b\n---\n\nbody\n',
     "the flow value is not closed"),
    ("a flow value with an unclosed quote",
     '---\nname: probe\ndescription: [a, "b]\n---\n\nbody\n',
     "the flow value carries an unclosed quote"),
    ("text after the flow value",
     '---\nname: probe\ndescription: [a, b] and more\n---\n\nbody\n',
     "something follows the flow value, which YAML cannot read"),
    ("a value that starts with a character YAML reserves",
     '---\nname: probe\ndescription: %reserved\n---\n\nbody\n',
     "the value starts with '%', which YAML reserves"),
    ("a value that starts with a structure",
     '---\nname: probe\ndescription: - dash\n---\n\nbody\n',
     "the value starts with '-', which YAML reads as a structure"),
    ("a tab inside the value",
     '---\nname: probe\ndescription: "A\ttab."\n---\n\nbody\n',
     "the value holds a tab, which YAML cannot read"),
    ("a tab in the indentation",
     '---\nname: probe\n\tdescription: "A description."\n---\n\nbody\n',
     "the frontmatter holds a tab, which YAML cannot read"),
    ("a line that is not a frontmatter line",
     '---\nname: probe\nthis is not a key line\ndescription: "A description."\n---\n\nbody\n',
     "the line is not a 'key: value' frontmatter line"),
    ("a file with no frontmatter",
     'name: probe\ndescription: "A description."\n\nbody\n',
     "the file has no frontmatter"),
    ("a frontmatter that is not closed",
     '---\nname: probe\ndescription: "A description."\n\nbody\n',
     "the frontmatter is not closed"),
    ("an empty name",
     '---\nname:\ndescription: "A description."\n---\n\nbody\n',
     "the 'name' is empty"),
    ("an empty description",
     '---\nname: probe\ndescription:\n---\n\nbody\n',
     "the 'description' is empty"),
    ("a description over the length a harness takes",
     '---\nname: probe\ndescription: "%s"\n---\n\nbody\n' % ("x" * 1100),
     "the 'description' is 1100 characters, over the 1024 a harness takes"),
    ("a description that is a block scalar",
     '---\nname: probe\ndescription: |\n  A description.\n---\n\nbody\n',
     "the 'description' is a block scalar; write it as one quoted line"),
    ("a name that is a block scalar",
     '---\nname: |\n  probe\ndescription: "A description."\n---\n\nbody\n',
     "the 'name' is a block scalar; write it as one quoted line"),
    ("a file that cannot be read",
     b"---\nname: probe\ndescription: \xff\xfe\n---\n\nbody\n",
     "the file cannot be read:"),
    ("an unquoted colon",
     "---\nname: probe\ndescription: Holds a colon: inside it.\n---\n\nbody\n",
     "the value is not quoted and holds a colon"),
    ("an unquoted hash",
     "---\nname: probe\ndescription: Friday, his #heritage-updates reply.\n---\n\nbody\n",
     "the value is not quoted and holds a '#'"),
    ("a value YAML reads as something other than text",
     '---\nname: yes\ndescription: "A description."\n---\n\nbody\n',
     "the 'name' is not quoted and YAML reads it as something other than text"),
    ("a name that is a list",
     '---\nname: [a, b]\ndescription: "A description."\n---\n\nbody\n',
     "the 'name' is a list or a mapping"),
    ("a frontmatter with no name",
     '---\ndescription: "A description."\n---\n\nbody\n',
     "the frontmatter has no 'name'"),
    ("a frontmatter with no description",
     '---\nname: probe\n---\n\nbody\n',
     "the frontmatter has no 'description'"),
    ("a name that is not the folder",
     '---\nname: other\ndescription: "A description."\n---\n\nbody\n',
     "the 'name' is 'other' but the folder is 'probe'"),
]


def problem_templates():
    """The refusal messages the lint can produce, read from the lint itself.

    The lint is the one place that knows what it can refuse, so the test reads its messages
    out of the source instead of keeping a second list that can drift.
    """
    source = (ROOT / "scripts" / "lint_skills.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    templates = set()
    for node in ast.walk(tree):
        if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                and node.func.id == "Problem" and len(node.args) >= 3):
            continue
        message = node.args[2]
        if isinstance(message, ast.BinOp) and isinstance(message.op, ast.Mod):
            message = message.left
        if isinstance(message, ast.Constant) and isinstance(message.value, str):
            templates.add(message.value)
    return templates


def template_pattern(template):
    """The template as a pattern: the parts it fixes, and anything for the parts it fills."""
    pattern = re.escape(template)
    return re.sub(r"%[sd]", ".+", pattern)


class Discovery(unittest.TestCase):
    """Every skill of this repo carries frontmatter every harness can read."""

    def test_every_skill_of_this_repo_passes_the_frontmatter_lint(self):
        """The repo's own skills are the first thing the gate protects."""
        problems = LINTER.lint_dir(SKILLS)
        self.assertEqual([str(problem) for problem in problems], [])

    def test_the_linter_finds_a_skill_in_a_broken_frontmatter(self):
        """The lint reaches every skill of the directory, not only the first."""
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            broken = Path(tmp) / "broken"
            broken.mkdir()
            (broken / "SKILL.md").write_text(
                "---\nname: broken\ndescription: Holds a colon: inside it.\n---\n\nbody\n",
                encoding="utf-8")
            problems = LINTER.lint_dir(tmp)
            self.assertEqual(len(problems), 1)
            self.assertIn("colon", problems[0].message)


class RefusedFrontmatter(unittest.TestCase):
    """The frontmatter every harness reads faithfully, and the ones none does."""

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = tmp.name

    def assert_refused(self, frontmatter, because):
        problems = LINTER.lint_skill(write_skill(frontmatter, self.root))
        self.assertTrue(problems, "the lint accepted frontmatter that %s" % because)
        self.assertIn(because.split()[0], " ".join(problem.message for problem in problems))

    def assert_accepted(self, frontmatter):
        problems = LINTER.lint_skill(write_skill(frontmatter, self.root))
        self.assertEqual([str(problem) for problem in problems], [])

    def test_a_quoted_value_is_accepted(self):
        """The fix for a colon: quote the value."""
        self.assert_accepted('---\nname: probe\ndescription: "Holds a colon: inside it."\n---\n\nbody\n')

    def test_a_quoted_value_with_inner_quotes_is_accepted(self):
        """A description that quotes itself stays one string."""
        self.assert_accepted(
            '---\nname: probe\ndescription: "Says \\"capture this\\" or \\"park this\\"."\n---\n\nbody\n')

    def test_a_single_quoted_value_is_accepted(self):
        """Single quotes carry a value with inner double quotes."""
        self.assert_accepted('---\nname: probe\ndescription: \'Says "capture this" or "park this".\'\n---\n\nbody\n')

    def test_an_unquoted_colon_is_refused(self):
        """The bug Pi reported: YAML reads the value as a nested mapping."""
        self.assert_refused("---\nname: probe\ndescription: Holds a colon: inside it.\n---\n\nbody\n",
                            "colon")

    def test_an_unquoted_hash_is_refused(self):
        """The quieter bug: YAML cuts the value at the '#'."""
        self.assert_refused("---\nname: probe\ndescription: Friday, his #heritage-updates reply.\n---\n\nbody\n",
                            "#")

    def test_a_value_that_is_not_text_is_refused(self):
        """YAML reads 'yes' as a boolean, so the harness never sees the text."""
        self.assert_refused("---\nname: probe\ndescription: yes\n---\n\nbody\n", "text")

    def test_a_list_as_a_description_is_refused(self):
        """A harness reads a description as text, never as a list."""
        self.assert_refused("---\nname: probe\ndescription: [a, b]\n---\n\nbody\n", "list")

    def test_a_name_that_does_not_match_its_folder_is_refused(self):
        """The harness routes on the name, which must be the folder."""
        self.assert_refused('---\nname: other\ndescription: "A description."\n---\n\nbody\n', "folder")

    def test_a_missing_description_is_refused(self):
        """Without a description a harness has nothing to route on."""
        self.assert_refused('---\nname: probe\n---\n\nbody\n', "description")

    def test_a_tab_is_refused(self):
        """YAML cannot read a tab."""
        self.assert_refused('---\nname: probe\ndescription: "A\ttab."\n---\n\nbody\n', "tab")


GOOD_SKILL = '---\nname: probe\ndescription: "A description."\n---\n\nbody\n'


def make_skill(root, files):
    """A skill folder named probe under root, holding the given files; returns its SKILL.md."""
    directory = Path(root) / "probe"
    for relative, text in {"SKILL.md": GOOD_SKILL, **files}.items():
        target = directory / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
    return directory / "SKILL.md"


def symlinked_file(root):
    """A skill whose reference is a symlink to a file outside the folder."""
    skill = make_skill(root, {})
    target = Path(root) / "elsewhere.md"
    target.write_text("text\n", encoding="utf-8")
    os.symlink(target, skill.parent / "link.md")
    return skill


def symlinked_folder(root):
    """A skill whose whole folder is a symlink to a folder elsewhere."""
    real = make_skill(Path(root) / "real", {}).parent
    link = Path(root) / "probe"
    os.symlink(real, link)
    return link / "SKILL.md"


# Every hygiene defect the lint names: a hardcoded skill path, an invocation syntax, an absolute
# user path, a symlink, and a copied skill whose NOTICE names no upstream or no licence. Each case
# builds a skill under a temp root, and names the message and the line the lint must give.
HYGIENE = [
    ("a hardcoded Claude skill path",
     lambda root: make_skill(root, {"SKILL.md": GOOD_SKILL + "Install into ~/.claude/skills/probe.\n"}),
     "the skill hardcodes a skill path", 7),
    ("a hardcoded Codex and Pi skill path",
     lambda root: make_skill(root, {"SKILL.md": GOOD_SKILL + "Install into ~/.agents/skills/probe.\n"}),
     "the skill hardcodes a skill path", 7),
    ("a Pi invocation syntax",
     lambda root: make_skill(root, {"SKILL.md": GOOD_SKILL + "Run /skill:probe first.\n"}),
     "the skill carries an invocation syntax", 7),
    ("an invocation instruction",
     lambda root: make_skill(root, {"SKILL.md": GOOD_SKILL + "Invoke it as probe.\n"}),
     "the skill carries an invocation syntax", 7),
    ("an absolute user path in a reference",
     lambda root: make_skill(root, {"references/notes.md": "Read /Users/someone/notes.md first.\n"}),
     "the file holds an absolute user path", 1),
    ("a hardcoded skill path in a reference",
     lambda root: make_skill(root, {"references/install.md": "Install into ~/.claude/skills/probe.\n"}),
     "the skill hardcodes a skill path", 1),
    ("an invocation syntax in a reference",
     lambda root: make_skill(root, {"references/usage.md": "Run /skill:probe first.\n"}),
     "the skill carries an invocation syntax", 1),
    ("a symlinked file",
     symlinked_file,
     "is a symlink", 1),
    ("a symlinked skill folder",
     symlinked_folder,
     "is a symlink", 1),
    ("a NOTICE that names no upstream",
     lambda root: make_skill(root, {"NOTICE.md": "Derived by hand. MIT License.\n"}),
     "NOTICE.md does not name its upstream", 1),
    ("a NOTICE that names no licence",
     lambda root: make_skill(root, {"NOTICE.md": "Derived from https://github.com/example/skills.\n"}),
     "NOTICE.md does not name its licence", 1),
]


def hygiene_problems(build):
    """The problems the lint finds in one skill a case builds under a temp root."""
    with tempfile.TemporaryDirectory() as tmp:
        return LINTER.lint_skill(build(Path(tmp)))


class Refusals(unittest.TestCase):
    """Every defect the lint names is refused, and every refusal it can produce is asserted."""

    def lint(self, body, folder="probe"):
        """The problems the lint finds in one SKILL.md, written in a temp folder."""
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp) / folder
            directory.mkdir()
            skill = directory / "SKILL.md"
            if isinstance(body, bytes):
                skill.write_bytes(body)
            else:
                skill.write_text(body, encoding="utf-8")
            return LINTER.lint_skill(skill)

    def test_S23_the_lint_refuses_every_defect_it_names(self):
        """Every refusal the lint can produce is exercised, and names the file, the line and the reason."""
        said = []
        for label, body, expected in DEFECTS:
            with self.subTest(defect=label):
                problems = self.lint(body)
                messages = [problem.message for problem in problems]
                said.extend(messages)
                self.assertTrue(messages, "the lint accepted %s" % label)
                self.assertTrue(any(expected in message for message in messages),
                                "the lint refused %s with %r, not %r" % (label, messages, expected))
                for problem in problems:
                    self.assertTrue(str(problem).startswith(str(problem.path)),
                                    "the refusal does not name the file: %s" % problem)
                    self.assertIn(":%d: " % problem.line, str(problem),
                                  "the refusal does not name the line: %s" % problem)
        for label, build, _, _ in HYGIENE:
            said.extend(problem.message for problem in hygiene_problems(build))
        for template in sorted(problem_templates()):
            self.assertTrue(any(re.search(template_pattern(template), message) for message in said),
                            "the lint can refuse %r and nothing proves it" % template)


class Hygiene(unittest.TestCase):
    """The hygiene rules are lint problems: each names the file and the line it found the defect on."""

    def test_S32_a_skill_that_hardcodes_a_path_or_a_syntax_or_a_user_path_or_is_a_symlink_is_named(self):
        """S32: WHEN a skill hardcodes a skill path, carries an invocation syntax, holds an absolute user
        path or is a symlink, THEN the lint names the file and the line."""
        for label, build, expected, line in HYGIENE:
            with self.subTest(defect=label):
                problems = hygiene_problems(build)
                messages = [problem.message for problem in problems]
                self.assertTrue(any(expected in message for message in messages),
                                "the lint refused %s with %r, not %r" % (label, messages, expected))
                for problem in problems:
                    self.assertTrue(str(problem).startswith(str(problem.path)),
                                    "the refusal does not name the file: %s" % problem)
                    self.assertIn(":%d: " % problem.line, str(problem),
                                  "the refusal does not name the line: %s" % problem)
                self.assertIn(line, [problem.line for problem in problems if expected in problem.message],
                              "the lint names the wrong line for %s" % label)


class ExitCodes(unittest.TestCase):
    """The exit code the lint answers with."""

    def run_lint(self, *directories):
        """The exit code and the output of the lint over the given directories."""
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = LINTER.main(["lint_skills.py", *directories])
        return code, out.getvalue(), err.getvalue()

    def test_S24_the_lint_exits_one_for_problems_two_for_a_bad_path_and_zero_for_a_clean_folder(self):
        """The gate reads the exit code, so every outcome has its own."""
        with tempfile.TemporaryDirectory() as tmp:
            clean = Path(tmp) / "clean"
            (clean / "skill-a").mkdir(parents=True)
            (clean / "skill-a" / "SKILL.md").write_text(
                '---\nname: skill-a\ndescription: "A description."\n---\n\nbody\n', encoding="utf-8")
            code, out, err = self.run_lint(str(clean))
            self.assertEqual(code, 0)
            self.assertEqual(out, "")

            broken = Path(tmp) / "broken"
            (broken / "skill-b").mkdir(parents=True)
            (broken / "skill-b" / "SKILL.md").write_text(
                "---\nname: skill-b\ndescription: A description: with a colon.\n---\n\nbody\n",
                encoding="utf-8")
            code, out, err = self.run_lint(str(broken))
            self.assertEqual(code, 1)
            self.assertIn("colon", out)

            code, out, err = self.run_lint(str(Path(tmp) / "missing"))
            self.assertEqual(code, 2)
            self.assertIn("not a directory", err)


class RepoSkills(unittest.TestCase):
    """The skills of this repository, linted as one folder."""

    def frontmatter(self, skill):
        """The fields of the frontmatter of one skill."""
        text = skill.read_text(encoding="utf-8")
        block = text[4:text.find("\n---\n", 3)]
        fields = {}
        for line in block.splitlines():
            key, separator, value = line.partition(":")
            if separator and key.strip():
                fields[key.strip()] = value.strip()
        return fields

    def test_S34_every_skill_of_this_repo_names_its_folder_and_describes_itself_in_text(self):
        """One test over every skill: the name is the folder and the description is text."""
        skills = sorted(SKILLS.glob("*/SKILL.md"))
        self.assertTrue(skills, "the repository holds no skill")
        for skill in skills:
            with self.subTest(skill=skill.parent.name):
                problems = LINTER.lint_skill(skill)
                self.assertEqual([str(problem) for problem in problems], [])
                fields = self.frontmatter(skill)
                self.assertEqual(fields.get("name", "").strip("\"'"), skill.parent.name)
                description = fields.get("description", "")
                self.assertTrue(description, "the skill has no description")
                self.assertNotIn("\n", description, "the description is not one line")
                self.assertFalse(description.startswith(("[", "{")),
                                 "the description is a list or a mapping: %r" % description)
                self.assertNotIn(description.lower(),
                                 ("yes", "no", "true", "false", "on", "off", "null", "~"),
                                 "YAML reads the description as something other than text")


if __name__ == "__main__":
    unittest.main()
