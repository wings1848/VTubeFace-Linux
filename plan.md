# OpenSeeFace 重构实施计划

## 概述

本计划覆盖 15 个问题点，按优先级分 5 个阶段实施。每个阶段内的任务可并行，阶段间有依赖关系。

**前置约束：**
- 所有 Python 代码修改后需要通过 `python -m openseeface --help` 和 `python -m openseeface configure` 冒烟测试
- C++ 代码修改后需要重新编译 SVM wrapper DLL（如有构建环境）
- 阶段间建议提交 checkpoint

---

## 阶段一：修复致命缺陷（P0，阻断性问题）

本阶段修复导致项目无法正常运行的 5 个缺陷。**必须一次性完成**，因为 P0-1 和 P0-4 在同一文件内紧密耦合。

### 任务 1.1: facatracker.py 模块级代码移入 main() 函数

**问题：** `facetracker.py` 中 argparse 定义 (`parser = argparse.ArgumentParser(...)`)、`args = parser.parse_args()`、摄像机列表、基准测试、主追踪循环全部在模块级执行。`__main__.py:32` 尝试 `from .facetracker import main` 但 `facetracker.py` 根本没有 `main()` 函数——这导致直接追踪模式完全崩溃。

**文件：** `src/openseeface/facetracker.py`

**变更内容：**

1. 保留模块顶层：import 语句、`OutputLog` 类定义、`gc.set_threshold()` 调用
2. 新增函数 `create_argparser() -> argparse.ArgumentParser`：包含所有 `parser.add_argument(...)` 调用（约第 9-86 行）
3. 新增函数 `main()`：
   - 调用 `create_argparser()` 获取 parser → `args = parser.parse_args()`
   - 设置 `os.environ["OMP_NUM_THREADS"]`（第 89 行）
   - 处理 `--log-output` 的 stdout/stderr 重定向（第 110-113 行）
   - 处理 Windows dshowcapture 初始化（第 115-127 行）
   - 处理摄像机列表模式（第 129-162 行）
   - 处理 benchmark 模式（第 172-186 行）
   - 执行主追踪循环（第 188-438 行）
4. 文件末尾添加：
   ```python
   if __name__ == "__main__":
       main()
   ```

**验收标准：**
- `python -m openseeface --help` 正常显示帮助（不启动追踪）
- `python -m openseeface --benchmark 1` 正常运行基准测试
- `python -c "import openseeface.facetracker"` 不触发 argparse
- `python -m openseeface start` 后台启动正常

**注意：** `cli.py:282` 的 `cmd_benchmark` 函数需要适配——它目前 `from .facetracker import main as run_facetracker` 然后修改 `sys.argv`，包裹后应在 `main()` 内部处理即可。

---

### 任务 1.2: 修复 Python 版本冲突

**问题：** `pyproject.toml` → `>=3.11,<3.15`；`uv.lock` → `>=3.14`；`start_opensseface.sh:40` → `uv venv -p 3.14`；`start_opensseface.bat:14` → 注释写 "3.7-3.10"。Python 3.14 在 2026-06 仍为 alpha/pre-release，不应作为默认要求。

**文件：**
- `pyproject.toml`
- `uv.lock`
- `start_opensseface.sh`
- `start_opensseface.bat`

**变更内容：**

| 文件 | 位置 | 旧值 | 新值 |
|------|------|------|------|
| `pyproject.toml` | L8 | `>=3.11,<3.15` | `>=3.11,<3.13` |
| `start_opensseface.sh` | L52 | `uv venv -p 3.14 .venv` | `uv venv .venv`（使用当前 python3） |
| `start_opensseface.bat` | L14 | `echo [ERROR] 未找到 Python，请安装 Python 3.7-3.10` | `echo [ERROR] 未找到 Python，请安装 Python 3.11+` |

`uv.lock` 需重新生成：
```bash
rm uv.lock && uv lock
```

---

### 任务 1.3: 统一到 uv 包管理器

**问题：** `poetry.lock` 和 `uv.lock` 并存，`pyproject.toml` 使用 `[tool.poetry]` 格式但所有启动脚本使用 `uv pip install`。

**文件：**
- 删除：`poetry.lock`
- 修改：`pyproject.toml`（考虑转换为 PEP 621 格式以与 uv 更好配合，但非必须 — uv 也支持 poetry 格式）

