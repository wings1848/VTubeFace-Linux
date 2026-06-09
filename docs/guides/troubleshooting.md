# 常见问题排查

## 安装类

### Python 版本问题

**症状**：安装依赖时报语法错误或不兼容。

**解决**：使用 Python 3.7–3.10。Python 3.11+ 可能因 `onnxruntime` 旧版本兼容性问题无法安装。

```bash
python3 --version
```

如果版本不对，使用 `pyenv` 或 `conda` 管理 Python 版本。

### onnxruntime 安装失败

**症状**：`pip install onnxruntime` 报错。

**解决**：

```bash
# CPU 版
uv pip install onnxruntime

# GPU 版（需要 CUDA 12.x）
uv pip install onnxruntime-gpu nvidia-cublas-cu12 nvidia-cuda-runtime-cu12 nvidia-cufft-cu12
```

如果使用启动脚本，它会自动处理依赖安装。

### CUDA 错误

**症状**：`CUDAExecutionProvider` 不可用或 `cudart` 加载失败。

**解决**：

1. 确认 NVIDIA 驱动版本 ≥ 525（`nvidia-smi`）
2. CUDA 12.x 运行时由 pip 包提供，无需单独安装 CUDA Toolkit
3. 启动脚本自动设置 `LD_LIBRARY_PATH`；手动运行时需自行设置：

```bash
export LD_LIBRARY_PATH="$(python3 -c 'import site; print(site.getsitepackages()[0])')/nvidia/cublas/lib:$(python3 -c 'import site; print(site.getsitepackages()[0])')/nvidia/cuda_runtime/lib:$LD_LIBRARY_PATH"
```

4. 如果使用 AMD 显卡或无 GPU，项目会自动回退到 CPU 推理

## 运行类

### 找不到摄像头

**症状**：`No device found` 或 `can't open camera`。

**解决**：

```bash
# Linux：列出视频设备
v4l2-ctl --list-devices

# 尝试不同的设备编号
./start_opensseface.sh reconfig
# 或在手动运行时指定
python -m openseeface -c 1
```

Windows 下使用 `--list-cameras 1` 查看可用摄像头。

### 检测不到人脸

**症状**：程序正常运行，但无面部识别数据输出。

**解决**：

1. 开启 `--try-hard 1`
2. 降低检测阈值：`--detection-threshold 0.4`
3. 关闭 3D 自适应：`--no-3d-adapt 1`
4. 确保光线充足，面部正对摄像头
5. 尝试更低质量的模型：`--model 0` 或 `--model -1`（对微小动作更敏感）

### 帧率过低

**症状**：FPS 远低于摄像头帧率。

**解决**：

1. 减少线程数：`--max-threads 1`（某些系统多线程反而降低性能）
2. 使用更低质量的模型：`--model 1` 或 `--model 0`
3. 关闭眼球追踪：`--gaze-tracking 0`
4. 关闭 3D 自适应：`--no-3d-adapt 1`
5. 降低摄像头分辨率：`-W 320 -H 240`
6. 使用 GPU 加速（确保安装了 `.[gpu]` extra）

### VTube Studio 未连接

**症状**：VTube Studio 显示"未连接"。

**解决**：

1. 检查 `ip.txt` 文件是否存在于 VTube Studio 的 `StreamingAssets` 目录
2. 确认 `ip.txt` 的 IP 和端口与 OpenSeeFace 的 `-i` / `-p` 一致
3. 确认 OpenSeeFace 正在运行
4. 防火墙是否阻止了 UDP 端口的通信
5. 重启 VTube Studio（它只在启动时读取 `ip.txt`）

## 性能类

### 如何选择最佳模型？

参考 [模型选择参考](../reference/models.md)。

简单规则：

- **GPU 够强**（NVIDIA）+ 追求精度 → 模型 3
- **需要眨眼检测** → 模型 4
- **CPU 推理** → 模型 1 或模型 -2
- **最低配置** → 模型 -1

### GPU 加速不生效

1. 确认安装了 `.[gpu]` extra 而非 `.[cpu]`
2. 确认 onnxruntime-gpu 版本 ≥ 1.17
3. 启动时检查日志输出，应看到 `CUDAExecutionProvider` 被使用
4. 如果提示 `cudart` 找不到，检查 `LD_LIBRARY_PATH` 设置

## 集成类

### UDP 收不到数据

1. 使用 `tcpdump` 或 Wireshark 抓包确认数据是否发出
2. 检查 IP 地址：本地回环用 `127.0.0.1`，跨机器用目标机器 IP
3. 检查端口是否被占用
4. 跨机器时 OpenSeeFace 需指定 `-i 0.0.0.0` 监听所有接口

### 跨机器延迟过高

1. 使用有线网络而非 Wi-Fi
2. 降低帧率：`-F 20`
3. 降低摄像头分辨率
