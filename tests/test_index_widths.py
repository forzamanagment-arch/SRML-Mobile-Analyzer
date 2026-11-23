import unittest

from srml_analyzer.errors import FormatError
from srml_analyzer.index_widths import (
    count_index_width,
    decode_variable_index,
    derive_v39_index_widths,
    infer_type_index_width,
)


class IndexWidthTests(unittest.TestCase):
    def test_count_width_boundaries(self):
        self.assertEqual(count_index_width(0), 1)
        self.assertEqual(count_index_width(255), 1)
        self.assertEqual(count_index_width(256), 2)
        self.assertEqual(count_index_width(65535), 2)
        self.assertEqual(count_index_width(65536), 4)

    def test_type_width_from_interface_offset_records(self):
        self.assertEqual(infer_type_index_width(5 * 8, 5, 0, 0), 4)
        self.assertEqual(infer_type_index_width(5 * 5, 5, 0, 0), 1)
        self.assertEqual(infer_type_index_width(5 * 6, 5, 0, 0), 2)

    def test_type_width_from_field_records_fallback(self):
        self.assertEqual(infer_type_index_width(0, 0, 10 * 9, 10), 1)

    def test_derive_v39_widths(self):
        widths = derive_v39_index_widths(
            type_definitions_count=300,
            generic_containers_count=20,
            parameters_count=70000,
            interface_offsets_size=0,
            interface_offsets_count=0,
            fields_size=12 * 10,
            fields_count=10,
        )
        self.assertEqual(widths.type_definition_index, 2)
        self.assertEqual(widths.generic_container_index, 1)
        self.assertEqual(widths.parameter_definition_index, 4)
        self.assertEqual(widths.type_index, 4)

    def test_decode_null_sentinel(self):
        self.assertEqual(decode_variable_index(b"\xff", 0, 1), -1)
        self.assertEqual(decode_variable_index(b"\xff\xff", 0, 2), -1)
        self.assertEqual(decode_variable_index(b"\x34\x12", 0, 2), 0x1234)

    def test_rejects_invalid_width_and_bounds(self):
        with self.assertRaises(FormatError):
            decode_variable_index(b"\x00", 0, 3)
        with self.assertRaises(FormatError):
            decode_variable_index(b"\x00", 1, 1)


if __name__ == "__main__":
    unittest.main()
