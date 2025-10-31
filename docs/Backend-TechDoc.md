# CabbageEditor 后端技术文档

## 概述
后端基于 PySide6 的 Qt + QWebEngine 提供编辑器主程序与 Dock 容器，使用 Qt WebChannel 将 C++/Python 能力暴露给前端。当前架构采用“服务化 + 薄桥”设计：
- WebChannelHelper 统一注册与清理服务对象
- Bridge 作为后端信号/槽的聚合点，优先将请求委托给具体服务
- 服务对象（Service）按领域拆分：App/Scene/Project/Scripting/AI
- BrowserWidget 是主 Web 容器，负责主页面的 WebChannel 接线与 Dock 的创建/销毁
- RouteDockWidget 是每个 Dock 的 Web 容器，内置 WebChannel 并支持拖拽/缩放事件
- CentralManager 维护所有 Dock 的注册表

目录涉及的关键模块：
- Backend/ui/browser_widget.py
- Backend/ui/dock_widget.py
- Backend/utils/webchannel_helper.py
- Backend/utils/{app_service.py, scene_service.py, project_service.py, scripting_service.py, ai_service.py}
- Backend/utils/{bridge.py, central_manager.py, static_components.py}

## 运行时流程总览
1. 启动 main.py，创建主窗口并加载 Frontend/dist/index.html
2. BrowserWidget 调用 WebChannelHelper：注册 Bridge 与各 Service，并将 AppService 的“创建/删除 Dock”的信号回接到 BrowserWidget.AddDockWidget/RemoveDockWidget
3. 前端 new QWebChannel 后获得 window.appService/sceneService/...，发起业务调用
4. Bridge 接到调用后优先委托到对应 Service；Service 完成逻辑后以信号返回结果
5. Dock 页面通过 appService.send_message_to_dock 抛送拖拽/缩放/浮动事件，RouteDockWidget 识别并执行 move/resize/setFloating

## WebChannel 与服务对象
WebChannel 暴露的对象（对象名 → 类）：
- appService → AppService
- sceneService → SceneService
- projectService → ProjectService
- scriptingService → ScriptingService
- aiService → AIService

Bridge 仍存在于后端，仅用于：
- 信号聚合：create_route/remove_route/command_to_main/ai_response/dock_event
- 将服务信号映射到旧事件（如 dock_event），便于渐进迁移

### AppService（应用/窗口编排）
方法（Slot）：
- add_dock_widget(routename: str, routepath: str, position: str = "left", floatposition: str = "None", size: str|None)
- remove_dock_widget(routename: str)
- send_message_to_dock(routename: str, json_data: str)
- send_command_to_main(command_name: str, command_data: str)
- close_process()

信号（Signal）：
- create_route_requested(name, path, pos, floatpos, sizeObj)
- remove_route_requested(name)
- message_to_dock_requested(name, json)
- command_to_main_requested(name, data)

WebChannelHelper 默认接线：
- create_route_requested → BrowserWidget.AddDockWidget（或回退到 Bridge.create_route.emit）
- remove_route_requested → BrowserWidget.RemoveDockWidget（或回退到 Bridge.remove_route.emit）
- message_to_dock_requested → CentralManager.send_json_to_dock（若可用）
- command_to_main_requested → Bridge.command_to_main.emit

### SceneService（场景/Actor/相机/光源）
方法（Slot）：
- create_scene(data: str JSON {sceneName})
- create_actor(scene_name: str, obj_path: str)
- remove_actor(scene_name: str, actor_name: str)
- actor_operation(data: str JSON {sceneName, actorName, Operation, x,y,z})
- camera_move(data: str JSON {sceneName, position, forward, up, fov})
- sun_direction(data: str JSON {sceneName, px, py, pz})

信号（Signal）：
- actor_created(str JSON {name, path})
- scene_loaded(str JSON {actors: [{name,path}, ...]})
- scene_error(str JSON)

数据面向引擎的抽象在 Backend/utils/scene.py 内部通过 EngineObjectFactory 访问底层 C++ ECS（如可用），并保持 Python 端薄包装。

