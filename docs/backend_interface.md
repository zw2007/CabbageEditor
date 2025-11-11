## Frontend ↔ Backend Contract (Refactored)

| Service          | Entry (WebChannel) | Method/Signal                      | Payload (JSON)                                                    | Notes |
|------------------|--------------------|------------------------------------|-------------------------------------------------------------------|-------|
| `appService`     | `send_command_to_main` | `{ "command": "go_home" }` etc.  | Routed to `BrowserWidget.handle_command_to_main`.                 | Unchanged. |
| `sceneService`   | Slot `create_scene(data)` | `{ "sceneName": "MainScene" }` | Creates/returns snapshot via `scene_loaded` signal.               | Backed by `SceneApplicationService`. |
|                  | Slot `create_actor(scene, path)` | plain args | Emits `actor_created` after `SceneApplicationService.add_actor`. | |
|                  | Slot `actor_operation(payload)` | `{ sceneName, actorName, Operation, x, y, z }` | Applies transform, emits `actor_created` event with delta. | |
|                  | Slot `camera_move(payload)` | `{ sceneName, position, forward, up, fov }` | Updates camera姿态；无直接回调，仅错误时触发 `scene_error`. | |
|                  | Slot `sun_direction(payload)` | `{ sceneName, px, py, pz }` | 更新太阳方向；无直接回调，仅错误时触发 `scene_error`. | |
| `projectService` | Slot `open_file_dialog(scene, type)` | `type` in `model/scene/multimedia` | Wraps file dialog + `SceneApplicationService`; 成功导入模型会额外触发 `sceneService.actor_created`. | |
|                  | Slot `scene_save(data)` | Scene JSON | Emits `scene_saved` with status + `filepath`. | |
| `scriptingService` | Slot `execute_python_code(code, index)` | raw python, index | Writes to `Backend/script`, regenerates `runScript.py`. | Path derived from `Settings.paths.script_dir`. |
| `aiService`      | Slot `send_message_to_ai(payload)` | `{ "message": "<text>" }` | Calls `AIApplicationService.ask`. Emits `ai_response`. | Uses `LLMClient` + MCP tools. |

Signals:  
`actor_created`, `scene_loaded`, `scene_saved`, `script_error`, `ai_response`, `create_route_requested`, `remove_route_requested`, `message_to_dock_requested`, `command_to_main_requested`.

All payloads are UTF-8 JSON strings. Schema definitions live in `Frontend/src/types/backend.ts`.

### Secret Management
- 运行 `python Backend/config/cli_secrets.py`，在 `Backend/config/secrets.toml` 中写入 `api_key` / `base_url`。
- Runtime order: `secrets.toml` > `Backend/config/mcp_client_secrets.json`（旧格式）> `Backend/config/mcp_client_secrets_example.json`。

### Service Composition
```
Frontend (WebChannel)
   -> `window_layout.services.*` (`sceneService`, `projectService`, `aiService`, ...)
       -> Core services (`engine_core.services.*`, `artificial_intelligence.services.*`)
           -> Engine runtime (`engine_core` bindings) / AI adapters (`artificial_intelligence`)
```

Use `Backend/tools/bootstrap.py` to register new services before touching Qt/UI.
