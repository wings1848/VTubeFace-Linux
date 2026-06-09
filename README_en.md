# OpenSeeFace

[![OSF.png](images/OSF.png)](https://github.com/emilianavt/OpenSeeFace)

> 📖 **中文文档: [README.md](README.md)**

A facial landmark tracking library based on MobileNetV3, sending real-time tracking data over UDP to VTube Studio and other applications.

---

## Features

- **Real-time face tracking** via ONNX Runtime (GPU CUDA / CPU)
- **8 tracking models** from ultra-fast (-3) to high-precision (4)
- **VTube Studio integration** out of the box
- **Multi-face tracking** up to 4 faces simultaneously
- **Head pose** 3D rotation, translation, Euler angles
- **Expression features** 14-dim eye, eyebrow, mouth parameters
- **Cross-platform** Linux / Windows

## Quick Start

```bash
git clone https://github.com/wings1848/OpenSeeFace
cd OpenSeeFace
./start_opensseface.sh
```

First run automatically creates a virtual environment, installs dependencies, and launches an interactive setup wizard.

## Documentation

| Section | Description |
|---------|-------------|
| [Quick Start](docs/guides/quick-start.md) | Get running in 5 minutes |
| [Installation](docs/guides/installation.md) | Manual setup |
| [VTube Studio Setup](docs/guides/vtube-studio-setup.md) | UDP configuration |
| [CLI Reference](docs/reference/cli.md) | All command-line options |
| [Config Reference](docs/reference/config.md) | Config file format |
| [UDP Protocol](docs/reference/udp-protocol.md) | Packet format specification |
| [Models](docs/reference/models.md) | Model comparison |
| [Architecture](docs/development/architecture.md) | Module overview |
| [Troubleshooting](docs/guides/troubleshooting.md) | FAQ |
| [CHANGELOG](docs/changelog/CHANGELOG.md) | Full changelog |
| [Optimization Report](docs/reports/OPTIMIZATION_REPORT.md) | Performance tuning |
| [Experience](docs/reports/EXPERIENCE.md) | Development notes |

## Management Commands

```bash
python -m openseeface start       # Start daemon
python -m openseeface stop        # Stop daemon
python -m openseeface status      # Show status
python -m openseeface configure   # Interactive setup
python -m openseeface benchmark   # Run benchmark
```

## Manual Usage

```bash
# After activating the virtual environment
python -m openseeface \
  -c 0 -F 30 --model 3 --try-hard 1 \
  --gaze-tracking 1 --max-threads 2 \
  -i 127.0.0.1 -p 11573 --visualize 1
```

## GPU Acceleration

NVIDIA GPU acceleration via onnxruntime-gpu + CUDA 12.x.

The startup script detects GPU automatically. Manual install:

```bash
uv pip install -e ".[gpu]"   # GPU version
uv pip install -e ".[cpu]"   # CPU version
```

GTX 1660 Ti实测: model 3 goes from 125 → 210 FPS (×1.68 speedup).

## Related Projects

- [Original OpenSeeFace](https://github.com/emilianavt/OpenSeeFace)
- [VSeeFace](https://www.vseeface.icu/) (3D avatar puppeteering)
- [VTube Studio](https://denchisoft.com/) (Live2D puppeteering)

## License

BSD 2-Clause License. Third-party licenses in [licenses/](licenses/).
