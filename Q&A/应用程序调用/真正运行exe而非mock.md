think silently:
用户提出了一个非常实际的问题：当前的 MCP 服务器脚本中，很多工具函数（如 `run_MIP`, `run_Aifrac` 等）虽然名字叫“运行程序”，但实际上只是返回了一个预设的图片 URL（Mock 数据），并没有真正等待 EXE 计算完成并使用其产生的新数据。

用户希望解决这个问题，让 Agent **真正地调用 EXE 进行计算**，并且能够获取计算后的真实结果（比如生成的图片或数据）。

我需要分析当前脚本存在的问题，并提供解决方案。

**当前脚本的问题分析：**
1.  **Popen 是异步/不阻塞的**：`subprocess.Popen(..., creationflags=DETACHED_PROCESS)` 启动了 EXE 后，Python 脚本**立刻**就往下执行了。
2.  **直接返回 URL**：紧接着 Popen 之后，代码直接 `img_url = ...` 并 return 了。此时，EXE 可能才刚刚启动，甚至还没开始计算，结果文件（图片）肯定还不存在，或者还是旧的。
3.  **Mock 数据**：为了演示，代码里写死了一些 URL 或者在 `try...except` 里直接返回了固定链接。

**解决方案思路：**
要实现“真计算、真结果”，需要改变代码的执行流程。

**方案 A：同步等待 (Synchronous Blocking)**
*   **做法**：使用 `subprocess.run` 或 `process.wait()`。
*   **流程**：启动 EXE -> Python 暂停等待 -> EXE 计算 10 分钟 -> EXE 结束 -> Python 醒来 -> Python 去找生成的文件 -> 返回结果。
*   **缺点**：如果计算时间很长（石油软件经常跑好几个小时），HTTP 请求（DeepSeek API）会超时。MCP 协议通常也期望较快的响应。

**方案 B：异步任务 + 轮询 (Async Task + Polling) —— 推荐用于 Web/App**
*   **做法**：
    1.  工具 1 `start_simulation`：启动 EXE，立刻返回一个“任务ID”或“正在运行”的消息。
    2.  工具 2 `check_status`：Agent 过一会儿来问一下“任务ID”好了没。
    3.  工具 3 `get_result`：好了之后，获取结果。
*   **优点**：不会超时，符合长耗时任务的逻辑。

**方案 C：同步等待但设置超时 (对于短时间任务)**
*   如果计算只需要几秒钟或一分钟内，可以直接在 Python 里 `wait()`。

**结合用户代码的改进建议：**
用户提供的代码看起来是一个 Demo，想要变成实用工具。针对石油/地质软件（通常计算慢），**直接等待（方案 A）**可能会导致 AI 对话框卡死或者超时报错。

但如果用户坚持要在一次对话交互中完成（或者假设计算很快），我可以先提供**方案 A（同步等待）**的代码，因为改动最小，逻辑最直观。

同时，必须指出**文件生成的时序问题**。如果 EXE 还没跑完，代码就去读取图片，肯定报错或读到旧图。

**具体修改点：**
1.  **替换 Popen 为 run 或者增加 wait()**：确保 EXE 跑完了再往下走。
2.  **移除 Hardcoded URL**：不要返回固定的 `image2.gif`，而是去检查 EXE 输出目录里到底有没有新文件生成。
3.  **动态文件名**：如果 EXE 输出文件名是固定的（覆盖旧文件），需要处理缓存问题；如果文件名带时间戳，需要捕获该文件名。
4.  **图片转 URL**：本地生成的图片，浏览器（DeepSeek 网页端）是访问不到 `E:\GeFrac\...` 的。必须通过 HTTP 服务（Flask）把这个文件 serve 出来。代码里已经有 `url_for`，说明这一步已经考虑了，但需要确保 Flask 的 `static` 目录和 EXE 的输出目录是挂钩的，或者有文件复制操作。

**重构 `run_MIP` 为例：**

*   *旧逻辑*：启动 EXE (不等待) -> 返回固定 URL。
*   *新逻辑*：启动 EXE -> **等待结束** -> **检查输出文件是否存在** -> **将输出文件复制到 Flask static 目录** -> 生成该文件的 URL -> 返回。

**需要特别注意的点：**
*   `DETACHED_PROCESS` 是为了让子进程独立，这通常用于“发射后不管”。如果我们要结果，就不能“不管”，必须等它结束。
*   Flask 的 `static` 目录：EXE 生成的文件通常在工作目录下，为了让 Web 能访问，通常需要把生成的图片 copy 到 Flask 的 static 文件夹下。

