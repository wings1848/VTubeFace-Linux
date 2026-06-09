"""
OpenSeeFace CLI 子命令
======================
提供 configure / start / stop / status / benchmark 命令。
"""

import os
import signal
import subprocess
import sys
import time
from pathlib import Path

from .config_manager import get_config, ConfigManager


# ── 路径 ──────────────────────────────────────────────────

def _get_root() -> Path:
    return ConfigManager().root


def _get_run_dir() -> Path:
    d = _get_root() / "run"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _pid_file() -> Path:
    return _get_run_dir() / "daemon.pid"


def _log_file() -> Path:
    return _get_run_dir() / "daemon.log"


# ── 颜色输出（跨平台） ─────────────────────────────────────

def _color(code: int, text: str) -> str:
    if sys.platform == "win32":
        return text
    return f"\033[{code}m{text}\033[0m"


def _info(msg: str) -> None:
    print(f"{_color(36, '[INFO]')}   {msg}")


def _ok(msg: str) -> None:
    print(f"{_color(32, '[OK]')}    {msg}")


def _warn(msg: str) -> None:
    print(f"{_color(33, '[WARN]')}  {msg}")


def _err(msg: str) -> None:
    print(f"{_color(31, '[ERROR]')} {msg}")


# ── 进程管理 ──────────────────────────────────────────────

def _read_pid() -> int | None:
    """读取 PID 文件。"""
    pid_path = _pid_file()
    if pid_path.exists():
        try:
            return int(pid_path.read_text().strip())
        except (ValueError, OSError):
            return None
    return None


def _is_pid_alive(pid: int) -> bool:
    """检查 PID 是否存活。"""
    try:
        os.kill(pid, 0)
        return True
    except (OSError, ProcessLookupError):
        return False


def _kill_pid(pid: int, force: bool = False) -> bool:
    """尝试终止进程。"""
    try:
        if force:
            os.kill(pid, signal.SIGKILL)
        else:
            os.kill(pid, signal.SIGTERM)
        return True
    except (OSError, ProcessLookupError):
        return False


