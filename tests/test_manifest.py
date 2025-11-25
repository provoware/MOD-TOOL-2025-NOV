import json
import pathlib
import tempfile
import unittest

from mod_tool.manifest import (
    LayoutSection,
    ManifestWriter,
    default_layout_manifest,
    default_structure_manifest,
)


class ManifestTests(unittest.TestCase):
    def test_manifest_writer_creates_file(self):
        manifest = default_structure_manifest(["Hell", "Dunkel"])
        with tempfile.TemporaryDirectory() as tmp_dir:
            target = pathlib.Path(tmp_dir) / "manifest.json"
            writer = ManifestWriter(target)
            path = writer.write(manifest)
            self.assertTrue(path.exists())
            data = json.loads(path.read_text(encoding="utf-8"))
            self.assertIn("layout_manifest", data)
            self.assertEqual(data["layout_manifest"]["themes"], ["Hell", "Dunkel"])

    def test_layout_section_validation(self):
        section = LayoutSection(
            identifier="header",
            title="Steuerung",
            purpose="Start",
            accessibility_label="oben"
        )
        section.validate()  # should not raise
        manifest = default_layout_manifest(["Kontrast"])
        self.assertGreaterEqual(len(manifest.sections), 3)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
