import struct
import tempfile
import unittest
from pathlib import Path

from srml_analyzer.errors import FormatError
from srml_analyzer.strings import decode_string_pool, inspect_string_pool
from srml_analyzer.v39_header import MAGIC, V39_SECTIONS, v39_header_size


class StringPoolTests(unittest.TestCase):
    def test_decodes_utf8_and_preserves_byte_offsets(self):
        blob = b"\x00System\x00Slime\xe2\x98\x80\x00"
        entries = decode_string_pool(blob, 0, len(blob))
        self.assertEqual(
            entries,
            [
                {"offset": 0, "value": ""},
                {"offset": 1, "value": "System"},
                {"offset": 8, "value": "Slime☀"},
            ],
        )

    def test_rejects_unterminated_blob(self):
        with self.assertRaises(FormatError):
            decode_string_pool(b"System", 0, 6)

    def test_rejects_invalid_utf8(self):
        with self.assertRaises(FormatError):
            decode_string_pool(b"bad\xff\x00", 0, 5)

    def test_rejects_section_outside_file(self):
        with self.assertRaises(FormatError):
            decode_string_pool(b"abc", 2, 2)

    def test_empty_section(self):
        self.assertEqual(decode_string_pool(b"", 0, 0), [])

    def test_inspect_reports_count_without_assuming_it_is_entry_count(self):
        header_size = v39_header_size()
        blob = b"Assembly-CSharp.dll\x00Game\x00"
        data = bytearray(header_size)
        data[:4] = MAGIC
        struct.pack_into("<i", data, 4, 39)
        cursor = 8
        for name, has_count in V39_SECTIONS:
            if name == "strings":
                struct.pack_into("<II", data, cursor, header_size, len(blob))
                cursor += 8
                struct.pack_into("<I", data, cursor, 999)
                cursor += 4
            else:
                struct.pack_into("<II", data, cursor, 0, 0)
                cursor += 8
                if has_count:
                    struct.pack_into("<I", data, cursor, 0)
                    cursor += 4
        data.extend(blob)

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "global-metadata.dat"
            path.write_bytes(data)
            result = inspect_string_pool(path, limit=1)

        self.assertEqual(result["decoded_entries"], 2)
        self.assertEqual(result["header_count_field"], 999)
        self.assertFalse(result["count_field_matches_entries"])
        self.assertEqual(result["entries"][0]["value"], "Assembly-CSharp.dll")
        self.assertEqual(result["entries_omitted"], 1)


if __name__ == "__main__":
    unittest.main()
