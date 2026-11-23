import tempfile
import unittest
from pathlib import Path
from srml_analyzer.metadata import inspect_metadata, MAGIC
from srml_analyzer.errors import FormatError


class MetadataTests(unittest.TestCase):
    def test_recognizes_version_39_header(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "global-metadata.dat"
            path.write_bytes(MAGIC + (39).to_bytes(4, "little") + bytes(64))
            result = inspect_metadata(path)
            self.assertEqual(result["version"], 39)
            self.assertFalse(result["table_schema_decoded"])

    def test_rejects_wrong_magic(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.dat"
            path.write_bytes(b"NOPE" + bytes(64))
            with self.assertRaises(FormatError):
                inspect_metadata(path)


if __name__ == "__main__":
    unittest.main()
