import enum


class HttpMethod(enum.Enum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"


class ApiLevel(enum.Enum):
    P0 = "P0"  # 核心接口
    P1 = "P1"  # 重要接口
    P2 = "P2"  # 一般接口
    P3 = "P3"  # 次要接口
    P4 = "P4"  # 测试接口


class ParamLocation(enum.Enum):
    QUERY = "query"
    PATH = "path"
    HEADER = "header"
    COOKIE = "cookie"
    BODY = "body"


class ParamType(enum.Enum):
    STRING = "string"
    INT = "int"
    DOUBLE = "double"
    BOOLEAN = "boolean"
    ARRAY = "array"
    OBJECT = "object"
    BINARY = "binary"


class UserRole(enum.Enum):
    FRONTEND = "frontend"  # 前端开发
    BACKEND = "backend"  # 后端开发
    FULLSTACK = "fullstack"  # 全栈开发
    QA = "qa"  # 测试工程师
    DEVOPS = "devops"  # 运维工程师
    PRODUCT_MANAGER = "product_manager"  # 产品经理
    DESIGNER = "designer"  # 设计师
    ARCHITECT = "architect"  # 系统架构师
    PROJ_LEAD = "proj_lead"  # 项目负责人
    GUEST = "guest"  # 访客


# 用户等级，从高到低
class UserLevel(enum.Enum):
    L0 = 0
    L1 = 1
    L2 = 2
    L3 = 3
    L4 = 4
