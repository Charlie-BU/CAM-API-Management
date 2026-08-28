# BE-CAM 后端服务

CAM（API Management）的后端服务，负责用户鉴权、服务与接口资产管理、版本迭代，以及 API 草稿的 AI 生成。它是管理台与 `cam-fe-code-generator` CLI 共同依赖的服务端事实来源。

## 功能

- 用户注册、登录、JWT 鉴权、个人资料查询与密码修改。
- Service 的创建、查询、软删除与恢复，以及基于 `service_uuid + version` 的历史版本读取。
- 以迭代为工作区管理 API 变更：创建草稿、编辑参数树、提交新版本。
- API 分类与 API 定义管理；请求参数按 `query`、`path`、`header`、`cookie`、`body` 组织，响应参数按状态码组织。
- 可选的 AI API 草稿建议能力（只生成并校验提案，不直接写库）。
- 面向前端和 CLI 的 JSON HTTP API，路由前缀为 `/v1/user`、`/v1/service`、`/v1/api`、`/v1/ai`。

## 技术栈

Python 3.13+、[Robyn](https://robyn.tech/)、SQLAlchemy、PostgreSQL、Alembic、`uv`、JWT（python-jose）。

## 快速开始

### 1. 准备依赖

安装 Python 3.13+、[uv](https://docs.astral.sh/uv/) 和可访问的 PostgreSQL 数据库。

```bash
uv sync
```

### 2. 配置环境变量

基于 `.env.example` 在项目根目录创建 `.env`（不要提交到仓库）。

首次启动会连接数据库并按当前 ORM 模型创建尚不存在的数据表。生产环境应先准备数据库备份与受控的迁移流程。

### 3. 启动

```bash
# 开发：热重载
uv run ./run-dev.sh

# 生产进程配置
uv run ./run-prod.sh
```

健康检查：`GET /` 返回 `OK`。

## 数据库迁移

修改 `database/models.py` 后，可生成并应用 Alembic 迁移：

```bash
uv run database/db-migrate.sh
```

执行前请审查自动生成的迁移内容；不要把生产库结构变更仅交给自动迁移决定。

## 核心模型与版本语义

`Service` 保存当前已发布版本；`ServiceIteration` 保存一次迭代及其草稿快照。启动迭代后，API 与参数会复制到 `ApiDraft`、`RequestParamDraft`、`ResponseParamDraft`；提交迭代后再同步回正式表并更新 Service 版本。这样，最新版本与历史版本均可按 `service_uuid + version` 读取。

受保护接口使用 `Authorization: Bearer <access_token>`。`L0` 为管理员级别；普通用户只能操作其拥有或被授权维护的资源。路由仅负责参数与响应，业务和权限校验应放在 `services/`。

## 目录结构

```text
app.py                 # 应用入口、路由挂载、CORS 与启动钩子
authentication.py      # JWT / Robyn 鉴权处理
subRouters/v1/         # HTTP 路由：user、service、api、ai
services/              # 业务逻辑、权限校验与 AI 提案
database/              # SQLAlchemy 模型、枚举、连接与迁移脚本
mailer.py              # SMTP 邮件发送
docs/                  # 开发说明与产品约束
```

## 与其他仓库的关系

- `FE-CAM`：通过 `VITE_API_BASE_URL` 指向本服务，提供管理界面。
- `cam-fe-code-generator`：登录后从本服务拉取指定 Service 与 API 定义，生成 TypeScript 调用代码。

拆库后请把 API 合同（路径、请求/响应字段、版本语义）作为跨仓库变更的一部分同步维护；不要只修改某一端。

## 开发约定

- 路由新增在 `subRouters/v1/`，对应业务放入 `services/`；数据库模型与枚举放入 `database/`。
- 密码必须使用模型提供的哈希方法；不得记录 JWT、数据库口令、SMTP 或模型服务凭据。
- 新增受保护路由应启用 `auth_required=True` 并在业务层校验资源归属。
- AI 功能的输入和模型输出必须经过现有校验，且不应绕过迭代权限校验。

## 许可证

仓库拆分时请在此仓库根目录补充并明确适用的 `LICENSE`。
