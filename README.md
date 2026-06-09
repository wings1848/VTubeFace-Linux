# OpenSeeFace — Linux 端 VTube Studio 面捕方案

[![OSF.png](images/OSF.png)](https://github.com/emilianavt/OpenSeeFace)

> 📖 **English: [README_en.md](README_en.md)**

基于 MobileNetV3 的人脸特征点检测项目。通过摄像头或视频文件进行实时面部追踪，通过 UDP 协议将数据发送给 VTube Studio 等应用。

---

## 特性

- **实时面部追踪**：基于 ONNX Runtime 推理，支持 GPU（CUDA）和 CPU
- **多模型可选**：8 个模型覆盖极速到高精度
- **VTube Studio 集成**：UDP 协议直接对接，零配置
- **多人脸追踪**：最多 4 张人脸同时追踪
- **头部姿态**：3D 旋转 + 位移 + 欧拉角
- **表情特征**：14 维面部动作参数（眼、眉、嘴）
- **跨平台**：Linux / Windows

## 快速上手

```bash
git clone https://github.com/wings1848/OpenSeeFace
cd OpenSeeFace
./start_opensseface.sh
```

首次运行自动创建虚拟环境、安装依赖、进入交互式向导。

## 文档

| 章节 | 说明 |
|------|------|
| [快速开始](docs/guides/quick-start.md) | 5 分钟跑起来 |
| [安装指南](docs/guides/installation.md) | 手动安装与环境配置 |
| [VTube Studio 集成](docs/guides/vtube-studio-setup.md) | UDP 配置细节 |
| [CLI 参考](docs/reference/cli.md) | 全部 30+ 参数详解 |
| [配置文件](docs/reference/config.md) | JSON 配置格式 |
| [UDP 协议](docs/reference/udp-protocol.md) | 网络数据包格式 |
| [模型选择](docs/reference/models.md) | 各模型性能对比 |
| [架构概览](docs/development/architecture.md) | 核心模块与数据流 |
| [常见问题](docs/guides/troubleshooting.md) | 故障排查 |
| [CHANGELOG](docs/changelog/CHANGELOG.md) | 完整变更日志 |
| [优化报告](docs/reports/OPTIMIZATION_REPORT.md) | 性能优化记录 |
| [经验总结](docs/reports/EXPERIENCE.md) | 开发经验 |

## 手动运行

## 管理命令

```bash
python -m openseeface start       # 后台启动
python -m openseeface stop        # 停止
python -m openseeface status      # 查看状态
python -m openseeface configure   # 交互式配置
python -m openseeface benchmark   # 基准测试
```

## 手动运行

```bash
# 激活虚拟环境后
python -m openseeface \
  -c 0 -F 30 --model 3 --try-hard 1 \
  --gaze-tracking 1 --max-threads 2 \
  -i 127.0.0.1 -p 11573 --visualize 1
```

## GPU 加速

支持 NVIDIA GPU 加速（onnxruntime-gpu + CUDA 12.x）。

启动脚本自动检测 GPU 并安装对应依赖。手动安装：

```bash
uv pip install -e ".[gpu]"   # GPU 版
uv pip install -e ".[cpu]"   # CPU 版
```

GTX 1660 Ti 实测模型 3 从 125 → 210 FPS（×1.68 加速）。

## 相关项目

- [原项目 OpenSeeFace](https://github.com/emilianavt/OpenSeeFace)
- [VSeeFace](https://www.vseeface.icu/)（3D 模型驱动）
- [VTube Studio](https://denchisoft.com/)（Live2D 驱动）

## 许可

BSD 2-Clause License。第三方库许可见 [licenses/](licenses/)。
