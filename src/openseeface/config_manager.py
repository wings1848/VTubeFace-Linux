"""
OpenSeeFace 配置管理
====================
JSON 格式配置文件读写，支持从旧 .facetracker_config 迁移。

配置路径: config/config.json (相对于项目根目录)
旧配置路径: config/.facetracker_config
"""

import json
import os
import shlex
from pathlib import Path
from typing import Any, Dict, Optional

# ---------- 路径 ----------
_PROJECT_ROOT: Optional[Path] = None


def _get_project_root() -> Path:
    """获取项目根目录（向上搜索标记文件或约定路径）。"""
    global _PROJECT_ROOT
    if _PROJECT_ROOT is not None:
        return _PROJECT_ROOT

    # 优先从当前文件位置推导
    this_file = Path(__file__).resolve()  # .../src/openseeface/config_manager.py
    # src/openseeface/ 的父级 src/ 的父级 = 项目根
    candidate = this_file.parent.parent.parent
    if (candidate / "pyproject.toml").exists() or (candidate / "config").is_dir():
        _PROJECT_ROOT = candidate
        return _PROJECT_ROOT

    # fallback: 当前工作目录
    _PROJECT_ROOT = Path.cwd()
    return _PROJECT_ROOT


# ---------- 默认配置 ----------
DEFAULT_CONFIG = {
    "general": {
        "mode": "camera",           # camera | video
    },
    "camera": {
        "id": 0,
        "fps": 30,
        "width": 640,
        "height": 480,
        "mirror": False,
    },
    "video": {
        "path": "",
    },
    "tracking": {
        "model": 3,
        "quality_preset": 3,        # 1=极致性能, 2=快速, 3=均衡, 4=高质量, 5=眨眼优化
        "detection_threshold": 0.6,
        "threshold": 0.85,
        "no_3d_adapt": False,
        "try_hard": True,
        "gaze": True,
        "max_threads": 4,
    },
    "network": {
        "ip": "127.0.0.1",
        "port": 11573,
    },
    "logging": {
        "data": "",
        "output": "",
        "visualize": False,
    },
}


# ---------- 旧配置 → 新配置 映射 ----------
_OLD_TO_NEW = {
    "RUN_MODE":              ("general", "mode", lambda v: "camera" if v.strip('"') == "1" else "video"),
    "CAM_ID":                ("camera", "id", int),
    "CAM_FPS":               ("camera", "fps", int),
    "CAM_W":                 ("camera", "width", int),
    "CAM_H":                 ("camera", "height", int),
    "MIRROR":                ("camera", "mirror", lambda v: v.strip('"') == "1"),
    "VIDEO_PATH":            ("video", "path", lambda v: v.strip('"')),
    "MODEL":                 ("tracking", "model", int),
    "QUALITY_PRESET":        ("tracking", "quality_preset", int),
    "DETECTION_THRESHOLD":   ("tracking", "detection_threshold", float),
    "THRESHOLD":             ("tracking", "threshold", float),
    "NO_3D_ADAPT":           ("tracking", "no_3d_adapt", lambda v: v.strip('"') == "1"),
    "TRY_HARD":              ("tracking", "try_hard", lambda v: v.strip('"') == "1"),
    "GAZE":                  ("tracking", "gaze", lambda v: v.strip('"') == "1"),
    "MAX_THREADS":           ("tracking", "max_threads", int),
    "UDP_IP":                ("network", "ip", lambda v: v.strip('"')),
    "UDP_PORT":              ("network", "port", int),
    "LOG_DATA":              ("logging", "data", lambda v: v.strip('"')),
    "LOG_OUTPUT":            ("logging", "output", lambda v: v.strip('"')),
    "VISUALIZE":             ("logging", "visualize", lambda v: v.strip('"') == "1"),
}


