正在优化工具选择...

读取 [](file:///d%3A/code/ds/MYGPTAIv2/pyproject.toml)

读取 [](file:///d%3A/code/ds/MYGPTAIv2)

读取 [](file:///d%3A/code/ds/MYGPTAIv2/install-pyenv-win.ps1#1-1)，行 1 到 100

读取 [](file:///d%3A/code/ds/MYGPTAIv2/.gitignore)

已创建 [](file:///d%3A/code/ds/MYGPTAIv2/setup.ps1)

已创建 [](file:///d%3A/code/ds/MYGPTAIv2/clean_for_export.ps1)

这是一个因为 Python 虚拟环境（.venv）不可移植（Portable）导致的常见问题。虚拟环境在创建时会将 Python 解释器的**绝对路径**硬编码在配置文件中，因此直接拷贝到另一台电脑会导致路径失效。

我为您编写了两个 PowerShell 脚本来彻底解决这个问题，让您的项目迁移变得“傻瓜式”操作。

### 解决方案

#### 1. 迁移前清理 (clean_for_export.ps1)
在您的**当前电脑**上，准备打包或拷贝项目给别人之前，运行此脚本。它会自动删除 .venv、__pycache__ 等不应迁移的临时文件。
*   **作用**：减小项目体积，防止将错误的坏境配置带到新电脑。

#### 2. 在新电脑一键恢复 (setup.ps1)
在**新电脑**上解压或放入项目后，直接运行此脚本。
*   **作用**：自动检测/创建新的 .venv，并根据您的 pyproject.toml 自动安装所有依赖。

---

### 如何使用

**步骤 1：在当前电脑（发送方）**
在终端运行清理脚本：
```powershell
.\clean_for_export.ps1
```
*(清理完成后，您可以放心地打包压缩整个文件夹拷贝给别人)*

**步骤 2：在目标电脑（接收方）**
将项目拷贝过去后，在终端运行安装脚本：
```powershell
.\setup.ps1
```
*(脚本会自动完成环境创建和依赖安装)*

此后，只需在新电脑运行 Activate.ps1 即可激活环境。

### 新增文件说明

我已经为您创建了以下文件：

1.  **setup.ps1**: 智能环境配置脚本。
    *   会自动检查 .venv 是否存在/损坏。
    *   如果是坏的（比如直接拷过来的），它会自动删除重建。
    *   会自动识别 pyproject.toml 或 `requirements.txt` 并安装依赖。

2.  **clean_for_export.ps1**: 清理脚本。
    *   安全删除 .venv, __pycache__, .idea 等无需迁移的文件。

Made changes.