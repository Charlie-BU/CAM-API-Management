import json
from robyn import SubRouter
from robyn.robyn import Request, Response
from robyn.authentication import BearerGetter

from authentication import AuthHandler
from database.database import session
from services.user import userGetUserIdByAccessToken
from services.service import *  # type: ignore


serviceRouterV1 = SubRouter(__file__, prefix="/v1/service")


# 全局异常处理
@serviceRouterV1.exception
def handle_exception(error):
    return Response(status_code=500, description=f"error msg: {error}", headers={})


# 鉴权中间件
serviceRouterV1.configure_authentication(AuthHandler(token_getter=BearerGetter()))


# 通过服务id获取服务详情
@serviceRouterV1.get("/getServiceById", auth_required=True)
def getServiceById(request: Request):
    id = request.query_params.get("id", None)
    if not id:
        return Response(status_code=400, description="id is required", headers={})
    user_id = userGetUserIdByAccessToken(request=request)
    with session() as db:
        res = serviceGetServiceById(db=db, id=int(id), user_id=user_id)
    return res


# 获取全部服务
@serviceRouterV1.get("/getAllServices", auth_required=True)
def getAllServices(request: Request):
    page_size = request.query_params.get("page_size", "10")
    current_page = request.query_params.get("current_page", "1")
    user_id = userGetUserIdByAccessToken(request=request)
    with session() as db:
        res = serviceGetAllServices(
            db=db,
            user_id=user_id,
            page_size=int(page_size) if page_size else 10,
            current_page=int(current_page) if current_page else 1,
        )
    return res


# 通过用户id获取用户的所有最新版本服务（Service表中）的列表
@serviceRouterV1.get("/getHisNewestServicesByOwnerId", auth_required=True)
def getHisNewestServicesByOwnerId(request: Request):
    page_size = request.query_params.get("page_size", "10")
    current_page = request.query_params.get("current_page", "1")
    is_my_services = request.query_params.get("is_my_services", "true")
    my_id = userGetUserIdByAccessToken(request=request)
    assert is_my_services is not None
    if json.loads(is_my_services.lower()):
        owner_id = my_id
    else:
        owner_id = request.query_params.get("owner_id", None)
        if not owner_id:
            return Response(
                status_code=400,
                description="owner_id is required when is_my_services is false",
                headers={},
            )
    with session() as db:
        res = serviceGetHisNewestServicesByOwnerId(
            db=db,
            owner_id=int(owner_id),
            my_id=my_id,
            page_size=int(page_size) if page_size else 10,
            current_page=int(current_page) if current_page else 1,
        )
    return res


# 通过用户id获取用户的所有维护服务（Service表中）的列表
@serviceRouterV1.get("/getHisMaintainedServicesByUserId", auth_required=True)
def getHisMaintainedServicesByUserId(request: Request):
    page_size = request.query_params.get("page_size", "10")
    current_page = request.query_params.get("current_page", "1")
    my_id = userGetUserIdByAccessToken(request=request)
    user_id = request.query_params.get("user_id", str(my_id))

    with session() as db:
        res = serviceGetHisMaintainedServicesByUserId(
            db=db,
            user_id=int(user_id),
            my_id=my_id,
            page_size=int(page_size) if page_size else 10,
            current_page=int(current_page) if current_page else 1,
        )
    return res


# 通过service_uuid和version获取服务详情（根据version判断是否为最新版本）
@serviceRouterV1.get("/getServiceByUuidAndVersion", auth_required=True)
def getServiceByUuidAndVersion(request: Request):
    service_uuid = request.query_params.get("service_uuid", None)
    version = request.query_params.get("version", None)
    if not service_uuid or not version:
        return Response(
            status_code=400,
            description="service_uuid and version are required",
            headers={},
        )
    user_id = userGetUserIdByAccessToken(request=request)
    with session() as db:
        res = serviceGetServiceByUuidAndVersion(
            db=db,
            service_uuid=service_uuid,
            version=version,
            user_id=user_id,
        )
    return res


# 通过service_uuid获取全部版本号
@serviceRouterV1.get("/getAllVersionsByUuid", auth_required=True)
def getAllVersionsByUuid(request: Request):
    service_uuid = request.query_params.get("service_uuid", None)
    if not service_uuid:
        return Response(
            status_code=400,
            description="service_uuid is required",
            headers={},
        )
    user_id = userGetUserIdByAccessToken(request=request)
    with session() as db:
        res = serviceGetAllVersionsByUuid(
            db=db,
            service_uuid=service_uuid,
            user_id=user_id,
        )
    return res


# 创建新服务
@serviceRouterV1.post("/createNewService", auth_required=True)
def createNewService(request: Request):
    data = request.json()
    service_uuid = data["service_uuid"]
    description = data["description"]
    owner_id = userGetUserIdByAccessToken(request=request)
    with session() as db:
        res = serviceCreateNewService(
            db=db,
            service_uuid=service_uuid,
            owner_id=owner_id,
            description=description,
        )
    return res


# 通过user_id获取全部删除的服务
@serviceRouterV1.get("/getAllDeletedServicesByUserId", auth_required=True)
def getAllDeletedServicesByUserId(request: Request):
    page_size = request.query_params.get("page_size", "10")
    current_page = request.query_params.get("current_page", "1")
    user_id = userGetUserIdByAccessToken(request=request)
    with session() as db:
        res = serviceGetAllDeletedServicesByUserId(
            db=db,
            user_id=user_id,
            page_size=int(page_size) if page_size else 10,
            current_page=int(current_page) if current_page else 1,
        )
    return res


