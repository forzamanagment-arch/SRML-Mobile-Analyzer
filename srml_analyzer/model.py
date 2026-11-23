"""Cross-table validation and compact metadata model summaries."""
from __future__ import annotations

from pathlib import Path

from .core_tables import decode_fields, decode_methods, decode_parameters, decode_types
from .extra_tables import (
    decode_events, decode_fixed_i32_array, decode_generic_containers,
    decode_generic_parameters, decode_interface_offsets, decode_properties,
    decode_u32_array, decode_variable_index_array,
)
from .images_assemblies import decode_assemblies, decode_images
from .v39_header import parse_v39_header


def _check_range(label: str, start: int, count: int, total: int, errors: list[str]) -> None:
    if start == -1 and count == 0:
        return
    if start < 0 or count < 0 or start > total or count > total - start:
        errors.append(f"{label} range [{start}, {start + count}) is outside table size {total}.")


def _check_method_ref(label: str, value: int, methods_count: int, errors: list[str]) -> None:
    if value != -1 and not 0 <= value < methods_count:
        errors.append(f"{label} method index {value} is outside method table size {methods_count}.")


def build_model(data: bytes) -> dict:
    header = parse_v39_header(data)
    types = decode_types(data, header)
    fields = decode_fields(data, header)
    methods = decode_methods(data, header)
    parameters = decode_parameters(data, header)
    properties = decode_properties(data, header)
    events = decode_events(data, header)
    generic_containers = decode_generic_containers(data, header)
    generic_parameters = decode_generic_parameters(data, header)
    interfaces = decode_variable_index_array(data, header, "interfaces", "type_index")
    constraints = decode_variable_index_array(data, header, "generic_parameter_constraints", "type_index")
    nested_types = decode_fixed_i32_array(data, header, "nested_types")
    vtable_methods = decode_u32_array(data, header, "vtable_methods")
    interface_offsets = decode_interface_offsets(data, header)
    images = decode_images(data, header)
    assemblies = decode_assemblies(data, header)

    errors: list[str] = []
    warnings: list[str] = []

    for item in types:
        label = f"type[{item['index']}] {item['namespace']}.{item['name']}"
        _check_range(label + " fields", item["field_start"], item["field_count"], len(fields), errors)
        _check_range(label + " methods", item["method_start"], item["method_count"], len(methods), errors)
        _check_range(label + " properties", item["property_start"], item["property_count"],
                     len(properties), errors)
        _check_range(label + " events", item["event_start"], item["event_count"], len(events), errors)
        _check_range(label + " nested types", item["nested_types_start"], item["nested_type_count"],
                     len(nested_types), errors)
        _check_range(label + " interfaces", item["interfaces_start"], item["interfaces_count"],
                     len(interfaces), errors)
        _check_range(label + " vtable", item["vtable_start"], item["vtable_count"],
                     len(vtable_methods), errors)
        _check_range(label + " interface offsets", item["interface_offsets_start"],
                     item["interface_offsets_count"], len(interface_offsets), errors)
        for key in ("declaring_type_index", "parent_type_index"):
            ref = item[key]
            if ref != -1 and not 0 <= ref < len(types):
                errors.append(f"{label} {key}={ref} is outside type-definition table size {len(types)}.")

    for index, nested in enumerate(nested_types):
        if nested != -1 and not 0 <= nested < len(types):
            errors.append(f"nested_types[{index}]={nested} is outside type-definition table size {len(types)}.")

    for method in methods:
        label = f"method[{method['index']}] {method['name']}"
        owner = method["declaring_type"]
        if owner != -1 and not 0 <= owner < len(types):
            errors.append(f"{label} declaring type {owner} is outside type-definition table size {len(types)}.")
        _check_range(label + " parameters", method["parameter_start"], method["parameter_count"],
                     len(parameters), errors)

    for prop in properties:
        _check_method_ref(f"property[{prop['index']}] getter", prop["getter_method"], len(methods), errors)
        _check_method_ref(f"property[{prop['index']}] setter", prop["setter_method"], len(methods), errors)

    for event in events:
        _check_method_ref(f"event[{event['index']}] add", event["add_method"], len(methods), errors)
        _check_method_ref(f"event[{event['index']}] remove", event["remove_method"], len(methods), errors)
        _check_method_ref(f"event[{event['index']}] raise", event["raise_method"], len(methods), errors)

    for container in generic_containers:
        owner_count = len(methods) if container["is_method"] else len(types)
        _check_range(f"generic_container[{container['index']}] owner",
                     container["owner_index"], 1, owner_count, errors)
        _check_range(f"generic_container[{container['index']}] parameters",
                     container["generic_parameter_start"], container["type_argument_count"],
                     len(generic_parameters), errors)

    for parameter in generic_parameters:
        _check_range(f"generic_parameter[{parameter['index']}] constraints",
                     parameter["constraints_start"], parameter["constraints_count"],
                     len(constraints), errors)
        owner = parameter["owner_index"]
        if owner != -1 and not 0 <= owner < len(generic_containers):
            errors.append(f"generic_parameter[{parameter['index']}] owner {owner} is outside generic-container table size {len(generic_containers)}.")

    for image in images:
        _check_range(f"image[{image['index']}] {image['name']} types", image["type_start"],
                     image["type_count"], len(types), errors)
        assembly = image["assembly_index"]
        if assembly != -1 and not 0 <= assembly < len(assemblies):
            errors.append(f"image[{image['index']}] assembly index {assembly} is outside assembly table size {len(assemblies)}.")

    for assembly in assemblies:
        image = assembly["image_index"]
        if image != -1 and not 0 <= image < len(images):
            errors.append(f"assembly[{assembly['index']}] image index {image} is outside image table size {len(images)}.")

    # TypeIndex values refer to the native metadata-registration type array,
    # not directly to TypeDefinitions. Their names are resolved in the ELF stage.
    unresolved_type_refs = sum(1 for x in fields if x["type_index"] != -1)
    unresolved_type_refs += sum(1 for x in parameters if x["type_index"] != -1)
    unresolved_type_refs += sum(1 for x in events if x["type_index"] != -1)
    unresolved_type_refs += sum(1 for x in interfaces if x != -1)
    unresolved_type_refs += sum(1 for x in constraints if x != -1)
    unresolved_type_refs += sum(1 for x in interface_offsets if x["type_index"] != -1)
    if unresolved_type_refs:
        warnings.append(
            f"{unresolved_type_refs} TypeIndex references are structurally decoded but need "
            "libil2cpp.so metadata-registration data for name resolution."
        )

    status = "invalid" if errors else ("partial" if warnings else "valid")
    class_summaries = []
    for t in types:
        field_items = fields[t["field_start"]:t["field_start"] + t["field_count"]] if t["field_start"] >= 0 else []
        method_items = methods[t["method_start"]:t["method_start"] + t["method_count"]] if t["method_start"] >= 0 else []
        property_items = properties[t["property_start"]:t["property_start"] + t["property_count"]] if t["property_start"] >= 0 else []
        event_items = events[t["event_start"]:t["event_start"] + t["event_count"]] if t["event_start"] >= 0 else []
        class_summaries.append({
            "index": t["index"],
            "full_name": f"{t['namespace']}.{t['name']}".strip("."),
            "token": t["token"],
            "flags": t["flags"],
            "is_enum": t["is_enum"],
            "is_value_type": t["is_value_type"],
            "parent_type_index": t["parent_type_index"],
            "fields": [{"index": x["index"], "name": x["name"], "type_index": x["type_index"], "token": x["token"]} for x in field_items],
            "methods": [{
                "index": x["index"], "name": x["name"], "return_type_index": x["return_type"],
                "parameter_count": x["parameter_count"], "token": x["token"],
                "parameters": [
                    {"index": p["index"], "name": p["name"], "type_index": p["type_index"]}
                    for p in parameters[x["parameter_start"]:x["parameter_start"] + x["parameter_count"]]
                ] if x["parameter_start"] >= 0 else [],
            } for x in method_items],
            "properties": [{"index": x["index"], "name": x["name"], "getter_method": x["getter_method"],
                            "setter_method": x["setter_method"], "token": x["token"]} for x in property_items],
            "events": [{"index": x["index"], "name": x["name"], "type_index": x["type_index"],
                        "add_method": x["add_method"], "remove_method": x["remove_method"],
                        "raise_method": x["raise_method"]} for x in event_items],
        })

    return {
        "format": "il2cpp-v39-model",
        "status": status,
        "counts": {
            "images": len(images), "assemblies": len(assemblies), "types": len(types),
            "fields": len(fields), "methods": len(methods), "parameters": len(parameters),
            "properties": len(properties), "events": len(events),
            "generic_containers": len(generic_containers), "generic_parameters": len(generic_parameters),
            "interfaces": len(interfaces), "nested_types": len(nested_types),
            "vtable_methods": len(vtable_methods), "interface_offsets": len(interface_offsets),
        },
        "assemblies": [
            {"index": a["index"], "name": a["name"], "version": a["version"],
             "image_index": a["image_index"]}
            for a in assemblies
        ],
        "images": [
            {"index": i["index"], "name": i["name"], "assembly_index": i["assembly_index"],
             "type_start": i["type_start"], "type_count": i["type_count"]}
            for i in images
        ],
        "types": class_summaries,
        "generic_containers": generic_containers,
        "generic_parameters": generic_parameters,
        "validation": {"errors": errors, "warnings": warnings},
    }


def inspect_model(path: str | Path) -> dict:
    source = Path(path)
    result = build_model(source.read_bytes())
    result["file"] = source.name
    return result
