import unittest
import xml.etree.ElementTree as ET

from scripts.generate_snap import render_svg


class SnapSvgTests(unittest.TestCase):
    def test_calendar_positions_and_accessibility(self):
        weeks = [
            {"contributionDays": [
                {"date": "2026-11-22", "weekday": 0, "contributionCount": 0, "contributionLevel": "NONE"},
                {"date": "2026-11-24", "weekday": 2, "contributionCount": 3, "contributionLevel": "SECOND_QUARTILE"},
            ]},
            {"contributionDays": [
                {"date": "2026-11-30", "weekday": 1, "contributionCount": 8, "contributionLevel": "FOURTH_QUARTILE"},
            ]},
        ]
        svg = render_svg(weeks, "dark", "AAAA", "BBBB")
        root = ET.fromstring(svg)
        ns = "{http://www.w3.org/2000/svg}"
        cells = [element for element in root.iter(f"{ns}rect") if element.find(f"{ns}title") is not None]
        self.assertEqual([(cell.get("x"), cell.get("y")) for cell in cells],
                         [("30", "37"), ("30", "71"), ("47", "54")])
        self.assertEqual(len(cells), 3)
        self.assertEqual(sum(element.get("class", "").startswith("crumb") for element in root.iter()), 7)
        children = list(root)
        self.assertLess(next(i for i, element in enumerate(children) if element.get("shape-rendering")),
                        next(i for i, element in enumerate(children) if element.get("class") == "gauntlet"))
        self.assertLess(next(i for i, element in enumerate(children) if element.get("class") == "gauntlet"),
                        next(i for i, element in enumerate(children) if element.get("class") == "red-gauntlet"))
        gold = root.find(f".//{ns}g[@class='gauntlet']/{ns}svg")
        red = root.find(f".//{ns}g[@class='red-gauntlet']/{ns}svg")
        self.assertEqual([gold.get(key) for key in ("x", "y", "width", "height")],
                         [red.get(key) for key in ("x", "y", "width", "height")])
        self.assertEqual(gold.get("viewBox"), "456 52 48 53")
        self.assertEqual(gold.get("preserveAspectRatio"), "none")
        self.assertEqual({element.get("class") for element in root.iter(f"{ns}use")},
                         {None, "index-finger", "thumb", "red-index", "red-thumb"})
        self.assertIn("3 contributions", svg)
        self.assertIn("2 filled contribution squares", svg)
        self.assertIn("71.0%", svg)
        self.assertIn("70.5%", svg)
        self.assertIn("prefers-reduced-motion", svg)
        self.assertNotEqual(render_svg(weeks, "light", "AAAA", "BBBB"), svg)


if __name__ == "__main__":
    unittest.main()
