from __future__ import annotations

import json
from pathlib import Path

from Backend.core.project.models import ProjectAsset, SceneDocument
from Backend.application.services.scene_service import SceneApplicationService
from Backend.shared.logging import get_logger


logger = get_logger(__name__)


class ProjectApplicationService:
    def __init__(self, scene_service: SceneApplicationService) -> None:
        self.scene_service = scene_service

    def import_model(self, scene_name: str, model_path: str) -> str:
        payload = self.scene_service.add_actor(scene_name, model_path)
        return json.dumps({"status": "success", **payload})

    def import_scene_file(self, scene_name: str, json_content: str) -> str:
        data = json.loads(json_content)
        actors = []
        for actor in data.get("actors", []):
            result = self.scene_service.add_actor(scene_name, actor["path"])
            actors.append(result.get("actor"))
        logger.info("Scene '%s' imported from payload", scene_name)
        return json.dumps({"status": "success", "scene": scene_name, "actors": actors})

    def export_scene_file(self, scene_name: str, destination: Path) -> Path:
        snapshot = self.scene_service.export_scene(scene_name)
        destination.write_text(snapshot, encoding="utf-8")
        logger.info("Scene '%s' exported to %s", scene_name, destination)
        return destination

    def build_scene_document(self, scene_name: str) -> SceneDocument:
        data = json.loads(self.scene_service.export_scene(scene_name))
        actors = [
            ProjectAsset(name=a["name"], path=Path(a["path"]), type=Path(a["path"]).suffix.lstrip("."))
            for a in data.get("actors", [])
        ]
        return SceneDocument(name=scene_name, actors=actors)
