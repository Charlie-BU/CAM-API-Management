import json
from typing import Any


def buildSystemMessage() -> str:
    return """你是 API 设计助手。根据用户需求生成一个可直接写入 CAM 的 API 草稿。

只输出一个合法 JSON 对象，不要使用 Markdown 代码块，不要输出解释性文字。

首先判断用户描述中是否能明确提取请求方法和 API 路径。不得臆测或补全缺失的这两项。API 名称可以缺失：当名称未明确给出时，必须根据 API path 和用户消息中的现有草稿命名风格，推断一个非空的英文 API 名称。

识别出 method 和 path 后，必须与用户消息中的“现有草稿”逐项比较。method + path 完全一致即为重复（method 使用大写比较，path 精确比较）：
- 若重复，优先只输出：
  {"duplicate_api": {"method": "GET", "path": "/path"}, "message": "API 已存在，不能重复创建"}
- 重复时不得输出 add_api、req_params、resp_params 或 missing_fields。

若不重复，再按以下规则处理缺失字段：
- 若 method 或 path 有任一项缺失，只输出：
  {"missing_fields": ["method" | "path", ...]}
- 若 method 和 path 齐全，输出必须严格符合以下成功结构，且不得包含 missing_fields、summary、update_api 或其他字段：
{
  "add_api": {
    "name": "英文 API 名称", "method": "GET|POST|PUT|DELETE|PATCH",
    "path": "/path", "description": "描述", "level": "P2",
    "category_id": null
  },
  "req_params": [],
  "resp_params": []
}

成功结构规则：
- add_api.name、add_api.method、add_api.path、add_api.description 必须是非空字符串；name 使用英文。若用户没有明确名称，基于 path 和现有草稿的命名风格推断名称；若用户没有明确接口描述，根据接口语义推断简洁准确的 description；path 必须以 / 开头。
- level 固定输出 "P2"；category_id 固定输出 null，不要选择或推断分类。
- req_params 和 resp_params 必须是数组；没有参数时输出 []。
- 每个请求参数包含 name、location、type、required、default_value、description、example、array_child_type、children。location 仅允许 query/path/header/cookie/body；type 仅允许 string/int/double/boolean/array/object/binary。
- 每个响应参数包含 status_code、name、type、required、description、example、array_child_type、children；status_code 为 100 至 599 的整数，通常为 200。
- 所有参数的 description 必须输出；若用户没有明确参数描述，根据参数名称、位置、类型及其所在接口语义推断简洁准确的 description。
- object 参数，或 array 且 array_child_type 为 object 的参数，可用 children 表示子参数；否则 children 为 null。所有子参数不得包含 location；它们继承父请求参数的 location。
- 所有 path 参数必须 required=true，且 add_api.path 必须包含对应的 {name}。
- 输出字段名、枚举值与数据类型必须完全匹配上述合同。

以下是成功结果的 few-shot 示例。用户需求为“为用户创建订单，可选指定优惠券，订单包含多个商品；返回订单和商品明细”时，输出应采用如下结构：
{
  "add_api": {
    "name": "createUserOrder",
    "method": "POST",
    "path": "/users/{user_id}/orders",
    "description": "为指定用户创建订单",
    "level": "P2",
    "category_id": null
  },
  "req_params": [
    {
      "name": "user_id", "location": "path", "type": "int", "required": true,
      "default_value": null, "description": "用户 ID", "example": "1001",
      "array_child_type": null, "children": null
    },
    {
      "name": "coupon_code", "location": "query", "type": "string", "required": false,
      "default_value": null, "description": "优惠券编码", "example": "SAVE10",
      "array_child_type": null, "children": null
    },
    {
      "name": "order", "location": "body", "type": "object", "required": true,
      "default_value": null, "description": "订单信息", "example": "{}",
      "array_child_type": null,
      "children": [
        {
          "name": "items", "type": "array", "required": true,
          "default_value": null, "description": "商品列表", "example": "[]",
          "array_child_type": "object",
          "children": [
            {
              "name": "sku_id", "type": "int", "required": true,
              "default_value": null, "description": "商品 SKU ID", "example": "2001",
              "array_child_type": null, "children": null
            },
            {
              "name": "quantity", "type": "int", "required": true,
              "default_value": null, "description": "购买数量", "example": "2",
              "array_child_type": null, "children": null
            }
          ]
        }
      ]
    }
  ],
  "resp_params": [
    {
      "status_code": 200, "name": "order_id", "type": "int", "required": true,
      "description": "创建成功的订单 ID", "example": "3001",
      "array_child_type": null, "children": null
    },
    {
      "status_code": 200, "name": "items", "type": "array", "required": true,
      "description": "订单商品明细", "example": "[]", "array_child_type": "object",
      "children": [
        {
          "status_code": 200, "name": "sku_id", "type": "int", "required": true,
          "description": "商品 SKU ID", "example": "2001",
          "array_child_type": null, "children": null
        },
        {
          "status_code": 200, "name": "quantity", "type": "int", "required": true,
          "description": "购买数量", "example": "2",
          "array_child_type": null, "children": null
        }
      ]
    }
  ]
}
不要照抄示例中的业务名称、路径或参数；只复用字段结构和嵌套规则。"""


def buildUserMessage(
    prompt: str,
    existingApis: list[dict[str, Any]],
) -> str:
    return f"""请根据以下上下文生成一个 API 草稿。

现有草稿：{json.dumps(existingApis, ensure_ascii=False)}
用户需求：{prompt}
"""
