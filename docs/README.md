# OpenSeeFace 文档

> 基于 MobileNetV3 的人脸特征点检测项目，通过 UDP 协议将实时面部追踪数据发送给 VTube Studio 等应用。

## 🚀 管理命令

```bash
python -m openseeface start       # 后台启动面捕
python -m openseeface stop        # 停止
python -m openseeface status      # 查看状态
python -m openseeface configure   # 交互式配置
python -m openseeface benchmark   # 基准测试
```

或通过启动脚本：`./start_opensseface.sh`（Linux） / `start_opensseface.bat`（Windows）

## 📖 使用指南

- [快速开始](guides/quick-start.md) —— 5 分钟跑起来
- [安装指南](guides/installation.md)
- [VTube Studio 集成](guides/vtube-studio-setup.md)
- [Unity 集成](guides/unity-integration.md)
- [常见问题排查](guides/troubleshooting.md)

## 📚 参考手册

- [CLI 参数参考](reference/cli.md) —— 全部启动参数 + 管理子命令详解
- [配置文件参考](reference/config.md) —— JSON 配置格式说明
- [UDP 协议规范](reference/udp-protocol.md) —— 网络数据包格式
- [模型选择参考](reference/models.md) —— 各模型质量与速度对比

## 🔧 开发文档

- [架构概览](development/architecture.md) —— 模块职责与数据流
- [构建指南](development/building.md)
- [贡献指南](development/contributing.md)

## 📋 变更日志

- [CHANGELOG](changelog/CHANGELOG.md)

## 📊 报告

- [性能优化报告](reports/OPTIMIZATION_REPORT.md)
- [经验总结](reports/EXPERIENCE.md)
