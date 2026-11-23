import struct
import unittest

from srml_analyzer.core_tables import decode_fields, decode_methods, decode_parameters, decode_types
from srml_analyzer.v39_header import MAGIC, V39_SECTIONS, parse_v39_header, v39_header_size


def sample():
    strings = b"Thing\\x00System\\x00value\\x00Run\\x00arg\\x00"
    offsets = {"Thing": 0, "System": 6, "value": 13, "Run": 19, "arg": 23}
    fields = struct.pack("<IBI", offsets["value"], 1, 0x04000001)
    params = struct.pack("<IIB", offsets["arg"], 0x08000001, 1)
    methods = (
        struct.pack("<I", offsets["Run"]) + bytes([0, 1]) +
        struct.pack("<I", 0x08000000) + bytes([0, 0]) +
        struct.pack("<I4H", 0x06000001, 6, 0, 1, 1)
    )
    types = (
        struct.pack("<II", offsets["Thing"], offsets["System"]) +
        bytes([0, 255, 255, 255]) + struct.pack("<I", 1) +
        struct.pack("<8i", 0, 0, 0, 0, 0, 0, 0, 0) +
        struct.pack("<8H", 1, 0, 1, 0, 0, 0, 0, 0) +
        struct.pack("<II", 1, 0x02000001)
    )
    payloads = {
        "strings": strings, "fields": fields, "parameters": params,
        "methods": methods, "type_definitions": types,
    }
    counts = {"strings": 5, "fields": 1, "parameters": 1, "methods": 1, "type_definitions": 1}
    cursor = v39_header_size()
    sections = {}
    for name, payload in payloads.items():
        sections[name] = (cursor, len(payload), counts[name])
        cursor += len(payload)
    data = bytearray(cursor)
    data[:4] = MAGIC
    struct.pack_into("<i", data, 4, 39)
    pos = 8
    for name, _ in V39_SECTIONS:
        off, size, count = sections.get(name, (0, 0, 0))
        struct.pack_into("<III", data, pos, off, size, count)
        pos += 12
    for name, payload in payloads.items():
        off = sections[name][0]
        data[off:off + len(payload)] = payload
    return bytes(data)


class CoreTableTests(unittest.TestCase):
    def setUp(self):
        self.data = sample()
        self.header = parse_v39_header(self.data)

    def test_fields_and_parameters(self):
        self.assertEqual(decode_fields(self.data, self.header)[0]["name"], "value")
        self.assertEqual(decode_parameters(self.data, self.header)[0]["name"], "arg")

    def test_method(self):
        method = decode_methods(self.data, self.header)[0]
        self.assertEqual(method["name"], "Run")
        self.assertEqual(method["parameter_count"], 1)
        self.assertEqual(method["token"], 0x06000001)

    def test_type(self):
        item = decode_types(self.data, self.header)[0]
        self.assertEqual(item["name"], "Thing")
        self.assertEqual(item["namespace"], "System")
        self.assertTrue(item["is_value_type"])

    def test_rejects_wrong_table_size(self):
        damaged = bytearray(self.data)
        section = self.header["sections"]["fields"]
        pos = 8
        for name, _ in V39_SECTIONS:
            if name == "fields":
                struct.pack_into("<I", damaged, pos + 4, section["size"] - 1)
                break
            pos += 12
        with self.assertRaises(Exception):
            decode_fields(bytes(damaged), parse_v39_header(bytes(damaged)))


if __name__ == "__main__":
    unittest.main()
