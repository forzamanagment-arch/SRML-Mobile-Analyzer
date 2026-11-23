import test from "node:test";
import assert from "node:assert/strict";
import { parseHeader, decode } from "./analyzer.js";

function u32(value){const b=new Uint8Array(4);new DataView(b.buffer).setUint32(0,value,true);return b;}
function u16(value){const b=new Uint8Array(2);new DataView(b.buffer).setUint16(0,value,true);return b;}
function join(...parts){const out=new Uint8Array(parts.reduce((n,p)=>n+p.length,0));let at=0;for(const p of parts){out.set(p,at);at+=p.length;}return out;}

function emptyV39() {
  const bytes = new Uint8Array(380);
  bytes.set([0xaf, 0x1b, 0xb1, 0xfa], 0);
  new DataView(bytes.buffer).setInt32(4, 39, true);
  return bytes.buffer;
}

function sampleV39() {
  const names = new TextEncoder().encode("Thing\0System\0value\0Run\0arg\0");
  const payloads = {
    strings: [names, 5],
    fields: [join(u32(13), Uint8Array.of(1), u32(0x04000001)), 1],
    parameters: [join(u32(23), u32(0x08000001), Uint8Array.of(1)), 1],
    methods: [join(u32(19), Uint8Array.of(0,1), u32(0x08000000),
      Uint8Array.of(0,255), u32(0x06000001), u16(6), u16(0), u16(1), u16(1)), 1],
    type_definitions: [join(u32(0), u32(6), Uint8Array.of(0,255,255,255), u32(1),
      new Uint8Array(32), u16(1), u16(0), u16(1), u16(0),
      u16(0), u16(0), u16(0), u16(0), u32(1), u32(0x02000001)), 1]
  };
  const sectionNames = [
    "string_literals","string_literal_data","strings","events","properties","methods",
    "parameter_default_values","field_default_values","field_and_parameter_default_value_data",
    "field_marshaled_sizes","parameters","fields","generic_parameters","generic_parameter_constraints",
    "generic_containers","nested_types","interfaces","vtable_methods","interface_offsets",
    "type_definitions","images","assemblies","field_refs","referenced_assemblies","attribute_data",
    "attribute_data_ranges","unresolved_virtual_call_parameter_types",
    "unresolved_virtual_call_parameter_ranges","windows_runtime_type_names",
    "windows_runtime_strings","exported_type_definitions"
  ];
  const total = 380 + Object.values(payloads).reduce((sum, item) => sum + item[0].length, 0);
  const bytes = new Uint8Array(total);
  bytes.set([0xaf,0x1b,0xb1,0xfa],0);
  const view = new DataView(bytes.buffer);
  view.setInt32(4,39,true);
  let cursor = 380;
  for (let i=0;i<sectionNames.length;i++) {
    const item = payloads[sectionNames[i]];
    if (!item) continue;
    const [blob,count] = item;
    view.setUint32(8+i*12,cursor,true);
    view.setUint32(12+i*12,blob.length,true);
    view.setUint32(16+i*12,count,true);
    bytes.set(blob,cursor);
    cursor += blob.length;
  }
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

test("browser parser links a synthetic class, field, method and parameter", () => {
  const result = decode(sampleV39());
  assert.equal(result.types[0].full_name, "System.Thing");
  assert.equal(result.types[0].fields[0].name, "value");
  assert.equal(result.types[0].methods[0].name, "Run");
  assert.equal(result.types[0].methods[0].parameters[0].name, "arg");
  assert.equal(result.validation.errors.length, 0);
});
