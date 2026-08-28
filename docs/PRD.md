# 【PRD】CAM API Management

## 1. 背景与问题

在一个典型的团队里，接口定义通常分散在多处：后端代码、接口文档平台、前端请求封装、测试用例与脚本。随着服务数量增加、版本不断演进，常见问题会集中爆发：

- 接口定义不是单一事实来源：文档与实现、前后端类型与字段逐渐偏离
- 版本不可追溯：同一个 `service_uuid` 在不同时间点的接口形态难以还原
- 变更不可控：一次迭代内多个接口改动混在一起，无法做到“先草稿、再发布”
- 联调效率低：前端需要手工维护 types 与 request，重复劳动且容易出错

CAM 试图把“接口定义”从附属产物变成核心资产：把 Service/API/参数/迭代过程结构化存储，并提供 UI 与代码生成能力，降低协作成本。

## 2. 产品目标

- 让 Service 与 API 定义成为团队内部“唯一可信源”
- 支持可回溯的版本管理，能还原任意版本的 Service 与 API 形态
- 以迭代为单位组织变更：草稿态可编辑、可撤销，提交后进入正式版本
- 为前端提供可直接接入的 TypeScript 调用代码生成能力，减少手写与对齐成本

## 3. 范围与非目标

### 3.1 本期范围（基于当前代码实现）

- 用户：注册、登录、JWT 鉴权、获取个人信息、修改密码
- Service：创建、查询、分页列表、软删除与恢复、按 `service_uuid + version` 拉取、版本列表
- 迭代：发起迭代、迭代内编辑 service 描述、提交迭代并更新版本、删除迭代记录
- API：分类管理、按分类获取 API 列表、查询 API 详情（含参数树）
- 迭代内 API 草稿：新增、删除、更新（同时更新请求/响应参数草稿）
- 前端 Web：围绕上述能力的完整管理 UI
- npm 包（`cam-fe-code-generator`）：CLI 登录、选择 Service 并生成 TS 服务类与类型定义

### 3.2 非目标（当前不做 / 未落地）

- OpenAPI/Swagger/Thrift 文件导入与导出
- 在线 Mock、在线测试台、自动化测试用例生成
- 多人协作与 maintainer 权限体系（当前以 owner 为主）
- 复杂的差异对比 UI（diff）与变更审计流

## 4. 用户画像与使用场景

### 4.1 角色

- 后端开发：维护接口与版本，组织一次迭代内的变更并提交
- 前端开发：查看接口定义、参数结构，拉取或生成类型安全的调用代码
- 团队负责人/架构师：关注接口资产沉淀、版本治理与协作效率

### 4.2 典型场景

1) 新建服务并定义接口
- 创建 Service（`service_uuid` 为 `a/b/c`）
- 发起迭代，新增 API 草稿，编辑参数结构
- 提交迭代，服务版本从 `0.0.1` 演进到 `0.0.2`

2) 线上接口需要回溯与复现
- 通过 `service_uuid` 获取版本列表
- 选择旧版本，查看当时的 API 列表与参数结构

3) 前端一键生成调用代码
- 通过 CLI 登录，配置要拉取的 Service（支持 `latest` 或具体版本）
- 自动生成 Service Class + namespaces 类型定义，直接接入 axios/fetch

## 5. 核心概念与数据模型（产品视角）

### 5.1 Service

- 唯一标识：`service_uuid`（格式 `a/b/c`）
- 版本：`x.y.z` 语义化版本
- 所有者：`owner_id`
- 描述信息：`description`
- 状态：支持软删除（仅影响最新版本）

### 5.2 迭代（ServiceIteration）

一次迭代代表“从某个稳定版本出发的一组变更”。迭代的关键价值是把“编辑行为”与“发布行为”解耦：

- 迭代开始后，系统会把当前最新版本的 API 与参数复制为草稿
- 所有编辑都发生在草稿层（ApiDraft/ParamDraft）
- 提交迭代后，把草稿写回正式表（Api/Param），并更新 Service 版本号

### 5.3 API 与参数

- API 的唯一性：同一 Service 内，`method + path`、`method + name` 需要保持唯一
- 请求参数：按位置组织（query/path/header/cookie/body），并支持 object/array 的树形嵌套
- 响应参数：按 HTTP 状态码组织，参数同样支持嵌套

## 6. 关键流程（用户可感知）

### 6.1 登录与鉴权

