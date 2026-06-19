#!/usr/bin/env bash
# 课程资料智能大礼包 - 一键安装脚本（macOS / Linux）
set -e

echo "============================================"
echo "  课程资料智能大礼包 - 一键安装脚本"
echo "  macOS / Linux 版本"
echo "============================================"
echo

# === Step 1: 检测 Python ===
echo "[1/5] 检测 Python..."
if command -v python3 >/dev/null 2>&1; then
    PYVER=$(python3 --version 2>&1)
    echo "      Python 已装，版本: $PYVER"
    SYS_PY=python3
elif command -v python >/dev/null 2>&1; then
    PYVER=$(python --version 2>&1)
    echo "      Python 已装，版本: $PYVER"
    SYS_PY=python
else
    echo
    echo "[错误] 没有检测到 Python。请先安装 Python 3.11+："
    echo "  macOS:  brew install python@3.11"
    echo "  Debian/Ubuntu:  sudo apt update && sudo apt install python3 python3-pip"
    echo "  CentOS/RHEL:  sudo yum install python3 python3-pip"
    echo "  或访问 https://www.python.org/downloads/"
    exit 1
fi
echo

# === Step 2: 创建虚拟环境 ===
echo "[2/5] 创建 Python 虚拟环境..."
if [ ! -d "venv" ]; then
    $SYS_PY -m venv venv
    if [ $? -ne 0 ]; then
        echo "      [错误] 创建虚拟环境失败"
        exit 1
    fi
    echo "      虚拟环境已创建: venv/"
else
    echo "      venv 已存在，跳过创建"
fi

# 后续 Python 命令用 venv 里的
PY="venv/bin/python"
if [ ! -x "$PY" ]; then
    echo "[错误] venv 里的 python 不存在: $PY"
    exit 1
fi
echo

# === Step 3: 检测并安装 LibreOffice ===
echo "[3/5] 检测 LibreOffice..."
SOFFICE_PATH=""
if command -v soffice >/dev/null 2>&1; then
    SOFFICE_PATH=$(command -v soffice)
elif [ -x "/Applications/LibreOffice.app/Contents/MacOS/soffice" ]; then
    SOFFICE_PATH="/Applications/LibreOffice.app/Contents/MacOS/soffice"
fi

if [ -n "$SOFFICE_PATH" ]; then
    echo "      LibreOffice 已装: $SOFFICE_PATH"
else
    echo "      LibreOffice 未检测到，尝试自动安装..."
    echo
    OS_TYPE="$(uname -s)"
    case "$OS_TYPE" in
        Darwin)
            # macOS
            if command -v brew >/dev/null 2>&1; then
                echo "      使用 Homebrew 安装 LibreOffice..."
                brew install --cask libreoffice
            else
                echo "      [警告] Homebrew 未装。请手动安装："
                echo "        1. 装 Homebrew: https://brew.sh/"
                echo "        2. 再跑: brew install --cask libreoffice"
                echo "      或访问 https://www.libreoffice.org/download/ 下载 .dmg"
                exit 1
            fi
            ;;
        Linux)
            # Linux
            if command -v apt >/dev/null 2>&1; then
                echo "      使用 apt 安装 LibreOffice..."
                sudo apt update
                sudo apt install -y libreoffice
            elif command -v yum >/dev/null 2>&1; then
                echo "      使用 yum 安装 LibreOffice..."
                sudo yum install -y libreoffice
            elif command -v dnf >/dev/null 2>&1; then
                echo "      使用 dnf 安装 LibreOffice..."
                sudo dnf install -y libreoffice
            elif command -v pacman >/dev/null 2>&1; then
                echo "      使用 pacman 安装 LibreOffice..."
                sudo pacman -S --noconfirm libreoffice-fresh
            else
                echo "      [警告] 不支持的 Linux 发行版，请手动装 LibreOffice"
                echo "        访问 https://www.libreoffice.org/download/"
                exit 1
            fi
            ;;
        *)
            echo "      [警告] 不支持的系统: $OS_TYPE"
            echo "        访问 https://www.libreoffice.org/download/ 手动下载"
            exit 1
            ;;
    esac
fi
echo

# === Step 4: 安装 Python 依赖到 venv ===
echo "[4/5] 安装 Python 依赖到虚拟环境..."
$PY -m pip install --upgrade pip >/dev/null 2>&1 || true
if ! $PY -m pip install -r requirements.txt; then
    echo "      官方源安装失败，尝试清华镜像源..."
    $PY -m pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
fi
echo "      依赖安装完成（在 venv/ 内，不污染系统 Python）"
echo

# === Step 5: 创建 .env 文件 ===
echo "[5/5] 准备 .env 配置文件..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo "      已从 .env.example 创建 .env"
else
    echo "      .env 已存在，保留你的配置"
fi
echo

echo "============================================"
echo "  安装完成！"
echo "============================================"
echo
echo "下一步："
echo "  1. 用编辑器打开当前目录下的 .env 文件"
echo "  2. 填入凭证（飞书/DeepSeek/智谱/阿里云）"
echo "     详细字段说明见 docs/00-快速开始.md 第三节"
echo "  3. 跑 source venv/bin/activate 激活虚拟环境"
echo "     或直接用 venv 里的 python:"
echo "       venv/bin/python deploy.py init-bitable"
echo "  4. 完整流程见 README.md"
echo
echo "注意：所有 python deploy.py 命令必须在激活的虚拟环境里跑，"
echo "否则找不到依赖。也可以用 bash start.sh 一键激活并打开 shell。"
echo
