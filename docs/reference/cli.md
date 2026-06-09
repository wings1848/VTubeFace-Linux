# CLI 参数参考

## 基本用法

```bash
python -m openseeface [选项]
# 或通过启动脚本
./start_opensseface.sh
```

## 管理子命令

```bash
python -m openseeface configure   # 交互式配置向导
python -m openseeface start       # 后台启动守护进程
python -m openseeface stop        # 停止守护进程
python -m openseeface status      # 查看运行状态
python -m openseeface benchmark   # 运行基准测试
python -m openseeface help        # 显示本帮助
```

> `configure`、`start`、`stop`、`status` 也可以通过 `./start_opensseface.sh` 调用，
> 例如 `./start_opensseface.sh stop` 等价于 `python -m openseeface stop`。

---

## 追踪参数

## 输入源

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `-c, --capture` | `0` | 摄像头编号（如 `0`、`1`）或视频文件路径 |
| `-F, --fps` | `24` | 摄像头帧率 |
| `-W, --width` | `640` | 画面宽度 |
| `-H, --height` | `360` | 画面高度 |
| `-M, --mirror-input` | 关 | 镜像画面输入 |
| `--raw-rgb` | `0` | 从标准输入读取原始 RGB 数据（替代摄像头） |
| `--repeat-video` | `0` | 视频文件循环播放 |

## 网络输出

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `-i, --ip` | `127.0.0.1` | UDP 发送目标 IP |
| `-p, --port` | `11573` | UDP 发送端口 |

## 追踪参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--model` | `3` | 追踪模型质量（-3~4），越大精度越高速度越慢 |
| `--threshold` | 自动 | 追踪置信度阈值，低于此值丢弃结果 |
| `--detection-threshold` | `0.6` | 人脸检测阈值，越低越容易检测到人脸 |
| `--faces` | `1` | 最大追踪人脸数（最多 4 个）。越多人脸越慢 |
| `--try-hard` | `0` | 开启后更努力寻找人脸（增加检测开销） |
| `--no-3d-adapt` | `1` | 关闭 3D 模型自适应（关闭可提升速度） |
| `--gaze-tracking` | `1` | 开启眼球追踪（关闭可提升速度） |
| `--max-threads` | `1` | 最大推理线程数 |
| `--scan-retinaface` | `0` | 多人脸时用 RetinaFace 扫描（更准但更慢） |
| `--scan-every` | `3` | 多人脸时每隔多少帧扫描一次新脸 |
| `--discard-after` | `10` | 人脸丢失后继续追踪的秒数 |
| `--max-feature-updates` | `900` | 特征值停止更新的秒数 |
| `--face-id-offset` | `0` | 人脸 ID 偏移量，用于多数据源混合 |

## 可视化 / 日志

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `-v, --visualize` | `0` | 可视化窗口。1=显示追踪, 2=显示ID, 3=显示置信度, 4=显示点编号 |
| `-P, --pnp-points` | `0` | 在可视化中显示 3D 拟合点 |
| `-s, --silent` | `0` | 静默模式，不输出控制台日志 |
| `--log-data` | 空 | 追踪数据 CSV 日志文件路径 |
| `--log-output` | 空 | 控制台输出日志文件路径 |
| `--video-out` | 空 | 保存追踪可视化视频为 AVI 文件 |
| `--video-scale` | `1` | 输出视频分辨率缩放（1~4） |
| `--video-fps` | `24` | 输出视频帧率 |
| `--benchmark` | `0` | 运行模型基准测试，比较各模型速度 |
| `--dump-points` | 空 | 退出时保存对称化的 3D 点到文件 |
| `--model-dir` | 自动 | 模型文件目录路径 |

## Windows 特有

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `-l, --list-cameras` | `0` | 列出可用摄像头并退出 |
| `-a, --list-dcaps` | `None` | 列出摄像头支持的能力列表 |
| `-D, --dcap` | `None` | 使用指定设备能力行 |
| `-B, --blackmagic` | `0` | 启用 Blackmagic 设备支持 |
| `--use-dshowcapture` | `1` | 使用 libdshowcapture 替代 OpenCV 采集 |
| `--blackmagic-options` | `None` | 传给 Blackmagic 库的额外选项字符串 |
| `--priority` | `None` | 进程优先级（0=空闲~5=实时） |

## Linux 特有

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--dformat` | `None` | 设备格式（MJPG, YUYV, RGB3 等） |
