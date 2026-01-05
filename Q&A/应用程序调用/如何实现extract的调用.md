已汇总会话历史记录

读取 [](file:///c%3A/program1/git/MYGPTAIv2/mcp_server_shihua.py#1-1)，行 1 到 100

读取 [](file:///c%3A/program1/git/MYGPTAIv2/mcp_server_shihua.py#101-101)，行 101 到 543

目前 Agent 对 `extract.py` 脚本的调用是通过 MCP (Model Context Protocol) 服务器中的 `extract_heights_from_image` 工具实现的。

以下是其核心实现逻辑的详细解析：

### 1. 工具定义与路径解析
Agent 首先定义了一个异步工具函数，并动态计算脚本的绝对路径，确保无论从哪里启动 MCP 服务器都能找到脚本。

```python
@mcp.tool()
async def extract_heights_from_image(image_path: str, grid_r: int = 100, grid_c: int = 100) -> str:
    # ... (省略部分检查代码)
    
    # 动态定位脚本：基于当前 MCP 服务器文件的相对位置寻找 extract.py
    script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "06-contours", "extract.py"))
    
    # 确定工作目录：以图片所在文件夹作为工作目录，确保输出文件生成在正确位置
    work_dir = os.path.dirname(image_path)
```

### 2. 构建执行命令
这是最关键的一步，为了解决之前的死锁和环境问题，我们构建了非常具体的命令参数：

```python
cmd = [
    sys.executable,  # 关键点1：使用当前环境的 Python (即 .venv)，确保能加载 cv2 等库
    "-u",            # 关键点2：启用 Unbuffered 模式，强制 Python 不缓存 stdout，防止管道死锁
    script_path,     # 目标脚本路径
    "--input", image_path, 
    "--gridr", str(grid_r), 
    "--gridc", str(grid_c)
]
```

### 3. 安全的子进程调用
使用 `subprocess.Popen` 启动进程，并配置了多个安全参数来防止 Agent 挂起：

```python
process = subprocess.Popen(
    cmd,
    cwd=work_dir,               # 在图片目录下运行
    stdin=subprocess.DEVNULL,   # 关键点3：切断标准输入，防止脚本因等待用户输入而永久挂起
    stdout=subprocess.PIPE,     # 捕获标准输出
    stderr=subprocess.PIPE,     # 捕获错误输出
    text=True                   # 以文本方式处理输出
)
```

### 4. 超时控制与结果验证
为了防止脚本无限期运行，增加了超时机制和结果检查：

```python
try:
    # 关键点4：设置 60秒 超时，如果脚本卡死则强制终止
    stdout, stderr = process.communicate(timeout=60)
except subprocess.TimeoutExpired:
    process.kill()
    return "提取脚本运行超时..."

# 检查返回值和输出文件是否存在
output_file = os.path.join(work_dir, "extracted_heights.txt")
if process.returncode == 0 and os.path.exists(output_file):
    return f"高程提取成功！输出文件: {output_file}..."
```

### 总结
这个实现通过 **环境隔离** (`sys.executable`)、**死锁预防** (`-u`, `DEVNULL`) 和 **超时熔断** (`timeout=60`) 三重机制，确保了 Agent 调用外部 Python 脚本时的稳定性和健壮性。