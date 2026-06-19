#!/usr/bin/env bash
# 课程资料智能大礼包 - 一键安装脚本（macOS / Linux）
set -e

echo "============================================"
echo "  课程资料智能大礼包 - 一键安装脚本"
echo "  macOS / Linux 版本"
echo "============================================"
echo

# === Step 1: 检测 Python ===
echo "[1/4] 检测 Python..."
if command -v python3 >/dev/null 2>&1; then
    PYVER=$(python3 --version 2>&1)
    echo "      Python 已装，版本: $PYVER"
    PY=python3
elif command -v python >/dev/null 2>&1; then
    PYVER=$(python --version 2>&1)
    echo "      Python 已装，版本: $PYVER"
    PY=python
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

# === Step 2: 检测并安装 LibreOffice ===
echo "[2/4] 检测 LibreOffice..."
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

# === Step 3: 安装 Python 依赖 ===
echo "[3/4] 安装 Python 依赖..."
$PY -m pip install --upgrade pip --user >/dev/null 2>&1 || true
if ! $PY -m pip install -r requirements.txt; then
    echo "      官方源安装失败，尝试清华镜像源..."
    $PY -m pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
fi
echo "      依赖安装完成"
echo

# === Step 4: 创建 .env 文件 ===
echo "[4/4] 准备 .env 配置文件..."
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
echo "  3. 跑 $PY deploy.py init-bitable 开始部署"
echo "  4. 完整流程见 README.md"
echo
