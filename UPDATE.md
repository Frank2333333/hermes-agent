# UPDATE

本文档说明当前企业分支 `dev` 相对原版 Hermes `main` 分支的主要变更。

基线版本：
- 原版基线分支：`main`
- 当前企业分支：`dev`
- 当前企业分支最近一次收敛提交：`32e3119b`

## 1. 分支目标

当前分支不再追求与原版 Hermes 的功能对等，而是收敛为一个适合企业内网部署的版本，核心目标是：

- 安全优先
- 仅允许内网/本地模型接入
- 仅保留企业实际需要的入口面
- 删除高风险、低必要性的公网集成能力

## 2. 入口面变化

相对原版 Hermes，本分支只保留以下入口：

- `hermes` CLI
- `api_server`

已移除或不再支持：

- `webhook` 平台入口
- 消费级/公网消息平台入口
- 多数“从外部平台直接与 Hermes 对话”的网关形态

当前推荐启动方式：

- 本地交互：`hermes`
- API 服务：`hermes gateway run`

## 3. 模型接入变化

原版 Hermes 支持多种公网模型服务商和 OAuth/云端接入方式；本分支已明显收缩。

当前分支主要变化：

- 默认语义改为仅允许企业内网或本地自建模型端点
- 运行时新增企业策略校验层：`enterprise_policy.py`
- `model.provider` 以 `custom` / 自建 OpenAI 兼容端点为主
- 对非白名单、非私网、非本地地址的模型端点增加拒绝逻辑
- 公网模型服务商相关能力和文案已被移除或降级

适用场景：

- Ollama / vLLM / LM Studio / 自建 OpenAI-compatible 网关
- 企业内网中的代理层或模型中台

## 4. 网络与安全策略变化

本分支新增了企业内网导向的统一网络策略。

主要变化：

- 增加 `enterprise.enabled`
- 增加 `enterprise.network_allowlist.hosts`
- 增加 `enterprise.network_allowlist.cidrs`
- 对模型访问、浏览器访问、网页提取、远程 MCP 等流量增加白名单约束
- 以“默认拒绝”为方向收敛公网访问面

这意味着：

- 原版里很多“能直接联网就能用”的能力，在本分支里不再默认可用
- 运维部署时需要明确配置允许访问的内网地址段或域名

## 5. 工具能力变化

### 已移除或禁用

- `web_search`
- `send_message`
- 大量依赖公网后端的搜索/分发能力

### 保留但受限

- `web_extract`
  仅适用于企业允许的地址范围
- `browser_*`
  保留本地/内网可用路径，云端浏览器能力已被清理
- `mcp`
  更偏向本地 stdio 或内网白名单地址

整体原则：

- 保留企业内部研发常用能力
- 删除容易穿透内网边界或引入外部依赖的能力

## 6. 网关与平台集成变化

这是本分支相对原版变化最大的一部分。

原版 Hermes 支持大量平台适配器；本分支已经删除或停止支持这些平台相关代码与测试：

- Telegram
- Discord
- Slack
- WhatsApp
- Signal
- Matrix
- Mattermost
- Email
- SMS
- DingTalk
- Feishu / Lark
- WeCom / WeCom Callback
- Weixin
- BlueBubbles
- QQ Bot
- Home Assistant
- Webhook

影响：

- 不再面向公网 IM、企业 IM、Webhook 事件驱动场景
- API 与 CLI 成为唯一保留的主要使用方式

## 7. CLI 变化

CLI 没有被删除，但定位发生了变化。

当前分支中：

- 保留 `hermes` 交互式 CLI
- 保留模型配置、工具配置、gateway 管理等运维入口
- 删除 `hermes webhook` 子命令
- 删除与已下线平台对应的 CLI 配置向导和帮助入口

简化理解：

- CLI 仍然可用
- 但 CLI 不再负责连接一堆外部平台

## 8. API Server 变化

API Server 被保留为企业版主要对外接口。

当前保留的典型接口包括：

- `GET /health`
- `GET /health/detailed`
- `GET /v1/models`
- `POST /v1/chat/completions`

部署特点：

- 默认监听本地地址
- 如果绑定到非回环地址，要求配置 `API_SERVER_KEY`
- 更适合放在企业网关、内网服务编排或上层业务系统后面

## 9. 配置与示例文件变化

本分支对配置面做了明显“去公网化”处理。

主要变化：

- `.env.example` 改成以内网/API 部署为主
- `cli-config.yaml.example` 改成企业版导向
- 默认 toolset 已恢复为 `hermes-cli`
- `api_server` 的平台 toolset 单独保留
- `webhook` 配置项和相关示例已移除

## 10. 文档变化

相对原版 Hermes，本分支文档不再宣传公网平台和外部 SaaS 能力。

已做的方向性调整：

- `README.md` 改为企业内网版说明
- `SECURITY.md` 改为企业部署假设
- `website/sidebars.ts` 移除大量不再支持的平台入口
- 删除顶层历史发布说明文档 `RELEASE_v0.2.0.md` 到 `RELEASE_v0.10.0.md`

## 11. 测试变化

测试也随代码一起收缩。

主要变化：

- 删除大量与已移除平台相关的测试
- 删除 `webhook` 相关测试
- 删除 `send_message`、公网搜索及部分公网工具相关测试
- 新增企业分支定向测试，例如：
  - `tests/test_enterprise_policy.py`
  - `tests/hermes_cli/test_enterprise_runtime_provider.py`
  - `tests/gateway/test_enterprise_gateway_config.py`

## 12. 兼容性影响

如果你之前按原版 Hermes 的方式使用项目，需要注意这些不兼容变化：

- 不能再直接接 Telegram / Discord / Slack 等平台
- 不能再依赖 `webhook` 驱动 agent
- 不能再直接使用公网模型服务商接入路径
- 不能再依赖 `web_search`
- 文档、示例配置、测试集都已偏向企业内网部署，而不是通用个人使用场景

## 13. 推荐使用方式

对于当前企业分支，推荐按下面的方式理解和部署：

1. 用 `hermes` CLI 做本地交互、运维和调试
2. 用 `api_server` 作为系统集成入口
3. 模型只接企业内网或本地自建 OpenAI-compatible 服务
4. 通过 `enterprise.network_allowlist.*` 明确收口网络访问面
5. 不再把这个分支当成“全平台通用版 Hermes”

## 14. 总结

一句话概括：

当前 `dev` 分支已经从“通用多平台 AI Agent”收敛成“企业内网可控版 Hermes”，重点保留 `CLI + API Server + 内网模型 + 受控工具访问`，并系统性删除了公网平台、公网搜索、公网模型接入和 `webhook` 事件入口。
