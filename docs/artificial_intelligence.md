# Artificial Intelligence Module

本目录汇总了 CabbageEditor 后端的 AI 能力，包括 LangChain Agent、模型客户端、工具系统与配置。下面从开发者角度介绍目录结构、配置方法以及多模型供应商的接入技巧。

## 1. 目录总览

```
Backend/artificial_intelligence/
├── agent/                # LangChain agent 装配逻辑
├── api/                  # 前端（Qt/WebChannel）调用入口，暴露 handle_user_message
├── config/               # app_config.toml + config.py（唯一配置入口）
├── models/               # 各种 LLM 客户端构建逻辑（目前基于 ChatOpenAI）
├── tools/
│   ├── builtin/          # 基础工具示例（search、get_weather 等）
│   ├── media/            # 图像/视频工具封装，读取 app_config 中的 provider
│   └── mcp/              # MCP 工具（内置 scene_tools，直接操作当前 SceneManager）
└── README / docs         # 见本文 & Backend/README.md
```

核心调用链：`Frontend → Backend.artificial_intelligence.api → agent/create_default_agent → models + tools`。

## 2. 统一配置：`app_config.toml`

所有模型、密钥与工具配置均集中在 `Backend/artificial_intelligence/config/app_config.toml`（首次可复制 `app_config.example.toml`）。该文件支持多模型供应商与多工具独立配置。

示例：
```toml
[[providers]]
name = "siliconflow"
type = "openai-compatible"
base_url = "https://api.siliconflow.cn/v1"
api_key = "sk-xxx"                # 可改用 api_key_env 指向环境变量

[[providers]]
name = "closeai"
type = "openai-compatible"
base_url = "https://api.closeai.com/v1"
api_key = "sk-yyy"

[llm.chat]
provider = "siliconflow"
model = "Qwen/Qwen3-Omni-30B-A3B-Instruct"
temperature = 0.2
request_timeout = 60
system_prompt = """..."""

[llm.tool_models.mcp]
provider = "siliconflow"
model = "Qwen/Qwen3-14B"

[media.image]
enable = true
provider = "closeai"
model = "gpt-image-1"

[media.video]
enable = false
provider = "closeai"
model = "sora"

```

- `[[providers]]`：声明所有可用模型供应商（支持多个 base_url + API Key）。
- `[llm.chat]`：LangChain Agent 默认使用的聊天模型配置。
- `[llm.tool_models.<name>]`：给工具（如内置 MCP scene_tools、图像等）指定专属模型。
- `[media.image]` / `[media.video]`：控制多模态工具是否启用以及对应 provider/model。

> 如需在服务器上隐藏密钥，可将 `api_key` 删除，改用 `api_key_env = "SILICONFLOW_KEY"` 并在环境变量中配置。

## 3. 多供应商/多模型接入点

- **LangChain Agent**：`agent/factory.py` 会读取 `[llm.chat]`，动态构建 `ChatOpenAI`（或其他 provider）。
- **MCP 工具**：`tools/base.py`/`tools/mcp/scene_tools.py` 会注册内置的场景控制工具（`scene_query`、`transform_model`），可通过 `[llm.tool_models.mcp]` 为这些工具选择专属模型或解析逻辑。
- **图像/视频工具**：`tools/media/image_tools.py`、`video_tools.py` 读取 `[media.image/video]`，可分别连接 CloseAI、硅基等不同供应商。
- **Fallback/CLI**：`api/__init__.py` 里的 `_fallback_completion()` 也复用 `[llm.chat]`，保证无论 Agent 返回如何都能退回主模型。

未来若需要接入更多类型（如 Embedding、RAG 检索等），只需在 `app_config.toml` 中新增 `llm.tool_models.embedding`、`retrieval` 等段，然后在对应工具里读取并创建模型即可。

## 4. 典型开发流程

1. **新增 provider**：在 `[[providers]]` 中添加条目，提供 base_url + API Key（或环境变量）。
2. **绑定功能 → provider**：在 `[llm.chat]` / `[llm.tool_models.*]` / `[media.*]` 中引用 provider 名称与模型标识。
3. **在代码中调用**：使用 `get_chat_model(config, provider_name=..., model_name=...)` 或自行根据 provider 信息构建客户端（如直接调用 `openai`/`httpx`）。
4. **测试**：运行 `python Backend/main.py`，通过 UI 或 CLI 验证 Agent 是否正确调用 MCP/媒体工具，以及是否选择了期望的供应商。

## 5. FAQ

- **如何在 MCP 内部也用模型？**  
  调用 `get_app_config().tool_models.get("mcp")` 获取 provider/model，再利用 `get_chat_model` 或自定义客户端即可。

- **如何为不同环境提供不同配置？**  
  除项目内 `app_config.toml` 外，也可以在 `~/.coronaengine/app_config.toml` 中写入覆盖字段，或通过 `CORONA_*` 环境变量重写关键配置（例如 `CORONA_LLM_PROVIDER`）。

- **能否混合非 OpenAI 协议的供应商？**  
  目前 `models/client_openai.py` 默认使用 OpenAI Compatible API；若需接入 Anthropic/Bedrock 等，可在 `models/` 目录添加对应构建函数，并在 `get_chat_model()` 中按 `provider.type` 路由。

---
如需进一步扩展或遇到问题，可参考 `Backend/README.md` 与本文件，或直接查看 `Backend/artificial_intelligence` 目录下的代码实现。*** End Patch
