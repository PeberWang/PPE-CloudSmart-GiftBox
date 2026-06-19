#!/usr/bin/env bash
# 课程资料智能大礼包 - 项目终端（激活 venv 后打开新 shell）
cd "$(dirname "$0")"

echo "============================================"
echo "  课程资料智能大礼包 - 项目终端"
echo "============================================"
echo

if [ ! -d "venv" ]; then
    echo "[错误] 未找到 venv 目录"
    echo
    echo "请先跑 bash setup.sh 完成安装。"
    exit 1
fi

# 激活 venv
source venv/bin/activate
echo "虚拟环境已激活。提示符前应有 (venv) 标志。"
echo
echo "可以跑命令了，常用命令："
echo "  python deploy.py init-bitable       初始化 bitable"
echo "  python deploy.py seed-course ...     录入课程"
echo "  python deploy.py wiki                建知识库"
echo "  python deploy.py docs                生成课程文档"
echo "  python deploy.py link                回填链接"
echo "  python deploy.py archive-materials   归档资料"
echo "  python deploy.py ocr-materials       OCR + 摘要"
echo "  python deploy.py sync                同步 bitable"
echo "  python deploy.py logs                查日志"
echo
echo "完整命令清单跑 python deploy.py --help"
echo
echo "退出虚拟环境：输入 exit 或 Ctrl+D"
echo

# 启动新的 shell（继承已激活的 venv）
exec $SHELL
