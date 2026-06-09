# 快速开始

5 分钟启动面部追踪。

## 前置条件

- Python 3.7–3.10
- 摄像头或视频文件
- （可选）NVIDIA GPU + CUDA 12.x

## 1. 克隆项目

```bash
git clone https://github.com/wings1848/OpenSeeFace
cd OpenSeeFace
```

## 2. 运行

```bash
# Linux
./start_opensseface.sh

# Windows
start_opensseface.bat
```

首次运行时脚本会自动：

1. 创建 Python 虚拟环境（`uv` 自动管理）
2. 检测 NVIDIA GPU 并安装对应依赖（`.[gpu]` 或 `.[cpu]`）
3. 进入交互式配置向导，引导设置摄像头、质量预设、UDP 输出
4. 保存配置到 `.facetracker_config`，后台启动追踪

后续运行直接使用已保存配置静默启动，无需再次交互。

## 3. 验证

- 如果启用了 `--visualize 1`，会出现显示窗口，面部特征点实时叠加
- VTube Studio 端收到数据即表示连接成功

## 下一步

- [安装指南](installation.md) —— 手动安装和环境配置
- [CLI 参数参考](../reference/cli.md) —— 全部启动参数
- [VTube Studio 集成](vtube-studio-setup.md) —— 配置 UDP 接收