**变更内容：**

1. **删除 `poetry.lock`**
   ```bash
   rm poetry.lock
   ```

2. **在 `.gitignore` 中确认 `poetry.lock` 不会被意外恢复**（已存在 `.venv/` 忽略，无需额外修改）

3. **（可选/建议）将 `pyproject.toml` 转为 PEP 621 格式**：
   - 在当前阶段只做最小改动：移除 `[tool.poetry.dev-dependencies]`（空节）
   - 保留 poetry 格式，uv 原生支持

**验证：**
```bash
uv pip install -e ".[cpu]"   # 应成功安装
python -m openseeface --help # 应正常
```

---

### 任务 1.4: 修复 stdout/stderr 全局替换

**问题：** `facetracker.py:110-113` 模块级替换 `sys.stdout` 和 `sys.stderr`。

**文件：** `src/openseeface/facetracker.py`

**变更内容：**

此项随 **任务 1.1** 一起修复。当代码移入 `main()` 后，`OutputLog` 替换仅影响该函数作用域。

具体做法：在 `main()` 函数内，仅当 `args.log_output != ""` 时才执行替换：

```python
def main():
    args = create_argparser().parse_args()
    # ...
    if args.log_output:
        output_logfile = open(args.log_output, "w")
        sys.stdout = OutputLog(output_logfile, sys.stdout)
        sys.stderr = OutputLog(output_logfile, sys.stderr)
    # ...
    # 在 main() 返回前恢复：
    # （finally 块中）
    sys.stdout = sys.__stdout__
    sys.stderr = sys.__stderr__
```

---

### 任务 1.5: 替换 ONNX Runtime 私有 API

**问题：** `onnxruntime.capi._pybind_state.get_available_providers()` 使用私有 API。

**文件：**
- `src/openseeface/tracker.py`（2 处：L489, L506）
- `src/openseeface/retinaface.py`（1 处：L70）

**变更内容：**

所有 3 处替换：
```python
# 旧（私有 API）
onnxruntime.capi._pybind_state.get_available_providers()

# 新（公开 API）
onnxruntime.get_available_providers()
```

**验收：**
```bash
python -c "import onnxruntime; print(onnxruntime.get_available_providers())"
```
确保返回结果与旧代码一致。

---

## 阶段二：修复逻辑与资源缺陷（P1，影响正确性）

依赖阶段一完成。

### 任务 2.1: 修复 no_3d_adapt 配置摘要显示逻辑

**问题：** `config_manager.py:244` — 字段名 `no_3d_adapt`，语义 `True=禁用自适应`，但显示逻辑是 `True → "开启"`，语义完全颠倒。

**文件：** `src/openseeface/config_manager.py`，第 244 行

**变更：** 单行修改
```python
# 旧
lines.append(f"  3D自适应 : {'开启' if t['no_3d_adapt'] else '关闭'}")
# 新
lines.append(f"  3D自适应 : {'关闭' if t['no_3d_adapt'] else '开启'}")
```

---

### 任务 2.2: 修复资源泄漏 — Socket 和 ONNX Session

**文件：** `src/openseeface/facetracker.py`

**问题：**
- UDP socket（L256）在 `main()` 中创建，无显式关闭
- 日志文件句柄（L110 `output_logfile`）无显式关闭

**变更：**

1. 在 `main()` 的主循环使用 `try-finally` 或 context manager：
```python
def main():
    sock = None
    output_logfile = None
    try:
        # ... 创建 socket, 追踪循环 ...
    finally:
        if sock:
            sock.close()
        if output_logfile:
            output_logfile.close()
        if input_reader:
            input_reader.close()
        if out:
            out.release()
        if args.visualize != 0:
            cv2.destroyAllWindows()
```

2. Tracker 的 ONNX Sessions（`self.session`, `self.gaze_model`, `self.detection`）建议添加 `close()` 方法，但非紧急（Python GC + ORT 引用计数会清理）。

---

### 任务 2.3: 修复 retinaface.py 线程安全问题

**文件：** `src/openseeface/retinaface.py`

**问题：**
1. `background_detect()` 工作线程未设 `daemon=True`，进程可能卡住
2. `get_results()` 在释放锁后访问 `results` Queue（TOCTOU 竞态）
3. L114 `if True:#is_background:` 死代码

