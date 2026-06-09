# 架构概览

## 整体流程图

```
┌──────────┐    ┌───────────┐    ┌──────────────┐    ┌──────────┐
│  摄像头   │───▶│ InputReader│───▶│   Tracker    │───▶│ UDP 发送 │───▶ VTube Studio
│  视频文件  │    │  (OpenCV)  │    │  .predict()  │    │   socket  │
└──────────┘    └───────────┘    └──────────────┘    └──────────┘
                                       │
                                       ▼
                                 ┌──────────────┐
                                 │  ONNX Runtime │
                                 │  GPU / CPU    │
                                 │  推理引擎      │
                                 └──────────────┘
```

## 核心模块

### facetracker.py（主入口）

程序入口，负责：

- 解析命令行参数
- 初始化 `InputReader` 和 `Tracker`
- 主循环：读取帧 → 调用 `Tracker.predict()` → 打包 UDP 数据 → 发送
- 可视化渲染和视频输出

### tracker.py（追踪核心）

`Tracker` 类实现面部追踪的核心逻辑：

- **人脸检测**：基于 MobileNetV3 的 ONNX 模型进行特征点检测
- **多人脸管理**：扫描、跟踪、丢弃策略
- **3D 拟合**：PnP 求解计算头部旋转和位移
- **特征提取**：计算眼开合、眉毛位置、嘴巴形状等 14 维特征向量
- **模型自适应**：可选地调整 3D 模型以贴合个人脸型

### input_reader.py（输入抽象）

`InputReader` 统一摄像头和视频文件的读取接口：

- OpenCV VideoCapture 后端
- Windows 下可选 DShowCapture 后端
- 原始 RGB 数据输入支持

### model.py（训练相关）

模型训练代码，一般不需要直接使用。

### retinaface.py（多人脸检测）

可选的高精度人脸检测器，用于多人脸场景的初始扫描。

### 其他模块

| 模块 | 说明 |
|------|------|
| `similaritytransform.py` | 相似变换计算 |
| `remedian.py` | 中位数过滤算法 |
| `platform/dshowcapture.py` | Windows DShowCapture 封装 |
| `platform/escapi.py` | Windows ESCAPI 封装 |

## 线程模型

- **主线程**：帧读取 → 推理 → UDP 发送（单线程循环）
- **多人脸检测线程**：`scan-retinaface` 启用时，后台线程运行 RetinaFace 检测新脸
- **线程安全**：多人脸检测通过线程锁与主线程同步

## 模型文件

所有 ONNX 模型位于 `models/` 目录：

```
models/
├── lm_model{0..4}_gpu.onnx        # 5 个 GPU 追踪模型
├── lm_model{0..4}_opt.onnx        # 5 个 CPU 追踪模型
├── lm_modelT_gpu.onnx / _opt.onnx  # Tiny 模型（~模型1）
├── lm_modelU_gpu.onnx / _opt.onnx  # 模型 U
├── lm_modelV_gpu.onnx / _opt.onnx  # 模型 V
├── mnv3_gaze32_split_gpu.onnx     # 眼球追踪模型（GPU）
├── mnv3_gaze32_split_opt.onnx     # 眼球追踪模型（CPU）
├── mnv3_detection_gpu.onnx        # 人脸检测模型（GPU）
├── mnv3_detection_opt.onnx        # 人脸检测模型（CPU）
├── retinaface_640x640_gpu.onnx    # RetinaFace 检测器（GPU）
├── retinaface_640x640_opt.onnx    # RetinaFace 检测器（CPU）
└── priorbox_640x640.json          # RetinaFace prior box 配置
```

## 数据流

1. **输入**：摄像头帧 → OpenCV BGR 格式
2. **预处理**：缩放到模型输入尺寸，归一化
3. **推理**：ONNX Runtime 执行 MobileNetV3 网络
4. **后处理**：从网络输出解码地标点坐标
5. **3D 拟合**：使用 PnP 算法计算头部姿态
6. **特征计算**：从地标点提取表情特征
7. **输出**：UDP 数据包发送到 VTube Studio / 其他应用
