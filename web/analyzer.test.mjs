import test from "node:test";
import assert from "node:assert/strict";
import { parseHeader, decode } from "./analyzer.js";

function emptyV39() {
  const bytes = new Uint8Array(380);
  bytes.set([0xaf, 0x1b, 0xb1, 0xfa], 0);
  new DataView(bytes.buffer).setInt32(4, 39, true);
  return bytes.buffer;
}

test("browser parser accepts an empty v39 header", () => {
  const header = parseHeader(emptyV39());
  assert.equal(header.version, 39);
  assert.equal(header.header_size, 380);
  assert.equal(header.sections.type_definitions.count, 0);
});

test("browser parser emits an empty structural report", () => {
  const result = decode(emptyV39());
  assert.equal(result.format, "il2cpp-v39-model");
  assert.equal(result.counts.types, 0);
  assert.equal(result.validation.errors.length, 0);
});

test("browser parser rejects a different metadata version", () => {
  const bytes = new Uint8Array(emptyV39());
  new DataView(bytes.buffer).setInt32(4, 38, true);
  assert.throws(() => parseHeader(bytes.buffer), /metadata v39/);
});
