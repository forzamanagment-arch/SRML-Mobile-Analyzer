import struct
import unittest

from srml_analyzer.errors import FormatError
from srml_analyzer.v39_header import MAGIC, V39_SECTIONS, parse_v39_header, v39_header_size


def make_header():
    data = bytearray(v39_header_size())
    data[:4] = MAGIC
    struct.pack_into("<i", data, 4, 39)
    cursor = 8
    for name, has_count in V39_SECTIONS:
        if name == "strings":
            struct.pack_into("<II", data, cursor, v39_header_size(), 4)
            cursor += 8
            struct.pack_into("<I", data, cursor, 4)
            cursor += 4
        elif name == "fields":
            struct.pack_into("<II", data, cursor, v39_header_size() + 4, 9)
            cursor += 8
            struct.pack_into("<I", data, cursor, 1)
            cursor += 4
        else:
            struct.pack_into("<II", data, cursor, 0, 0)
            cursor += 8
            if has_count:
                struct.pack_into("<I", data, cursor, 0)
                cursor += 4
    data.extend(b"test" + b"123456789")
    return bytes(data)


class V39HeaderTests(unittest.TestCase):
    def test_header_size_and_sections(self):
        data = make_header()
        result = parse_v39_header(data)
        self.assertEqual(result["header_size"], v39_header_size())
        self.assertEqual(result["sections"]["strings"]["count"], 4)
        self.assertEqual(result["sections"]["strings"]["end"], v39_header_size() + 4)

    def test_computes_index_widths_from_header_counts(self):
        result = parse_v39_header(make_header())
        self.assertEqual(result["index_widths"]["type_definition_index"], 1)
        self.assertEqual(result["index_widths"]["generic_container_index"], 1)
        self.assertEqual(result["index_widths"]["parameter_definition_index"], 1)
        self.assertEqual(result["index_widths"]["type_index"], 1)

    def test_rejects_wrong_version(self):
        data = bytearray(make_header())
        struct.pack_into("<i", data, 4, 38)
        with self.assertRaises(FormatError):
            parse_v39_header(bytes(data))

    def test_rejects_truncated_header(self):
        with self.assertRaises(FormatError):
            parse_v39_header(make_header()[:32])

    def test_rejects_section_outside_file(self):
        data = bytearray(make_header())
        # First section begins at byte 8.
        struct.pack_into("<II", data, 8, len(data) + 10, 20)
        with self.assertRaises(FormatError):
            parse_v39_header(bytes(data))


if __name__ == "__main__":
    unittest.main()
