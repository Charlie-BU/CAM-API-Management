from database.models import Api
from database.models import ApiDraft
from sqlalchemy.orm import Session
from typing import List, Dict
import re

from database.models import (
    Service,
    ServiceIteration,
    User,
    RequestParam,
    RequestParamDraft,
    ResponseParam,
    ResponseParamDraft,
)
from database.enums import ParamLocation, ParamType


# service 版本迭代行为权限校验（校验service_iteration是否存在，是否已提交，是否为当前user有权限操作）
def checkServiceIterationPermission(
    db: Session,
    service_iteration_id: int,
    user_id: int,
) -> dict:
    service_iteration = db.get(ServiceIteration, service_iteration_id)
    if not service_iteration or service_iteration.is_committed:  # type: ignore
        return {
            "is_ok": False,
            "error": {
                "status": -10,
                "message": "Service iteration not found or committed",
            },
        }
    # 已提交的迭代，不可进行迭代操作
    if service_iteration.is_committed:  # type: ignore
        return {
            "is_ok": False,
            "error": {
                "status": -20,
                "message": "Service iteration has been committed",
            },
        }
    # 非L0用户，为当前service owner或当前迭代creator，才有权限进行迭代操作（维护者也不可操作别人的迭代）
    user = db.get(User, user_id)
    if (
        service_iteration.service.owner_id != user_id
        and service_iteration.creator_id != user_id
        and user.level.value != 0  # type: ignore
    ):
        return {
            "is_ok": False,
            "error": {
                "status": -30,
                "message": "You are neither the owner of this service, nor the creator of this service iteration",
            },
        }
    return {
        "is_ok": True,
        "service_iteration": service_iteration,
        "user": user,
    }


# 组织请求参数，根据location分类
def organizeReqParams(
    request_params: List[RequestParam | RequestParamDraft],
) -> Dict[str, List[Dict]]:
    request_params_raw = [rp.toJson() for rp in request_params]
    request_params_by_location = {
        ParamLocation.QUERY.value: [],
        ParamLocation.PATH.value: [],
        ParamLocation.HEADER.value: [],
        ParamLocation.COOKIE.value: [],
        ParamLocation.BODY.value: [],
    }
    # 构建id到param的索引表，用于处理子参数
    req_index = {p["id"]: p for p in request_params_raw}
    # 处理location、type、array_child_type等枚举值，将其转换为对应的value
    for p in request_params_raw:
        loc = p.get("location")
        p["location"] = getattr(loc, "value", loc)
        t = p.get("type")
        p["type"] = getattr(t, "value", t)
        act = p.get("array_child_type")
        p["array_child_type"] = getattr(act, "value", act)
    for p in request_params_raw:
        parent_id = p.get("parent_param_id")
        # 存在parent_param_id的参数为子参数，将其添加到父参数的children_params中
        if parent_id:
            parent = req_index.get(parent_id)
            if parent is not None:
                parent.setdefault("children_params", []).append(p)
        # 不存在parent_param_id的参数为根参数，根据location添加到对应的列表中
        else:
            request_params_by_location[p["location"]].append(p)

    return request_params_by_location


def organizeRespParams(
    response_params: List[ResponseParam | ResponseParamDraft],
) -> Dict[str, List[Dict]]:
    response_params_raw = [rp.toJson() for rp in response_params]
    # 构建id到param的索引表，用于处理子参数
    resp_index = {p["id"]: p for p in response_params_raw}
    # 处理type、array_child_type等枚举值，将其转换为对应的value
    for p in response_params_raw:
        t = p.get("type")
        p["type"] = getattr(t, "value", t)
        act = p.get("array_child_type")
        p["array_child_type"] = getattr(act, "value", act)
    response_params_by_status_code = {}
    for p in response_params_raw:
        parent_id = p.get("parent_param_id")
        # 存在parent_param_id的参数为子参数，将其添加到父参数的children_params中
        if parent_id:
            parent = resp_index.get(parent_id)
            if parent is not None:
                parent.setdefault("children_params", []).append(p)
        # 不存在parent_param_id的参数为根参数，根据status_code添加到对应的列表中
        else:
            key = str(p["status_code"])  # Python中dict的key必须是str
            response_params_by_status_code.setdefault(key, []).append(p)

    return response_params_by_status_code