**变更内容：**

1. **后台线程设为 daemon**（L128）：
   ```python
   thread = threading.Thread(target=worker_thread, args=(self, im), daemon=True)
   ```

2. **修复 get_results() 竞态**（L130-142）：合并锁范围，在持有锁时 drain queue：
   ```python
   def get_results(self):
       with self._lock:
           if not self.finished:
               return []
           self.finished = False
           results = []
           try:
               while True:
                   results.append(self.results.get_nowait())
           except queue.Empty:
               pass
       return results
   ```

3. **移除死代码**（L114）：
   ```python
   # 删除 `if True:` 包装，直接执行 upsize 逻辑
   upsize = dets[:, 2:4] * np.array([[0.15, 0.2]])
   dets[:, 0:2] -= upsize
   dets[:, 2:4] += upsize * 2
   ```
   注意：原 `is_background` 参数保留但不再有分支逻辑（目前调用都传 `is_background=True`）

---

### 任务 2.4: C++ vsprintf → vsnprintf

**文件：** `bindings/cpp/svm.cpp`，第 56 行

**变更：**
```cpp
// 旧
static void info(const char *fmt,...)
{
    char buf[BUFSIZ];
    va_list ap;
    va_start(ap,fmt);
    vsprintf(buf,fmt,ap);     // 缓冲区溢出风险
    va_end(ap);
    (*svm_print_string)(buf);
}

// 新
static void info(const char *fmt,...)
{
    char buf[BUFSIZ];
    va_list ap;
    va_start(ap,fmt);
    vsnprintf(buf, BUFSIZ, fmt, ap);   // 安全
    va_end(ap);
    (*svm_print_string)(buf);
}
```

**注意：** 修改后需要重新编译 SVM wrapper DLL（Windows 下需 MSVC 或 MinGW，Unity 集成依赖此 DLL）。

---

### 任务 2.5: 清理硬编码路径

**文件：** `facetracker.spec`，第 7 行

**变更：**
```python
# 旧
pathex=['C:\\OpenSeeFaceBuild'],
# 新
pathex=[],
```

`bindings/dll/` 中的相对路径引用（`platform/escapi.py:69`，`platform/dshowcapture.py:47`）在 PyInstaller 打包场景中使用 `../../../` 相对路径是合理的设计（基于脚本位置推导），暂不修改。

---

## 阶段三：代码质量改进（P2，长期维护）

可独立于前两个阶段执行。

### 任务 3.1: 添加最小类型注解

**文件：** `src/openseeface/config_manager.py`

作为试点，为该文件添加类型注解（它是项目中最独立的模块）：

- `load() -> Dict[str, Any]` 已有
- `save() -> None` 已有
- 给 `__init__`、`to_cli_args`、`to_summary`、`_merge_defaults`、`_migrate_old_config` 添加返回类型
- `_data: Dict[str, Any]` 已有

此为部分修复，后续可扩展到 `tracker.py`、`cli.py` 等。

---

### 任务 3.2: 修复裸异常捕获

**文件：** `src/openseeface/input_reader.py`

| 位置 | 旧代码 | 修改 |
|------|--------|------|
| L94 | `except Exception:` 后 `gc.collect()` 静默重试 | 至少打印 warning 到 stderr |
| L226-228 | `except Exception:` 静默吞掉 DShowCapture 异常 | 已有 `traceback.print_exc()`，保持不变 |
| L249-252 | `except Exception:` 捕获 escapi 异常 | 同上，已有 traceback |

**文件：** `src/openseeface/facetracker.py`

| 位置 | 修改 |
|------|------|
| L288 | `except Exception as e: traceback.print_exc(); failures += 1` — 添加 `except KeyboardInterrupt: raise` 以保证 Ctrl+C 不被吞掉 |

---

### 任务 3.3: 添加基础测试骨架

**新文件：** `tests/__init__.py`，`tests/test_config_manager.py`

最小覆盖：
- 测试 `ConfigManager` 默认配置创建
- 测试 `to_cli_args` 输出格式
- 测试 `_merge_defaults` 行为
- 测试旧配置迁移

