const MAGIC = [0xaf, 0x1b, 0xb1, 0xfa];
const SECTION_NAMES = [
  "string_literals", "string_literal_data", "strings", "events", "properties",
  "methods", "parameter_default_values", "field_default_values",
  "field_and_parameter_default_value_data", "field_marshaled_sizes",
  "parameters", "fields", "generic_parameters", "generic_parameter_constraints",
  "generic_containers", "nested_types", "interfaces", "vtable_methods",
  "interface_offsets", "type_definitions", "images", "assemblies", "field_refs",
  "referenced_assemblies", "attribute_data", "attribute_data_ranges",
  "unresolved_virtual_call_parameter_types", "unresolved_virtual_call_parameter_ranges",
  "windows_runtime_type_names", "windows_runtime_strings", "exported_type_definitions"
];

function fail(message) { throw new Error(message); }
function viewOf(input) {
  if (input instanceof ArrayBuffer) return new DataView(input);
  if (ArrayBuffer.isView(input)) return new DataView(input.buffer, input.byteOffset, input.byteLength);
  fail("Ожидался бинарный файл.");
}
function parseHeader(input) {
  const view = viewOf(input);
  if (view.byteLength < 380) fail("Файл меньше заголовка IL2CPP v39.");
  for (let i = 0; i < 4; i++) if (view.getUint8(i) !== MAGIC[i]) fail("Неверная сигнатура global-metadata.dat.");
  const version = view.getInt32(4, true);
  if (version !== 39) fail(`Нужна metadata v39, получена v${version}.`);
  const sections = {};
  let cursor = 8;
  for (const name of SECTION_NAMES) {
    const offset = view.getUint32(cursor, true);
    const size = view.getUint32(cursor + 4, true);
    const count = view.getUint32(cursor + 8, true);
    cursor += 12;
    if (offset === 0 && size === 0 && count === 0) {
      sections[name] = { offset: 0, size: 0, count: 0, end: 0 };
      continue;
    }
    if (offset < 380 || offset > view.byteLength || size > view.byteLength - offset) {
      fail(`Раздел ${name} выходит за границы файла.`);
    }
    sections[name] = { offset, size, count, end: offset + size };
  }
  const fields = sections.fields;
  const offsets = sections.interface_offsets;
  let typeIndexWidth = 4;
  if (offsets.count) {
    if (offsets.size % offsets.count) fail("Некорректный размер interface_offsets.");
    typeIndexWidth = offsets.size / offsets.count - 4;
  } else if (fields.count) {
    if (fields.size % fields.count) fail("Некорректный размер fields.");
    typeIndexWidth = fields.size / fields.count - 8;
  }
  const widths = {
    type_index: typeIndexWidth,
    type_definition_index: indexWidth(sections.type_definitions.count),
    generic_container_index: indexWidth(sections.generic_containers.count),
    parameter_definition_index: indexWidth(sections.parameters.count)
  };
  for (const [name, width] of Object.entries(widths)) {
    if (![1, 2, 4].includes(width)) fail(`Некорректная ширина индекса ${name}: ${width}.`);
  }
  return { version, header_size: 380, sections, index_widths: widths, file_size: view.byteLength };
}
function indexWidth(count) {
  if (count < 0) fail("Отрицательное количество элементов.");
  return count <= 255 ? 1 : count <= 65535 ? 2 : 4;
}
function readIndex(view, offset, width) {
  if (offset < 0 || offset + width > view.byteLength) fail("Индекс выходит за границы таблицы.");
  const value = width === 1 ? view.getUint8(offset) :
    width === 2 ? view.getUint16(offset, true) : view.getUint32(offset, true);
  return value === (2 ** (width * 8) - 1) ? -1 : value;
}
function tableBytes(view, header, name, recordSize) {
  const s = header.sections[name];
  const expected = s.count * recordSize;
  if (s.size !== expected) fail(`Таблица ${name}: ожидалось ${expected} байт, получено ${s.size}.`);
  return { start: s.offset, count: s.count };
}
function stringAt(bytes, offset, label) {
  if (offset < 0 || offset >= bytes.length) fail(`${label}: строковый индекс ${offset} вне string pool.`);
  let end = offset;
  while (end < bytes.length && bytes[end] !== 0) end++;
  if (end === bytes.length) fail(`${label}: строка не завершена NUL.`);
  try { return new TextDecoder("utf-8", { fatal: true }).decode(bytes.subarray(offset, end)); }
  catch { fail(`${label}: некорректная UTF-8 строка.`); }
}
function sectionBytes(bytes, section) { return bytes.subarray(section.offset, section.end); }

