import React, { useMemo, useState } from "react";
import styles from "./index.module.less";
import { useSearchParams } from "react-router-dom";
import { useThisService, useServiceIteration } from "@/hooks/useService";
import useApi from "@/hooks/useApi";
import Detail from "./Detail";
import Header from "./Header";
import ApiList from "./ApiList";
import ApiEdit from "./ApiEdit";
import { Layout, Spin } from "@cloud-materials/common";
import type { UserProfile } from "@/services/user/types";
import type { AiApiProposal } from "@/services/ai/types";
import { inIterationWarning } from "@/utils";

const ApiManagement: React.FC = () => {
    const [searchParams] = useSearchParams();
    const uuid = searchParams.get("uuid") || "";
    const {
        loading,
        versions,
        currentVersion,
        isLatest,
        serviceDetail,
        apiCategories,
        treeData,
        inIteration,
        iterationId,
        setCurrentVersion,
        handleAddCategory,
        handleUpdateApiCategory,
        handleDeleteCategory,
        checkIsServiceMaintainer,
        handleAddOrRemoveServiceMaintainerById,
        handleExportOpenAPI,
        handleStartIteration,
        handleCompleteIteration,
        exitIteration,
    } = useThisService(uuid);

    const serviceUuid = useMemo(() => {
        return "service_uuid" in serviceDetail
            ? serviceDetail.service_uuid
            : serviceDetail?.service?.service_uuid || "";
    }, [serviceDetail]);

    const personInCharge = useMemo(() => {
        return "owner" in serviceDetail
            ? (serviceDetail.owner as UserProfile)
            : "creator" in serviceDetail
            ? (serviceDetail.creator as UserProfile)
            : ({} as UserProfile);
    }, [serviceDetail]);

    // 用于控制当前 API 相关逻辑
    const [selectedApiId, setSelectedApiId] = useState<number>(-1);
    const [aiPrefill, setAiPrefill] = useState<{
        apiDraftId: number;
        reqParams: AiApiProposal["req_params"];
        respParams: AiApiProposal["resp_params"];
    } | null>(null);

    const { loading: apiLoading, apiDetail } = useApi(
        selectedApiId,
        inIteration ? false : isLatest // 如果在迭代中，则 isLatest 为false
    );

    const {
        loading: iterationLoading,
        iterationDetail,
        iterationTreeData,
        handleAddApi,
        handleSmartCreateApi,
        handleSaveApiDraft,
        handleCopyApi,
        handleDeleteApi,
    } = useServiceIteration(iterationId, apiCategories);

    const isLoading =
        loading ||
        !versions ||
        !serviceUuid ||
        !treeData ||
        treeData.length === 0;

    // 单独把loading抽离出来，为了让ApiList中Tree支持autoExpandParent
    // （autoExpandParent 仅在 Tree 第一次挂载的时候生效。如果数据是从远程获取，可以在数据获取完成后，再去渲染 Tree 组件）
    if (isLoading) {
        return (
            <div className={styles.loadingCenter}>
                <Spin dot />
            </div>
        );
    }

    return (
        <Layout className={styles.apiPage}>
            <Layout.Header>
                <Header
                    loading={loading}
                    serviceUuid={serviceUuid}
                    versions={versions}
                    isLatest={isLatest}
                    currentVersion={currentVersion}
                    personInCharge={personInCharge}
                    maintainers={
                        "maintainers" in serviceDetail
                            ? (serviceDetail.maintainers as UserProfile[])
                            : []
                    }
                    inIteration={inIteration}
                    handlers={{
                        setCurrentVersion: (v) =>
                            inIterationWarning(
                                () => {
                                    setSelectedApiId(-1);
                                    setCurrentVersion(v);
                                },
                                inIteration,
                                "reject"
                            ),
                        exitIteration,
                        checkIsServiceMaintainer,
                        handleAddOrRemoveServiceMaintainerById,
                        handleExportOpenAPI,
                    }}
                />
            </Layout.Header>
            <Layout style={{ position: "relative" }}>
                {/* 左侧 API 列表 */}
                <Layout.Sider className={styles.sidebar} width={300}>
                    <ApiList
                        inIteration={inIteration}
                        isLatest={isLatest}
                        treeData={
                            inIteration && iterationDetail
                                ? iterationTreeData
                                : treeData
                        }
                        selectedApiId={selectedApiId}
                        setSelectedApiId={(id) => {
                            setSelectedApiId(id);
                        }}
                        handlers={{
                            handleAddApi,
                            handleSmartCreateApi: () =>
                                handleSmartCreateApi(({ apiDraftId, proposal }) => {
                                    setAiPrefill({
                                        apiDraftId,
                                        reqParams: proposal.req_params,
                                        respParams: proposal.resp_params,
                                    });
                                    setSelectedApiId(apiDraftId);
                                }),
                            handleAddCategory,
                            handleUpdateApiCategory,
                            handleDeleteCategory,
                            handleStartIteration,
                            handleCompleteIteration,
                        }}
                    />
                </Layout.Sider>
                <Layout.Content style={{ marginLeft: 300 }}>
                    {inIteration && iterationDetail ? (
                        <ApiEdit
                            loading={iterationLoading || apiLoading}
                            apiDetail={apiDetail}
                            aiPrefill={aiPrefill}
                            handlers={{
                                handleSaveApiDraft,
                                handleCopyApi,
                                handleDeleteApi,
                            }}
                        />
                    ) : (
                        <Detail loading={apiLoading} apiDetail={apiDetail} />
                    )}
                </Layout.Content>
            </Layout>
        </Layout>
    );
};

export default ApiManagement;
