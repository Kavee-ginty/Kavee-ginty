import unittest

from scripts.update_contribution_count import parse_count, replace_heading


class ContributionHeadingTests(unittest.TestCase):
    def test_parses_gitHub_heading_and_preserves_readme(self):
        page = ('<h2 id="js-contribution-activity-description">'
                '1,099 <span>contributions</span> in the last year</h2>')
        self.assertEqual(parse_count(page), 1099)
        readme = "Intro\r\n## 1,092 contributions in the last year\r\nAfter\r\n"
        self.assertEqual(replace_heading(readme, 1099),
                         "Intro\r\n## 1,099 contributions in the last year\r\nAfter\r\n")

    def test_rejects_missing_or_changed_heading(self):
        with self.assertRaises(ValueError):
            parse_count("<h2>1,099 contributions in the last year</h2>")
        with self.assertRaises(ValueError):
            replace_heading("## Contribution trail\n", 1099)


if __name__ == "__main__":
    unittest.main()
