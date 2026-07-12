#!/usr/bin/env python3
"""Validate the Draft 2020-12 keyword subset used by Modeskill v0.1."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

DRAFT_2020_12 = "https://json-schema.org/draft/2020-12/schema"


class SchemaError(Exception):
    pass


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def validate_document(schema: dict[str, Any], data: Any) -> None:
    if schema.get("$schema") != DRAFT_2020_12:
        raise SchemaError(f"schema must declare {DRAFT_2020_12}")
    _validate(schema, data, schema, "$")


def validate_file(schema_path: Path, data_path: Path) -> None:
    validate_document(load_json(schema_path), load_json(data_path))


def _validate(schema: dict[str, Any], data: Any, root: dict[str, Any], path: str) -> None:
    if "$ref" in schema:
        schema = _resolve_ref(schema["$ref"], root)
    if "oneOf" in schema:
        matches = sum(_matches(option, data, root, path) for option in schema["oneOf"])
        if matches != 1:
            raise SchemaError(f"{path}: expected exactly one oneOf match, got {matches}")
    if "anyOf" in schema and not any(_matches(option, data, root, path) for option in schema["anyOf"]):
        raise SchemaError(f"{path}: expected at least one anyOf match")
    if "const" in schema and data != schema["const"]:
        raise SchemaError(f"{path}: expected const {schema['const']!r}, got {data!r}")
    if "enum" in schema and data not in schema["enum"]:
        raise SchemaError(f"{path}: expected one of {schema['enum']!r}, got {data!r}")
    if "type" in schema:
        _validate_type(schema["type"], data, path)

    if isinstance(data, dict):
        for key in schema.get("required", []):
            if key not in data:
                raise SchemaError(f"{path}: missing required property {key!r}")
        properties = schema.get("properties", {})
        if schema.get("additionalProperties") is False:
            extra = set(data) - set(properties)
            if extra:
                raise SchemaError(f"{path}: unexpected properties {sorted(extra)!r}")
        for key, value in data.items():
            if key in properties:
                _validate(properties[key], value, root, f"{path}.{key}")

    if isinstance(data, list):
        if len(data) < schema.get("minItems", 0):
            raise SchemaError(f"{path}: expected at least {schema['minItems']} items")
        if "maxItems" in schema and len(data) > schema["maxItems"]:
            raise SchemaError(f"{path}: expected at most {schema['maxItems']} items")
        if schema.get("uniqueItems"):
            encoded = [json.dumps(item, sort_keys=True) for item in data]
            if len(encoded) != len(set(encoded)):
                raise SchemaError(f"{path}: expected unique items")
        if "items" in schema:
            for index, item in enumerate(data):
                _validate(schema["items"], item, root, f"{path}[{index}]")

    if isinstance(data, str):
        if len(data) < schema.get("minLength", 0):
            raise SchemaError(f"{path}: string is shorter than {schema['minLength']}")
        if "pattern" in schema and not re.search(schema["pattern"], data):
            raise SchemaError(f"{path}: value {data!r} does not match {schema['pattern']!r}")
    if isinstance(data, int) and not isinstance(data, bool):
        if "minimum" in schema and data < schema["minimum"]:
            raise SchemaError(f"{path}: expected minimum {schema['minimum']}, got {data}")
        if "maximum" in schema and data > schema["maximum"]:
            raise SchemaError(f"{path}: expected maximum {schema['maximum']}, got {data}")


def _matches(schema: dict[str, Any], data: Any, root: dict[str, Any], path: str) -> bool:
    try:
        _validate(schema, data, root, path)
        return True
    except SchemaError:
        return False


def _validate_type(expected: str, data: Any, path: str) -> None:
    checks = {
        "object": lambda value: isinstance(value, dict),
        "array": lambda value: isinstance(value, list),
        "string": lambda value: isinstance(value, str),
        "integer": lambda value: isinstance(value, int) and not isinstance(value, bool),
        "boolean": lambda value: isinstance(value, bool),
        "null": lambda value: value is None,
    }
    if expected not in checks:
        raise SchemaError(f"{path}: unsupported schema type {expected!r}")
    if not checks[expected](data):
        raise SchemaError(f"{path}: expected {expected}, got {type(data).__name__}")


def _resolve_ref(ref: str, root: dict[str, Any]) -> dict[str, Any]:
    if not ref.startswith("#/"):
        raise SchemaError(f"unsupported ref {ref!r}")
    current: Any = root
    for part in ref[2:].split("/"):
        current = current[part.replace("~1", "/").replace("~0", "~")]
    return current