# 通过candidate_id和service_id判断是否为服务的维护者
@serviceRouterV1.get("/isServiceMaintainer", auth_required=True)
def isServiceMaintainer(request: Request):
    service_id = request.query_params.get("service_id", None)
    candidate_id = request.query_params.get("candidate_id", None)
    if not service_id or not candidate_id:
        return Response(
            status_code=400,
            description="service_id and candidate_id are required",
            headers={},
        )
    user_id = userGetUserIdByAccessToken(request=request)
    with session() as db:
        res = serviceIsMaintainer(
            db=db,
            service_id=int(service_id),
            user_id=user_id,
            candidate_id=int(candidate_id),
        )
    return res


# 通过服务id添加或移除maintainer
@serviceRouterV1.post("/addOrRemoveServiceMaintainerById", auth_required=True)
def addOrRemoveServiceMaintainerById(request: Request):
    data = request.json()
    service_id = data["service_id"]
    candidate_id = data["candidate_id"]
    user_id = userGetUserIdByAccessToken(request=request)
    with session() as db:
        res = serviceAddOrRemoveServiceMaintainerById(
            db=db,
            service_id=int(service_id),
            user_id=user_id,
            candidate_id=int(candidate_id),
        )
    return res


# 通过服务id删除服务（最新版本），历史版本不动
@serviceRouterV1.post("/deleteServiceById", auth_required=True)
def deleteServiceById(request: Request):
    data = request.json()
    id = data["id"]
    user_id = userGetUserIdByAccessToken(request=request)
    with session() as db:
        res = serviceDeleteServiceById(db=db, id=id, user_id=user_id)
    return res


# 通过服务id还原服务（还原最新版本），历史版本不动
@serviceRouterV1.post("/restoreServiceById", auth_required=True)
def restoreServiceById(request: Request):
    data = request.json()
    id = data["id"]
    user_id = userGetUserIdByAccessToken(request=request)
    with session() as db:
        res = serviceRestoreServiceById(db=db, id=id, user_id=user_id)
    return res


# 通过service_iteration_id删除服务历史版本
@serviceRouterV1.post("/deleteIterationById", auth_required=True)
def deleteIterationById(request: Request):
    data = request.json()
    service_iteration_id = data["service_iteration_id"]
    user_id = userGetUserIdByAccessToken(request=request)
    with session() as db:
        res = serviceDeleteIterationById(
            db=db,
            service_iteration_id=service_iteration_id,
            user_id=user_id,
        )
    return res


# 彻底删除服务（包括所有历史版本）
@serviceRouterV1.post("/deleteServicePermanentlyById", auth_required=True)
def deleteServicePermanentlyById(request: Request):
    data = request.json()
    id = data["id"]
    user_id = userGetUserIdByAccessToken(request=request)
    with session() as db:
        res = serviceDeleteServicePermanentlyById(db=db, id=id, user_id=user_id)
    return res


# ---- ⚠️ 以下为service迭代流程相关路由 ----
@serviceRouterV1.get("/getIterationById", auth_required=True)
def getIterationById(request: Request):
    id = request.query_params.get("id", None)
    if not id:
        return Response(
            status_code=400,
            description="id is required",
            headers={},
        )
    user_id = userGetUserIdByAccessToken(request=request)
    with session() as db:
        res = serviceGetServiceIterationById(
            db=db,
            id=int(id),
            user_id=user_id,
        )
    return res


# 发起service迭代流程
@serviceRouterV1.post("/startIteration", auth_required=True)
def startIteration(request: Request):
    data = request.json()
    service_id = data["service_id"]
    user_id = userGetUserIdByAccessToken(request=request)
    with session() as db:
        res = serviceStartIteration(db=db, service_id=service_id, user_id=user_id)
    return res


# 完成service迭代流程，service版本更新
@serviceRouterV1.post("/commitIteration", auth_required=True)
async def commitIteration(request: Request):
    data = request.json()
    service_iteration_id = data["service_iteration_id"]
    new_version = data["new_version"]
    user_id = userGetUserIdByAccessToken(request=request)
    with session() as db:
        res = await serviceCommitIteration(
            db=db,
            service_iteration_id=service_iteration_id,
            new_version=new_version,
            user_id=user_id,
        )
    return res


# 通过 service_iteration_id 修改 service description
@serviceRouterV1.post("/updateDescription", auth_required=True)
def updateDescription(request: Request):
    data = request.json()
    service_iteration_id = data["service_iteration_id"]
    description = data["description"]
    user_id = userGetUserIdByAccessToken(request=request)
    with session() as db:
        res = serviceUpdateDescription(
            db=db,
            service_iteration_id=service_iteration_id,
            description=description,
            user_id=user_id,
        )
    return res


# 导出openapi
@serviceRouterV1.get("/exportOpenapiByUuidAndVersion", auth_required=True)
def exportOpenapiByUuidAndVersion(request: Request):
    service_uuid = request.query_params.get("service_uuid", None)
    version = request.query_params.get("version", None)
    if not service_uuid or not version:
        return Response(
            status_code=400,
            description="service_uuid and version are required",
            headers={},
        )
    user_id = userGetUserIdByAccessToken(request=request)
    with session() as db:
        res = serviceExportOpenapiByUuidAndVersion(
            db=db,
            service_uuid=service_uuid,
            version=version,
            user_id=user_id,
        )
    return res