### ProjectService（项目/文件）
方法（Slot）：
- open_file_dialog(sceneName: str, file_type: str in {"model", "scene"})
- scene_save(data: str JSON)

信号（Signal）：
- scene_saved(str JSON {status, filepath})

### ScriptingService（运行脚本）
方法（Slot）：
- execute_python_code(code: str, index: int)

行为：
- 将传入代码写入 Backend/script/blockly_code.py
- 生成 Backend/runScript.py，按顺序 import 所有 blockly_code*.py 并调用其 run()
- 控制台打印：
  - [DEBUG] 脚本文件创建成功: ...
  - [DEBUG] runScript.py创建/覆盖成功: ...

### AIService（AI 对话）
方法（Slot）：
- send_message_to_ai(ai_message: str JSON {message})

信号（Signal）：
- ai_response(str JSON {type, content, status, timestamp})

内部使用 WorkerThread 线程执行 qa_one_sync 并回传结果。

## BrowserWidget（主容器）
职责：
- 作为主页面的 Web 容器，承载前端 Router 根页面
- 通过 WebChannelHelper 注册服务对象
- 接线 AppService → AddDockWidget/RemoveDockWidget；CentralManager 转发消息到指定 Dock
- 处理 Bridge.command_to_main（如 go_home 重载首页；input_event 目前为占位）

AddDockWidget 逻辑：
- 根据 position/floatposition 选择 Dock 区域或浮动位置
- 复用 routename：若已存在则先删除后返回（实现“切换/关闭”行为）
- 为新 Dock 注入 window.__dockRouteName（供前端 useDragResize 识别目标）

## RouteDockWidget（Dock 容器）
职责：
- 承载对应路由页面（如 /Object、/SceneBar）
- 通过 WebChannelHelper 注册服务（Dock 页面也可直接调用服务）
- 处理来自前端的 Dock 事件：
  - JSON 负载统一格式：{event: 'drag'|'float'|'resize'|'close', routename, ...}
  - drag：deltaX/deltaY（仅浮动时移动）
  - float：isFloating（切换浮动）
  - resize：x/y/width/height（使用屏幕绝对坐标）
- 清理：断开信号、注销 channel、回收 QWebEngineProfile/QWebEnginePage

## CentralManager（Dock 注册表）
- register_dock(routename, dock)
- delete_dock(routename)
- send_json_to_dock(routename, json_data)：将字符串发给目标 Dock（RouteDockWidget.send_message_to_dock → Bridge.dock_event）

## 构建与运行
- Frontend 请先构建出 dist（Vite 构建），后端通过 static_components.url 指向 Frontend/dist/index.html
- 运行 Backend/main.py 即可（main.py 内默认启用软件渲染：QTWEBENGINE_DISABLE_GPU/Qt Quick software/OpenGL software）

## 事件/信号对照速查
- 前端 appService.add_dock_widget → BrowserWidget.AddDockWidget → 创建 QDockWidget
- 前端 appService.send_message_to_dock → Bridge.dock_event → RouteDockWidget.dock_event
- sceneService.actor_created → SceneBar 订阅并更新列表
- projectService.scene_saved → 可由前端订阅（或经 Bridge.dock_event 保持兼容）
- aiService.ai_response → AITalkBar 通过 Dock 页面的 JS 函数 window.receiveAIMessage 显示

## 约定与注意
- 前端所有 Service 调用须等待 window.webChannelReady
- add_dock_widget 的 size 参数为 JSON 字符串（如 {"width":520,"height":640}）
- Dock 事件负载必须包含 routename（后端将校验）
- 不再暴露 pyBridge；统一走服务对象

## 故障排查
- QWebChannel 未初始化：检查 index.html 是否引入 qwebchannel.js（相对路径）、main.js 是否 new QWebChannel
- 无法创建 Dock：确认 on_create_route 是否已由 BrowserWidget 接管（默认已接线），routename 未重复
- 拖拽不动：检查 window.__dockRouteName 是否注入；前端 useDragResize 是否通过 appService 发送；Dock 是否处于浮动
- 前端无法连接服务：等待 webChannelReady；检查对象名 sceneService/appService 等是否存在

