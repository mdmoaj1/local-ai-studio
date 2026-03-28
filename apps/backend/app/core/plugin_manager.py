from __future__ import annotations

import importlib.util
import json
from dataclasses import dataclass
from pathlib import Path

import app.engine_bootstrap  # noqa: F401

from engine.plugins.base_plugin import BasePlugin


@dataclass(frozen=True)
class DiscoveredPlugin:
    name: str
    title: str
    description: str
    relative_path: str


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def plugins_root() -> Path:
    return _repo_root() / "engine" / "plugins"


class PluginManager:
    """Filesystem discovery + dynamic import of `engine/plugins/*/plugin.py`."""

    def __init__(self) -> None:
        self._instances: dict[str, BasePlugin] = {}

    def discover(self) -> list[DiscoveredPlugin]:
        root = plugins_root()
        if not root.is_dir():
            return []
        out: list[DiscoveredPlugin] = []
        for child in sorted(root.iterdir()):
            if not child.is_dir():
                continue
            manifest = child / "plugin.json"
            plugin_file = child / "plugin.py"
            if not manifest.is_file() or not plugin_file.is_file():
                continue
            data = json.loads(manifest.read_text(encoding="utf-8"))
            pid = str(data.get("id", "")).strip()
            if not pid:
                continue
            rel = f"engine/plugins/{child.name}".replace("\\", "/")
            out.append(
                DiscoveredPlugin(
                    name=pid,
                    title=str(data.get("title", pid)),
                    description=str(data.get("description", "")),
                    relative_path=rel,
                ),
            )
        return out

    def load_plugin(self, relative_path: str, manifest_name: str) -> BasePlugin:
        if manifest_name in self._instances:
            return self._instances[manifest_name]
        root = _repo_root()
        mod_path = (root / relative_path).resolve()
        plugins_base = (root / "engine" / "plugins").resolve()
        try:
            mod_path.relative_to(plugins_base)
        except ValueError as exc:
            raise ValueError("Invalid plugin path") from exc
        plugin_py = mod_path / "plugin.py"
        if not plugin_py.is_file():
            raise FileNotFoundError(f"Missing plugin.py under {mod_path}")
        spec = importlib.util.spec_from_file_location(f"las_plugin_{manifest_name}", plugin_py)
        if spec is None or spec.loader is None:
            raise ImportError(f"Cannot load {plugin_py}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        cls = getattr(module, "Plugin", None)
        if cls is None:
            raise ImportError("plugin.py must define class Plugin")
        instance: BasePlugin = cls()
        self._instances[manifest_name] = instance
        return instance

    def clear_cache(self) -> None:
        self._instances.clear()
