# Backend（refactored）

新的后端遵循「配置 → 领域 → 应用 → 接口」分层，保证可维护性：

- `config/`：集中式配置与密钥（`settings.py`, `secrets.py`, `defaults.toml`）
- `core/`：纯领域模型（Scene/Actor/Conversation 等）
- `application/`：用例服务（Scene/Project/AI），通过 `application/bootstrap.py` 注册到全局容器
- `infrastructure/`：与外界交互（Qt WebChannel、LLM/MCP、文件系统等）
- `interfaces/`：运行入口（Qt、MCP Server、CLI 工具）
- legacy `ui/`、`services/`、`utils/` 继续存在，但它们现在只是一层适配器，全部委托给 application 服务

## 运行方式
1. 构建前端 `Frontend/dist`
2. `python -m Backend.interfaces.cli.secrets`（可选，初始化 `~/.coronaengine/credentials.toml`）
3. `python Backend/main.py`

`Backend/main.py` 会读取 `config/settings.py`，自动设置 Qt 渲染参数并完成依赖注入。  
WebChannel 的契约文档见 `docs/backend_interface.md`。

## 关键特性
- **统一密钥管理**：环境变量 > 用户级 `~/.coronaengine/credentials.toml` > 模板文件
- **LLM + MCP**：`LLMClient` 通过 `MCPToolAdapter` 自动列举并调用 `TransformMCP` 工具
- **可测试的领域层**：`SceneRepository`、`Conversation` 等与 Qt/文件系统完全解耦
- **前端接口清晰**：`sceneService/projectService/aiService/...` 的输入输出均为结构化 JSON，详见文档

## 环境变量
默认禁用 GPU，如需开启可设置 `CORONA_ENABLE_GPU=true`；其它变量（模型、日志等级等）在 `config/defaults.toml`。

