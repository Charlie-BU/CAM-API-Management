import json
import re
from typing import Any


SUPPORTED_METHODS = {"get", "post", "put", "delete", "patch"}
TYPE_MAPPING = {
    "string": "string",
    "integer": "int",
    "number": "double",
    "boolean": "boolean",
    "object": "object",
    "array": "array",
}


class OpenApiImportError(ValueError):
    pass


class _LocalRefResolver:
    def __init__(self, document: dict[str, Any]):
        self.document = document

    def resolve(
        self, node: Any, ref_stack: tuple[str, ...] = ()
    ) -> tuple[Any, tuple[str, ...]]:
        if not isinstance(node, dict) or "$ref" not in node:
            return node, ref_stack

        ref = node["$ref"]
        if not isinstance(ref, str) or not ref.startswith("#/"):
            raise OpenApiImportError(f"Only local $ref is supported: {ref}")
        if ref in ref_stack:
            raise OpenApiImportError(f"Recursive $ref is not supported: {ref}")

        target: Any = self.document
        for raw_part in ref[2:].split("/"):
            part = raw_part.replace("~1", "/").replace("~0", "~")
            if not isinstance(target, dict) or part not in target:
                raise OpenApiImportError(f"Unresolved $ref: {ref}")
            target = target[part]
        if not isinstance(target, dict):
            raise OpenApiImportError(f"$ref must point to an object: {ref}")

        merged = dict(target)
        merged.update({key: value for key, value in node.items() if key != "$ref"})
        return self.resolve(merged, (*ref_stack, ref))


def _stringValue(value: Any, field: str) -> str | None:
    if value is None:
        return None
    if isinstance(value, bool):
        result = "true" if value else "false"
    elif isinstance(value, (dict, list)):
        result = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    else:
        result = str(value)
    if len(result) > 256:
        raise OpenApiImportError(f"{field} exceeds CAM's 256 character limit")
    return result


def _operationName(method: str, path: str) -> str:
    parts = re.findall(r"[A-Za-z0-9]+", path)
    suffix = "".join(part[:1].upper() + part[1:] for part in parts)
    return f"{method.lower()}{suffix or 'Root'}"


