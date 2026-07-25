import { capitalizeFirstLetter } from "../utils/utils";

export const requestDemoCode = (demoServiceName: string) => {
    const demoClassName = capitalizeFirstLetter(`${demoServiceName}Service`);
    return `
// This is a demo request code for how to use auto generated service class.
// You can also use your own request instance like axios or fetch.

import axios, { type AxiosRequestConfig } from "axios"; // Install axios if you haven't
import ${demoClassName} from "./${demoServiceName}/index";

const BASE_URL = "http://localhost:3000"; // Change to the actual base URL

export const demoServiceForAxios = new ${demoClassName}<AxiosRequestConfig>({
    baseURL: BASE_URL,
    request: (config, _options) =>
        axios.request({ ...config }).then((res) => res.data),
});

export const demoServiceForFetch = new ${demoClassName}<RequestInit>({
    baseURL: BASE_URL,
        request: (config, _options) =>
            fetch(config.url, { ...config }).then((res) => res.json()),
});
`;
};
