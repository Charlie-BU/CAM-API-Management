import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";
import { fileURLToPath, URL } from "node:url";

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
    const env = loadEnv(mode, process.cwd(), "VITE_");
    const PORT = Number(env.VITE_FE_PORT) || 9000;
    const cloudMaterialsPath = fileURLToPath(
        new URL("./cloud-materials-common/@cloud-materials/common", import.meta.url)
    );

    return {
        plugins: [react()],
        resolve: {
            alias: {
                "@": fileURLToPath(new URL("./src", import.meta.url)),
                "@cloud-materials/common": cloudMaterialsPath,
            },
            dedupe: ["react", "react-dom"],
        },
        server: {
            port: PORT,
        },
    };
});
