# setup.ps1 - 项目环境一键配置脚本

$ErrorActionPreference = "Stop"

function Print-Color {
    param([string]$Message, [ConsoleColor]$Color = "White")
    Write-Host $Message -ForegroundColor $Color
}

Print-Color "开始配置开发环境..." "Cyan"

# 1. 检查 Python 是否安装
if (-not (Get-Command "python" -ErrorAction SilentlyContinue)) {
    Print-Color "错误: 未找到 Python。请先安装 Python 3.10+ (推荐使用 install-pyenv-win.ps1 安装)" "Red"
    exit 1
}

# 2. 虚拟环境处理
$venvInfo = ".venv"
$venvExists = Test-Path $venvInfo
$recreate = $false

if ($venvExists) {
    Print-Color "检测到已存在虚拟环境 '$venvInfo'..." "Yellow"
    
    # 简单的有效性检查
    $pythonPath = Join-Path $venvInfo "Scripts\python.exe"
    if (-not (Test-Path $pythonPath)) {
        Print-Color "虚拟环境结构不完整，准备重建..." "Red"
        $recreate = $true
    } else {
        try {
            # 尝试执行 python 打印路径，如果路径与当前不符（拷贝自其他机器），通常不会报错但 pip 安装会出问题
            # 这里简单尝试运行一下
            & $pythonPath -c "import sys; print('Python check ok')" | Out-Null
            Print-Color "虚拟环境似乎有效。" "Green"
        } catch {
            Print-Color "虚拟环境可能已损坏，准备重建..." "Red"
            $recreate = $true
        }
    }

    if ($recreate) {
        Remove-Item -Recurse -Force $venvInfo
    }
}

if (-not (Test-Path $venvInfo)) {
    Print-Color "正在创建新的虚拟环境..." "Cyan"
    python -m venv $venvInfo
    if (-not $?) {
        Print-Color "创建虚拟环境失败！" "Red"
        exit 1
    }
}

# 3. 依赖安装
Print-Color "正在安装/更新依赖..." "Cyan"
$pipPath = Join-Path $venvInfo "Scripts\pip.exe"

# 基础升级
& $pipPath install --upgrade pip

# 安装项目依赖
if (Test-Path "pyproject.toml") {
    Print-Color "检测到 pyproject.toml，正在安装依赖..." "Green"
    # 使用 -e . 安装项目自身及其依赖
    & $pipPath install -e .
} elseif (Test-Path "requirements.txt") {
    Print-Color "检测到 requirements.txt，正在安装依赖..." "Green"
    & $pipPath install -r requirements.txt
} else {
    Print-Color "警告: 未找到 pyproject.toml 或 requirements.txt，跳过依赖安装。" "Yellow"
}

Print-Color "`n----------------------------------------" "Green"
Print-Color "环境配置完成！" "Green"
Print-Color "您现在可以使用以下命令激活环境：" "Cyan"
Print-Color ".\\$venvInfo\Scripts\Activate.ps1" "White"
