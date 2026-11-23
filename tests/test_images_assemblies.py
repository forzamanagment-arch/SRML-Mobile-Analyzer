import struct
import unittest

from srml_analyzer.errors import FormatError
from srml_analyzer.images_assemblies import decode_assemblies, decode_images
from srml_analyzer.v39_header import MAGIC, V39_SECTIONS, v39_header_size


def make_sample():
    header_size = v39_header_size()
    strings = b"Assembly-CSharp.dll\\x00Image\\x00"
    image_width = 1
    image = struct.pack(
        "<Ii", 5, 0
    ) + bytes([0]) + struct.pack("<I", 3) + bytes([0]) + struct.pack(
        "<IiIiI", 2, -1, 0x20000001, 0, 0
    )
    assembly = struct.pack(
        "<iIIII", 0, 0x20000001, 0x06000001, 0, 0
    ) + struct.pack(
        "<10I", 0, 19, 0, 0, 0, 0, 1, 2, 3, 4
    ) + bytes.fromhex("0011223344556677")

    offsets = {}
    cursor = header_size
    offsets["strings"] = (cursor, len(strings), 2)
    cursor += len(strings)
    offsets["images"] = (cursor, len(image), 1)
    cursor += len(image)
    offsets["assemblies"] = (cursor, len(assembly), 1)
    cursor += len(assembly)

    data = bytearray(cursor)
    data[:4] = MAGIC
    struct.pack_into("<i", data, 4, 39)
    pos = 8
    for name, has_count in V39_SECTIONS:
        offset, size, count = offsets.get(name, (0, 0, 0))
        struct.pack_into("<II", data, pos, offset, size)
        pos += 8
        if has_count:
            struct.pack_into("<I", data, pos, count)
            pos += 4
    for name, payload in (("strings", strings), ("images", image), ("assemblies", assembly)):
        offset = offsets[name][0]
        data[offset:offset + len(payload)] = payload
    return bytes(data)


class ImageAssemblyTests(unittest.TestCase):
    def test_decodes_image_name_and_ranges(self):
        data = make_sample()
        from srml_analyzer.v39_header import parse_v39_header
        result = decode_images(data, parse_v39_header(data))
        self.assertEqual(result[0]["name"], "Image")
        self.assertEqual(result[0]["assembly_index"], 0)
        self.assertEqual(result[0]["type_count"], 3)
        self.assertEqual(result[0]["entry_point_index"], -1)

    def test_decodes_assembly_identity(self):
        data = make_sample()
        from srml_analyzer.v39_header import parse_v39_header
        result = decode_assemblies(data, parse_v39_header(data))
        self.assertEqual(result[0]["name"], "Assembly-CSharp.dll")
        self.assertEqual(result[0]["version"], {"major": 1, "minor": 2, "build": 3, "revision": 4})
        self.assertEqual(result[0]["public_key_token"], "0011223344556677")

    def test_rejects_inconsistent_image_record_size(self):
        data = bytearray(make_sample())
        from srml_analyzer.v39_header import parse_v39_header
        header = parse_v39_header(bytes(data))
        section = header["sections"]["images"]
        # Remove one byte from the declared table size without changing the file.
        pos = 8
        for name, has_count in V39_SECTIONS:
            if name == "images":
                struct.pack_into("<I", data, pos + 4, section["size"] - 1)
                break
            pos += 12
        with self.assertRaises(FormatError):
            decode_images(bytes(data), parse_v39_header(bytes(data)))


if __name__ == "__main__":
    unittest.main()
