# 配置文件参考

## 配置文件位置

配置文件位于 `config/config.json`，由交互式配置向导（`openseeface configure`）生成。

首次运行时，旧版 `.facetracker_config` 会自动迁移为 JSON 格式，原文件重命名为 `.bak`。

## 配置格式

JSON 格式，结构化分组：

```json
{
  "general": {
    "mode": "camera"
  },
  "camera": {
    "id": 0,
    "fps": 30,
    "width": 640,
    "height": 480,
    "mirror": false
  },
  "tracking": {
    "model": 3,
    "quality_preset": 4,
    "detection_threshold": 0.6,
    "threshold": 0.85,
    "no_3d_adapt": false,
    "try_hard": true,
    "gaze": true,
    "faces": 1,
    "max_threads": 4
  },
  "network": {
    "ip": "127.0.0.1",
    "port": 11573
  },
  "logging": {
    "data": "",
    "output": "",
    "visualize": false
  }
}
```

## 配置项说明

### general — 通用

| 键 | 类型 | 默认值 | 说明 |
|-----|------|---------|------|
| `mode` | string | `"camera"` | 运行模式：`camera`（摄像头）或 `video`（视频文件） |

### camera — 摄像头

| 键 | 类型 | 默认值 | 说明 |
|-----|------|---------|------|
| `id` | int | `0` | 摄像头编号 |
| `fps` | int | `30` | 采集帧率 |
| `width` | int | `640` | 采集宽度 |
| `height` | int | `480` | 采集高度 |
| `mirror` | bool | `false` | 水平镜像 |

### tracking — 追踪

| 键 | 类型 | 默认值 | 说明 |
|-----|------|---------|------|
| `model` | int | `3` | 追踪模型（-3~4），越大精度越高 |
| `quality_preset` | int | `3` | 质量预设（1~6）：1=极致性能 ... 4=高质量 ... 6=自定义 |
| `detection_threshold` | float | `0.6` | 人脸检测阈值 |
| `threshold` | float | `0.85` | 追踪置信度阈值 |
| `no_3d_adapt` | bool | `false` | 关闭 3D 自适应 |
| `try_hard` | bool | `true` | 尽力找脸模式 |
| `gaze` | bool | `true` | 眼球/视线追踪 |
| `faces` | int | `1` | 最大追踪人脸数 |
| `max_threads` | int | `4` | 最大推理线程数 |

### network — 网络

| 键 | 类型 | 默认值 | 说明 |
|-----|------|---------|------|
| `ip` | string | `"127.0.0.1"` | UDP 目标 IP |
| `port` | int | `11573` | UDP 目标端口 |

### logging — 日志

| 键 | 类型 | 默认值 | 说明 |
|-----|------|---------|------|
| `data` | string | `""` | 追踪数据 CSV 日志路径 |
| `output` | string | `""` | 控制台输出日志路径 |
| `visualize` | bool | `false` | 显示可视化窗口 |

## 手动编辑

配置可以手动编辑 JSON 文件，修改后重启守护进程生效：

```bash
python -m openseeface stop
# 编辑 config/config.json
python -m openseeface start
```

或通过交互式向导重新配置：

```bash
python -m openseeface configure
```