def _find_openseeface_processes() -> list[int]:
    """查找所有 openseeface 守护进程（非当前进程）。"""
    pids = []
    try:
        # 用更精确的匹配模式，排除 pgrep 自身和调用者
        result = subprocess.run(
            ["pgrep", "-f", "python3.*-m openseeface"],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0 and result.stdout.strip():
            my_pid = os.getpid()
            for pid_str in result.stdout.strip().split():
                pid = int(pid_str)
                if pid != my_pid:
                    pids.append(pid)
    except (FileNotFoundError, subprocess.TimeoutExpired, ValueError):
        pass
    return pids


def _stop_daemon(quiet: bool = False) -> bool:
    """停止守护进程。返回 True 表示有进程被停止。"""
    stopped = False
    pid = _read_pid()

    if pid and _is_pid_alive(pid):
        if not quiet:
            print(f"正在停止 openseeface (PID: {pid})...")
        _kill_pid(pid, force=False)
        for _ in range(10):
            if not _is_pid_alive(pid):
                break
            time.sleep(0.2)
        if _is_pid_alive(pid):
            _kill_pid(pid, force=True)
            time.sleep(0.3)
        stopped = True
        if not quiet:
            _ok("已停止")

    # 清理 PID 文件
    pid_path = _pid_file()
    if pid_path.exists():
        pid_path.unlink()

    return stopped


# ── 子命令 ────────────────────────────────────────────────

def cmd_configure() -> int:
    """
    交互式配置向导。
    替代原 bash 脚本中 200+ 行的交互问答。
    """
    cm = get_config()
    cfg = cm.data

    print(f"\n{_color(1, '━━━ OpenSeeFace 配置向导 ━━━')}\n")
    print("（直接回车使用方括号内的默认值）\n")

    # ── 运行模式 ──
    mode = input(f"  运行模式 [camera/视频路径] (默认: camera): ").strip()
    if mode:
        # 检查是否为文件路径
        if os.path.isfile(mode):
            cfg["general"]["mode"] = "video"
            cfg["video"]["path"] = mode
        else:
            cfg["general"]["mode"] = mode

    if cfg["general"]["mode"] == "video":
        path = input(f"  视频文件路径 (当前: {cfg['video']['path']}): ").strip()
        if path:
            cfg["video"]["path"] = path
    else:
        # ── 摄像头参数 ──
        cam_default = cfg["camera"]["id"]
        cam = input(f"  摄像头编号 (默认: {cam_default}): ").strip()
        if cam:
            cfg["camera"]["id"] = int(cam)

        fps_default = cfg["camera"]["fps"]
        fps = input(f"  帧率 FPS (默认: {fps_default}): ").strip()
        if fps:
            cfg["camera"]["fps"] = int(fps)

        w_default = cfg["camera"]["width"]
        w = input(f"  采集宽度 (默认: {w_default}): ").strip()
        if w:
            cfg["camera"]["width"] = int(w)

        h_default = cfg["camera"]["height"]
        h = input(f"  采集高度 (默认: {h_default}): ").strip()
        if h:
            cfg["camera"]["height"] = int(h)

        mirror = input(f"  水平镜像 [0=关闭, 1=开启] (默认: {'1' if cfg['camera']['mirror'] else '0'}): ").strip()
        if mirror:
            cfg["camera"]["mirror"] = mirror == "1"

    # ── 质量预设 ──
    print(f"\n  质量预设:")
    presets = [
        "1) 🚀 极致性能  — 最低延迟, 适合低配设备 (模型 -1)",
        "2) ⚡ 快速      — 平衡速度与质量 (模型 0)",
        "3) 🎯 均衡      — 推荐默认 (模型 2)",
        "4) ✨ 高质量    — 最佳追踪精度 (模型 3)",
        "5) 😉 眨眼优化  — 针对眨眼检测优化 (模型 4)",
        "6) 🔧 自定义    — 自行配置各项参数",
    ]
    for p in presets:
        print(f"    {p}")
    qp = input(f"  选择 [1-6] (默认: {cfg['tracking']['quality_preset']}): ").strip()
    if qp:
        cfg["tracking"]["quality_preset"] = int(qp)

    # ── 模型 ──
    m_default = cfg["tracking"]["model"]
    m = input(f"  模型编号 -3~4 (默认: {m_default}): ").strip()
    if m:
        cfg["tracking"]["model"] = int(m)

    # ── 阈值 ──
    dt = input(f"  检测阈值 (默认: {cfg['tracking']['detection_threshold']}): ").strip()
    if dt:
        cfg["tracking"]["detection_threshold"] = float(dt)
    t = input(f"  追踪阈值 (默认: {cfg['tracking']['threshold']}): ").strip()
    if t:
        cfg["tracking"]["threshold"] = float(t)

    # ── 追踪选项 ──
    for key, label, default in [
        ("no_3d_adapt", "3D自适应 [0=开启, 1=关闭]", cfg["tracking"]["no_3d_adapt"]),
        ("try_hard", "Try-Hard 模式 [0=关闭, 1=开启]", cfg["tracking"]["try_hard"]),
        ("gaze", "Gaze 视线追踪 [0=关闭, 1=开启]", cfg["tracking"]["gaze"]),
    ]:
        v = input(f"  {label} (默认: {'1' if default else '0'}): ").strip()
        if v:
            cfg["tracking"][key] = v == "1"

    # ── 线程数 ──
    mt = input(f"  最大线程数 (默认: {cfg['tracking']['max_threads']}): ").strip()
    if mt:
        cfg["tracking"]["max_threads"] = int(mt)

    # ── 网络 ──
    ip = input(f"  UDP 目标 IP (默认: {cfg['network']['ip']}): ").strip()
    if ip:
        cfg["network"]["ip"] = ip
    port = input(f"  UDP 端口 (默认: {cfg['network']['port']}): ").strip()
    if port:
        cfg["network"]["port"] = int(port)

    # ── 保存 ──
    cm.save()
    print()
    _ok("配置已保存")
    print()
    print(cm.to_summary())
    return 0


def cmd_start() -> int:
    """后台启动守护进程。"""
    # 检查旧 PID 文件（但不扫描进程列表，避免自伤）
    old_pid = _read_pid()
    if old_pid and _is_pid_alive(old_pid):
        _info(f"正在停止旧进程 (PID: {old_pid})...")
        _kill_pid(old_pid, force=False)
        for _ in range(10):
            if not _is_pid_alive(old_pid):
                break
            time.sleep(0.2)
        if _is_pid_alive(old_pid):
            _kill_pid(old_pid, force=True)
            time.sleep(0.3)
        _ok("旧进程已停止")
    # 清理旧 PID 文件
    pp = _pid_file()
    if pp.exists():
        pp.unlink()

    cm = get_config()
    cfg = cm.data
    args = cm.to_cli_args()

    # 构建完整命令
    python = sys.executable
    cmd = [python, "-m", "openseeface"] + args

    # 打印配置摘要
    print()
    print(f"{_color(1, '━━━ 启动 OpenSeeFace ━━━')}\n")
    print(cm.to_summary())
    print()

    # 启动子进程
    log = _log_file()
    try:
        proc = subprocess.Popen(
            cmd,
            stdout=open(log, "w"),
            stderr=subprocess.STDOUT,
            stdin=subprocess.DEVNULL,
            start_new_session=True,
        )
    except FileNotFoundError as e:
        _err(f"启动失败: {e}")
        return 1

    # 写 PID 文件
    pid_path = _pid_file()
    pid_path.write_text(str(proc.pid))

    _ok(f"已启动 (PID: {proc.pid})")
    print(f"  日志: {log}")
    print(f"  PID:  {pid_path}")
    print()
    print(f"  管理命令:")
    print(f"    查看日志: tail -f {log}")
    print(f"    停止进程: python -m openseeface stop")
    print()

    return 0


def cmd_stop() -> int:
    """停止守护进程。"""
    print()
    if _stop_daemon():
        print()
        _ok("所有进程已停止")
    else:
        _info("没有正在运行的面捕进程")
    return 0


def cmd_status() -> int:
    """查看守护进程状态。"""
    print()
    print(f"{_color(1, '━━━ OpenSeeFace 状态 ━━━')}\n")

    pid = _read_pid()
    if pid and _is_pid_alive(pid):
        # 获取进程信息
        try:
            import psutil
            p = psutil.Process(pid)
            uptime = time.time() - p.create_time()
            cpu = p.cpu_percent()
            mem = p.memory_info().rss / 1024 / 1024
            print(f"  状态     : {_color(32, '运行中')}")
            print(f"  PID      : {pid}")
            print(f"  运行时间 : {uptime:.0f} 秒 ({uptime/60:.1f} 分钟)")
            print(f"  CPU      : {cpu:.1f}%")
            print(f"  内存     : {mem:.0f} MiB")
        except ImportError:
            print(f"  状态     : {_color(32, '运行中')}")
            print(f"  PID      : {pid}")

        # 读取最近日志
        log = _log_file()
        if log.exists() and log.stat().st_size > 0:
            print()
            print(f"  最近日志 ({log.name}):")
            try:
                lines = log.read_text().strip().splitlines()
                for line in lines[-5:]:
                    print(f"    {line}")
            except OSError:
                pass
    else:
        print(f"  状态     : {_color(31, '未运行')}")

    # 配置信息
    cm = get_config()
    print()
    print(f"  配置文件 : {cm.config_path}")
    print()
    print(cm.to_summary())

    return 0


def cmd_benchmark() -> int:
    """运行基准测试。"""
    print()
    print(f"{_color(1, '━━━ OpenSeeFace Benchmark ━━━')}\n")

    from .facetracker import main as run_facetracker
    import argparse

    # 构建 benchmark 参数
    sys.argv = [sys.argv[0], "--benchmark", "1", "--max-threads", "4"]
    try:
        run_facetracker()
    except SystemExit:
        pass
    return 0


def cmd_help() -> int:
    """显示 CLI 子命令帮助。"""
    print("""
OpenSeeFace 管理命令
====================

用法:
  python -m openseeface <command> [选项]

命令:
  configure    交互式配置向导
  start        后台启动面捕守护进程
  stop         停止面捕守护进程
  status       查看运行状态
  benchmark    运行基准测试
  help         显示本帮助
  [参数...]    直接运行面捕追踪（原有 CLI 参数）

示例:
  python -m openseeface configure     # 配置
  python -m openseeface start         # 启动
  python -m openseeface stop          # 停止
  python -m openseeface status        # 查看状态
  python -m openseeface -c 0          # 直接运行追踪
""")
    return 0


# ── 命令路由表 ────────────────────────────────────────────

COMMANDS = {
    "configure": cmd_configure,
    "start": cmd_start,
    "stop": cmd_stop,
    "status": cmd_status,
    "benchmark": cmd_benchmark,
    "help": cmd_help,
    "--help": cmd_help,
    "-h": cmd_help,
}