**代码构建：**

我会修改其中一两个典型的函数（如 `run_MIP` 或 `run_Aifrac`）来展示如何实现“真调用”。

**步骤：**
1.  **引入等待机制**：用 `process.wait()`。
2.  **文件搬运**：计算完成后，用 `shutil.copy` 把结果搬到 Web 目录。
3.  **验证**：检查 `returncode` 确保计算成功。

Let's draft the response.

*   **问题核心**：代码用了 `DETACHED_PROCESS` 且没有 `wait`，导致 Python 不管 EXE 跑没跑完就直接返回了假数据。
*   **解决方法**：
    1.  去掉 `DETACHED_PROCESS` 或保留但配合 `wait()`。
    2.  使用 `subprocess.run` (简单粗暴，适合短任务)。
    3.  增加文件检查逻辑 (os.path.exists)。
    4.  增加文件移动逻辑 (move to static folder)。

由于石油软件通常运行慢，我需要提示用户：如果运行时间 > 1分钟，建议改为“提交任务 -> 查询状态”的模式。但为了直接回答用户“如何真调用”的问题，我先按同步模式改写。

**改写 `run_Aifrac` 示例：**

```python
@mcp.tool()
async def run_Aifrac(query: str) -> str:
    # ... checks ...
    exe_path = r"E:\GeFrac\01_C_Platform\runGefrac.exe"
    
    # 1. 定义输出文件的预期路径 (假设EXE会在当前目录生成 AiFrac_result.gif)
    expected_output = os.path.join(query, "AiFrac_result.gif")
    
    # 清理旧文件，确保拿到的是这次算出来的
    if os.path.exists(expected_output):
        os.remove(expected_output)

    try:
        # 2. 同步运行：等待 EXE 执行完毕
        # check=True 会在非0退出码时抛出异常
        subprocess.run([exe_path], cwd=query, check=True) 
        
        # 3. 检查文件是否真的生成了
        if not os.path.exists(expected_output):
             return "错误：程序运行结束，但未生成结果文件。"

        # 4. (关键) 将生成的文件复制到 Flask 的 static 目录，以便生成 URL
        # 假设 Flask static 目录在当前脚本相对位置 static/simulation/
        flask_static_dir = os.path.join(os.getcwd(), "static", "simulation")
        os.makedirs(flask_static_dir, exist_ok=True)
        
        target_filename = f"AiFrac_result_{int(time.time())}.gif" # 加时间戳防止缓存
        destination = os.path.join(flask_static_dir, target_filename)
        
        shutil.copy(expected_output, destination)
        
        # 5. 生成 URL
        img_url = url_for('static', filename=f'simulation/{target_filename}', _external=True)
        return f"![仿真结果]({img_url})"

    except subprocess.CalledProcessError as e:
        return f"仿真程序运行失败，错误码: {e.returncode}"
```

这样就闭环了。

Wait, I should also mention the Timeout issue. FastMCP or DeepSeek API might timeout if the exe takes too long.
But focusing on the "how to really invoke and get result" first.

Structure of the answer:
1.  **指出根本原因**：使用了 `DETACHED_PROCESS` 且没有 `wait()`，导致 Python 没等结果。
2.  **核心修改方案**：
    *   改为同步等待 (`subprocess.run` 或 `popen.wait()`)。
    *   增加文件搬运逻辑 (从工作目录 -> Web目录)。
    *   加上时间戳 (防止看到旧图)。
3.  **代码示例**：重写 `run_Aifrac`。
4.  **进阶建议**：对于长耗时任务（几小时），不能傻等，要用“异步任务ID”模式。

Let's refine the code. The user's code uses `FastMCP` and also seems to imply a Flask context (using `url_for`).
If `FastMCP` is running standalone, `url_for` might not work without an active request context or app context pushed. The user handled this with a `try-except RuntimeError` block constructing the URL manually. I should keep that logic.

**Refined `run_Aifrac` logic:**
1. Check inputs.
2. Clean old result in work dir.
3. Run exe with `subprocess.run(..., check=True)`. This blocks until finished.
4. Check if result file exists.
5. Copy result file to a directory served by the web server (e.g., `./static/`).
6. Construct the URL pointing to that static file.
7. Return markdown.

This directly solves "not really calculating".

One detail: user's code `from flask import url_for`. This implies there IS a Flask app running somewhere, or they are just using the helper.
I will assume there is a static file server running on localhost:5000.

