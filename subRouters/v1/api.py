import json
from robyn import SubRouter
from robyn.robyn import Request, Response
from robyn.authentication import BearerGetter

from authentication import AuthHandler
from database.database import session
from services.user import userGetUserIdByAccessToken
from services.api import *  # type: ignore
from utils import string2Bool


apiRouterV1 = SubRouter(__file__, prefix="/v1/api")


# 全局异常处理
@apiRouterV1.exception
def handle_exception(error):
    return Response(status_code=500, description=f"error msg: {error}", headers={})


# 鉴权中间件
apiRouterV1.configure_authentication(AuthHandler(token_getter=BearerGetter()))


# 通过service_id获取全部categories
@apiRouterV1.get("/getAllCategoriesByServiceId", auth_required=True)
def getAllCategoriesByServiceId(request: Request):
    service_id = request.query_params.get("service_id", None)
    if not service_id:
        return Response(
            status_code=400, headers={}, description="service_id is required"
        )
    user_id = userGetUserIdByAccessToken(request)
    with session() as db:
        res = apiGetAllCategoriesByServiceId(
            db=db, service_id=int(service_id), user_id=user_id
        )
    return res


# 通过service_id获取全部api（最新版本，可带category_id，不包括api内包含的params）
@apiRouterV1.get("/getAllApisByServiceId", auth_required=True)
def getAllApisByServiceId(request: Request):
    service_id = request.query_params.get("service_id", None)
    category_id = request.query_params.get("category_id", None)
    if not service_id or not category_id:
        return Response(
            status_code=400,
            headers={},
            description="service_id and category_id are required",
        )
    user_id = userGetUserIdByAccessToken(request)
    with session() as db:
        res = apiGetAllApisByServiceId(
            db=db,
            service_id=int(service_id),
            category_id=int(category_id),
            user_id=user_id,
        )
    return res


# 通过api_id获取api详情（包括api内包含的params）
@apiRouterV1.get("/getApiById", auth_required=True)
def getApiById(request: Request):
    api_id = request.query_params.get("api_id", None)
    if not api_id:
        return Response(status_code=400, headers={}, description="api_id is required")
    is_latest = request.query_params.get("is_latest", "true")
    user_id = userGetUserIdByAccessToken(request)
    with session() as db:
        res = apiGetApiById(
            db=db,
            api_id=int(api_id),
            user_id=user_id,
            is_latest=string2Bool(is_latest),
        )
    return res


# 通过service_id新增category
@apiRouterV1.post("/addCategoryByServiceId", auth_required=True)
def addCategoryByServiceId(request: Request):
    data = request.json()
    service_id = data["service_id"]
    category_name = data["category_name"]
    description = data["description"]
    user_id = userGetUserIdByAccessToken(request)
    with session() as db:
        res = apiAddCategoryByServiceId(
            db=db,
            service_id=int(service_id),
            user_id=user_id,
            category_name=category_name,
            description=description,
        )
    return res


# 通过category_id删除category
@apiRouterV1.post("/deleteCategoryById", auth_required=True)
def deleteCategoryById(request: Request):
    data = request.json()
    category_id = data["category_id"]
    user_id = userGetUserIdByAccessToken(request)
    with session() as db:
        res = apiDeleteCategoryById(db=db, category_id=category_id, user_id=user_id)
    return res


# 通过category_id修改category
@apiRouterV1.post("/updateCategoryById", auth_required=True)
def updateCategoryById(request: Request):
    data = request.json()
    category_id = data["category_id"]
    category_name = data["category_name"]
    description = data["description"]
    user_id = userGetUserIdByAccessToken(request)
    with session() as db:
        res = apiUpdateCategoryById(
            db=db,
            category_id=int(category_id),
            user_id=user_id,
            category_name=category_name,
            description=description,
        )
    return res


# 通过api_id、category_id修改api所属分类（仅支持修改正式表Api，不支持草稿表ApiDraft）
@apiRouterV1.post("/updateApiCategoryById", auth_required=True)
def updateApiCategoryById(request: Request):
    data = request.json()
    api_id = data["api_id"]
    category_id = data["category_id"]
    user_id = userGetUserIdByAccessToken(request)
    with session() as db:
        res = apiUpdateApiCategory(
            db=db, api_id=int(api_id), category_id=int(category_id), user_id=user_id
        )
    return res


# ---- ⚠️ 以下为service迭代流程相关路由 ----
# 通过service_iteration_id新增api（存ApiDraft表，可指定category_id）
@apiRouterV1.post("/addApi", auth_required=True)
def addApi(request: Request):
    data = request.json()
    service_iteration_id = data["service_iteration_id"]
    name = data["name"]
    method = data["method"]
    path = data["path"]
    description = data["description"]
    level = data["level"]
    category_id = data.get("category_id", None)
    user_id = userGetUserIdByAccessToken(request)
    with session() as db:
        res = apiAddApi(
            db=db,
            service_iteration_id=int(service_iteration_id),
            user_id=user_id,
            name=name,
            method=method,
            path=path,
            description=description,
            level=level,
            category_id=int(category_id) if category_id else None,
        )
    return res


# 通过service_iteration_id、api_draft_id复制api
@apiRouterV1.post("/copyApiByApiDraftId", auth_required=True)
def copyApiByApiDraftId(request: Request):
    data = request.json()
    service_iteration_id = data["service_iteration_id"]
    api_draft_id = data["api_draft_id"]
    user_id = userGetUserIdByAccessToken(request)
    with session() as db:
        res = apiCopyApiByApiDraftId(
            db=db,
            service_iteration_id=int(service_iteration_id),
            api_draft_id=int(api_draft_id),
            user_id=user_id,
        )
    return res


# 通过service_iteration_id、api_draft_id删除api
@apiRouterV1.post("/deleteApiByApiDraftId", auth_required=True)
def deleteApiByApiDraftId(request: Request):
    data = request.json()
    service_iteration_id = data["service_iteration_id"]
    api_draft_id = data["api_draft_id"]
    user_id = userGetUserIdByAccessToken(request)
    with session() as db:
        res = apiDeleteApiByApiDraftId(
            db=db,
            service_iteration_id=int(service_iteration_id),
            api_draft_id=int(api_draft_id),
            user_id=user_id,
        )
    return res


# 通过service_iteration_id、api_draft_id更新API
@apiRouterV1.post("/updateApiByApiDraftId", auth_required=True)
def updateApiByApiDraftId(request: Request):
    data = request.json()
    service_iteration_id = data["service_iteration_id"]
    api_draft_id = data["api_draft_id"]
    name = data["name"]
    method = data["method"]
    path = data["path"]
    description = data["description"]
    level = data["level"]
    req_params = json.loads(data["req_params"])
    resp_params = json.loads(data["resp_params"])

    user_id = userGetUserIdByAccessToken(request)
    with session() as db:
        res = apiUpdateApiByApiDraftId(
            db=db,
            service_iteration_id=int(service_iteration_id),
            api_draft_id=int(api_draft_id),
            user_id=user_id,
            name=name,
            method=method,
            path=path,
            description=description,
            level=level,
            req_params=req_params,
            resp_params=resp_params,
        )
    return res
