# Backend（glue layer）

Backend 现在按职责拆分为 6 个顶层模块，方便在早期阶段快速对齐关注点：

| 目录 | 作用 |
| ---- | ---- |
| `network_service/` | 协同编辑 / MCP / LAN&WAN 相关服务。 |
| `artificial_intelligence/` | LangChain Agent 实现：`config/`（`config.py` + `app_config*.toml`）、`models/`、`tools/`（builtin/media/mcp）、`agent/`、`api/`。详见 `docs/artificial_intelligence.md`。 |
| `engine_core/` | 与 C++ 引擎交互的所有包装（Scene/Actor/Camera 等）以及与项目/场景相关的服务。 |
| `window_layout/` | PySide 窗口管理、Dock/吸附逻辑、以及通过 WebChannel 暴露给前端的 Qt Services。`widgets/` 是实际的 Qt 组件。 |
| `frontend_bridge/` | Python ↔ JS/Web 渠道，目前提供 WebChannel 初始化和清理。 |
| `artificial_intelligence/config/` | 配置与凭据所在：`config.py` + `app_config.example.toml`。运行时读取 `app_config.toml`（可用户自定义）。 |
| `tools/` | CLI / 服务入口（`bootstrap.py`, `mcp_client.py`, `corona_engine_fallback.py` 等）。 |

辅助目录：
- `shared/`：轻量工具（DI 容器、日志包装等）
- `script/`：Blockly/脚本生成目录（运行时写入）
- 根目录现在只保留 `main.py`（桌面端入口）与 README，其余入口统一放到 `tools/`

## 启动流程
1. 构建前端 `Frontend/dist`
2. 复制 `Backend/artificial_intelligence/config/app_config.example.toml` 为 `app_config.toml`，在 `[secrets]` 中填写 API Key / Base URL，并按需调整 `[llm]`、`[media]`。
3. `python Backend/main.py`
4. 如需 CLI / MCP：`python Backend/tools/mcp_client.py`

`Backend/main.py` 会读取 `artificial_intelligence/config/config.py`（并加载 `app_config.toml`），自动设置 Qt 渲染参数、完成依赖注入，然后加载 `window_layout.widgets.main_window`。

## Secrets / 配置
- 所有 API Key 与模型、服务配置均集中在 `Backend/artificial_intelligence/config/app_config.toml` 的 `[secrets]`、`[llm]`、`[media]` 段（可通过 `~/.coronaengine/app_config.toml` 或环境变量覆盖）。
- `config.py` 负责解析该文件并向整个项目提供 `AppConfig` 数据对象。

其他配置项可通过 `artificial_intelligence/config/app_config.toml` + 环境变量组合重写，详见 `artificial_intelligence/config/config.py`。

## 特性速览
- **引擎粘合层**：`engine_core` 暴露统一的 Scene/Actor API，供 `window_layout` 与 `network_service` 使用。
- **AI 与工具链**：`artificial_intelligence` 通过 LangChain `create_agent` 构建统一 Agent，`tools/` 聚合 MCP / media / builtin 工具，`api.handle_user_message` 供 Qt/Web 调用。
- **前端桥接**：`frontend_bridge/webchannel.py` 注册 `sceneService/projectService/aiService/...`，保持 JS 交互契约不变（详见 `docs/backend_interface.md`）。
- **容器化启动**：`Backend/utils/bootstrap.py` 负责注册场景/项目服务并初始化日志，LangChain Agent 本身懒加载。

默认禁用 GPU，如需开启可设置 `CORONA_ENABLE_GPU=true`；其它模型/日志参数在 `artificial_intelligence/config/app_config.toml` 中配置。凭据无需环境变量，全部由 `[secrets]` 段管理。

