# Backend 说明

本目录包含编辑器后端（PySide6 + QtWebEngine）代码，采用“服务化 + 薄桥”架构：

- ui/
  - browser_widget.py：主 Web 容器，负责 Dock 创建/销毁与 WebChannel 接线
  - dock_widget.py：Dock 容器，处理拖拽/缩放事件
- utils/
  - webchannel_helper.py：统一注册/清理 WebChannel 与服务对象
  - bridge.py：后端信号/槽聚合点，优先委托至服务对象
  - app_service.py / scene_service.py / project_service.py / scripting_service.py / ai_service.py：领域服务
  - central_manager.py：Dock 注册表
  - 其它：scene_manager.py / scene.py / engine_object_factory.py 等

运行方式：
- 先构建 Frontend 的 dist 目录
- 运行 Backend/main.py

环境变量（默认关闭 GPU 与使用软件渲染，可按需调整）：
- QTWEBENGINE_DISABLE_GPU=1
- QTWEBENGINE_CHROMIUM_FLAGS=--disable-gpu --disable-gpu-compositing --enable-logging=stderr
- QT_QUICK_BACKEND=software
- QT_OPENGL=software
- QT_DISABLE_DIRECT_COMPOSITION=1

说明：
- 不再暴露 pyBridge；前端通过 appService/sceneService/... 访问后端功能
- Dock 拖拽/缩放事件通过 appService.send_message_to_dock 传递，负载需携带 routename