- 登录成功后获得 `access_token`（JWT）
- 前端请求统一在拦截器里附加 `Authorization: Bearer <token>`
- 后端基于 Robyn 的 AuthenticationHandler 校验 token，并可对特定路由配置最低权限等级

### 6.2 Service 创建与管理

- 创建：输入 `service_uuid` 与描述，系统初始化版本为 `0.0.1`
- 列表：支持分页、范围切换（我的服务/他人服务/全部服务，具体由前端实现）
- 删除与恢复：作用于最新版本，历史迭代版本保持不动

### 6.3 版本管理（按 ServiceIteration 组织）

1) 发起迭代
- 返回 `service_iteration_id`，作为本次迭代的“工作区标识”
- 复制最新版本 API 与参数到草稿表

2) 迭代内编辑
- 更新 service 描述（作用于草稿上下文）
- 新增/删除/编辑 API（编辑时同时维护请求/响应参数树）

3) 提交迭代
- 输入 `new_version`
- 系统把草稿同步到正式表，并更新 Service 最新版本号

### 6.4 TS 调用代码自动生成

目标：让前端在“知道某个 service_uuid 与版本”后，自动得到可用的 TS 类型与调用入口，避免重复写 request 与 types。

当前实现包含三层产物：

- namespaces.ts：按接口拆分的请求/响应类型定义（含嵌套结构）
- index.ts：一个 Service 对应一个 Service Class，方法按 API 生成，可注入 request 实现
- request-demo.ts：演示如何用 axios/fetch 对接生成的 Service Class

CLI 使用流程：

1) `cam login`：保存 token 到 `~/.camrc`
2) `cam init`：在当前目录生成 `cam.config.json`
3) `cam add name:uuid@version|latest`：登记要生成的服务
4) `cam update`：拉取所有服务的 API 详情并生成代码（每次先清空输出目录再生成）

## 7. 新颖之处（差异化点）

### 7.1 “迭代即工作区”：把 API 变更过程产品化

很多系统只做“接口列表 + 文档”，但缺少“变更如何发生、如何提交”的结构化表达。CAM 的迭代机制把一次变更拆为三个明确阶段：

- 开始迭代：从稳定版本复制出草稿
- 迭代编辑：允许大量改动，但不影响正式版本
- 提交迭代：一次性写回并更新版本

这让团队可以把“接口治理”按迭代组织，而不是按接口零散修改。

### 7.2 参数树模型：支持复杂嵌套并可复原

请求与响应参数以“树”表示（parent/children），并按 location/status_code 组织：

- 能表达 object 嵌套、array of object 等常见复杂结构
- 同一份模型既能驱动 UI 编辑，也能驱动代码生成
- 在版本回溯时能完整复原当时的参数结构，而不是只留下扁平字段

### 7.3 前端代码生成不是“模板片段”，而是可注入的 Service Class

生成结果提供的是一个可复用的 Service Class，而不是把 axios/fetch 写死在模板里：

- 业务项目可直接注入现有 request 封装（axios 实例、fetch wrapper、埋点、重试等）
- 生成结果只关心 “url/method/data/params/headers” 这类通用字段，降低耦合
- 允许同一份生成结果在不同项目中复用（不同 baseURL、不同鉴权策略）

## 8. 技术难点（实现与治理挑战）

### 8.1 迭代草稿的“复制与提交”一致性

难点不在 CRUD，而在“一次迭代涉及多表、多层级数据复制”：

- 开始迭代时，需要把 Api、RequestParam、ResponseParam 复制成草稿，并保持 parent-child 关系不丢失
- 复制过程中必须建立 id 映射（旧 id -> 新草稿 id），再回填 parent_id
- 提交迭代时，需要把草稿同步回正式表，同时处理新增、删除、更新三类变更

这一部分会直接决定版本回溯是否可信，也是系统复杂度的主要来源。

### 8.2 API 唯一性约束与冲突处理

同一 Service 内：

- `method + path` 需要唯一
- `method + name` 需要唯一

并且冲突校验要覆盖两类数据源：

- 最新正式版本的 Api
- 当前迭代中的 ApiDraft

否则会出现“草稿可创建但提交失败”的体验断层。

### 8.3 参数类型到 TypeScript 类型的映射

把通用的参数模型映射到 TS，需要处理：

- 基础类型映射（int/double/bool/string 等）
- object/array 的递归展开
- array child type 为 object 时的命名与类型生成策略
- 字段 optional 与 required 的一致性
- 类型命名冲突（同名字段、不同层级对象）与稳定性

