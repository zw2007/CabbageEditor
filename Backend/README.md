# Backend（glue layer）

Backend 现在按职责拆分为 6 个顶层模块，方便在早期阶段快速对齐关注点：

| 目录 | 作用 |
| ---- | ---- |
| `network_service/` | 协同编辑 / MCP / LAN&WAN 相关服务。当前包含 `mcp/server.py` 与 `transform_server.py`。 |
| `artificial_intelligence/` | AI 会话、Agent、LLM 接入。`foundation_api/` 暴露统一的 `LLMClient`，`adapters/` 负责与 MCP 工具互操作，`services/` 提供 AI 业务接口。 |
| `engine_core/` | 与 C++ 引擎交互的所有包装（Scene/Actor/Camera 等）以及与项目/场景相关的服务。 |
| `window_layout/` | PySide 窗口管理、Dock/吸附逻辑、以及通过 WebChannel 暴露给前端的 Qt Services。`widgets/` 是实际的 Qt 组件。 |
| `frontend_bridge/` | Python ↔ JS/Web 渠道，目前提供 WebChannel 初始化和清理。 |
| `config/` | 所有配置、密钥、CLI 初始化脚本。`secrets.toml` 是唯一可信来源，`settings.py` 负责聚合配置。 |
| `tools/` | CLI / 服务入口（`bootstrap.py`, `mcp_client.py`, `transform_server.py`, `corona_engine_fallback.py` 等）。 |

辅助目录：
- `shared/`：轻量工具（DI 容器、日志包装等）
- `script/`：Blockly/脚本生成目录（运行时写入）
- 根目录现在只保留 `main.py`（桌面端入口）与 README，其余入口统一放到 `tools/`

## 启动流程
1. 构建前端 `Frontend/dist`
2. 运行 `python Backend/config/cli_secrets.py`（首次部署时填入 API Key/Base URL，写入 `Backend/config/secrets.toml`）
3. `python Backend/main.py`
4. 如需 CLI / MCP：`python Backend/tools/mcp_client.py` 或 `python Backend/tools/transform_server.py`

`Backend/main.py` 会读取 `config/settings.py`，自动设置 Qt 渲染参数、完成依赖注入，然后加载 `window_layout.widgets.main_window`。

## Secrets / 配置
- 所有 API Key 均保存在 `Backend/config/secrets.toml`（明文）。
- `Backend/config/mcp_client_secrets.json` 依旧保留，供 MCP 工具链或脚本复用；`secrets.py` 会优先读取 `secrets.toml`，再回退到 JSON。
- 如需命令行配置，可执行 `python Backend/config/cli_secrets.py`。

其他配置项仍可通过 `config/defaults.toml` + 环境变量组合重写，详见 `config/settings.py`。

## 特性速览
- **引擎粘合层**：`engine_core` 暴露统一的 Scene/Actor API，供 `window_layout` 与 `network_service` 使用。
- **AI 与工具链**：`artificial_intelligence` 统一管理会话、工具适配、LLM 接入，`MCPToolAdapter` 自动列举 `TransformMCP` 工具。
- **前端桥接**：`frontend_bridge/webchannel.py` 注册 `sceneService/projectService/aiService/...`，保持 JS 交互契约不变（详见 `docs/backend_interface.md`）。
- **容器化启动**：`Backend/tools/bootstrap.py` 负责注册所有服务，外部入口只需调用一次。

默认禁用 GPU，如需开启可设置 `CORONA_ENABLE_GPU=true`；其它模型/日志参数在 `config/defaults.toml`。凭据无需环境变量，全部由 `config/secrets.toml` 管理。