Let's provide the modified code.

Also need to explain **why** the current code fails (it returns immediately before the EXE finishes).

And warning about **Timeout**: AI agents have a timeout (usually 30-60s). If the exe takes longer, this synchronous approach will fail (AI will say "Error" or "Timeout").

I will provide the synchronous solution first as it's what they asked for ("how to fix it"), then mention the async pattern as a best practice.

**Summary of changes to the script:**
1. Import `shutil`, `time`.
2. Remove `DETACHED_PROCESS`.
3. Use `subprocess.run` instead of `Popen`.
4. Add file copy logic.
5. Construct URL dynamically based on the copied file name.

I will select one function `run_Aifrac` to demonstrate the transformation.

User's script uses `url_for('simulation', ...)` which suggests a blueprint or route named simulation serving files.
If I can't guarantee the Flask setup, I will suggest a manual URL construction or keeping their existing `try/except` fallback but pointing to the *newly copied* file.

Let's write the response.

**Response Structure:**
1.  **直接回答**：指出现象原因（异步启动未等待）和解决核心（改为同步等待+文件搬运）。
2.  **代码修改实战**：以 `run_Aifrac` 为例，展示修改前后的对比和完整代码。
3.  **关键步骤解析**：
    *   **同步执行**：让 Python 停下来等 EXE。
    *   **清理与验证**：删旧文件，查新文件。
    *   **结果搬运**：把 EXE 生成在深层目录的文件复制到 Web 服务器能访问的 `static` 目录。
    *   **防缓存**：给文件名加时间戳。
4.  **重要提示（关于耗时）**：如果 EXE 跑太久怎么办？（引入异步查询模式的概念）。

This covers all bases. The user wants to know *how* to make it real. The answer is "Wait for it".

One small correction: `subprocess.run` captures stdout/stderr, but for GUI/Simulation tools, they often output files. The key is simply waiting for the process to exit.

I will also modify `run_MIP` or `run_Petrel2Aifrac` as examples, maybe `run_Aifrac` is best as it produces a gif.

Let's generate the code.
`subprocess.run([exe_path], cwd=query, check=True)` is the standard way.

Also, `shutil.copy` is needed.

The user's code structure:
```python
@mcp.tool()
async def run_Aifrac(query: str) -> str:
   ...
```
I will keep this signature.

Ready.write_response.

---
**Thinking Process End.**

针对你提出的“**只是后台调用了图片，没有真正运行计算**”的问题，根本原因在于你当前的代码使用了 **“发射后不管”** 的模式。

### 问题根源分析
1.  **异步启动**：你使用了 `subprocess.Popen` 配合 `DETACHED_PROCESS`（分离进程）。这意味着 Python 脚本在启动 EXE 后，**立刻**就继续往下执行了。
2.  **时间差**：当 Python 执行到 `return f"![...](url)"` 时，EXE 可能才刚刚启动，甚至还没开始加载数据，结果文件肯定还没生成。为了防止报错，之前的代码只能返回一个“假的”或“旧的”图片链接。
3.  **结果获取**：Web 浏览器无法直接访问你本地磁盘（如 `E:\GeFrac\...`）的文件，必须将生成的结果复制到 Web 服务器（Flask）的静态目录中。

---

### 解决方案：改为“同步等待”模式

要实现“真计算、真结果”，你需要修改代码逻辑，遵循以下 **4步流程**：

1.  **清理现场**：在运行前删除旧的结果文件，确保拿到的是最新的。
2.  **同步等待**：使用 `subprocess.run` 代替 `Popen`，让 Python 脚本**暂停**，直到 EXE 运行结束。
3.  **结果搬运**：计算结束后，将 EXE 在工作目录生成的图片，**复制**到 Flask 的 `static` 目录。
4.  **返回链接**：指向这个新复制的、带有时间戳的图片。

### 代码修改示例

以你的 `run_Aifrac`（仿真模拟）为例，这是修改后的代码。请注意注释中的变化：

