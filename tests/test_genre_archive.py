import tempfile
import unittest
from pathlib import Path

from mod_tool.genre_archive import GenreArchive


class GenreArchiveTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.archive = GenreArchive(Path(self.tmp.name))

    def tearDown(self) -> None:  # pragma: no cover - cleanup helper
        self.tmp.cleanup()

    def test_archive_created_and_summary(self):
        path = self.archive.ensure_archive()
        self.assertTrue(path.exists())
        summary = self.archive.summary_lines()
        self.assertTrue(summary)

    def test_add_profile_and_duplicate_check(self):
        self.archive.add_profile("Rock", "Indie", "Gitarrenbasiert")
        profiles = self.archive.list_profiles()
        self.assertEqual(len(profiles), 1)
        with self.assertRaises(ValueError):
            self.archive.add_profile("Rock", "Indie", "Nochmals")

    def test_category_filtering(self):
        self.archive.add_profile("Jazz", "Modern", "Kreativ")
        self.archive.add_profile("Rock", "Classic", "Zeitlos")
        jazz_only = self.archive.list_profiles(category="Jazz")
        self.assertEqual(len(jazz_only), 1)
        self.assertEqual(jazz_only[0].category, "Jazz")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
