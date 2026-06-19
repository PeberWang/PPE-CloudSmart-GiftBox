@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion

echo ============================================
echo   课程资料智能大礼包 - 一键安装脚本
echo   Windows 版本
echo ============================================
echo.

REM === Step 1: 检测 Python ===
echo [1/4] 检测 Python...
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

REM === Step 2: 检测并安装 LibreOffice ===
echo [2/4] 检测 LibreOffice...
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

REM === Step 3: 安装 Python 依赖 ===
echo [3/4] 安装 Python 依赖...
python -m pip install --upgrade pip >nul 2>&1
python -m pip install -r requirements.txt
if !errorlevel! neq 0 (
    echo       官方源安装失败，尝试清华镜像源...
    python -m pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
    if !errorlevel! neq 0 (
        echo.
        echo [错误] Python 依赖安装失败
        pause
        exit /b 1
    )
)
echo       依赖安装完成
echo.

REM === Step 4: 创建 .env 文件 ===
echo [4/4] 准备 .env 配置文件...
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
echo   3. 跑 python deploy.py init-bitable 开始部署
echo   4. 完整流程见 README.md
echo.
pause
