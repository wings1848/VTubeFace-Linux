"""
OpenSeeFace 入口
================
支持 CLI 子命令和原有追踪参数两种模式。
"""

import sys
import os


def main():
    # CLI 子命令列表（需要在导入 facetracker 之前检查，
    # 因为 facetracker 模块级代码会立即解析 argparse 参数）
    cli_commands = {
        "configure", "start", "stop", "status",
        "benchmark", "help",
    }

    if len(sys.argv) > 1 and sys.argv[1] in cli_commands:
        cmd = sys.argv[1]
        # 移除命令名，传给处理函数
        sys.argv = [sys.argv[0]] + sys.argv[2:]

        # 延迟导入，避免 facetracker 的 argparse 干扰
        if __package__ is None and not hasattr(sys, 'frozen'):
            sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            from openseeface.cli import COMMANDS
        else:
            from .cli import COMMANDS

        COMMANDS[cmd]()
    else:
        # 原有追踪模式
        if __package__ is None and not hasattr(sys, 'frozen'):
            sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            from openseeface.facetracker import main as run_facetracker
        else:
            from .facetracker import main as run_facetracker

        run_facetracker()


if __name__ == '__main__':
    main()
