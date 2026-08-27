# 本地离线使用 @cloud-materials/common

本项目不通过 pnpm 安装 `@cloud-materials/common`，因此不需要访问字节内网。
使用离线仓库提供的安装脚本，将组件库 clone 到本项目根目录：

```bash
bash /path/to/cloud-materials-common/setup-consumer.sh .
```

也可以手动执行：

```bash
git clone git@github.com:Charlie-BU/cloud-materials-common.git ./cloud-materials-common
```

生成的 `./cloud-materials-common/` 已加入 `.gitignore`，不会被提交到消费项目。
Vite 在 `vite.config.ts` 中通过 alias 从固定目录读取组件库：

```ts
import { fileURLToPath, URL } from "node:url";

const cloudMaterialsPath = fileURLToPath(
    new URL("./cloud-materials-common/@cloud-materials/common", import.meta.url)
);

export default defineConfig({
    resolve: {
        alias: {
            "@cloud-materials/common": cloudMaterialsPath,
        },
        dedupe: ["react", "react-dom"],
    },
});
```

`tsconfig.app.json` 同时配置类型和子路径解析：

```json
{
  "compilerOptions": {
    "baseUrl": ".",
    "paths": {
      "@cloud-materials/common": [
        "cloud-materials-common/@cloud-materials/common"
      ],
      "@cloud-materials/common/*": [
        "cloud-materials-common/@cloud-materials/common/*"
      ]
    }
  }
}
```

组件库路径采用固定的项目根目录约定，不需要配置环境变量。

随后照常执行：

```bash
pnpm install
pnpm dev
```

Vite 会从该离线目录解析组件库及其子路径，并强制与本项目共用 React 18。