```python
import pytest
from openseeface.config_manager import ConfigManager

def test_default_config_creation(tmp_path):
    cm = ConfigManager(config_dir=tmp_path)
    cfg = cm.load()
    assert cfg["general"]["mode"] == "camera"
    assert cfg["tracking"]["model"] == 3

def test_to_cli_args():
    cm = ConfigManager(config_dir=tmp_path)
    cm.load()
    args = cm.to_cli_args()
    assert "-c" in args
    assert "--model" in args
```

---

### 任务 3.4: 修复文件名拼写

**文件：** `start_opensseface.sh` → `start_openseeface.sh`

（注：`opensseface` 是 `openseeface` 的拼写错误，少了一个 `e`）

**变更内容：**

1. 重命名文件：
   ```bash
   mv start_opensseface.sh start_openseeface.sh
   mv start_opensseface.bat start_openseeface.bat
   ```

2. 更新所有文档引用此文件名的地方：
   - `README.md:26`
   - `README_en.md:26`
   - `docs/README.md:15`
   - `docs/changelog/CHANGELOG.md`（多处）
   - `docs/guides/quick-start.md`（2 处）
   - `docs/guides/troubleshooting.md:62`
   - `docs/reference/cli.md`（3 处）

---

## 阶段四：跨平台兼容性

### 任务 4.1: C++ 代码移除 Windows 特定头文件

**文件：** `bindings/cpp/svm.cpp`

`#include <combaseapi.h>` 是 Windows COM API，破坏 Linux 编译。

**变更：**
```cpp
// 旧
#include <combaseapi.h>
// 新：条件编译
#ifdef _WIN32
#include <combaseapi.h>
#endif
```

---

### 任务 4.2: Unity BinaryFormatter 迁移计划

**文件：** `Unity/OpenSeeExpression.cs`

`BinaryFormatter` 在 .NET 5+ 标记为过时，.NET 8+ 默认抛出异常。但此修改需要替代方案（JSON/protobuf），属于较大变更。

**短期方案：** 在文件顶部添加：
```csharp
#pragma warning disable SYSLIB0011 // BinaryFormatter is obsolete
```
**长期方案：** 替换为 `System.Text.Json` 序列化（需同步修改序列化格式）。

---

## 阶段五：文档与打包清理

### 任务 5.1: 更新 facetracker.spec 二进制依赖

**文件：** `facetracker.spec`

问题：引用了可能不存在的 DLL（`msvcp140.dll`、`vcomp140.dll`、`concrt140.dll`、`vccorlib140.dll`）。这些是 Visual C++ 运行时，不应打包进 exe（用户系统应有）。

**变更：**
```python
# 移除 VC++ 运行时 DLL 引用
binaries=[('bindings/dll/dshowcapture/dshowcapture_x86.dll', '.'),
          ('bindings/dll/dshowcapture/dshowcapture_x64.dll', '.'),
          ('bindings/dll/dshowcapture/libminibmcapture32.dll', '.'),
          ('bindings/dll/dshowcapture/libminibmcapture64.dll', '.'),
          ('bindings/dll/escapi/escapi_x86.dll', '.'),
          ('bindings/dll/escapi/escapi_x64.dll', '.'),
          ('scripts/run.bat', '.')],
```

---

## 文件修改总览

| 阶段 | 文件 | 操作 |
|------|------|------|
| 1.1 | `src/openseeface/facetracker.py` | 重构：模块级代码 → `main()` 函数 |
| 1.2 | `pyproject.toml` | 修改 Python 版本约束 |
| 1.2 | `start_opensseface.sh` | 修改 venv 创建命令 |
| 1.2 | `start_opensseface.bat` | 修改错误消息 |
| 1.2 | `uv.lock` | 删除后重新生成 |
| 1.3 | `poetry.lock` | **删除** |
| 1.3 | `pyproject.toml` | 移除空的 `[tool.poetry.dev-dependencies]` 节 |
| 1.5 | `src/openseeface/tracker.py` | `_pybind_state` → 公开 API（2 处） |
| 1.5 | `src/openseeface/retinaface.py` | `_pybind_state` → 公开 API（1 处） |
| 2.1 | `src/openseeface/config_manager.py` | 修复 no_3d_adapt 显示逻辑（1 行） |
| 2.2 | `src/openseeface/facetracker.py` | 添加 try-finally 资源清理 |
| 2.3 | `src/openseeface/retinaface.py` | 线程安全修复 + 死代码移除 |
| 2.4 | `bindings/cpp/svm.cpp` | `vsprintf` → `vsnprintf` |
| 2.5 | `facetracker.spec` | 移除硬编码 `C:\\OpenSeeFaceBuild` |
| 3.1 | `src/openseeface/config_manager.py` | 补充类型注解 |
| 3.2 | `src/openseeface/input_reader.py` | 改善异常处理 |
| 3.2 | `src/openseeface/facetracker.py` | KeyboardInterrupt 优先级 |
| 3.3 | `tests/__init__.py` | **新建** |
| 3.3 | `tests/test_config_manager.py` | **新建** |
| 3.4 | `start_opensseface.sh` | **重命名** → `start_openseeface.sh` |
| 3.4 | `start_opensseface.bat` | **重命名** → `start_openseeface.bat` |
| 3.4 | `README.md`, `README_en.md`, `docs/*.md` | 更新脚本名引用（~15 处） |
| 4.1 | `bindings/cpp/svm.cpp` | `combaseapi.h` 条件编译 |
| 4.2 | `Unity/OpenSeeExpression.cs` | BinaryFormatter 警告抑制 |
| 5.1 | `facetracker.spec` | 移除 VC++ 运行时 DLL |

