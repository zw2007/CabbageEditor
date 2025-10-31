import os
import sys
import importlib.util
import glob
import queue

# 强制软件渲染，避免 GPU/Direct Composition 对 QtWebEngine 的兼容问题
os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = "--disable-gpu --disable-gpu-compositing --enable-logging=stderr"
os.environ["QTWEBENGINE_DISABLE_GPU"] = "1"
os.environ["QT_QUICK_BACKEND"] = "software"
os.environ['QT_OPENGL'] = 'software'
os.environ["QT_DISABLE_DIRECT_COMPOSITION"] = "1"

_cleaned_up = False

from Backend.ui import main_window

# 初始化 Qt 应用与主窗口
app, window = main_window.init_app()
msg_queue = queue.Queue()


def cleanup_blockly_files():
    """删除上次运行残留的 blockly 脚本与入口文件，避免热更新时导入冲突。"""
    global _cleaned_up
    try:
        if _cleaned_up:
            return

        current_dir = os.path.dirname(os.path.abspath(__file__))
        runscript_path = os.path.join(current_dir, 'runScript.py')
        if os.path.exists(runscript_path):
            try:
                os.remove(runscript_path)
                print(f"已删除: {runscript_path}")
            except PermissionError:
                print(f"无法删除 {runscript_path}，文件可能被占用")

        script_dir = os.path.join(current_dir, 'script')
        if os.path.exists(script_dir):
            for file in glob.glob(os.path.join(script_dir, 'blockly_code*.py')):
                try:
                    os.remove(file)
                    print(f"已删除: {file}")
                except PermissionError:
                    print(f"无法删除 {file}，文件可能被占用")

        _cleaned_up = True
    except Exception as e:
        print(f"清理Blockly文件时出错: {str(e)}")


def run(isReload):
    """按需清理残留，热重载时清理模块缓存后调用 runScript.run()。"""
    global _cleaned_up
    if not _cleaned_up:
        cleanup_blockly_files()

    if (isReload):
        for module_name in list(sys.modules.keys()):
            if 'runScript' in module_name or 'script' in module_name:
                del sys.modules[module_name]
        print("python hotfix")

    runscript_spec = importlib.util.find_spec("runScript")
    if runscript_spec is not None:
        runScript = importlib.util.module_from_spec(runscript_spec)
        runscript_spec.loader.exec_module(runScript)
        try:
            runScript.run()
        except Exception as e:
            print(f"runScript.run 执行失败: {e}")

    if not msg_queue.empty():
        print(msg_queue.get())

    app.processEvents()


def put_queue(msg):
    msg_queue.put(msg)


if __name__ == '__main__':
    cleanup_blockly_files()
    while True:
        try:
            runscript_spec = importlib.util.find_spec("runScript")
            if runscript_spec is not None:
                runScript = importlib.util.module_from_spec(runscript_spec)
                runscript_spec.loader.exec_module(runScript)
                try:
                    runScript.run()
                except Exception as e:
                    print(f"runScript.run 执行失败: {e}")
            app.processEvents()
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"主循环异常: {e}")
            app.processEvents()
