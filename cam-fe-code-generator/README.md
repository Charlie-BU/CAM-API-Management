# cam-fe-code-generator

`cam-fe-code-generator` 是 CAM 的 npm CLI。它从 CAM 后端拉取指定 Service 的 API 定义与参数结构，生成 TypeScript 类型、可注入请求实现的 Service Class，以及 axios/fetch 使用示例。

> 该包依赖可访问的 CAM 后端和具有相应 Service 权限的账号；它不是 OpenAPI 文件生成器。

## 安装

```bash
npm install -g cam-fe-code-generator
```

也可在项目中安装：

```bash
npm install -D cam-fe-code-generator
npx cam --help
```

## 使用流程

```bash
# 1. 登录 CAM；交互式输入用户名和密码
cam login

# 2. 在业务项目根目录初始化配置
cam init

# 3. 添加需要生成的服务
cam add user-service:team/user/service@latest

# 4. 拉取接口定义并生成代码
cam update
```

`cam add` 的格式为 `名称:service_uuid@版本`：

- `名称` 用作输出子目录名称，必须是合法文件名；
- `service_uuid` 是 CAM 中的 Service 唯一标识；
- `版本` 可以是 `latest` 或 `x.y.z`。

其他命令：

```bash
cam whoami                 # 查看当前本地登录用户
cam logout                 # 清除本地登录态
cam remove user-service    # 从当前项目配置中移除服务并重新生成
```

## 配置与产物

`cam init` 会在当前目录创建 `cam.config.json`：

```json
{
  "services": {},
  "outDir": "src/cam-auto-generate",
  "generateConfig": {}
}
```

运行 `cam update`（以及成功的 `cam add` / `cam remove`）会清空并重建 `outDir`，因此不要在生成目录中手写业务代码。每个已配置服务会生成：

```text
src/cam-auto-generate/
  <服务名称>/
    index.ts          # Service Class：每个 API 对应一个方法
    namespaces.ts     # 请求/响应 TypeScript 类型
  request-demo.ts     # axios / fetch 接入示例
```

生成的 Service Class 不绑定网络库：通过构造函数传入 `baseURL` 与 `request` 即可接入现有的 axios 实例、fetch 封装、重试或埋点能力。`request-demo.ts` 给出了 axios 和 fetch 的最小示例。

登录 token 与用户摘要保存在用户主目录的 `~/.camrc`，文件写入权限为 `0600`。不要共享该文件或将其提交到版本控制。

## 服务端地址

当前 CLI 的服务端地址定义在 `src/request/index.ts` 的 `BASE_URL`。私有部署或本地联调时，请在发布前将其改为目标 CAM API 根地址并重新构建；修改后应验证登录、拉取 Service 和生成代码三条链路。

## 本地开发

前置条件：Node.js（建议 LTS）与 npm。

```bash
npm install
npm run build

# 在当前仓库直接验证编译后的 CLI
node dist/cli/index.js --help

# 可选：以全局命令方式联调
npm link
cam --help
```

`npm run build` 会先从 `package.json` 写入版本常量，再将 TypeScript 编译到 `dist/`。构建产物同时包含 CommonJS 入口、命令行入口和类型声明。

## 发布 npm

```bash
npm run build
npm pack --dry-run
npm version patch  # 或 minor / major
npm publish
```

`prepublishOnly` 会在 `npm publish` 前再次执行构建，发布包仅包含 `dist/` 与 npm 默认包含的元数据文件。发布前请确认：版本号符合语义化版本、`BASE_URL` 指向正确环境、生成器能处理目标 API 合同，并且 npm 账号拥有包名发布权限。

## 开发约定

- CLI 命令注册在 `src/cli/`，远端调用放在 `src/services/apis/`，生成逻辑放在 `src/services/code-generate/`。
- 类型映射和模板改动必须以 CAM 后端的参数模型为准，特别关注嵌套 object、object 数组、可选字段与历史版本草稿。
- 不要编辑生成目录作为修复手段；应修改模板或生成器并重新运行 `cam update`。
- 当前 `test` 脚本尚未提供自动化测试；拆库后建议优先为命令解析、参数树类型生成和端到端拉取流程补齐测试。

## 许可证

当前包元数据标记为 `ISC`。拆库发布前请在根目录提供对应的 `LICENSE` 文件并确认与团队政策一致。
