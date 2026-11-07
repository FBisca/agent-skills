"""The skill frontmatter contract: every SKILL.md must be readable by every harness.

A harness (Claude Code, Codex, Pi) reads a skill's frontmatter as YAML. Frontmatter that YAML
cannot parse makes the skill disappear; frontmatter that YAML reads as something other than the
text the author wrote makes the harness route on a description the author never wrote. Neither
is loud, so the gate checks it here.

`scripts/lint_skills.py` holds the rules and names the file, the line and the reason. This test
runs it over the skills of this repo, and over a set of frontmatter that must be refused.
"""

from pathlib import Path
import importlib.util
import sys
import unittest

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


def write_skill(body):
    """A SKILL.md with the given frontmatter, in a temp folder."""
    import tempfile
    directory = Path(tempfile.mkdtemp()) / "probe"
    directory.mkdir()
    skill = directory / "SKILL.md"
    skill.write_text(body, encoding="utf-8")
    return skill


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

    def assert_refused(self, frontmatter, because):
        problems = LINTER.lint_skill(write_skill(frontmatter))
        self.assertTrue(problems, "the lint accepted frontmatter that %s" % because)
        self.assertIn(because.split()[0], " ".join(problem.message for problem in problems))

    def assert_accepted(self, frontmatter):
        problems = LINTER.lint_skill(write_skill(frontmatter))
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


if __name__ == "__main__":
    unittest.main()
