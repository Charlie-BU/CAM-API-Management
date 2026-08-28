import { api } from "@/request";
import type { GenerateApiProposalResponse } from "./types";

const prefix = "/v1/ai";

export const GenerateApiProposal = async (
    service_iteration_id: number,
    prompt: string,
) => {
    return api.post<GenerateApiProposalResponse>(
        `${prefix}/generateApiProposal`,
        { service_iteration_id, prompt },
    );
};
