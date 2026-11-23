import struct
import unittest

from srml_analyzer.extra_tables import (
    decode_events, decode_generic_containers, decode_generic_parameters, decode_properties,
)
from srml_analyzer.model import build_model
from srml_analyzer.v39_header import V39_SECTIONS, parse_v39_header
from test_core_tables import sample


def extended_sample():
    data = bytearray(sample())
    base_header = parse_v39_header(bytes(data))
    type_offset = base_header["sections"]["type_definitions"]["offset"]
    struct.pack_into("<8H", data, type_offset + 48, 1, 1, 1, 1, 0, 0, 0, 0)
    cursor = len(data)
    payloads = {
        "properties": struct.pack("<IiiII", 19, 0, -1, 0, 0x17000001),
        "events": struct.pack("<IBiiiI", 23, 2, 0, -1, -1, 0x14000001),
        "generic_containers": struct.pack("<4i", 0, 1, 0, 0),
        "generic_parameters": struct.pack("<BIhhHH", 0, 23, 0, 0, 0, 0),
    }
    pos = 8
    for name, _ in V39_SECTIONS:
        if name in payloads:
            payload = payloads[name]
            struct.pack_into("<III", data, pos, cursor, len(payload), 1)
            data.extend(payload)
            cursor += len(payload)
        pos += 12
    return bytes(data)


class ExtraTableTests(unittest.TestCase):
    def setUp(self):
        self.data = extended_sample()
        self.header = parse_v39_header(self.data)

    def test_property_and_event(self):
        prop = decode_properties(self.data, self.header)[0]
        event = decode_events(self.data, self.header)[0]
        self.assertEqual(prop["name"], "Run")
        self.assertEqual(prop["getter_method"], 0)
        self.assertEqual(event["name"], "arg")
        self.assertEqual(event["type_index"], 2)

    def test_generic_tables(self):
        container = decode_generic_containers(self.data, self.header)[0]
        parameter = decode_generic_parameters(self.data, self.header)[0]
        self.assertEqual(container["type_argument_count"], 1)
        self.assertFalse(container["is_method"])
        self.assertEqual(parameter["name"], "arg")
        self.assertEqual(parameter["owner_index"], 0)

    def test_integrated_model_contains_members_and_generics(self):
        result = build_model(self.data)
        self.assertEqual(result["types"][0]["properties"][0]["name"], "Run")
        self.assertEqual(result["types"][0]["events"][0]["name"], "arg")
        self.assertEqual(result["counts"]["generic_parameters"], 1)
        self.assertEqual(result["validation"]["errors"], [])


if __name__ == "__main__":
    unittest.main()
