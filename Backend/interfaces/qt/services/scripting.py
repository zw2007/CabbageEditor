from __future__ import annotations
import os
import json
from PySide6.QtCore import QObject, Signal, Slot
from Backend.config.settings import get_settings


class ScriptingService(QObject):
    script_error = Signal(str)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        settings = get_settings()
        self.script_dir = str(settings.paths.script_dir)
        os.makedirs(self.script_dir, exist_ok=True)

    @Slot(str, int)
    def execute_python_code(self, code: str, index: int) -> None:
        try:
            filename = "blockly_code.py"
            filepath = os.path.join(self.script_dir, filename)
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(code)

            run_script_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "runScript.py"
            )
            script_files = []
            for f in os.listdir(self.script_dir):
                if f.startswith("blockly_code") and f.endswith(".py"):
                    script_files.append(f.replace(".py", ""))

            run_script_content = ""
            for script in script_files:
                run_script_content += f"from Backend.script import {script}\n"
            run_script_content += "\n\ndef run():\n"
            for script in script_files:
                run_script_content += f"    {script}.run()\n"

            with open(run_script_path, "w", encoding="utf-8") as f:
                f.write(run_script_content)
            print(f"[DEBUG] 脚本文件创建成功: {filepath}")
            print(f"[DEBUG] runScript.py创建/覆盖成功: {run_script_path}")

            try:
                for sf in script_files:
                    sf_path = os.path.join(self.script_dir, f"{sf}.py")
                    if os.path.exists(sf_path):
                        with open(sf_path, 'r', encoding='utf-8') as sf_f:
                            content = sf_f.read()
                        new_content = content.replace('from utils.', 'from Backend.utils.').replace(
                            'from corona_engine_fallback import', 'from Backend.corona_engine_fallback import')
                        if new_content != content:
                            with open(sf_path, 'w', encoding='utf-8') as sf_f:
                                sf_f.write(new_content)
            except Exception:
                pass
        except Exception as e:
            print(f"[ERROR] 执行Python代码时出错: {str(e)}")
            error_response = {
                "status": "error",
                "message": str(e),
            }
            try:
                self.script_error.emit(json.dumps(error_response))
            except Exception:
                pass

