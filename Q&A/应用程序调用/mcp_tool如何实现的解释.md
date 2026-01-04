# 代码分析：地形高程数据提取工具

## 功能概述
这是一个异步的MCP（Model Context Protocol）工具函数，用于从地形等高线图片中提取高程数据，并生成网格化的高程文件。

---

## 代码结构分析

### 1. **函数签名**
```python
async def extract_heights_from_image(image_path: str, grid_r: int = 100, grid_c: int = 100) -> str
```
- **异步函数**：使用 `async` 定义，但内部实际是同步操作（存在优化空间）
- **参数**：
  - `image_path`: 输入图片路径
  - `grid_r/grid_c`: 网格分辨率（默认100×100）
- **返回值**：字符串类型的执行结果信息

---

## 执行流程

### 阶段 1: 文件验证
```python
if not os.path.exists(image_path):
    return f"图片文件不存在: {image_path}"
```
✅ **优点**：提前验证输入文件
⚠️ **建议**：可添加文件格式验证（如 `.png`, `.jpg`）

### 阶段 2: 脚本路径定位
```python
script_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "06-contours", "extract.py")
)
```
- 使用相对路径定位 `extract.py` 脚本
- **隐患**：依赖固定的目录结构（`06-contours`）

### 阶段 3: 子进程调用
```python
cmd = ["python", script_path, "--input", image_path, 
       "--gridr", str(grid_r), "--gridc", str(grid_c)]

process = subprocess.Popen(
    cmd, cwd=work_dir,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True
)
```
- **优点**：使用 `Popen` 可捕获输出
- **问题**：`communicate()` 会阻塞，与 `async` 不匹配

---

## 主要问题与优化建议

### ❌ **问题 1：假异步**
```python
async def extract_heights_from_image(...):
    # ... 
    stdout, stderr = process.communicate()  # 🚫 同步阻塞调用
```

**影响**：阻塞事件循环，无法并发处理其他请求

**解决方案**：
```python
import asyncio

async def extract_heights_from_image(...):
    # 使用异步子进程
    process = await asyncio.create_subprocess_exec(
        *cmd,
        cwd=work_dir,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await process.communicate()
```

---

### ⚠️ **问题 2：依赖未检查**
代码注释提到需要：
- `opencv-python`
- `pytesseract`
- Tesseract-OCR 软件

**建议**：添加依赖检查
```python
def check_dependencies():
    try:
        import cv2
        import pytesseract
        pytesseract.get_tesseract_version()
        return True
    except Exception as e:
        return f"缺少依赖: {str(e)}"
```

---

### ⚠️ **问题 3：错误处理不完整**
当前仅捕获通用异常：
```python
except Exception as e:
    return f"调用提取脚本时发生异常: {str(e)}"
```

**改进**：
```python
try:
    # 原有代码
except FileNotFoundError:
    return "Python解释器未找到，请检查环境配置"
except subprocess.TimeoutExpired:
    return "脚本执行超时，图片可能过大"
except Exception as e:
    return f"未知错误: {type(e).__name__}: {str(e)}"
```

---

### ⚠️ **问题 4：输出截断**
```python
return f"... \n{stdout[-500:]}"  # 只返回最后500字符
```

**问题**：可能丢失关键错误信息

**建议**：
```python
# 区分成功和失败的日志处理
if len(stdout) > 1000:
    log_summary = f"[前100字符]\n{stdout[:100]}\n...\n[后400字符]\n{stdout[-400:]}"
else:
    log_summary = stdout
```

---

## 安全性考量

### 🔒 **路径注入风险**
```python
work_dir = os.path.dirname(image_path)  # 用户可控路径
```

**建议**：验证路径合法性
```python
def validate_path(path: str) -> bool:
    # 检查路径遍历攻击
    abs_path = os.path.abspath(path)
    if ".." in abs_path or abs_path.startswith("/etc"):
        return False
    return True
```

---

## 优化后的完整代码

