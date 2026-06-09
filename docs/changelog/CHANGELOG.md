# OpenSeeFace 变更日志

> 本文件记录本 Fork 相对于上游的所有改动，按模块分类。

---

## 性能优化 (CPU)

### 1. `group_rects` 字典键类型优化
- **文件**: `tracker.py`
- **变更**: `str(rect)` → `tuple(rect)` 作为字典键
- **效果**: 消除每帧不必要的字符串哈希开销
- **风险**: 极低

### 2. Gaze 模型按需跳过
- **文件**: `tracker.py`
- **变更**: 单脸/多人脸推理路径均加入 `no_gaze` 检查，`--gaze-tracking 0` 时完全跳过 `get_eye_state`
- **效果**: 关闭眼球追踪时节省 2-5 ms/帧
- **风险**: 极低

### 3. 人脸检测自适应退避
- **文件**: `tracker.py`
- **变更**: 新增 `no_face_consecutive` 计数器。无人脸 >30 帧 → 每 3 帧检测一次；>90 帧 → 每 10 帧检测一次
- **效果**: 无人脸场景下减少 70-90% 检测开销
- **风险**: 低（有人脸后立即恢复正常频率）

### 4. `adjust_3d` 间隔控制
- **文件**: `tracker.py`
- **变更**: 新增 `adjust_3d_interval` 参数（默认 1）。仅当 `frame_count % interval == 0` 时调用 `adjust_3d()`
- **效果**: 可配置降低 CPU 占用
- **风险**: 极低（默认值保持原行为）

### 5. 低置信度跳过 3D 拟合
- **文件**: `tracker.py`
- **变更**: `conf <= 0.3` 时跳过 `estimate_depth` / `adjust_3d`，使用原始 landmark 边界框
- **效果**: 低质量检测时节省计算
- **风险**: 极低

### 6. UDP 批量打包
- **文件**: `facetracker.py`
- **变更**: 18 次独立 `struct.pack` + `bytearray` 调用合并为 5 次，使用 `=` 前缀确保标准对齐
- **效果**: 减少 Python 函数调用开销
- **风险**: 极低（UDP 二进制格式逐字节一致）

### 7. 移除冗余 `bytearray()` 包装
- **文件**: `facetracker.py`
- **变更**: landmark、3D 点、特征打包中删除不必要的 `bytearray()` 包装
- **效果**: 减少中间内存分配
- **风险**: 极低

### 8. GC 降频
- **文件**: `facetracker.py`
- **变更**: `gc.collect()` 从每帧 → 每 30 帧；新增 `gc.set_threshold(700, 10, 10)`
- **效果**: 减少 stop-the-world 卡顿
- **风险**: 低

---

## GPU 加速 (CUDA)

### 9. CUDA 推理支持
- **文件**: `tracker.py`, `retinaface.py`, `models/*_gpu.onnx`
- **变更**:
  - 安装 `onnxruntime-gpu==1.23.2` + CUDA 12.x 运行时 (`nvidia-cublas-cu12`, `nvidia-cuda-runtime-cu12`, `nvidia-cufft-cu12`)
  - 后升级至 `onnxruntime-gpu==1.26.0`（参见 #11）
  - 为 11 个 ONNX 模型创建 `_gpu.onnx` 版本：将 CPU 专用 `FusedConv` 分解为 `Conv + 激活函数`
  - `tracker.py`: 自动检测 `CUDAExecutionProvider`，有 GPU 则使用 `_gpu.onnx` + `['CUDAExecutionProvider', 'CPUExecutionProvider']`
  - `retinaface.py`: 新增 `providers` 参数，接收显式 provider 列表（避免 TensorRT 探测错误）
- **性能**: 1.4×–2.0× FPS 提升（GTX 1660 Ti）

### 10. pyproject.toml 依赖管理
- **文件**: `pyproject.toml`
- **变更**:
  - 添加 `packages` 配置（项目为扁平结构，逐文件声明）
  - `onnxruntime` / `onnxruntime-gpu` / nvidia 包改为 optional
  - 新增 `[tool.poetry.extras]`:
    - `cpu` → `onnxruntime`
    - `gpu` → `onnxruntime-gpu` + nvidia CUDA 运行时
  - 版本约束从 `^` 放宽为 `>=`

### 11. Python 3.14 + onnxruntime 1.26.0 升级
- **文件**: `pyproject.toml`, `start_opensseface.sh`, `uv.lock`
- **变更**:
  - Python 版本约束: `>=3.7,<3.11` → `>=3.11,<3.15`
  - onnxruntime 下限: `>=1.9.0` → `>=1.24.1`
  - onnxruntime-gpu 下限: `>=1.23.2` → `>=1.24.1`
  - `start_opensseface.sh`: `uv venv -p 3.10` → `uv venv -p 3.14`
  - 新增 `cuda_nvrtc`/`nvjitlink` 到 LD_LIBRARY_PATH（`_set_cuda_env`）
  - 实际安装: Python 3.14.5 + onnxruntime-gpu 1.26.0 + CUDA 12.9 运行时
- **性能**: Python 层（预处理/后处理/特征提取）加速 20–40%
- **风险**: 低（需 Python ≥ 3.11，所有核心依赖已支持 3.14）

---

## 启动脚本 (`start_opensseface.sh`)