def openapiTemplate(service: Service | ServiceIteration, is_latest: bool) -> Dict:
    """
    根据 Service 或 ServiceIteration 生成 OpenAPI 3.1.0 规范文档。
    参考：https://openapi.apifox.cn/
    原理：
    1. 遍历 Service 中的所有 API。
    2. 将内部定义的 RequestParam 和 ResponseParam 转换为 OpenAPI 的 Schema 对象。
    3. 递归处理对象和数组类型的嵌套结构。
    4. 根据参数位置（query, path, header, cookie, body）将参数放置到对应的 OpenAPI 字段中。
    5. 组装 Info, Paths, Components 等顶级字段。
    """
    contact: User = service.owner if is_latest else service.creator
    apis: List[Api | ApiDraft] = service.apis if is_latest else service.api_drafts
    paths = {}
    components_schemas = {}

    def _to_component_name(name: str) -> str:
        """
        Convert name to PascalCase for component names.
        """
        # Insert space before capital letters to handle camelCase/PascalCase
        s1 = re.sub(r"(?<!^)(?=[A-Z])", " ", name)
        # Replace non-alphanumeric characters with spaces
        clean = re.sub(r"[^a-zA-Z0-9]", " ", s1)
        return "".join(word.capitalize() for word in clean.split())

    def _get_type_schema(type_name: str) -> Dict:
        """
        将内部类型映射为 OpenAPI 支持的数据类型。
        例如：int -> integer (int64), double -> number (double)
        """
        mapping = {
            "string": {"type": "string"},
            "int": {"type": "integer", "format": "int64"},
            "double": {"type": "number", "format": "double"},
            "boolean": {"type": "boolean"},
            "binary": {"type": "string", "format": "binary"},
            "object": {"type": "object"},
            "array": {"type": "array"},
        }
        return mapping.get(type_name, {"type": "string"})

    def _build_param_schema(param: Dict) -> Dict:
        """
        递归构建参数的 Schema。
        - 如果是 object 类型，递归构建 properties。
        - 如果是 array 类型，递归构建 items。
        - 处理 description, example, default 等元数据。
        """
        schema = _get_type_schema(param.get("type", "string"))

        if param.get("type") == "object":
            properties = {}
            required = []
            for child in param.get("children_params", []):
                properties[child["name"]] = _build_param_schema(child)
                if child.get("required"):
                    required.append(child["name"])
            if properties:
                schema["properties"] = properties
                schema["additionalProperties"] = False
            if required:
                schema["required"] = required

        elif param.get("type") == "array":
            child_type = param.get("array_child_type", "string")
            if child_type == "object":
                item_schema = {"type": "object"}
                properties = {}
                required = []
                for child in param.get("children_params", []):
                    properties[child["name"]] = _build_param_schema(child)
                    if child.get("required"):
                        required.append(child["name"])
                if properties:
                    item_schema["properties"] = properties
                    item_schema["additionalProperties"] = False
                if required:
                    item_schema["required"] = required
                schema["items"] = item_schema
            else:
                schema["items"] = _get_type_schema(child_type)

        if param.get("example"):
            schema["example"] = param.get("example")
        if param.get("default_value"):
            if (
                param.get("default_value") == "null"
                or param.get("default_value") == "undefined"
            ):
                schema["default"] = None
            else:
                match param.get("type"):
                    case "string":
                        schema["default"] = str(param.get("default_value"))
                    case "int":
                        schema["default"] = int(param.get("default_value"))
                    case "double":
                        schema["default"] = float(param.get("default_value"))
                    case "boolean":
                        schema["default"] = bool(param.get("default_value"))
                    case _:
                        schema["default"] = param.get("default_value")

        return schema

    def _build_root_schema(params: List[Dict], schema_name: str = None) -> Dict:
        """
        构建根对象的 Schema（用于 RequestBody 或 Response Content）。
        将一组参数列表转换为一个 Object Schema。
        如果提供了 schema_name，则将其注册到 components 中并返回引用。
        """
        schema = {
            "type": "object",
            "properties": {},
            "required": [],
            "additionalProperties": False,
        }
        for p in params:
            schema["properties"][p["name"]] = _build_param_schema(p)
            if p.get("required"):
                schema["required"].append(p["name"])
        if not schema["required"]:
            del schema["required"]

        if schema_name:
            components_schemas[schema_name] = schema
            return {"$ref": f"#/components/schemas/{schema_name}"}

        return schema

    for api in apis:
        # 处理request_params
        request_params_by_location = organizeReqParams(api.request_params)
        # 处理response_params
        response_params_by_status_code = organizeRespParams(api.response_params)

        if api.path not in paths:
            paths.setdefault(api.path, {})

        parameters = []
        for loc in ["query", "path", "header", "cookie"]:
            for p in request_params_by_location.get(loc, []):
                param_obj = {
                    "name": p["name"],
                    "in": loc,
                    "required": p.get("required", False),
                    "schema": _build_param_schema(p),
                }
                if p.get("description"):
                    param_obj["description"] = p["description"]
                parameters.append(param_obj)

        request_body = None
        body_params = request_params_by_location.get("body", [])
        if body_params:
            req_name = _to_component_name(api.name) + "Request"
            request_body = {
                "required": True,
                "content": {
                    "application/json": {
                        "schema": _build_root_schema(body_params, req_name)
                    }
                },
            }

        responses = {}
        for status_code, params in response_params_by_status_code.items():
            suffix = "" if str(status_code) == "200" else str(status_code)
            resp_name = _to_component_name(api.name) + "Response" + suffix
            responses[status_code] = {
                "description": f"Response for {status_code}",
                "content": {
                    "application/json": {
                        "schema": _build_root_schema(params, resp_name)
                    }
                },
            }

        operation = {
            "description": api.description,
            "operationId": api.name,
            "parameters": parameters,
            "responses": responses,
            "deprecated": not api.is_enabled,
        }
        if request_body:
            operation["requestBody"] = request_body

        # Use api.method.value.lower() to ensure we get 'get', 'post', etc.
        method_str = (
            api.method.value.lower()
            if hasattr(api.method, "value")
            else str(api.method).lower()
        )
        paths[api.path][method_str] = operation

    return {
        "openapi": "3.1.0",
        "info": {
            "title": (
                service.service_uuid if is_latest else service.service.service_uuid
            ),
            "description": service.description
            or (service.service.description if not is_latest else ""),
            "contact": {
                "name": contact.username,
                "email": contact.email,
            },
            "version": service.version,
        },
        "paths": paths,
        "components": {"schemas": components_schemas},
    }
