import { ApiOption } from "../../templates/service-class";
import { capitalizeFirstLetter } from "../../utils/utils";
import {
    ApiDetail,
    ApiDraftDetail,
    ParamLocation,
    RequestParam,
    RequestParamDraft,
    ResponseParam,
    ResponseParamDraft,
} from "../apis/api/types";

interface GeneratedCode {
    namespaces: string[];
    apiOption: ApiOption;
}

const tsTypeMap = (type: string, arrayChildType?: string | null): string => {
    switch (type) {
        case "int":
        case "float":
        case "double":
        case "long":
            return "number";
        case "string":
        case "text":
            return "string";
        case "boolean":
        case "bool":
            return "boolean";
        case "array":
        case "list":
            if (arrayChildType) {
                return `${tsTypeMap(arrayChildType)}[]`;
            }
            return "any[]";
        case "object":
        case "map":
            return "any"; // Complex objects are handled by creating new interfaces
        default:
            return "any";
    }
};

const formatInterfaceFieldName = (name: string): string =>
    name.includes("-") ? JSON.stringify(name) : name;

const generateInterface = (
    name: string,
    params: any[],
    _parentName: string = ""
): string[] => {
    const interfaces: string[] = [];
    const fields: string[] = [];
    const interfaceName = `${capitalizeFirstLetter(name)}`;

    params.forEach((param) => {
        let type = tsTypeMap(param.type, param.array_child_type);
        const fieldName = param.name;
        const formattedFieldName = formatInterfaceFieldName(fieldName);
        const isOptional = !param.required;
        const comment = param.description
            ? `  /** ${param.description} */\n`
            : "";

        if (
            param.type === "object" &&
            param.children_params &&
            param.children_params.length > 0
        ) {
            // 添加interfaceName前缀防止命名冲突
            const childInterfaceName = `${interfaceName}${capitalizeFirstLetter(
                fieldName
            )}`;
            const childInterfaces = generateInterface(
                childInterfaceName,
                param.children_params,
                interfaceName
            );
            interfaces.push(...childInterfaces);
            type = childInterfaceName; // Use the generated interface name
        } else if (
            param.type === "array" &&
            param.array_child_type === "object" &&
            param.children_params &&
            param.children_params.length > 0
        ) {
            // Handle array of objects if needed
            // 添加interfaceName前缀防止命名冲突
            const childInterfaceName = `${interfaceName}${capitalizeFirstLetter(
                fieldName
            )}Item`;
            const childInterfaces = generateInterface(
                childInterfaceName,
                param.children_params,
                interfaceName
            );
            interfaces.push(...childInterfaces);
            type = `${childInterfaceName}[]`;
        }

        fields.push(
            `${comment}  ${formattedFieldName}${isOptional ? "?" : ""}: ${type};`
        );
    });

    const currentInterface = `export interface ${interfaceName} {\n${fields.join(
        "\n"
    )}\n}`;
    interfaces.push(currentInterface);

    return interfaces;
};

export const generateTSCode = (
    api: ApiDetail | ApiDraftDetail
): GeneratedCode => {
    const namespaces: string[] = [];
    let requestInterfaceName = "";
    let responseInterfaceName = "";

    // 5类请求参数分别生成的interface名和所有类别响应参数生成的interface名
    let reqBodyInterfaceName = "";
    let reqQueryInterfaceName = "";
    let reqPathInterfaceName = "";
    let reqHeaderInterfaceName = "";
    let reqCookieInterfaceName = "";
    let respInterfaceNames: string[] = [];

    // 1. Generate Request Interface (Query, Body, etc.)
    const requestParams =
        api.request_params_by_location ||
        ({} as
            | Record<ParamLocation, RequestParam[]>
            | Record<ParamLocation, RequestParamDraft[]>);

    for (const location of Object.keys(requestParams)) {
        const params = requestParams[location as ParamLocation];
        if (params.length > 0) {
            requestInterfaceName = `${capitalizeFirstLetter(
                api.name
            )}${capitalizeFirstLetter(location)}Request`;
            const reqInterfaces = generateInterface(
                requestInterfaceName,
                params
            );

            switch (location) {
                case "body":
                    reqBodyInterfaceName = requestInterfaceName;
                    break;
                case "query":
                    reqQueryInterfaceName = requestInterfaceName;
                    break;
                case "path":
                    reqPathInterfaceName = requestInterfaceName;
                    break;
                case "header":
                    reqHeaderInterfaceName = requestInterfaceName;
                    break;
                case "cookie":
                    reqCookieInterfaceName = requestInterfaceName;
                    break;
            }
            namespaces.push(...reqInterfaces);
        }
    }

    // 2. Generate Response Interface
    const responseParams =
        api.response_params_by_status_code ||
        ({} as
            | Record<number, ResponseParam[]>
            | Record<number, ResponseParamDraft[]>);

    for (const statusCode of Object.keys(responseParams)) {
        const params = responseParams[Number(statusCode)];
        if (!params) {
            continue;
        }
        if (params.length > 0) {
            responseInterfaceName = `${capitalizeFirstLetter(
                api.name
            )}${statusCode}Response`;
            const resInterfaces = generateInterface(
                responseInterfaceName,
                params
            );
            respInterfaceNames.push(responseInterfaceName);
            namespaces.push(...resInterfaces);
        }
    }

    // 3. Generate Index Preparation
    const apiOption: ApiOption = {
        functionName: `${capitalizeFirstLetter(api.name)}${api.method}`,
        apiMethod: api.method,
        apiPath: api.path,
        apiDescription: api.description || "",
        reqBodyInterfaceName,
        reqQueryInterfaceName,
        reqPathInterfaceName,
        reqHeaderInterfaceName,
        reqCookieInterfaceName,
        respInterfaceNames,
        reqBodyFields:
            api.request_params_by_location?.body.map((param) => param.name) ||
            [],
        reqQueryFields:
            api.request_params_by_location?.query.map((param) => param.name) ||
            [],
        reqPathFields:
            api.request_params_by_location?.path.map((param) => param.name) ||
            [],
        reqHeaderFields:
            api.request_params_by_location?.header.map((param) => param.name) ||
            [],
        reqCookieFields:
            api.request_params_by_location?.cookie.map((param) => param.name) ||
            [],
    };

    return {
        namespaces,
        apiOption,
    };
};
