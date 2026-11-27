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
        svg = render_svg(weeks, "dark", "AAAA")
        root = ET.fromstring(svg)
        ns = "{http://www.w3.org/2000/svg}"
        cells = [element for element in root.iter(f"{ns}rect") if element.find(f"{ns}title") is not None]
        self.assertEqual([(cell.get("x"), cell.get("y")) for cell in cells],
                         [("210", "37"), ("210", "71"), ("227", "54")])
        self.assertEqual(len(cells), 3)
        self.assertEqual(sum(element.get("class", "").startswith("crumb") for element in root.iter()), 7)
        self.assertIn("3 contributions", svg)
        self.assertIn("then 2 filled squares", svg)
        self.assertIn("prefers-reduced-motion", svg)
        self.assertNotEqual(render_svg(weeks, "light", "AAAA"), svg)


if __name__ == "__main__":
    unittest.main()
