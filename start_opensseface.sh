#!/usr/bin/env bash
# =============================================================================
# OpenSeeFace 启动脚本
# 精简版：环境检测 + 调用 Python CLI
# 优先使用 uv 管理虚拟环境，无 uv 时用 python3 -m venv
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# ---------- 帮助 ----------
if [ "${1:-}" = "-h" ] || [ "${1:-}" = "--help" ]; then
    echo "用法: $(basename "$0") [reconfig|stop]"
    echo ""
    echo "  (无参数)  启动面捕（有配置时跳过交互向导）"
    echo "  reconfig  强制进入交互式配置向导"
    echo "  stop      停止面捕守护进程"
    echo "  -h, --help  显示本帮助"
    echo ""
    echo "配置保存在: $SCRIPT_DIR/config/config.json"
    exit 0
fi

# ---------- 兼容旧参数 ----------
if [ "${1:-}" = "reconfig" ]; then
    set -- "configure"
fi

# ---------- 颜色 ----------
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'
info()  { echo -e "${CYAN}[INFO]${NC}  $*"; }
ok()    { echo -e "${GREEN}[OK]${NC}    $*"; }
err()   { echo -e "${RED}[ERROR]${NC} $*"; }

# ---------- 1. 虚拟环境 ----------
if [ ! -d ".venv" ]; then
    info "正在创建虚拟环境..."
    if command -v uv &>/dev/null; then
        uv venv -p 3.14 .venv 2>&1 | sed 's/^/  /'
    else
        python3 -m venv .venv 2>&1 | sed 's/^/  /'
    fi
    ok "虚拟环境已创建"
fi

source .venv/bin/activate
ok "虚拟环境已激活 ($(python3 --version 2>&1))"

# ---------- 2. CUDA 环境 ----------
_set_cuda_env() {
    local venv_site
    venv_site="$(python3 -c "import site; print(site.getsitepackages()[0])" 2>/dev/null)"
    for _cd in "$venv_site/nvidia/cublas/lib" "$venv_site/nvidia/cuda_runtime/lib" \
               "$venv_site/nvidia/cufft/lib" "$venv_site/nvidia/cuda_nvrtc/lib" \
               "$venv_site/nvidia/nvjitlink/lib"; do
        [ -d "$_cd" ] && export LD_LIBRARY_PATH="${_cd}${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
    done
    export ORT_TENSORRT_UNAVAILABLE=1
}
_set_cuda_env

# ---------- 3. 依赖检查 ----------
_ensure_deps() {
    if ! python3 -c "import onnxruntime" 2>/dev/null; then
        info "正在安装依赖..."
        local extra="cpu"
        if python3 -c "import torch; quit(torch.cuda.is_available())" 2>/dev/null || \
           nvidia-smi &>/dev/null; then
            extra="gpu"
        fi
        if command -v uv &>/dev/null; then
            uv pip install -e ".[$extra]" 2>&1 | sed 's/^/  /'
        else
            pip install -e ".[$extra]" 2>&1 | sed 's/^/  /'
        fi
        ok "依赖安装完成"
    fi
}
_ensure_deps

# ---------- 4. 启动 ----------
info "CUDA 加速: $(python3 -c "import onnxruntime; print('GPU' if 'CUDA' in str(onnxruntime.get_available_providers()) else 'CPU')" 2>/dev/null)"

case "${1:-}" in
    stop)
        exec python3 -m openseeface stop
        ;;
    configure)
        exec python3 -m openseeface configure
        ;;
    start|status)
        exec python3 -m openseeface "$@"
        ;;
    *)
        # 无参数：有配置则启动，否则进入配置向导
        if [ -f "config/config.json" ]; then
            exec python3 -m openseeface start
        else
            exec python3 -m openseeface configure
        fi
        ;;
esac
