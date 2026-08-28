from robyn import SubRouter
from robyn.authentication import BearerGetter
from robyn.robyn import Request, Response

from authentication import AuthHandler
from database.database import session
from services.ai_service.ai import aiGenerateApiProposal
from services.user import userGetUserIdByAccessToken


aiRouterV1 = SubRouter(__file__, prefix="/v1/ai")


@aiRouterV1.exception
def handleException(error):
    return Response(status_code=500, description=f"error msg: {error}", headers={})


aiRouterV1.configure_authentication(AuthHandler(token_getter=BearerGetter()))


# 智能生成 API 草稿
@aiRouterV1.post("/generateApiProposal", auth_required=True)
def generateApiProposal(request: Request):
    data = request.json()
    service_iteration_id = data["service_iteration_id"]
    prompt = data["prompt"]
    user_id = userGetUserIdByAccessToken(request)
    with session() as db:
        return aiGenerateApiProposal(
            db=db,
            serviceIterationId=int(service_iteration_id),
            userId=user_id,
            prompt=prompt,
        )
