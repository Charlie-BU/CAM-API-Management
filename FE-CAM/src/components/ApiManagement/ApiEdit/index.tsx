import React, { useEffect, useRef, useState } from "react";
import {
    Button,
    Space,
    Typography,
    Divider,
    Form,
    Message,
    Spin,
} from "@cloud-materials/common";
import sharedStyles from "../index.module.less";
import BriefInfoEdit from "./BriefInfoEdit";
import {
    transformReqParamsToApiInput,
    transformRespParamsToApiInput,
    transformAiReqParamsToFormValues,
    transformAiRespParamsToFormValues,
} from "./utils";
import type {
    ApiDetail,
    ApiDraftDetail,
    ApiReqParamInput,
    ApiRespParamInput,
    ParamLocation,
    UpdateApiByApiDraftIdRequest,
    UpdateApiByApiDraftIdResponse,
} from "@/services/api/types";
import RequestParamsEdit from "./RequestParamsEdit";
import ResponseParamsEdit from "./ResponseParamsEdit";
import { handleConfirm } from "@/utils";
import BlankPage from "@/components/BlankPage";

// 把请求参数tabs相关逻辑提到本层，便于根据apiDetail处理首个activeTab
export const tabs = [
    { key: "query", title: "Query 参数" },
    { key: "path", title: "Path 参数" },
    { key: "body", title: "Body 参数" },
    { key: "header", title: "Header 参数" },
    { key: "cookie", title: "Cookie 参数" },
];

interface ApiEditHandlers {
    handleSaveApiDraft: (
        data: Omit<UpdateApiByApiDraftIdRequest, "service_iteration_id">
    ) => Promise<UpdateApiByApiDraftIdResponse>;
    handleCopyApi: (apiDraftId: number) => Promise<void>;
    handleDeleteApi: (apiDraftId: number) => Promise<void>;
}

interface ApiEditProps {
    loading: boolean;
    apiDetail: ApiDetail | ApiDraftDetail;
    aiPrefill?: {
        apiDraftId: number;
        reqParams: ApiReqParamInput[];
        respParams: ApiRespParamInput[];
    } | null;
    handlers: ApiEditHandlers;
}

