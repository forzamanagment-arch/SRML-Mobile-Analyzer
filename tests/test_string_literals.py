import struct
import unittest

from srml_analyzer.errors import FormatError
from srml_analyzer.string_literals import decode_string_literals


class StringLiteralTests(unittest.TestCase):
    def test_decodes_lengths_from_adjacent_offsets(self):
        table_offset = 0
        data_offset = 8
        blob = b"HelloWorld"
        data = bytearray(data_offset + len(blob))
        struct.pack_into("<ii", data, table_offset, 0, 5)
        data[data_offset:] = blob

        entries = decode_string_literals(
            bytes(data), table_offset, 8, 2, data_offset, len(blob)
        )
        self.assertEqual(
            entries,
            [
                {"index": 0, "data_offset": 0, "value": "Hello"},
                {"index": 1, "data_offset": 5, "value": "World"},
            ],
        )

    def test_supports_empty_literals_and_utf8(self):
        table_offset = 0
        data_offset = 12
        blob = "☀x".encode("utf-8")
        data = bytearray(data_offset + len(blob))
        struct.pack_into("<iii", data, table_offset, 0, 0, 3)
        data[data_offset:] = blob

        entries = decode_string_literals(
            bytes(data), table_offset, 12, 3, data_offset, len(blob)
        )
        self.assertEqual([item["value"] for item in entries], ["", "☀", "x"])

    def test_rejects_non_monotonic_offsets(self):
        data = bytearray(12)
        struct.pack_into("<ii", data, 0, 4, 2)
        with self.assertRaises(FormatError):
            decode_string_literals(bytes(data), 0, 8, 2, 8, 4)

    def test_rejects_offset_outside_literal_data(self):
        data = bytearray(12)
        struct.pack_into("<i", data, 0, 5)
        with self.assertRaises(FormatError):
            decode_string_literals(bytes(data), 0, 4, 1, 4, 4)

    def test_rejects_wrong_table_size(self):
        with self.assertRaises(FormatError):
            decode_string_literals(bytes(8), 0, 8, 1, 0, 8)

    def test_rejects_invalid_utf8(self):
        data = bytearray(5)
        struct.pack_into("<i", data, 0, 0)
        data[4] = 0xFF
        with self.assertRaises(FormatError):
            decode_string_literals(bytes(data), 0, 4, 1, 4, 1)


if __name__ == "__main__":
    unittest.main()
