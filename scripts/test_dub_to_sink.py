import importlib.util
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location("converter", Path(__file__).with_name("dub-to-sink.py"))
converter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(converter)


def row(slug="FollowUp", domain="links.example.org", **changes):
    return {"Short link": f"https://{domain}/{slug}",
            "Destination URL": "https://example.org/form?id=test%2B1&source=email",
            "Archived": "No", "Tags": "", "Created at": "2026-08-27T15:41:25.773Z",
            "Updated at": "2026-08-28T13:59:49.399Z", **changes}


class ImportTests(unittest.TestCase):
    def test_preserves_case_query_and_timestamps_and_excludes_other_domains(self):
        source = row()
        result, skipped = converter.convert([source, row(domain="dub.sh"), row(slug="")], "links.example.org")
        self.assertEqual(result["count"], 1)
        link = result["links"][0]
        self.assertEqual(link["slug"], "FollowUp")
        self.assertEqual(link["url"], source["Destination URL"])
        self.assertEqual(link["createdAt"], 1787845285)
        self.assertEqual(skipped, {"other_domain": 1, "root": 1})
        self.assertEqual(link["id"], converter.convert([source], "links.example.org")[0]["links"][0]["id"])

    def test_refuses_ambiguous_or_unsupported_records(self):
        for rows in ([row(), row()], [row(slug="dashboard")], [row(slug="a/b")],
                     [row(Archived="Yes")], [row(Tags="important")],
                     [row(**{"Destination URL": "javascript:alert(1)"})]):
            with self.subTest(rows=rows), self.assertRaises(ValueError):
                converter.convert(rows, "links.example.org")


if __name__ == "__main__":
    unittest.main()