---

## 依赖关系

```
阶段一（P0）─────────────────────▶ 阶段二（P1）──▶ 阶段三（P2）
    │                                  │
    ├─ 1.1 (facetracker 重构)          ├─ 2.1 (config 显示)
    │   └── 依赖 1.4 (stdout 修复)     ├─ 2.2 (资源清理) ── 依赖 1.1
    ├─ 1.2 (版本统一)                  ├─ 2.3 (线程安全)
    ├─ 1.3 (包管理器统一)              ├─ 2.4 (C++ 安全)
    ├─ 1.4 (stdout) ── 依赖 1.1       └─ 2.5 (路径清理)
    └─ 1.5 (ORT API)
                                       
阶段三（P2）──▶ 阶段四（跨平台）──▶ 阶段五（打包）
    │               │
    ├─ 3.1-3.3      ├─ 4.1 (C++)
    └─ 3.4          └─ 4.2 (Unity)
```

**关键路径：** 1.1 → 2.2 → 3.2
**可并行：** 1.2 + 1.3 + 1.5 可与 1.1 并行准备，但合并时需解决冲突

---

## 风险

1. **facetracker.py 重构风险最高**（任务 1.1）。该文件 438 行几乎全部在模块级，移入 `main()` 需要精确保留所有控制流（摄像机列表提前退出、benchmark 提前退出、主循环逻辑）。**建议先做 git commit 保存当前状态。**

2. **uv.lock 重新生成可能引入依赖版本变化**（任务 1.2）。`poetry.lock` 中的 `onnxruntime==1.9.0` 很旧，uv 解析可能选择更新版本。需验证 ONNX 模型兼容性。

3. **C++ 修改无法测试**（任务 2.4、4.1）。项目可能没有 Windows C++ 构建环境。建议先改代码，文档注明需要重新编译。

4. **文件名重命名影响外部引用**（任务 3.4）。如果有外部文档/视频链接到 `start_opensseface.sh`，重命名会断链。可保留旧名作为符号链接。

5. **Unity BinaryFormatter**（任务 4.2）。Unity 使用的 Mono/IL2CPP 运行时对 `BinaryFormatter` 的兼容性不同于标准 .NET。短期抑制警告安全，长期替换为 JSON 序列化更可靠。

---

## 验证清单

每个阶段完成后执行：

### 阶段一验证
```bash
python -c "import openseeface; print(openseeface.__version__)"    # 不触发 argparse
python -m openseeface --help                                      # 显示帮助
python -m openseeface configure   # 交互式配置（Ctrl+C 退出）
python -m openseeface status      # 显示状态
rm uv.lock && uv lock && uv pip install -e ".[cpu]"               # 依赖正常
```

### 阶段二验证
```bash
python -m openseeface configure   # 检查 "3D自适应" 显示正确
python -c "
# 验证 ORT 公开 API
import onnxruntime
print(onnxruntime.get_available_providers())
"
# SVM wrapper 重编译（如有环境）
```

### 阶段三验证
```bash
python -m pytest tests/ -v       # 测试通过
ls start_opens*                  # 确认新文件名存在
```
