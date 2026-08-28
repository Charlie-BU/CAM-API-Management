import json
import os
from typing import Any

from openai import APIError, APIStatusError, OpenAI
from sqlalchemy.orm import Session

from services.ai_service.prompt import buildSystemMessage, buildUserMessage
from services.ai_service.utils import extractOutputText, parseJsonResponse, validateProposal
from services.utils import checkServiceIterationPermission


MAX_PROMPT_LENGTH = 8_000


def modelService(systemMessage: str, userMessage: str) -> str:
    """调用模型服务"""
    apiKey = os.getenv("ARK_API_KEY")
    baseUrl = os.getenv("ARK_BASE_URL_CN")
    model = os.getenv("ENDPOINT_ID")
    if not apiKey or not baseUrl or not model:
        raise RuntimeError("AI service is not configured")

    client = OpenAI(base_url=baseUrl, api_key=apiKey)
    response = client.responses.create(
        model=model,
        input=[
            {"role": "system", "content": systemMessage},
            {"role": "user", "content": userMessage},
        ],
    )
    return extractOutputText(response)


def aiGenerateApiProposal(
    db: Session, serviceIterationId: int, userId: int, prompt: str
) -> dict[str, Any]:
    """Generate and validate an API proposal without writing API data."""
    if not isinstance(prompt, str) or not prompt.strip():
        return {"status": -1, "message": "prompt is required"}
    if len(prompt) > MAX_PROMPT_LENGTH:
        return {"status": -2, "message": "prompt is too long"}

    checkResult = checkServiceIterationPermission(
        db=db, service_iteration_id=serviceIterationId, user_id=userId
    )
    if not checkResult["is_ok"]:
        return checkResult["error"]

    iteration = checkResult["service_iteration"]
    existingApis = [
        {"name": api.name, "method": api.method.value, "path": api.path}
        for api in iteration.api_drafts
    ]
    try:
        systemMessage = buildSystemMessage()
        userMessage = buildUserMessage(prompt.strip(), existingApis)
        
        proposal = parseJsonResponse(modelService(systemMessage, userMessage))
        proposal = validateProposal(proposal, existingApis)
        return {"status": 200, "message": "Generate API proposal success", "proposal": proposal}
    except (json.JSONDecodeError, ValueError) as error:
        return {"status": -4, "message": f"AI 返回结果不符合 API 合同：{error}"}
    except (APIStatusError, APIError, RuntimeError) as error:
        return {"status": -5, "message": f"AI 服务调用失败：{error}"}
    except Exception:
        return {"status": -6, "message": "AI 服务暂时不可用"}