```python
import shutil
import time
import subprocess
import os
from flask import url_for

# ... 其他引用保持不变 ...

@mcp.tool()
async def run_Aifrac(query: str) -> str:
    """运行仿真模拟程序（真计算版本）

    Args:
        query: 工作路径
    """
    if query is None or not os.path.exists(query):
        return f"工作路径 {query} 不存在，请检查"

    exe_path = r"E:\GeFrac\01_C_Platform\runGefrac.exe"
    
    # 1. 定义预期生成的结果文件名 (假设 EXE 会在工作目录下生成 result.gif)
    # 你需要确认 EXE 到底生成什么文件
    result_filename = "result.gif" 
    result_path_in_workdir = os.path.join(query, result_filename)

    # 2. 【清理】运行前先删除旧文件，防止假结果
    if os.path.exists(result_path_in_workdir):
        try:
            os.remove(result_path_in_workdir)
        except Exception:
            pass # 如果删不掉就算了

    try:
        # 3. 【真运行】使用 subprocess.run 并去掉 DETACHED_PROCESS
        # check=True 表示如果 EXE 报错(返回码不为0)，Python 也会抛出异常
        # timeout=600 表示如果 10 分钟没算完，就强制报错停止，防止 Agent 卡死
        print(f"正在启动仿真程序: {exe_path}，请等待...")
        
        subprocess.run(
            [exe_path], 
            cwd=query, 
            check=True, 
            timeout=600, # 设置一个合理的超时时间
            stdout=subprocess.DEVNULL, # 如果不需要看黑框输出，可以隐藏
            stderr=subprocess.PIPE     # 捕获错误信息
        )
        
        # 4. 【验证】程序跑完了，检查文件生成了吗？
        if not os.path.exists(result_path_in_workdir):
            return "错误：仿真程序运行结束，但未检测到结果文件生成。请检查模型参数。"

        # 5. 【搬运】将生成的图片复制到 Web 服务器的 static 目录
        # 假设 Flask 的 static 目录在当前脚本同级的 static/simulation/
        flask_static_dir = os.path.join(os.getcwd(), "static", "simulation")
        os.makedirs(flask_static_dir, exist_ok=True)
        
        # 加时间戳，防止浏览器缓存旧图
        timestamp = int(time.time())
        new_filename = f"AiFrac_result_{timestamp}.gif"
        final_dest_path = os.path.join(flask_static_dir, new_filename)
        
        shutil.copy(result_path_in_workdir, final_dest_path)

        # 6. 【返回】构造指向新文件的 URL
        try:
            # 尝试使用 Flask 的 url_for
            img_url = url_for('static', filename=f'simulation/{new_filename}', _external=True)
        except RuntimeError:
            # 如果没有 Flask 上下文，手动拼接
            img_url = f"http://localhost:5000/static/simulation/{new_filename}"

        return f"仿真计算完成！\n![四维地应力结果]({img_url})"

    except subprocess.TimeoutExpired:
        return "错误：仿真计算超时（超过10分钟），请检查模型规模或稍后查询。"
    except subprocess.CalledProcessError as e:
        return f"仿真程序运行崩溃，错误码: {e.returncode}\n错误信息: {e.stderr.decode('gbk', errors='ignore')}"
    except Exception as e:
        return f"调用过程发生未知异常: {str(e)}"
```

### 关键改进点解释

1.  **`subprocess.run(..., check=True)`**：
    *   这是改动的核心。Python 会**卡在这里等待** EXE 运行结束。只有 EXE 窗口关闭了，代码才会往下走。这样保证了结果一定是计算完之后的。

2.  **`os.remove(result_path_in_workdir)`**：
    *   **防呆设计**。如果这次计算失败了，而文件夹里还留着上次成功的图，Agent 可能会误报成功。删掉旧图能确保逻辑严密。

3.  **`shutil.copy(...)` 与 时间戳**：
    *   Web 服务器（Flask）通常只能读取特定目录（static）下的文件。直接把 URL 指向 `E:\...` 是不行的。
    *   给文件名加上 `_{timestamp}`（如 `result_1715423.gif`），可以避免 Agent 在对话中展示图片时，浏览器因为缓存而一直显示第一张旧图。

### 一个潜在的新问题：计算太慢怎么办？

如果你的 EXE 也就是 `runGefrac.exe` 运行一次需要 **3分钟以上**，上面的代码会导致 AI 的对话框**超时报错**（大部分 LLM API 的超时时间在 60秒到 120秒左右）。

**如果计算非常耗时，你需要改成“异步任务模式”：**

1.  **Agent 调用工具**：启动 EXE（用 `Popen`），记录 PID，直接返回：“任务已启动，正在后台计算，请稍后再问我结果。”
2.  **用户等待**：过了一会儿。
3.  **用户问**：“算好了没？”
4.  **Agent 调用查询工具**：Python 脚本去检查那个 PID 还在不在，或者检查结果文件生成了没。如果生成了，再返回图片。

如果计算通常在 **1分钟以内**，上面的**同步代码**是完全没问题的。