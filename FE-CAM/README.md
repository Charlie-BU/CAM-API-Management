# FE-CAM 前端

CAM 的 Web 管理界面，用于登录、管理 Service、维护 API 分类与参数、发起/提交版本迭代，以及获取 AI API 草稿建议。前端只负责交互与展示，数据和权限以 CAM 后端 API 为准。

## 技术栈

React 18、TypeScript、Vite、React Router、Zustand、Axios、i18next、Less；包管理器使用 pnpm。

## 前置条件

- Node.js：建议使用当前 Vite 7 支持的 LTS 版本。
- pnpm：仓库包含 `pnpm-lock.yaml`，请优先使用 pnpm。
- 已启动的 CAM 后端服务。
- UI 依赖 `@cloud-materials/common`。当前仓库提供 `setup-consumer.sh` 以获取配套的离线依赖仓库；拆库时建议将其改为正常的包依赖或保留该初始化步骤。

## 快速开始

```bash
# 安装依赖
pnpm install

# 若本地没有 @cloud-materials/common，按需执行（参数为消费项目根目录）
./setup-consumer.sh .

# 在项目根目录创建 .env.local 并配置环境变量

# 启动开发服务
pnpm dev
```

在 `.env.local` 中配置后端地址：

```ini
VITE_API_BASE_URL=http://localhost:1024
# 可选；当前开发服务器默认使用 9000
VITE_FE_PORT=9000
```

`VITE_API_BASE_URL` 是必填项；请填写 API 服务的根地址，不要额外拼接 `/v1`。Vite 环境变量会被打进浏览器产物，切勿放入任何密钥。

## 常用命令

```bash
pnpm dev       # 本地开发
pnpm lint      # ESLint 检查
pnpm build     # TypeScript 检查并构建生产产物到 dist/
pnpm preview   # 本地预览生产构建
```

## 功能范围

- 注册、登录、个人资料和密码修改；登录 token 保存于浏览器 `localStorage`。
- Service 列表、创建、删除/恢复、所有者与维护者视图。
- Service 迭代：查看历史版本、创建迭代、编辑描述与 API 草稿、提交版本。
- API 分类管理、API 详情与请求/响应参数树编辑。
- 通过后端 AI 接口生成 API 草稿建议。
- 中英文界面，本地化文件位于 `src/i18n/locales/`。

## 目录结构

```text
src/
  components/             # 页面与业务 UI：用户、Service、API、布局
  hooks/                  # useUser、useService、useApi 等状态/业务 Hook
  services/               # 按 user/service/api/ai 划分的 API 调用与类型
  request/                # Axios 实例、Bearer token 与统一错误处理
  i18n/                   # 国际化初始化与语言包
  router.tsx               # 路由和登录保护
  main.tsx                 # React 入口
public/                    # 静态资源
```

## 与后端的集成

所有 API 请求经 `src/request/index.ts` 发送；它会读取 `cam_access_token` 并追加 `Authorization: Bearer <token>`。当后端返回 401 或网络错误时，客户端会清理登录态并刷新页面。

接口路径和类型定义按领域收敛在 `src/services/`。新增或调整后端合同（字段、错误语义、路由）时，应同时更新对应的 `types.ts` 与调用封装，再更新 UI；避免在组件里直接拼接请求。

## 部署

执行 `pnpm build` 后部署 `dist/`。部署环境需要：

- 以构建时环境变量注入正确的 `VITE_API_BASE_URL`；
- 对 SPA 路由配置回退到 `index.html`；
- 在后端 `CORS_ORIGINS` 中放行此前端的实际访问来源。

## 开发约定

- 保持组件、服务层、请求层分离；复用 `src/services/` 和 `src/request/` 的封装。
- 文案需要同时维护 `zh-CN.json` 与 `en-US.json`。
- 不要在前端代码、环境变量或日志中保存服务端密钥；浏览器端仅可使用公开配置。
- 构建、lint 通过后再提交；新增关键交互时补充对应的测试方案。

## 许可证

仓库拆分时请在根目录补充并明确适用的 `LICENSE`。