function decode(input) {
  const view = viewOf(input);
  const bytes = new Uint8Array(view.buffer, view.byteOffset, view.byteLength);
  const header = parseHeader(view);
  const strings = sectionBytes(bytes, header.sections.strings);
  const w = header.index_widths;

  const fieldsTable = tableBytes(view, header, "fields", 8 + w.type_index);
  const fields = [];
  for (let i = 0; i < fieldsTable.count; i++) {
    const p = fieldsTable.start + i * (8 + w.type_index);
    const nameIndex = view.getUint32(p, true);
    fields.push({ index: i, name: stringAt(strings, nameIndex, `field[${i}]`),
      type_index: readIndex(view, p + 4, w.type_index),
      token: view.getUint32(p + 4 + w.type_index, true) });
  }

  const paramsTable = tableBytes(view, header, "parameters", 8 + w.type_index);
  const parameters = [];
  for (let i = 0; i < paramsTable.count; i++) {
    const p = paramsTable.start + i * (8 + w.type_index);
    const nameIndex = view.getUint32(p, true);
    parameters.push({ index: i, name: stringAt(strings, nameIndex, `parameter[${i}]`),
      token: view.getUint32(p + 4, true), type_index: readIndex(view, p + 8, w.type_index) });
  }

  const methodsTable = tableBytes(view, header, "methods",
    20 + w.type_definition_index + w.type_index + w.parameter_definition_index + w.generic_container_index);
  const methods = [];
  for (let i = 0; i < methodsTable.count; i++) {
    let p = methodsTable.start + i * (20 + w.type_definition_index + w.type_index +
      w.parameter_definition_index + w.generic_container_index);
    const nameIndex = view.getUint32(p, true); p += 4;
    const declaringType = readIndex(view, p, w.type_definition_index); p += w.type_definition_index;
    const returnType = readIndex(view, p, w.type_index); p += w.type_index;
    const returnParameterToken = view.getUint32(p, true); p += 4;
    const parameterStart = readIndex(view, p, w.parameter_definition_index); p += w.parameter_definition_index;
    const genericContainer = readIndex(view, p, w.generic_container_index); p += w.generic_container_index;
    const token = view.getUint32(p, true); p += 4;
    const flags = view.getUint16(p, true), iflags = view.getUint16(p + 2, true);
    const slot = view.getUint16(p + 4, true), parameterCount = view.getUint16(p + 6, true);
    methods.push({ index: i, name: stringAt(strings, nameIndex, `method[${i}]`),
      declaring_type: declaringType, return_type_index: returnType, return_parameter_token: returnParameterToken,
      parameter_start: parameterStart, generic_container_index: genericContainer,
      token, flags, iflags, slot, parameter_count: parameterCount });
  }

  const typesTable = tableBytes(view, header, "type_definitions",
    68 + 3 * w.type_index + w.generic_container_index);
  const types = [];
  for (let i = 0; i < typesTable.count; i++) {
    let p = typesTable.start + i * (68 + 3 * w.type_index + w.generic_container_index);
    const nameIndex = view.getUint32(p, true), namespaceIndex = view.getUint32(p + 4, true); p += 8;
    const byval = readIndex(view, p, w.type_index); p += w.type_index;
    const declaring = readIndex(view, p, w.type_index); p += w.type_index;
    const parent = readIndex(view, p, w.type_index); p += w.type_index;
    const generic = readIndex(view, p, w.generic_container_index); p += w.generic_container_index;
    const flags = view.getUint32(p, true); p += 4;
    const starts = Array.from({ length: 8 }, (_, n) => view.getInt32(p + n * 4, true)); p += 32;
    const counts = Array.from({ length: 8 }, (_, n) => view.getUint16(p + n * 2, true)); p += 16;
    const bitfield = view.getUint32(p, true), token = view.getUint32(p + 4, true);
    types.push({ index: i, name: stringAt(strings, nameIndex, `type[${i}]`),
      namespace: stringAt(strings, namespaceIndex, `type[${i}] namespace`),
      byval_type_index: byval, declaring_type_index: declaring, parent_type_index: parent,
      generic_container_index: generic, flags, field_start: starts[0], method_start: starts[1],
      event_start: starts[2], property_start: starts[3], nested_types_start: starts[4],
      interfaces_start: starts[5], vtable_start: starts[6], interface_offsets_start: starts[7],
      method_count: counts[0], property_count: counts[1], field_count: counts[2],
      event_count: counts[3], nested_type_count: counts[4], vtable_count: counts[5],
      interfaces_count: counts[6], interface_offsets_count: counts[7],
      bitfield, is_value_type: !!(bitfield & 1), is_enum: !!(bitfield & 2), token });
  }

  const propertiesTable = tableBytes(view, header, "properties", 20);
  const properties = [];
  for (let i = 0; i < propertiesTable.count; i++) {
    const p = propertiesTable.start + i * 20, nameIndex = view.getUint32(p, true);
    properties.push({ index: i, name: stringAt(strings, nameIndex, `property[${i}]`),
      getter_method: view.getInt32(p + 4, true), setter_method: view.getInt32(p + 8, true),
      attributes: view.getUint32(p + 12, true), token: view.getUint32(p + 16, true) });
  }

  const eventsTable = tableBytes(view, header, "events", 20 + w.type_index);
  const events = [];
  for (let i = 0; i < eventsTable.count; i++) {
    const p = eventsTable.start + i * (20 + w.type_index), nameIndex = view.getUint32(p, true);
    events.push({ index: i, name: stringAt(strings, nameIndex, `event[${i}]`),
      type_index: readIndex(view, p + 4, w.type_index),
      add_method: view.getInt32(p + 4 + w.type_index, true),
      remove_method: view.getInt32(p + 8 + w.type_index, true),
      raise_method: view.getInt32(p + 12 + w.type_index, true),
      token: view.getUint32(p + 16 + w.type_index, true) });
  }

  const genericContainersTable = tableBytes(view, header, "generic_containers", 16);
  const genericContainers = [];
  for (let i = 0; i < genericContainersTable.count; i++) {
    const p = genericContainersTable.start + i * 16;
    genericContainers.push({ index: i, owner_index: view.getInt32(p, true),
      type_argument_count: view.getInt32(p + 4, true), is_method: !!view.getInt32(p + 8, true),
      generic_parameter_start: view.getInt32(p + 12, true) });
  }

  const genericParametersTable = tableBytes(view, header, "generic_parameters", 12 + w.generic_container_index);
  const genericParameters = [];
  for (let i = 0; i < genericParametersTable.count; i++) {
    const p = genericParametersTable.start + i * (12 + w.generic_container_index);
    const owner = readIndex(view, p, w.generic_container_index), nameIndex = view.getUint32(p + w.generic_container_index, true);
    const q = p + w.generic_container_index + 4;
    genericParameters.push({ index: i, owner_index: owner,
      name: stringAt(strings, nameIndex, `generic_parameter[${i}]`),
      constraints_start: view.getInt16(q, true), constraints_count: view.getInt16(q + 2, true),
      number: view.getUint16(q + 4, true), flags: view.getUint16(q + 6, true) });
  }

  const modelTypes = types.map(t => {
    const slice = (start, count, source) => start < 0 ? [] : source.slice(start, start + count);
    const typeFields = slice(t.field_start, t.field_count, fields);
    const typeMethods = slice(t.method_start, t.method_count, methods).map(m => ({
      ...m, parameters: m.parameter_start < 0 ? [] :
        parameters.slice(m.parameter_start, m.parameter_start + m.parameter_count)
    }));
    return { ...t, full_name: [t.namespace, t.name].filter(Boolean).join("."),
      fields: typeFields, methods: typeMethods,
      properties: slice(t.property_start, t.property_count, properties),
      events: slice(t.event_start, t.event_count, events) };
  });

  const errors = [];
  const range = (label, start, count, total) => {
    if (!(start === -1 && count === 0) &&
        (start < 0 || count < 0 || start > total || count > total - start))
      errors.push(`${label}: диапазон [${start}, ${start + count}) вне таблицы размером ${total}.`);
  };
  for (const t of types) {
    const label = `type[${t.index}] ${t.namespace}.${t.name}`;
    range(label + " fields", t.field_start, t.field_count, fields.length);
    range(label + " methods", t.method_start, t.method_count, methods.length);
    range(label + " properties", t.property_start, t.property_count, properties.length);
    range(label + " events", t.event_start, t.event_count, events.length);
    range(label + " nested types", t.nested_types_start, t.nested_type_count, header.sections.nested_types.count);
    range(label + " interfaces", t.interfaces_start, t.interfaces_count, header.sections.interfaces.count);
    for (const key of ["declaring_type_index", "parent_type_index"]) {
      const ref = t[key];
      if (ref !== -1 && (ref < 0 || ref >= types.length)) errors.push(`${label}: ${key}=${ref} вне type definitions.`);
    }
  }
  for (const m of methods) {
    if (m.declaring_type !== -1 && (m.declaring_type < 0 || m.declaring_type >= types.length))
      errors.push(`method[${m.index}]: declaring type вне таблицы.`);
    range(`method[${m.index}] parameters`, m.parameter_start, m.parameter_count, parameters.length);
  }
  const warnings = ["TypeIndex хранится как числовой индекс; для разрешения имён типов понадобится этап анализа libil2cpp.so."];
  return {
    format: "il2cpp-v39-model", status: errors.length ? "invalid" : "partial",
    counts: { types: types.length, fields: fields.length, methods: methods.length,
      parameters: parameters.length, properties: properties.length, events: events.length,
      generic_containers: genericContainers.length, generic_parameters: genericParameters.length },
    index_widths: w, types: modelTypes, generic_containers: genericContainers,
    generic_parameters: genericParameters, validation: { errors, warnings }
  };
}

export { parseHeader, decode };