### 11. 交互式配置向导
- **新增**: 8 步交互式配置流程（运行模式、摄像头、质量预设、多人脸、UDP、日志、线程、可视化）
- **5 种质量预设**: 极致性能 / 快速 / 均衡 / 高质量 / 眨眼优化 + 自定义
- **Benchmark 模式**: 测试全部 7 个模型性能

### 12. 配置持久化
- **新增**: `_save_config()` / `_load_config()`
- 首次运行后 22 个参数保存到 `.facetracker_config`
- 后续运行静默跳过交互式向导
- `./start_opensseface.sh reconfig` 强制重置

### 13. 自动虚拟环境管理
- **新增**: `_ensure_venv()` — 检测 `uv` 命令，自动创建 `.venv`
- pip 依赖通过 `uv pip install -e ".[cpu]"` 或 `uv pip install -e ".[gpu]"` 安装
- GPU 自动检测: `nvidia-smi` 可用 → 安装 `.[gpu]` extra；否则 `.[cpu]`

### 14. 进程管理
- **新增**: `_kill_one()` / `_stop_all_trackers()` — 优雅终止 → 强制终止 → pgrep 扫描残留
- `./start_opensseface.sh stop` — 一键安全停止
- 启动前自动清理所有残留 `facetracker.py` 进程

### 15. 输入校验
- `MODEL` 自动校验范围 (-3~4)
- `FACES` 自动校验范围 (1~4)
- `MAX_THREADS` 自动校验为正整数

### 16. 显示优化
- 命令行拼接修复：`(IFS=' '; echo "${CMD_ARGS[*]}")` 临时覆盖全局 `IFS=$'\n\t'`
- GPU 检测结果缓存 (`GPU_LABEL`)，避免重复 subshell
- 摄像头扫描一趟完成（`CAM_LIST` 数组 + `CAM_COUNT`）

### 17. 代码重构
- `_kill_one` / `_stop_all_trackers` 共享函数，消除 ~50 行重复
- `_save_config` 用关联数组循环替代逐行硬编码
- `_check_imports` 统一 4 个 Python 模块的导入检查

---

## 文档

### 18. README
- **README.md** (英文，~411 行):
  - 顶部中英双语链接
  - VTube Studio Linux 配置教程
  - GPU 加速章节（自动检测 + pyproject.toml extras）
  - 启动脚本使用说明
  - 配置持久化说明
- **README_zh.md** (中文，~368 行):
  - 同上，完整中文版
  - VTube Studio 配置（含 Flatpak 路径、`key=value` 格式）
  - `stop` 子命令用法

### 19. Docs
- `Docs/CHANGELOG.md` — 本文件
- `Docs/EXPERIENCE.md` — 可复用经验总结

---

---

## 项目重构 (结构 + 启动脚本 + 文档)

### 20. 目录结构重组
- **变更**: 从平铺根目录迁移为标准 `src/` 布局
- `facetracker.py`, `tracker.py` 等 9 个 .py → `src/openseeface/` 包
- `dshowcapture.py`, `escapi.py` → `src/openseeface/platform/`
- `model.py` → `src/openseeface/training/`
- `Source/` → `bindings/cpp/`
- `dshowcapture/`, `escapi/` DLL → `bindings/dll/`
- 启动脚本 → `start_opensseface.sh`（根目录）
- 配置文件 → `config/.facetracker_config`
- 运行时文件 → `run/`
- `Docs/`, `Images/`, `Licenses/` → 小写 `docs/`, `images/`, `licenses/`
- **效果**: 根目录从 30+ 条目减至 7 个核心文件
- **风险**: 低。所有内部导入已更新为相对导入，启动脚本路径已修正

### 21. 启动脚本 Python 化重构
- **变更**: 将 627 行 bash 脚本拆分为 Python CLI 模块 + 精简 bash 启动器
- 新增 `src/openseeface/cli.py`：`configure/start/stop/status/benchmark` 子命令
- 新增 `src/openseeface/config_manager.py`：JSON 配置读写 + 旧配置自动迁移
- 重写 `start_opensseface.sh`：从 627 行精简至 ~100 行
- 重写 `start_opensseface.bat`：Windows 启动脚本
- 更新 `src/openseeface/__main__.py`：子命令路由
- 配置文件格式从 bash `source` 改为 JSON（`config/config.json`）
- 旧 `.facetracker_config` 首次运行时自动迁移
- **效果**: 更安全、可维护、跨平台一致的启动体验
- **风险**: 低。`./start_opensseface.sh` 接口完全向后兼容

### 22. 文档重构
- **变更**: 从 5 篇扩至 11+ 篇，README 精简至 79 行
- `Docs/` → `docs/`，新增 guides/ reference/ development/ changelog/ reports/ 子目录
- 新增：快速开始、故障排查、CLI 完整参考、UDP 协议规范、配置参考、模型参考、架构概览
- `README.md`：411 行 → 79 行，作为项目入口 + 文档索引
- `README_en.md`：同步精简
- **效果**: 文档职责清晰，新用户上手更快

---

## 兼容性保证

- ✅ UDP 二进制格式逐字节一致
- ✅ 所有追踪 CLI 参数不变
- ✅ 类公共接口不变
- ✅ `./start_opensseface.sh` 接口完全向后兼容
- ✅ 旧 `.facetracker_config` 自动迁移到新 JSON 格式
- ✅ 无 GPU 自动回退 CPU
- ✅ 默认参数保持原行为
