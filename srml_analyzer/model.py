"""Cross-table validation and compact metadata model summaries."""
from __future__ import annotations

from pathlib import Path

from .core_tables import decode_fields, decode_methods, decode_parameters, decode_types
from .errors import FormatError
from .images_assemblies import decode_assemblies, decode_images
from .v39_header import parse_v39_header


def _check_range(label: str, start: int, count: int, total: int, errors: list[str]) -> None:
    if start == -1 and count == 0:
        return
    if start < 0 or count < 0 or start > total or count > total - start:
        errors.append(f"{label} range [{start}, {start + count}) is outside table size {total}.")


def build_model(data: bytes) -> dict:
    header = parse_v39_header(data)
    types = decode_types(data, header)
    fields = decode_fields(data, header)
    methods = decode_methods(data, header)
    parameters = decode_parameters(data, header)
    images = decode_images(data, header)
    assemblies = decode_assemblies(data, header)

    errors: list[str] = []
    warnings: list[str] = []

    for item in types:
        label = f"type[{item['index']}] {item['namespace']}.{item['name']}"
        _check_range(label + " fields", item["field_start"], item["field_count"], len(fields), errors)
        _check_range(label + " methods", item["method_start"], item["method_count"], len(methods), errors)
        _check_range(label + " nested types", item["nested_types_start"], item["nested_type_count"],
                     header["sections"]["nested_types"]["count"], errors)
        _check_range(label + " interfaces", item["interfaces_start"], item["interfaces_count"],
                     header["sections"]["interfaces"]["count"], errors)
        for key in ("declaring_type_index", "parent_type_index"):
            ref = item[key]
            if ref != -1 and not 0 <= ref < len(types):
                errors.append(f"{label} {key}={ref} is outside type table size {len(types)}.")

    for method in methods:
        label = f"method[{method['index']}] {method['name']}"
        owner = method["declaring_type"]
        if owner != -1 and not 0 <= owner < len(types):
            errors.append(f"{label} declaring type {owner} is outside type table size {len(types)}.")
        _check_range(label + " parameters", method["parameter_start"], method["parameter_count"],
                     len(parameters), errors)

    for field in fields:
        ref = field["type_index"]
        if ref != -1 and not 0 <= ref < header["sections"]["type_definitions"]["count"] + header["sections"]["generic_parameters"]["count"]:
            # TypeIndex addresses the global type table, whose total count is not
            # the type-definition count. Keep this as a warning until decoded.
            warnings.append(f"field[{field['index']}] type index {ref} cannot yet be resolved without the global type table.")

    for parameter in parameters:
        ref = parameter["type_index"]
        if ref != -1:
            warnings.append(f"parameter[{parameter['index']}] type index {ref} awaits global type-table decoding.")

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

    if errors:
        status = "invalid"
    elif warnings:
        status = "partial"
    else:
        status = "valid"

    return {
        "format": "il2cpp-v39-model",
        "status": status,
        "counts": {
            "images": len(images), "assemblies": len(assemblies), "types": len(types),
            "fields": len(fields), "methods": len(methods), "parameters": len(parameters),
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
        "types": [
            {"index": t["index"], "full_name": f"{t['namespace']}.{t['name']}".strip("."),
             "field_start": t["field_start"], "field_count": t["field_count"],
             "method_start": t["method_start"], "method_count": t["method_count"],
             "is_enum": t["is_enum"], "is_value_type": t["is_value_type"]}
            for t in types
        ],
        "validation": {"errors": errors, "warnings": warnings},
    }


def inspect_model(path: str | Path) -> dict:
    source = Path(path)
    result = build_model(source.read_bytes())
    result["file"] = source.name
    return result
