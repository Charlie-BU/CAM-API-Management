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
    const nativeMapShimPath = fileURLToPath(
        new URL("./src/shims/babel-runtime-map.ts", import.meta.url)
    );

    return {
        plugins: [react()],
        resolve: {
            alias: {
                "@": fileURLToPath(new URL("./src", import.meta.url)),
                "@cloud-materials/common": cloudMaterialsPath,
                // `@storage-fe/formily-arco` 会引入这个 core-js-pure 包装模块。
                // Vite 在生产构建时转换 CommonJS，可能将其默认导出转换为不可构造的对象。
                // 现代浏览器已原生支持 Map，因此这里将该模块解析为原生 Map 构造函数。
                "@babel/runtime-corejs3/core-js-stable/map": nativeMapShimPath,
            },
            dedupe: ["react", "react-dom"],
        },
        server: {
            port: PORT,
        },
    };
});
