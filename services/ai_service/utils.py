import json
import re
from typing import Any

from database.enums import ApiLevel, HttpMethod, ParamLocation, ParamType


MAX_PARAM_DEPTH = 8


def buildDuplicateProposal(method: str, path: str) -> dict[str, Any]:
    return {
        "duplicate_api": {"method": method, "path": path},
        "message": "API 已存在，不能重复创建",
    }


def extractOutputText(response: Any) -> str:
    """Extract text in the Responses API shape used by the ARK endpoint."""
    texts: list[str] = []
    for item in response.output:
        if item.type != "message":
            continue
        for content in item.content:
            if content.type == "output_text":
                texts.append(content.text)
    return "".join(texts).strip()


def parseJsonResponse(text: str) -> dict[str, Any]:
    """Parse a JSON object, tolerating a Markdown fence around model output."""
    if text.startswith("```"):
        lines = text.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()

    result = json.loads(text)
    if not isinstance(result, dict):
        raise ValueError("模型返回的根节点必须是 JSON 对象")
    return result


def validateParams(
    params: Any,
    *,
    isRequest: bool,
    isChild: bool = False,
    depth: int = 0,
) -> None:
    if not isinstance(params, list):
        raise ValueError("参数列表必须是数组")
    if depth > MAX_PARAM_DEPTH:
        raise ValueError("参数嵌套层级超过限制")

    validTypes = {member.value for member in ParamType}
    validLocations = {member.value for member in ParamLocation}
    for param in params:
        if not isinstance(param, dict):
            raise ValueError("参数项必须是对象")
        requiredFields = {
            "name",
            "type",
            "required",
            "nullable",
            "description",
            "example",
            "array_child_type",
            "children",
        }
        if isRequest:
            requiredFields.add("default_value")
            if not isChild:
                requiredFields.add("location")
        else:
            requiredFields.add("status_code")
        if not requiredFields.issubset(param):
            raise ValueError("参数项缺少必填字段")
        if not isinstance(param.get("name"), str) or not param["name"].strip():
            raise ValueError("参数名称不能为空")
        if param.get("type") not in validTypes:
            raise ValueError("参数类型不合法")
        if not isinstance(param["required"], bool):
            raise ValueError("required 必须为布尔值")
        if not isinstance(param["nullable"], bool):
            raise ValueError("nullable 必须为布尔值")

        if isRequest:
            if isChild:
                if "location" in param:
                    raise ValueError("请求子参数不能包含 location")
            elif param.get("location") not in validLocations:
                raise ValueError("请求参数 location 不合法")
            elif (
                param.get("location") == ParamLocation.PATH.value
                and (not param["required"] or param["nullable"])
            ):
                raise ValueError("Path 参数必须 required=true 且 nullable=false")
        else:
            statusCode = param["status_code"]
            if not isinstance(statusCode, int) or not 100 <= statusCode <= 599:
                raise ValueError("响应参数 status_code 不合法")

        childType = param.get("array_child_type")
        if childType is not None and childType not in validTypes:
            raise ValueError("array_child_type 不合法")
        children = param.get("children")
        allowsChildren = param["type"] == "object" or (
            param["type"] == "array" and childType == "object"
        )
        if children is not None:
            if not allowsChildren:
                raise ValueError("只有 object 或 array<object> 参数可以包含 children")
            validateParams(
                children,
                isRequest=isRequest,
                isChild=True,
                depth=depth + 1,
            )


def validateProposal(
    proposal: dict[str, Any],
    existingApis: list[dict[str, Any]],
) -> dict[str, Any]:
    if "missing_fields" in proposal:
        if set(proposal) != {"missing_fields"}:
            raise ValueError("缺失字段结果不能包含其他字段")
        missingFields = proposal["missing_fields"]
        if (
            not isinstance(missingFields, list)
            or not missingFields
            or not set(missingFields).issubset({"method", "path"})
            or len(set(missingFields)) != len(missingFields)
        ):
            raise ValueError("missing_fields 只能包含不重复的 method 或 path")
        return proposal

    if "duplicate_api" in proposal:
        if set(proposal) != {"duplicate_api", "message"}:
            raise ValueError("重复 API 结果不能包含其他字段")
        duplicateApi = proposal["duplicate_api"]
        if not isinstance(duplicateApi, dict) or set(duplicateApi) != {
            "method",
            "path",
        }:
            raise ValueError("duplicate_api 格式不合法")
        if not isinstance(proposal["message"], str) or not proposal["message"].strip():
            raise ValueError("重复 API 提示信息不能为空")
        if duplicateApi["method"] not in {member.value for member in HttpMethod}:
            raise ValueError("duplicate_api.method 不合法")
        if not isinstance(duplicateApi["path"], str) or not duplicateApi["path"].startswith("/"):
            raise ValueError("duplicate_api.path 不合法")
        if not any(
            api.get("method") == duplicateApi["method"]
            and api.get("path") == duplicateApi["path"]
            for api in existingApis
        ):
            raise ValueError("duplicate_api 未在现有 API 中找到")
        return proposal

    requiredTopLevel = {"add_api", "req_params", "resp_params"}
    if set(proposal) != requiredTopLevel:
        raise ValueError("成功结果必须且只能包含 add_api、req_params、resp_params")

    addApi = proposal["add_api"]
    if not isinstance(addApi, dict):
        raise ValueError("add_api 必须是对象")

    apiFields = ("name", "method", "path", "description", "level")
    validMethods = {member.value for member in HttpMethod}
    for field in apiFields:
        if not isinstance(addApi.get(field), str) or not addApi[field].strip():
            raise ValueError(f"add_api.{field} 必须是非空字符串")
    if set(addApi) != {"name", "method", "path", "description", "level", "category_id"}:
        raise ValueError("add_api 字段不符合合同")
    if re.search(r"[\u4e00-\u9fff]", addApi["name"]):
        raise ValueError("add_api.name 必须为英文名称")
    if addApi["method"] not in validMethods:
        raise ValueError("HTTP method 不合法")
    if addApi["level"] != ApiLevel.P2.value:
        raise ValueError("AI 创建 API 的 level 必须为 P2")
    if not addApi["path"].startswith("/"):
        raise ValueError("API path 必须以 / 开头")
    if addApi["category_id"] is not None:
        raise ValueError("AI 创建 API 的 category_id 必须为 null")
    if any(
        api.get("method") == addApi["method"] and api.get("path") == addApi["path"]
        for api in existingApis
    ):
        return buildDuplicateProposal(addApi["method"], addApi["path"])

    validateParams(proposal["req_params"], isRequest=True)
    validateParams(proposal["resp_params"], isRequest=False)

    pathParamNames = {
        param["name"]
        for param in proposal["req_params"]
        if param.get("location") == ParamLocation.PATH.value
    }
    if any(f"{{{name}}}" not in addApi["path"] for name in pathParamNames):
        raise ValueError("每个 Path 参数都必须出现在 API path 中")
    return proposal
