// service层：只关心http请求，不关心业务逻辑
import { api } from "@/request";
import type {
    ServiceListResponse,
    GetServiceByIdResponse,
    GetServiceByUuidAndVersionResponse,
    GetAllVersionsByUuidResponse,
    CreateNewServiceRequest,
    CreateNewServiceResponse,
    GetAllDeletedServicesByUserIdResponse,
    DeleteServiceByIdRequest,
    DeleteServiceByIdResponse,
    RestoreServiceByIdRequest,
    RestoreServiceByIdResponse,
    DeleteIterationByIdRequest,
    DeleteIterationByIdResponse,
    GetIterationByIdResponse,
    StartIterationRequest,
    StartIterationResponse,
    CommitIterationRequest,
    CommitIterationResponse,
    UpdateDescriptionRequest,
    UpdateDescriptionResponse,
    GetAllServicesResponse,
    AddOrRemoveServiceMaintainerByIdRequest,
    AddOrRemoveServiceMaintainerByIdResponse,
    IsServiceMaintainerRequest,
    IsServiceMaintainerResponse,
    ExportOpenapiByUuidAndVersionResponse,
} from "./types";

const prefix = "/v1/service";

// 获取当前登录用户的所有最新版本服务列表
export const GetMyNewestServices = async (
    page_size?: number,
    current_page?: number
) => {
    return api.get<ServiceListResponse>(
        `${prefix}/getHisNewestServicesByOwnerId`,
        { page_size, current_page, is_my_services: true }
    );
};

// 获取当前登录用户的所有维护服务列表
export const GetMyMaintainedServices = async (
    page_size?: number,
    current_page?: number
) => {
    return api.get<ServiceListResponse>(
        `${prefix}/getHisMaintainedServicesByUserId`,
        { page_size, current_page }
    );
};

// 获取所有服务（包含已删除服务）
export const GetAllServices = async (
    page_size?: number,
    current_page?: number
) => {
    return api.get<GetAllServicesResponse>(`${prefix}/getAllServices`, {
        page_size,
        current_page,
    });
};

// 通过 owner_id 获取所有最新版本服务
export const GetHisNewestServicesByOwnerId = async (
    owner_id: number,
    page_size?: number,
    current_page?: number
) => {
    return api.get<ServiceListResponse>(
        `${prefix}/getHisNewestServicesByOwnerId`,
        { page_size, current_page, is_my_services: false, owner_id }
    );
};

// 通过服务id获取服务详情
export const GetServiceById = async (id: number) => {
    return api.get<GetServiceByIdResponse>(`${prefix}/getServiceById`, { id });
};

// 通过 service_uuid 和 version 获取服务详情
export const GetServiceByUuidAndVersion = async (
    service_uuid: string,
    version: string
) => {
    return api.get<GetServiceByUuidAndVersionResponse>(
        `${prefix}/getServiceByUuidAndVersion`,
        { service_uuid, version }
    );
};

// 通过 service_uuid 获取全部版本号
export const GetAllVersionsByUuid = async (service_uuid: string) => {
    return api.get<GetAllVersionsByUuidResponse>(
        `${prefix}/getAllVersionsByUuid`,
        { service_uuid }
    );
};

// 创建新服务
export const CreateNewService = async (data: CreateNewServiceRequest) => {
    return api.post<CreateNewServiceResponse>(
        `${prefix}/createNewService`,
        data
    );
};

// 获取当前用户的全部已删除服务
export const GetAllDeletedServicesByUserId = async (
    page_size?: number,
    current_page?: number
) => {
    return api.get<GetAllDeletedServicesByUserIdResponse>(
        `${prefix}/getAllDeletedServicesByUserId`,
        { page_size, current_page }
    );
};

// 通过服务id删除服务（最新版本），历史版本不动
export const DeleteServiceById = async (data: DeleteServiceByIdRequest) => {
    return api.post<DeleteServiceByIdResponse>(
        `${prefix}/deleteServiceById`,
        data
    );
};

// 通过服务id还原服务（还原最新版本），历史版本不动
export const RestoreServiceById = async (data: RestoreServiceByIdRequest) => {
    return api.post<RestoreServiceByIdResponse>(
        `${prefix}/restoreServiceById`,
        data
    );
};

// 通过 service_iteration_id 删除服务历史版本
export const DeleteIterationById = async (data: DeleteIterationByIdRequest) => {
    return api.post<DeleteIterationByIdResponse>(
        `${prefix}/deleteIterationById`,
        data
    );
};

// 通过服务id彻底删除服务（最新版本），历史版本也会删除
export const PermanentlyDeleteServiceById = async (data: DeleteServiceByIdRequest) => {
    return api.post<DeleteServiceByIdResponse>(
        `${prefix}/deleteServicePermanentlyById`,
        data
    );
};

// 通过id获取服务迭代详情
export const GetIterationById = async (id: number) => {
    return api.get<GetIterationByIdResponse>(`${prefix}/getIterationById`, {
        id,
    });
};

// 发起 service 迭代流程
export const StartIteration = async (data: StartIterationRequest) => {
    return api.post<StartIterationResponse>(`${prefix}/startIteration`, data);
};

// 提交 service 迭代流程，更新版本
export const CommitIteration = async (data: CommitIterationRequest) => {
    return api.post<CommitIterationResponse>(`${prefix}/commitIteration`, data);
};

// 更新 service description（通过 service_iteration_id）
export const UpdateDescription = async (data: UpdateDescriptionRequest) => {
    return api.post<UpdateDescriptionResponse>(
        `${prefix}/updateDescription`,
        data
    );
};

// 通过candidate_id和service_id判断是否为服务的维护者
export const IsServiceMaintainer = async (data: IsServiceMaintainerRequest) => {
    return api.get<IsServiceMaintainerResponse>(
        `${prefix}/isServiceMaintainer`,
        {
            ...data,
        }
    );
};

// 通过服务id添加或移除maintainer
export const AddOrRemoveServiceMaintainerById = async (
    data: AddOrRemoveServiceMaintainerByIdRequest
) => {
    return api.post<AddOrRemoveServiceMaintainerByIdResponse>(
        `${prefix}/addOrRemoveServiceMaintainerById`,
        data
    );
};

// 导出openapi
export const ExportOpenapiByUuidAndVersion = async (
    service_uuid: string,
    version: string
) => {
    return api.get<ExportOpenapiByUuidAndVersionResponse>(
        `${prefix}/exportOpenapiByUuidAndVersion`,
        { service_uuid, version }
    );
};

