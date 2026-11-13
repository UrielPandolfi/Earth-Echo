"""Genera tipos TypeScript desde el JSON Schema exportado por Pydantic."""

import json
from typing import Any

_SKIPPED = {
    "$schema",
    "$comment",
    "title",
    "description",
    "default",
    "examples",
    "format",
    "minLength",
    "maxLength",
    "minimum",
    "maximum",
    "exclusiveMinimum",
    "exclusiveMaximum",
    "pattern",
    "minItems",
    "maxItems",
    "additionalProperties",
    "discriminator",
    "uniqueItems",
}


def emit_typescript(schema: dict[str, Any]) -> str:
    definitions = schema.get("$defs", {})
    blocks = [
        "/* Este archivo se genera desde los modelos Pydantic. No lo edites a mano. */",
        "",
    ]
    for name in sorted(definitions):
        blocks.append(_emit_definition(name, definitions[name]))
        blocks.append("")
    if schema.get("title") and schema.get("type") == "object":
        blocks.append(_emit_definition(schema["title"], schema))
        blocks.append("")
    return "\n".join(blocks).rstrip() + "\n"


def _emit_definition(name: str, node: dict[str, Any]) -> str:
    if _extends(node) is not None:
        parent, extra = _extends(node)
        fields = _fields(extra)
        return f"export interface {name} extends {parent} {{\n{fields}}}"
    if node.get("type") == "object" or "properties" in node:
        return f"export interface {name} {{\n{_fields(node)}}}"
    return f"export type {name} = {emit_type(node)};"


def _extends(node: dict[str, Any]) -> tuple[str, dict[str, Any]] | None:
    options = node.get("allOf")
    if not isinstance(options, list) or len(options) != 1:
        return None
    ref = options[0].get("$ref") if isinstance(options[0], dict) else None
    if not isinstance(ref, str) or not ref.startswith("#/$defs/"):
        return None
    return ref.removeprefix("#/$defs/"), node


def _fields(node: dict[str, Any]) -> str:
    required = set(node.get("required", []))
    properties = node.get("properties") or {}
    if not isinstance(properties, dict):
        raise ValueError(f"properties inválidas en {node.get('title')}")
    lines = []
    for key, prop in properties.items():
        optional = "" if key in required else "?"
        lines.append(f"  {key}{optional}: {emit_type(prop)};")
    return "\n".join(lines) + ("\n" if lines else "")


def emit_type(node: Any) -> str:
    if not isinstance(node, dict):
        raise TypeError(f"Nodo de esquema inesperado: {node!r}")
    if "$ref" in node:
        ref = node["$ref"]
        if not isinstance(ref, str) or not ref.startswith("#/$defs/"):
            raise ValueError(f"Referencia no soportada: {ref}")
        _reject_unknown(node, allowed={"$ref"})
        return ref.removeprefix("#/$defs/")
    for key in ("oneOf", "anyOf"):
        if key in node:
            _reject_unknown(node, allowed={key})
            return " | ".join(emit_type(option) for option in node[key])
    if "allOf" in node:
        if len(node["allOf"]) == 1 and "properties" not in node:
            return emit_type(node["allOf"][0])
        raise ValueError(f"allOf no soportado: {node}")
    if "const" in node:
        _reject_unknown(node, allowed={"const", "type"})
        return json.dumps(node["const"], ensure_ascii=False)
    if "enum" in node:
        _reject_unknown(node, allowed={"enum", "type"})
        return " | ".join(json.dumps(item, ensure_ascii=False) for item in node["enum"])
    schema_type = node.get("type")
    if isinstance(schema_type, list):
        return " | ".join(emit_type({**node, "type": item}) for item in schema_type)
    if schema_type == "string":
        return "string"
    if schema_type in {"number", "integer"}:
        return "number"
    if schema_type == "boolean":
        return "boolean"
    if schema_type == "null":
        return "null"
    if schema_type == "array":
        item = emit_type(node["items"])
        if item.endswith(">") or "|" in item:
            return f"Array<{item}>"
        return f"{item}[]"
    if schema_type == "object" or "properties" in node:
        additional = node.get("additionalProperties")
        properties = node.get("properties")
        if properties:
            inner = _fields(node).rstrip()
            return f"{{\n{inner}\n}}"
        if isinstance(additional, dict):
            return f"Record<string, {emit_type(additional)}>"
        return "Record<string, unknown>"
    raise ValueError(f"Esquema no soportado: {node}")


def _reject_unknown(node: dict[str, Any], allowed: set[str]) -> None:
    unknown = set(node) - allowed - _SKIPPED
    if unknown:
        raise ValueError(f"Claves de esquema no soportadas {sorted(unknown)} en {node}")