class ConfigManager:
    """管理 OpenSeeFace 配置。"""

    def __init__(self, config_dir: Optional[Path] = None):
        self.root = _get_project_root()
        self.config_dir = Path(config_dir) if config_dir else (self.root / "config")
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.config_path = self.config_dir / "config.json"
        self._data: Dict[str, Any] = {}

    # ── 读写 ──────────────────────────────────────────────

    def load(self) -> Dict[str, Any]:
        """加载配置，如果不存在则创建默认配置。"""
        if self.config_path.exists():
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    self._data = json.load(f)
                # 补全新字段
                self._merge_defaults()
                return self._data
            except (json.JSONDecodeError, OSError):
                pass

        # 尝试从旧配置迁移
        if self._migrate_old_config():
            return self._data

        # 使用默认配置
        self._data = dict(DEFAULT_CONFIG)
        self.save()
        return self._data

    def save(self) -> None:
        """保存配置到文件。"""
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(self._data, f, indent=2, ensure_ascii=False)
            f.write("\n")

    @property
    def data(self) -> Dict[str, Any]:
        return self._data

    # ── 旧配置迁移 ────────────────────────────────────────

    def _migrate_old_config(self) -> bool:
        """尝试从旧 .facetracker_config 迁移。"""
        old_path = self.config_dir / ".facetracker_config"
        if not old_path.exists():
            return False

        import re
        parsed: Dict[str, str] = {}
        with open(old_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, _, val = line.partition("=")
                    parsed[key.strip()] = val.strip()

        new_config = dict(DEFAULT_CONFIG)
        for old_key, (section, field, converter) in _OLD_TO_NEW.items():
            if old_key in parsed:
                try:
                    new_config[section][field] = converter(parsed[old_key])
                except (ValueError, TypeError):
                    pass

        self._data = new_config
        self.save()

        # 重命名旧配置作为备份
        old_path.rename(old_path.with_suffix(".bak"))
        return True

    def _merge_defaults(self) -> None:
        """补全新版新增的字段（配置升级兼容）。"""
        for section, fields in DEFAULT_CONFIG.items():
            if section not in self._data:
                self._data[section] = {}
            for field, default in fields.items():
                if field not in self._data[section]:
                    self._data[section][field] = default

    # ── 转换为 CLI 参数 ────────────────────────────────────

    def to_cli_args(self) -> list:
        """将配置转换为 facetracker CLI 参数列表。"""
        cfg = self._data
        args = []

        if cfg["general"]["mode"] == "video" and cfg["video"]["path"]:
            args.extend(["-c", cfg["video"]["path"]])
        else:
            args.extend(["-c", str(cfg["camera"]["id"])])
            args.extend(["-F", str(cfg["camera"]["fps"])])
            args.extend(["-W", str(cfg["camera"]["width"])])
            args.extend(["-H", str(cfg["camera"]["height"])])
            if cfg["camera"]["mirror"]:
                args.append("-M")

        tracking = cfg["tracking"]
        args.extend(["--model", str(tracking["model"])])
        args.extend(["--detection-threshold", str(tracking["detection_threshold"])])
        args.extend(["--threshold", str(tracking["threshold"])])
        args.extend(["--no-3d-adapt", "1" if tracking["no_3d_adapt"] else "0"])
        args.extend(["--try-hard", "1" if tracking["try_hard"] else "0"])
        args.extend(["--gaze-tracking", "1" if tracking["gaze"] else "0"])
        args.extend(["--max-threads", str(tracking["max_threads"])])

        network = cfg["network"]
        args.extend(["-i", network["ip"]])
        args.extend(["-p", str(network["port"])])

        logging = cfg["logging"]
        if logging.get("data"):
            args.extend(["--log-data", logging["data"]])
        if logging.get("output"):
            args.extend(["--log-output", logging["output"]])
        if logging["visualize"]:
            args.extend(["-v", "3"])
        else:
            args.extend(["-v", "0", "--silent", "1"])

        return args

    def to_summary(self) -> str:
        """返回配置摘要（人类可读）。"""
        cfg = self._data
        lines = []
        if cfg["general"]["mode"] == "video":
            lines.append(f"  视频文件 : {cfg['video']['path']}")
        else:
            cam = cfg["camera"]
            lines.append(f"  摄像头   : {cam['id']} ({cam['width']}x{cam['height']} @ {cam['fps']}FPS)")

        t = cfg["tracking"]
        presets = {1: "极致性能", 2: "快速", 3: "均衡", 4: "高质量", 5: "眨眼优化", 6: "自定义"}
        preset_name = presets.get(t["quality_preset"], "自定义")
        lines.append(f"  质量预设 : {preset_name}")
        lines.append(f"  模型     : {t['model']}")
        lines.append(f"  阈值     : 检测={t['detection_threshold']}, 追踪={t['threshold']}")
        lines.append(f"  3D自适应 : {'开启' if t['no_3d_adapt'] else '关闭'}")
        lines.append(f"  Try-Hard : {'开启' if t['try_hard'] else '关闭'}")
        lines.append(f"  Gaze追踪 : {'开启' if t['gaze'] else '关闭'}")
        lines.append(f"  线程数   : {t['max_threads']}")

        n = cfg["network"]
        lines.append(f"  UDP 输出 : {n['ip']}:{n['port']}")

        return "\n".join(lines)


# ── 便捷函数 ──────────────────────────────────────────────

def get_config() -> ConfigManager:
    """获取配置管理器实例（已加载）。"""
    cm = ConfigManager()
    cm.load()
    return cm