当前生成器通过“接口名 + 字段名”的前缀策略降低冲突概率，但仍需在复杂场景下保证可读性与可维护性。

### 8.4 版本拉取与历史版本的双态数据模型

在“查看某个版本”时，API 详情可能来自：

- 最新版本：Api + RequestParam/ResponseParam
- 历史版本（迭代记录）：ApiDraft + RequestParamDraft/ResponseParamDraft

对前端与生成器而言，需要用同一套模型消费两种来源，并在调用链上携带 `is_latest` 的上下文，否则会出现“同一个 api_id 在不同模式下语义不同”的问题。

### 8.5 代码生成的工程化边界

生成器在工程层面需要保证：

- 幂等：同一份配置重复生成结果一致
- 可回收：更新时清空输出目录，避免残留文件造成“幽灵接口”
- 可接入：生成代码不绑定具体网络库，业务侧可以自由注入
- 可调试：CLI 的登录态需要跨命令持久化（当前使用 `~/.camrc`）

### 8.6 兼容产品现实的错误返回与前端处理策略

当前后端接口在“逻辑失败”时通常仍返回 HTTP 200，并通过响应体里的 `status`（负数）与 `message` 表达失败原因；而缺参、参数格式错误等属于请求不合法的场景，会返回 HTTP 400。

这会带来几个产品侧与工程侧的挑战：

- 前端与 CLI 需要对两类错误分别处理：HTTP 层失败与业务层失败
- 告警与监控不能只依赖 HTTP 状态码，需要引入业务状态码维度的统计
- 文档与 SDK 生成需要清晰表达“成功/失败的判断条件”，避免使用者误判

## 9. 关键接口（便于对齐前后端/生成器）

以 `/v1` 为前缀，核心路由分为三类：

### 9.1 用户（/v1/user）

- `POST /login`
- `POST /register`
- `POST /modifyPassword`
- `GET /getMyInfo`
- `GET /getUserById`
- `GET /getUserByUsernameOrNicknameOrEmail`

### 9.2 服务（/v1/service）

- `GET /getAllServices`（分页）
- `GET /getServiceById`
- `GET /getHisNewestServicesByOwnerId`（分页）
- `GET /getServiceByUuidAndVersion`
- `GET /getAllVersionsByUuid`
- `POST /createNewService`
- `GET /getAllDeletedServicesByUserId`（分页）
- `POST /deleteServiceById`
- `POST /restoreServiceById`
- `POST /deleteIterationById`
- `GET /getIterationById`
- `POST /startIteration`
- `POST /commitIteration`
- `POST /updateDescription`

### 9.3 API（/v1/api）

- `GET /getAllCategoriesByServiceId`
- `GET /getAllApisByServiceId`（要求同时传 service_id 与 category_id）
- `GET /getApiById`（支持 `is_latest`）
- `POST /addCategoryByServiceId`
- `POST /deleteCategoryById`
- `POST /updateCategoryById`
- `POST /updateApiCategoryById`（仅支持正式表）
- 迭代相关：
  - `POST /addApi`
  - `POST /deleteApiByApiDraftId`
  - `POST /updateApiByApiDraftId`（更新 API 草稿及其参数）

## 10. 指标与验收标准（建议）

- 协作效率
  - 前端接入新服务接口的平均耗时（从“获取接口列表”到“可发起请求”）下降
  - 由于类型/字段不一致导致的联调返工次数下降
- 版本治理
  - 任意 `service_uuid` 可在 1 分钟内定位并复现指定版本的接口形态
  - 迭代提交成功率与失败原因可追踪（校验失败/冲突/权限等）
- 生成质量
  - 生成代码可直接编译通过（TypeScript）
  - 对嵌套参数的类型表达覆盖常见场景（object/array/object-in-array）

## 11. 风险与后续规划

### 11.1 风险

- 迭代复制与提交流程复杂，容易在极端嵌套结构或部分删除场景出现“关系断裂”
- API 唯一性约束与前端编辑体验需要持续打磨，否则会影响使用信心
- 代码生成的命名策略在大型服务里可能产生可读性问题，需要更系统的命名与模块划分策略
- 当前后端错误语义以业务状态码为主，若缺少统一规范与监控配套，线上排障成本会被放大

### 11.2 规划方向（与现有设计一致）

- API 定义导入（OpenAPI/Thrift）与导出（OpenAPI）
- 版本差异对比（Service/API/参数树 diff）
- 迭代审批/变更审计
- 团队协作（maintainer、成员权限、跨服务访问策略）
