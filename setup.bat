@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion

echo ============================================
echo   课程资料智能大礼包 - 一键安装脚本
echo   Windows 版本
echo ============================================
echo.

REM === Step 1: 检测 Python ===
echo [1/5] 检测 Python...
python --version >nul 2>&1
if !errorlevel! neq 0 (
    echo.
    echo [错误] 没有检测到 Python。
    echo.
    echo 请先安装 Python 3.11+：
    echo   1. 访问 https://www.python.org/downloads/
    echo   2. 下载并运行安装包
    echo   3. 安装时务必勾选底部「Add Python.exe to PATH」
    echo   4. 装完后关闭此窗口，重新双击 setup.bat
    echo.
    echo 按任意键打开 Python 下载页面...
    pause >nul
    start https://www.python.org/downloads/
    exit /b 1
)
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYVER=%%i
echo       Python 已装，版本: !PYVER!
echo.

REM === Step 2: 创建虚拟环境 ===
echo [2/5] 创建 Python 虚拟环境...
if not exist venv (
    python -m venv venv
    if !errorlevel! neq 0 (
        echo       [错误] 创建虚拟环境失败
        pause
        exit /b 1
    )
    echo       虚拟环境已创建: venv\
) else (
    echo       venv 已存在，跳过创建
)
echo.

REM 设置 Python 命令为 venv 里的（后续所有 pip 命令都在 venv 里跑）
set "PY_CMD=venv\Scripts\python.exe"
if not exist "!PY_CMD!" (
    echo [错误] venv 里的 python.exe 不存在
    pause
    exit /b 1
)

REM === Step 3: 检测并安装 LibreOffice ===
echo [3/5] 检测 LibreOffice...
set "SOFFICE_PATH="
if exist "C:\Program Files\LibreOffice\program\soffice.exe" (
    set "SOFFICE_PATH=C:\Program Files\LibreOffice\program\soffice.exe"
) else if exist "C:\Program Files (x86)\LibreOffice\program\soffice.exe" (
    set "SOFFICE_PATH=C:\Program Files (x86)\LibreOffice\program\soffice.exe"
)

if defined SOFFICE_PATH (
    echo       LibreOffice 已装: !SOFFICE_PATH!
) else (
    echo       LibreOffice 未检测到，尝试自动安装...
    echo.
    echo       接下来可能弹出 UAC 权限提示，请点「是」授权。
    echo       安装过程需要下载约 350MB，请耐心等待。
    echo.

    REM 优先用 winget（Windows 10 1809+ 自带）
    winget --version >nul 2>&1
    if !errorlevel! equ 0 (
        echo       使用 winget 自动安装 LibreOffice...
        winget install --id TheDocumentFoundation.LibreOffice -e --accept-package-agreements --accept-source-agreements
        if !errorlevel! neq 0 (
            echo.
            echo [警告] winget 安装失败。请手动安装：
            echo   1. 访问 https://www.libreoffice.org/download/
            echo   2. 下载 Windows x86_64 版本
            echo   3. 双击 .msi 文件按向导安装
            echo   4. 装完后重新跑 setup.bat 验证
            echo.
            pause
        )
    ) else (
        echo       [警告] winget 不可用（系统版本过旧）。
        echo       请手动安装 LibreOffice：
        echo         访问 https://www.libreoffice.org/download/ 下载 .msi 安装
        echo.
        pause
    )

    REM 验证安装结果
    if exist "C:\Program Files\LibreOffice\program\soffice.exe" (
        set "SOFFICE_PATH=C:\Program Files\LibreOffice\program\soffice.exe"
        echo       LibreOffice 安装成功
    ) else if exist "C:\Program Files (x86)\LibreOffice\program\soffice.exe" (
        set "SOFFICE_PATH=C:\Program Files (x86)\LibreOffice\program\soffice.exe"
        echo       LibreOffice 安装成功
    ) else (
        echo       [警告] LibreOffice 仍未检测到，可能需要重启电脑后重新验证
    )
)
echo.

REM === Step 4: 安装 Python 依赖到 venv ===
echo [4/5] 安装 Python 依赖到虚拟环境...
"!PY_CMD!" -m pip install --upgrade pip >nul 2>&1
"!PY_CMD!" -m pip install -r requirements.txt
if !errorlevel! neq 0 (
    echo       官方源安装失败，尝试清华镜像源...
    "!PY_CMD!" -m pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
    if !errorlevel! neq 0 (
        echo.
        echo [错误] Python 依赖安装失败
        pause
        exit /b 1
    )
)
echo       依赖安装完成（在 venv\ 内，不污染系统 Python）
echo.

REM === Step 5: 创建 .env 文件 ===
echo [5/5] 准备 .env 配置文件...
if not exist .env (
    copy .env.example .env >nul
    echo       已从 .env.example 创建 .env
) else (
    echo       .env 已存在，保留你的配置
)
echo.

echo ============================================
echo   安装完成！
echo ============================================
echo.
echo 下一步：
echo   1. 用记事本打开当前目录下的 .env 文件
echo   2. 填入凭证（飞书/DeepSeek/智谱/阿里云）
echo      详细字段说明见 docs\00-快速开始.md 第三节
echo   3. 双击 start.bat 打开已激活虚拟环境的终端
echo   4. 在终端里跑 python deploy.py init-bitable 开始部署
echo   5. 完整流程见 README.md
echo.
echo 注意：所有 python deploy.py 命令必须先双击 start.bat
echo 在激活的虚拟环境里跑，否则找不到依赖。
echo.
pause