const ApiEdit: React.FC<ApiEditProps> = ({
    loading,
    apiDetail,
    aiPrefill,
    handlers: { handleSaveApiDraft, handleCopyApi, handleDeleteApi },
}) => {
    const [form] = Form.useForm();
    const [editLoading, setEditLoading] = useState(false);
    const [isDraft, setIsDraft] = useState(false);
    const [reqParamsActiveTab, setReqParamsActiveTab] = useState("query");
    const [rejectSubmit, setRejectSubmit] = useState(false); // 是否由于表单填写不全拒绝提交
    const appliedAiPrefillIdRef = useRef<number | null>(null);

    const getFirstTabWithValue = () => {
        if (!apiDetail.request_params_by_location) {
            return "query";
        }
        for (const tab of tabs) {
            if (
                apiDetail.request_params_by_location[tab.key as ParamLocation]
                    .length > 0
            ) {
                return tab.key;
            }
        }
        return "query";
    };

    useEffect(() => {
        form.setFieldsValue(apiDetail);
        setIsDraft(false);
        setReqParamsActiveTab(getFirstTabWithValue());
    }, [apiDetail, form]);

    useEffect(() => {
        if (
            !aiPrefill ||
            apiDetail.id !== aiPrefill.apiDraftId ||
            appliedAiPrefillIdRef.current === aiPrefill.apiDraftId
        ) {
            return;
        }
        const requestParamsByLocation = transformAiReqParamsToFormValues(
            aiPrefill.reqParams,
        );
        const responseParamsByStatusCode = transformAiRespParamsToFormValues(
            aiPrefill.respParams,
        );
        form.setFieldsValue({
            ...apiDetail,
            request_params_by_location: requestParamsByLocation,
            response_params_by_status_code: responseParamsByStatusCode,
        });
        const firstActiveTab = tabs.find(
            (tab) => requestParamsByLocation[tab.key as ParamLocation].length,
        );
        setReqParamsActiveTab(firstActiveTab?.key || "query");
        setIsDraft(true);
        appliedAiPrefillIdRef.current = aiPrefill.apiDraftId;
    }, [aiPrefill, apiDetail, form]);

    // 提交本次apiDraft改动
    const handleSubmit = async () => {
        if (rejectSubmit) {
            return;
        }
        const values = await form.validate();
        setEditLoading(true);

        const req_params: ApiReqParamInput[] = transformReqParamsToApiInput(
            values.request_params_by_location
        );
        // 检查是否有请求参数name为空
        if (req_params.some((param) => !param.name)) {
            Message.warning("存在名称为空的请求参数");
            setEditLoading(false);
            return;
        }
        // 检查是否有Path参数
        const hasPathParams = req_params.some(
            (param) => param.location === "path"
        );
        if (hasPathParams) {
            // 检查apiPath是否包含{param}
            const apiPath = values.path;
            const allPathParams = req_params.filter(
                (param) => param.location === "path"
            );
            // path参数不能为选填
            if (allPathParams.some((param) => param.required === false)) {
                Message.warning("Path 参数不能为选填");
                setEditLoading(false);
                return;
            }
            const allPathParamsShouldInPath = allPathParams.map(
                (param) => `{${param.name}}`
            );

            if (
                !allPathParamsShouldInPath.every((param) =>
                    apiPath.includes(param)
                )
            ) {
                Message.warning(
                    "Path 参数必须用花括号包含在路径中，如：{param}"
                );
                setEditLoading(false);
                return;
            }
        }
        const resp_params: ApiRespParamInput[] = transformRespParamsToApiInput(
            values.response_params_by_status_code
        );
        // 检查是否有响应参数name为空
        if (resp_params.some((param) => !param.name)) {
            Message.warning("存在名称为空的响应参数");
            setEditLoading(false);
            return;
        }

        const data: Omit<UpdateApiByApiDraftIdRequest, "service_iteration_id"> =
            {
                api_draft_id: apiDetail.id,
                name: values.name,
                method: values.method,
                path: values.path,
                description: values.description,
                level: values.level || "P2",
                req_params,
                resp_params,
            };
        try {
            const res = await handleSaveApiDraft(data);
            setIsDraft(false);
            Message.success(res.message || "API 保存成功");
        } catch (error) {
            const msg = error instanceof Error ? error.message : "API 保存失败";
            Message.error(msg);
        }
        setEditLoading(false);
    };

    if (!apiDetail || Object.keys(apiDetail).length === 0) {
        return <BlankPage message="暂无 API，请点击左侧 ··· 创建 API" />;
    }

    return (
        <div className={sharedStyles.content}>
            <Spin size={40} loading={loading}>
                <div className={sharedStyles.header}>
                    <Typography.Title heading={5}>
                        Service 迭代
                    </Typography.Title>
                    <Space>
                        <Button
                            type="default"
                            status="success"
                            onClick={handleSubmit}
                            loading={editLoading}
                            disabled={!isDraft || rejectSubmit}
                        >
                            {isDraft ? "保存 API" : "当前 API 已保存"}
                        </Button>
                        <Button
                            type="default"
                            status="default"
                            onClick={() => handleCopyApi(apiDetail.id)}
                        >
                            复制 API
                        </Button>
                        <Button
                            type="default"
                            status="danger"
                            onClick={() =>
                                handleConfirm(
                                    () => handleDeleteApi(apiDetail.id),
                                    "删除",
                                    "确认删除当前 API？"
                                )
                            }
                        >
                            删除 API
                        </Button>
                    </Space>
                </div>
                <Form
                    form={form}
                    layout="vertical"
                    scrollToFirstError
                    initialValues={apiDetail}
                    onValuesChange={() => {
                        setIsDraft(true);
                    }}
                >
                    <BriefInfoEdit />
                    <Divider />
                    <RequestParamsEdit
                        reqParamsActiveTab={reqParamsActiveTab}
                        setReqParamsActiveTab={setReqParamsActiveTab}
                        setRejectSubmit={setRejectSubmit}
                    />
                    <Divider />
                    <ResponseParamsEdit setRejectSubmit={setRejectSubmit} />
                </Form>
            </Spin>
        </div>
    );
};

export default ApiEdit;