```python
import asyncio
import os
import subprocess
from pathlib import Path

@mcp.tool()
async def extract_heights_from_image(
    image_path: str, 
    grid_r: int = 100, 
    grid_c: int = 100,
    timeout: int = 300  # 新增超时参数
) -> str:
    """
    从地形图图片中提取高程数据（异步版本）
    
    Args:
        image_path: 输入图片路径
        grid_r: 行方向网格数 (默认: 100)
        grid_c: 列方向网格数 (默认: 100)
        timeout: 执行超时时间（秒，默认: 300）
    
    Returns:
        执行结果信息
    """
    # 1. 路径验证
    img_path = Path(image_path).resolve()
    if not img_path.exists():
        return f"❌ 图片文件不存在: {image_path}"
    
    if img_path.suffix.lower() not in ['.png', '.jpg', '.jpeg', '.bmp']:
        return f"❌ 不支持的图片格式: {img_path.suffix}"
    
    # 2. 脚本路径定位
    script_path = Path(__file__).parent / "06-contours" / "extract.py"
    if not script_path.exists():
        return f"❌ 提取脚本不存在: {script_path}"
    
    # 3. 构建命令
    cmd = [
        "python", str(script_path),
        "--input", str(img_path),
        "--gridr", str(grid_r),
        "--gridc", str(grid_c)
    ]
    
    try:
        # 4. 异步执行子进程
        process = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=str(img_path.parent),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        # 5. 等待完成（带超时）
        stdout, stderr = await asyncio.wait_for(
            process.communicate(), 
            timeout=timeout
        )
        
        # 6. 解码输出
        stdout_str = stdout.decode('utf-8', errors='ignore')
        stderr_str = stderr.decode('utf-8', errors='ignore')
        
        # 7. 检查结果
        if process.returncode != 0:
            return f"❌ 脚本执行失败 (退出码: {process.returncode})\n{stderr_str}"
        
        output_file = img_path.parent / "extracted_heights.txt"
        if output_file.exists():
            file_size = output_file.stat().st_size
            return (
                f"✅ 高程提取成功！\n"
                f"📄 输出文件: {output_file}\n"
                f"📊 文件大小: {file_size / 1024:.2f} KB\n"
                f"🔍 网格规格: {grid_r}×{grid_c}\n\n"
                f"--- 执行日志（最后500字符）---\n{stdout_str[-500:]}"
            )
        else:
            return f"⚠️ 脚本运行完成但未生成输出文件\n{stdout_str}"
    
    except asyncio.TimeoutError:
        return f"⏱️ 执行超时（>{timeout}秒），请尝试减少网格密度或使用更小的图片"
    
    except FileNotFoundError:
        return "❌ Python解释器未找到，请检查系统环境变量"
    
    except Exception as e:
        return f"❌ 未知错误: {type(e).__name__}: {str(e)}"
```

---

## 关键改进点总结

| 改进项 | 原代码问题 | 优化方案 |
|--------|-----------|---------|
| **异步处理** | 假异步阻塞 | 使用 `asyncio.create_subprocess_exec` |
| **超时控制** | 无超时机制 | 添加 `asyncio.wait_for` |
| **路径处理** | 字符串拼接 | 使用 `pathlib.Path` |
| **错误分类** | 通用异常捕获 | 细化异常类型处理 |
| **输出格式** | 信息混乱 | 使用emoji和结构化输出 |
| **文件验证** | 仅检查存在性 | 验证文件格式和可读性 |

---

## 依赖的 extract.py 脚本预期接口

根据调用方式推测，`extract.py` 应满足：

```python
# extract.py 的命令行接口
python extract.py \
    --input /path/to/terrain.png \
    --gridr 100 \
    --gridc 100

# 输出文件：与输入图片同目录下的 extracted_heights.txt
# 格式示例：
# 100 100
# 125.5 126.3 127.1 ...
# 124.8 125.9 126.5 ...
```

---

如需进一步分析 `extract.py` 的实现细节或优化建议，请提供该脚本的代码内容。