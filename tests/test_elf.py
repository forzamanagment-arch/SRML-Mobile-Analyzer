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


def elf_with_dynsym():
    data = bytearray(64)
    data[:4] = b"\x7fELF"
    data[4:7] = bytes((2, 1, 1))
    shstr = b"\x00.shstrtab\x00.dynstr\x00.dynsym\x00"
    dynstr = b"\x00il2cpp_init\x00"
    shstr_off = len(data)
    data.extend(shstr)
    dynstr_off = len(data)
    data.extend(dynstr)
    while len(data) % 8:
        data.append(0)
    dynsym_off = len(data)
    data.extend(bytes(24))
    data.extend(struct.pack("<IBBHQQ", 1, 0x12, 0, 1, 0x1234, 16))
    while len(data) % 8:
        data.append(0)
    shoff = len(data)
    sections = [
        (0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
        (1, 3, 0, 0, shstr_off, len(shstr), 0, 0, 1, 0),
        (11, 3, 0, 0, dynstr_off, len(dynstr), 0, 0, 1, 0),
        (20, 11, 0, 0, dynsym_off, 48, 2, 1, 8, 24),
    ]
    for section in sections:
        data.extend(struct.pack("<IIQQQQIIQQ", *section))
    struct.pack_into("<HHIQQQIHHHHHH", data, 16,
                     3, 183, 1, 0, 0, shoff, 0, 64, 56, 0, 64, 4, 1)
    return bytes(data)


class ElfTests(unittest.TestCase):
    def test_recognizes_aarch64_elf64(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "libil2cpp.so"
            path.write_bytes(minimal_elf64())
            result = inspect_elf(path)
            self.assertTrue(result["is_aarch64"])
            self.assertEqual(result["format"], "ELF64")

    def test_discovers_dynamic_il2cpp_symbols(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "libil2cpp.so"
            path.write_bytes(elf_with_dynsym())
            result = inspect_elf(path)
            self.assertEqual(result["symbol_table_entries"], 2)
            self.assertEqual(result["interesting_symbols"][0]["name"], "il2cpp_init")
            self.assertEqual(result["interesting_symbols"][0]["value"], 0x1234)

    def test_rejects_non_elf(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.so"
            path.write_bytes(bytes(64))
            with self.assertRaises(FormatError):
                inspect_elf(path)


if __name__ == "__main__":
    unittest.main()
