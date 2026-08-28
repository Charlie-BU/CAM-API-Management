import type {
    AddApiRequest,
    ApiReqParamInput,
    ApiRespParamInput,
    BaseResponse,
} from "@/services/api/types";

export type AiAddApiInput = Omit<AddApiRequest, "service_iteration_id">;

export interface AiApiProposal {
    add_api: AiAddApiInput;
    req_params: ApiReqParamInput[];
    resp_params: ApiRespParamInput[];
}

export interface AiMissingFieldsProposal {
    missing_fields: Array<"method" | "path">;
}

export interface AiDuplicateApiProposal {
    duplicate_api: {
        method: string;
        path: string;
    };
    message: string;
}

export type GenerateApiProposalResult =
    | AiApiProposal
    | AiMissingFieldsProposal
    | AiDuplicateApiProposal;

export interface GenerateApiProposalResponse extends BaseResponse {
    proposal?: GenerateApiProposalResult;
}