def _optionalText(value: Any, field: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise OpenApiImportError(f"{field} must be a string")
    return value


def parseOpenApiDocument(document: Any) -> dict[str, Any]:
    if not isinstance(document, dict):
        raise OpenApiImportError("openapi_object must be a JSON object")

    version = document.get("openapi")
    if not isinstance(version, str) or not version.startswith(("3.0.", "3.1.")):
        raise OpenApiImportError("Only OpenAPI 3.0.x and 3.1.x are supported")

    info = document.get("info")
    if not isinstance(info, dict):
        raise OpenApiImportError("OpenAPI info must be an object")
    if not isinstance(info.get("title"), str) or not info["title"].strip():
        raise OpenApiImportError("OpenAPI info.title is required")
    if not isinstance(info.get("version"), str) or not info["version"].strip():
        raise OpenApiImportError("OpenAPI info.version is required")
    paths = document.get("paths")
    if not isinstance(paths, dict):
        raise OpenApiImportError("OpenAPI paths must be an object")

    resolver = _LocalRefResolver(document)
    warnings: list[str] = []
    apis: list[dict[str, Any]] = []
    method_paths: set[tuple[str, str]] = set()
    method_names: set[tuple[str, str]] = set()

    def rejectComposition(schema: dict[str, Any], context: str) -> None:
        for keyword in ("allOf", "oneOf", "anyOf", "not"):
            if keyword in schema:
                raise OpenApiImportError(
                    f"Schema keyword {keyword} is not supported for {context}"
                )

    def schemaType(schema: dict[str, Any]) -> tuple[str, bool]:
        raw_type = schema.get("type")
        nullable = bool(schema.get("nullable", False))
        if isinstance(raw_type, list):
            non_null_types = [item for item in raw_type if item != "null"]
            nullable = nullable or "null" in raw_type
            if len(non_null_types) != 1:
                raise OpenApiImportError(
                    "Schema type unions other than a nullable union are not supported"
                )
            raw_type = non_null_types[0]
        if raw_type is None:
            if "properties" in schema or "additionalProperties" in schema:
                raw_type = "object"
            elif "items" in schema:
                raw_type = "array"
            else:
                raw_type = "string"
        if not isinstance(raw_type, str) or raw_type not in TYPE_MAPPING:
            raise OpenApiImportError(f"Unsupported schema type: {raw_type}")
        cam_type = TYPE_MAPPING[raw_type]
        if raw_type == "string" and schema.get("format") in {"binary", "byte"}:
            cam_type = "binary"
        return cam_type, nullable

    def schemaToParam(
        name: str,
        raw_schema: Any,
        required: bool,
        *,
        location: str | None = None,
        description: Any = None,
        example: Any = None,
        status_code: int | None = None,
        ref_stack: tuple[str, ...] = (),
    ) -> dict[str, Any]:
        schema, resolved_stack = resolver.resolve(raw_schema, ref_stack)
        if not isinstance(schema, dict):
            raise OpenApiImportError(f"Schema for {name} must be an object")
        rejectComposition(schema, name)

        cam_type, nullable = schemaType(schema)
        children: list[dict[str, Any]] = []
        array_child_type = None

        if cam_type == "object":
            properties = schema.get("properties", {})
            if not isinstance(properties, dict):
                raise OpenApiImportError(f"properties for {name} must be an object")
            required_children = schema.get("required", [])
            if not isinstance(required_children, list):
                raise OpenApiImportError(f"required for {name} must be an array")
            for child_name, child_schema in properties.items():
                if not isinstance(child_name, str) or len(child_name) > 64:
                    raise OpenApiImportError(
                        f"Parameter name exceeds CAM's 64 character limit: {child_name}"
                    )
                children.append(
                    schemaToParam(
                        child_name,
                        child_schema,
                        child_name in required_children,
                        status_code=status_code,
                        ref_stack=resolved_stack,
                    )
                )
            if schema.get("additionalProperties") not in (None, False) and not properties:
                warnings.append(
                    f"Dynamic object properties for {name} cannot be represented in CAM"
                )

        elif cam_type == "array":
            items, item_stack = resolver.resolve(schema.get("items", {}), resolved_stack)
            if not isinstance(items, dict):
                raise OpenApiImportError(f"Array items for {name} must be an object")
            rejectComposition(items, f"array items for {name}")
            array_child_type, _ = schemaType(items)
            if array_child_type == "array":
                raise OpenApiImportError(f"Nested arrays are not supported for {name}")
            if array_child_type == "object":
                properties = items.get("properties", {})
                if not isinstance(properties, dict):
                    raise OpenApiImportError(
                        f"Array item properties for {name} must be an object"
                    )
                required_children = items.get("required", [])
                if not isinstance(required_children, list):
                    raise OpenApiImportError(
                        f"Array item required for {name} must be an array"
                    )
                for child_name, child_schema in properties.items():
                    if not isinstance(child_name, str) or len(child_name) > 64:
                        raise OpenApiImportError(
                            f"Parameter name exceeds CAM's 64 character limit: {child_name}"
                        )
                    children.append(
                        schemaToParam(
                            child_name,
                            child_schema,
                            child_name in required_children,
                            status_code=status_code,
                            ref_stack=item_stack,
                        )
                    )

        param = {
            "name": name,
            "type": cam_type,
            "required": required,
            "nullable": nullable,
            "default_value": _stringValue(schema.get("default"), f"default for {name}"),
            "description": _optionalText(
                description if description is not None else schema.get("description"),
                f"description for {name}",
            ),
            "example": _stringValue(
                example if example is not None else schema.get("example"),
                f"example for {name}",
            ),
            "array_child_type": array_child_type,
            "children": children or None,
        }
        if location is not None:
            param["location"] = location
        if status_code is not None:
            param["status_code"] = status_code
        return param

    def objectSchemaToParams(
        raw_schema: Any,
        *,
        location: str | None = None,
        status_code: int | None = None,
        fallback_name: str,
    ) -> list[dict[str, Any]]:
        schema, ref_stack = resolver.resolve(raw_schema)
        if not isinstance(schema, dict):
            raise OpenApiImportError("Content schema must be an object")
        rejectComposition(schema, fallback_name)
        cam_type, _ = schemaType(schema)
        if cam_type != "object" or not isinstance(schema.get("properties"), dict):
            return [
                schemaToParam(
                    fallback_name,
                    schema,
                    True,
                    location=location,
                    status_code=status_code,
                    ref_stack=ref_stack,
                )
            ]

        required_names = schema.get("required", [])
        if not isinstance(required_names, list):
            raise OpenApiImportError("Schema required must be an array")
        result = []
        for name, child_schema in schema["properties"].items():
            if not isinstance(name, str) or len(name) > 64:
                raise OpenApiImportError(
                    f"Parameter name exceeds CAM's 64 character limit: {name}"
                )
            result.append(
                schemaToParam(
                    name,
                    child_schema,
                    name in required_names,
                    location=location,
                    status_code=status_code,
                    ref_stack=ref_stack,
                )
            )
        return result

    def jsonSchemaFromContent(content: Any, context: str) -> Any:
        if not isinstance(content, dict):
            raise OpenApiImportError(f"content for {context} must be an object")
        media = content.get("application/json")
        if media is None:
            for media_type, candidate in content.items():
                if isinstance(media_type, str) and media_type.endswith("+json"):
                    media = candidate
                    break
        if media is None:
            warnings.append(f"Skipped non-JSON content for {context}")
            return None
        if not isinstance(media, dict) or "schema" not in media:
            raise OpenApiImportError(f"JSON content for {context} has no schema")
        return media["schema"]

    for path, path_item in paths.items():
        if not isinstance(path, str) or not path.startswith("/"):
            raise OpenApiImportError(f"Invalid OpenAPI path: {path}")
        if len(path) > 256:
            raise OpenApiImportError(f"Path exceeds CAM's 256 character limit: {path}")
        path_item, _ = resolver.resolve(path_item)
        if not isinstance(path_item, dict):
            raise OpenApiImportError(f"Path item for {path} must be an object")
        path_parameters = path_item.get("parameters", [])
        if not isinstance(path_parameters, list):
            raise OpenApiImportError(f"Path parameters for {path} must be an array")

        for method, raw_operation in path_item.items():
            method_lower = method.lower()
            if method_lower not in SUPPORTED_METHODS:
                if method_lower in {"head", "options", "trace"}:
                    warnings.append(f"Skipped unsupported method {method.upper()} {path}")
                continue
            operation, _ = resolver.resolve(raw_operation)
            if not isinstance(operation, dict):
                raise OpenApiImportError(f"Operation {method.upper()} {path} must be an object")

            operation_id = operation.get("operationId") or _operationName(method, path)
            if not isinstance(operation_id, str) or not operation_id.strip():
                raise OpenApiImportError(f"Invalid operationId for {method.upper()} {path}")
            operation_id = operation_id.strip()
            if len(operation_id) > 128:
                raise OpenApiImportError(
                    f"operationId exceeds CAM's 128 character limit: {operation_id}"
                )
            method_path = (method_lower, path)
            method_name = (method_lower, operation_id)
            if method_path in method_paths:
                raise OpenApiImportError(f"Duplicate operation: {method.upper()} {path}")
            if method_name in method_names:
                raise OpenApiImportError(
                    f"Duplicate operationId for method {method.upper()}: {operation_id}"
                )
            method_paths.add(method_path)
            method_names.add(method_name)

            merged_parameters: dict[tuple[str, str], dict[str, Any]] = {}
            operation_parameters = operation.get("parameters", [])
            if not isinstance(operation_parameters, list):
                raise OpenApiImportError(
                    f"Parameters for {method.upper()} {path} must be an array"
                )
            for raw_parameter in [*path_parameters, *operation_parameters]:
                parameter, _ = resolver.resolve(raw_parameter)
                if not isinstance(parameter, dict):
                    raise OpenApiImportError("Parameter must be an object")
                name = parameter.get("name")
                location = parameter.get("in")
                if not isinstance(name, str) or not isinstance(location, str):
                    raise OpenApiImportError("Parameter name and in are required")
                merged_parameters[(location, name)] = parameter

            request_params = []
            for (location, name), parameter in merged_parameters.items():
                if location not in {"query", "path", "header", "cookie"}:
                    warnings.append(
                        f"Skipped unsupported parameter location {location} for {name}"
                    )
                    continue
                if len(name) > 64:
                    raise OpenApiImportError(
                        f"Parameter name exceeds CAM's 64 character limit: {name}"
                    )
                schema = parameter.get("schema")
                if schema is None:
                    raise OpenApiImportError(f"Parameter {name} has no schema")
                request_params.append(
                    schemaToParam(
                        name,
                        schema,
                        True if location == "path" else bool(parameter.get("required")),
                        location=location,
                        description=parameter.get("description"),
                        example=parameter.get("example"),
                    )
                )

            raw_request_body = operation.get("requestBody")
            if raw_request_body is not None:
                request_body, _ = resolver.resolve(raw_request_body)
                if not isinstance(request_body, dict):
                    raise OpenApiImportError("requestBody must be an object")
                body_schema = jsonSchemaFromContent(
                    request_body.get("content"), f"request body of {method.upper()} {path}"
                )
                if body_schema is not None:
                    request_params.extend(
                        objectSchemaToParams(
                            body_schema,
                            location="body",
                            fallback_name="body",
                        )
                    )

            response_params = []
            responses = operation.get("responses", {})
            if not isinstance(responses, dict):
                raise OpenApiImportError(
                    f"Responses for {method.upper()} {path} must be an object"
                )
            for raw_status_code, raw_response in responses.items():
                try:
                    status_code = int(raw_status_code)
                except (TypeError, ValueError):
                    warnings.append(
                        f"Skipped response {raw_status_code} for {method.upper()} {path}"
                    )
                    continue
                response, _ = resolver.resolve(raw_response)
                if not isinstance(response, dict):
                    raise OpenApiImportError(f"Response {raw_status_code} must be an object")
                if "content" not in response:
                    warnings.append(
                        f"Response {raw_status_code} for {method.upper()} {path} has no body"
                    )
                    continue
                response_schema = jsonSchemaFromContent(
                    response["content"],
                    f"response {raw_status_code} of {method.upper()} {path}",
                )
                if response_schema is not None:
                    response_params.extend(
                        objectSchemaToParams(
                            response_schema,
                            status_code=status_code,
                            fallback_name="data",
                        )
                    )

            apis.append(
                {
                    "name": operation_id,
                    "method": method.upper(),
                    "path": path,
                    "description": _optionalText(
                        operation.get("description") or operation.get("summary"),
                        f"description for {method.upper()} {path}",
                    )
                    or "",
                    "level": "P2",
                    "is_enabled": not bool(operation.get("deprecated", False)),
                    "request_params": request_params,
                    "response_params": response_params,
                }
            )

    return {
        "description": _optionalText(info.get("description"), "info.description"),
        "apis": apis,
        "warnings": warnings,
    }
