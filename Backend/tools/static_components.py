from PySide6.QtCore import QUrl

from Backend.config.settings import get_settings

settings = get_settings()
root_dir = settings.paths.repo_root
html_path = settings.paths.frontend_dist
url = QUrl.fromLocalFile(str(html_path))
