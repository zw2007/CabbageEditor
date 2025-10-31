# CabbageEditor 前端技术文档

## 概述
前端基于 Vue 3 + Vite + Tailwind（样式），通过 Qt WebChannel 与后端交互；页面在 Qt 的 QWebEngineView 中运行。通道初始化后，后端暴露的服务对象会挂载到 window：
- window.appService
- window.sceneService
- window.projectService
- window.scriptingService
- window.aiService

为保证时序，提供 window.webChannelReady（Promise）与 `qwebchannel-ready` 事件。

目录要点：
- Frontend/index.html（qwebchannel.js 引入，使用相对路径）
- Frontend/src/main.js（WebChannel 初始化与服务导出）
- Frontend/src/composables/useDragResize.js（统一拖拽/缩放逻辑）
- Frontend/src/views/{MainPage.vue, SceneBar.vue, Object.vue, AITalkBar.vue, Pet.vue}
- Frontend/src/blockly/*（Blockly 定义与生成器）

## 通道初始化（main.js）
- 页面加载后检测 `QWebChannel` 与 `qt.webChannelTransport`，创建通道
- 把 channel.objects 中的 service 对象挂到 window
- 触发 window.webChannelReady 的 resolve，以及派发 `qwebchannel-ready` 事件
- 不再暴露 pyBridge，所有调用走服务对象 API

使用方式：
```js
await window.webChannelReady
window.appService.add_dock_widget("SceneBar", "/SceneBar?sceneName=scene1", "left", "None", JSON.stringify({width:520,height:640}))
```

## Dock 拖拽/缩放（useDragResize.js）
- 统一通过 appService.send_message_to_dock(routename, payload) 将事件发送到后端
- 负载格式：`{ event: 'drag'|'resize'|'float'|'close', routename, ... }`
- 节流：拖拽默认 20ms 一次；释放时补发一次终态
- 关键字段：
  - drag：deltaX, deltaY（仅在浮动模式生效）
  - float：isFloating（自动切换浮动/停靠）
  - resize：x, y, width, height（使用屏幕绝对坐标，修复上/左拉伸时的位移）
- 页面加载完成后，后端会在 Dock 页注入 `window.__dockRouteName = <routename>`，该值作为发送目标标识

使用示例（标题栏拖动）：
```html
<div class="titlebar" @mousedown="startDrag" @mousemove="onDrag" @mouseup="stopDrag" />
```

## 视图与服务调用
- MainPage.vue
  - 创建场景：`sceneService.create_scene({sceneName})`
  - 打开场景栏 Dock：`appService.add_dock_widget("SceneBar", "/SceneBar?sceneName=...", ...)`
  - 相机移动：`sceneService.camera_move({sceneName, position, forward, up, fov})`

- SceneBar.vue
  - 订阅 `sceneService.actor_created/scene_loaded` 更新 UI
  - 导入模型/场景：`projectService.open_file_dialog(sceneName, 'model'|'scene')`
  - 保存场景：`projectService.scene_save(JSON.stringify(sceneData))`
  - 双击对象打开属性 Dock：`appService.add_dock_widget("Object_<name>", "/Object?sceneName=...&objectName=...&path=...&routename=...", 'right')`
  - 删除对象：`sceneService.remove_actor(sceneName, actorName)` + `appService.remove_dock_widget(widgetName)`

- Object.vue
  - Blockly 生成并执行脚本：`scriptingService.execute_python_code(code, 0)`
  - 其余模型变换可扩展为 `sceneService.actor_operation`

- AITalkBar.vue
  - 发送消息：`aiService.send_message_to_ai(JSON.stringify({message: '...' }))`
  - 接收响应：RouteDockWidget 将 `ai_response` 转成 `window.receiveAIMessage(data)` 回调

- Pet.vue
  - 双击呼出 AITalkBar：`appService.add_dock_widget("AITalkBar", "/AITalkBar", 'left', ...)`
  - 标题/拖拽条接入 useDragResize，随鼠标移动 Dock

## 路由与资源
- 路由采用 Hash 模式，主入口为 Frontend/dist/index.html
- 各 Dock 页通过 fragment（hash）方式加载，例如 `/Object?sceneName=...`
- index.html 使用相对路径引入 `qwebchannel.js`，保证 file:/// 以及打包后的可访问性

## 事件与信号对照
- appService.add_dock_widget → 后端 BrowserWidget.AddDockWidget → 创建 Dock
- appService.send_message_to_dock → 后端 RouteDockWidget.dock_event → 处理 drag/float/resize
- sceneService.actor_created/scene_loaded → SceneBar 监听，更新 UI
- aiService.ai_response → 通过 window.receiveAIMessage(...) 通知 AITalkBar

## 编码约定
- 所有服务调用前 `await window.webChannelReady`
- 发送到 Dock 的事件必须包含 `routename`
- add_dock_widget 的 `size` 要传 JSON 字符串（例如 `JSON.stringify({width:520,height:640})`）
- 组件卸载时记得移除事件监听（mousemove/mouseup/…）

## 常见问题
- QWebChannel 未连接：检查 index.html 是否加载 qwebchannel.js、main.js 是否 new QWebChannel
- 拖拽不动：检查 window.__dockRouteName 是否注入、是否先切为浮动、前端是否通过 appService 发送
- Object/SceneBar 打不开：确认 routename 唯一且 BrowserWidget 未拦截为“切换/关闭”行为（同名会先关）
- AI 无响应：确保 aiService 可用、网络/qa_one_sync 可用；查看控制台是否有 JSON 格式错误

