import tempfile
import unittest
from pathlib import Path

from srml_analyzer.metadata import inspect_metadata, MAGIC
from srml_analyzer.errors import FormatError
from srml_analyzer.v39_header import v39_header_size


class MetadataTests(unittest.TestCase):
    def test_recognizes_and_validates_version_39_header(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "global-metadata.dat"
            path.write_bytes(MAGIC + (39).to_bytes(4, "little") + bytes(v39_header_size() - 8))
            result = inspect_metadata(path)
            self.assertEqual(result["version"], 39)
            self.assertEqual(result["status"], "v39-header-validated")
            self.assertFalse(result["table_records_decoded"])
            self.assertEqual(result["header_bytes"], v39_header_size())

    def test_rejects_wrong_magic(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.dat"
            path.write_bytes(b"NOPE" + bytes(64))
            with self.assertRaises(FormatError):
                inspect_metadata(path)


if __name__ == "__main__":
    unittest.main()
