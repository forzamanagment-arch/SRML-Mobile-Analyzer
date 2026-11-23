import struct
import tempfile
import unittest
from pathlib import Path
from srml_analyzer.elf import inspect_elf
from srml_analyzer.errors import FormatError


def minimal_elf64(machine=183):
    data = bytearray(64)
    data[:4] = b"\x7fELF"
    data[4:7] = bytes((2, 1, 1))
    struct.pack_into("<HHIQQQIHHHHHH", data, 16,
                     3, machine, 1, 0, 0, 0, 0, 64, 56, 0, 64, 0, 0)
    return bytes(data)


class ElfTests(unittest.TestCase):
    def test_recognizes_aarch64_elf64(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "libil2cpp.so"
            path.write_bytes(minimal_elf64())
            result = inspect_elf(path)
            self.assertTrue(result["is_aarch64"])
            self.assertEqual(result["format"], "ELF64")

    def test_rejects_non_elf(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.so"
            path.write_bytes(bytes(64))
            with self.assertRaises(FormatError):
                inspect_elf(path)


if __name__ == "__main__":
    unittest.main()
