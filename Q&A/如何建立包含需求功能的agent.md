你好！这是一项非常具体的自动化任务，结合了**大模型（LLM）的语义理解能力**和**本地系统操作**。

DeepSeek 的 API 目前完全兼容 OpenAI 的 SDK 格式，这使得调用非常方便。

以下是实现这两个功能的完整方案：

### 核心思路

1.  **功能一（一致性校验）：** 利用 DeepSeek 的“阅读理解”能力。我们不需要自己写复杂的正则表达式去匹配表格和文字，而是直接把包含文字和表格的内容（字符串格式）传给 DeepSeek，利用 Prompt 让它提取两个数值并进行比对，最后以结构化数据（如 JSON）返回结果。
2.  **功能二（调用 exe）：** 使用 Python 标准库 `subprocess`，这是执行外部命令最安全、最标准的方法。

---

### 第一步：准备工作

你需要安装 OpenAI 的 Python 库（因为 DeepSeek 兼容该协议）：

```bash
pip install openai
```

### 第二步：完整代码实现

下面的代码展示了如何将两者结合：首先调用 DeepSeek API 进行比对，然后根据比对结果（或直接）调用本地的 `.exe` 程序。

```python
import os
import json
import subprocess
from openai import OpenAI

# 1. 配置 DeepSeek API
# 建议将 API Key 放在环境变量中，或者在此处直接替换
API_KEY = "sk-your-deepseek-api-key" 
BASE_URL = "https://api.deepseek.com"

client = OpenAI(api_key=API_KEY, base_url=BASE_URL)

def check_consistency_with_deepseek(content):
    """
    使用 DeepSeek API 分析文本和表格中的流速是否一致
    """
    system_prompt = """
    你是一个文档分析助手。你需要完成以下任务：
    1. 从提供的文本内容中识别“流速”相关的数值。
    2. 从提供的表格内容中识别“流速”相关的数值。
    3. 对比这两个数值是否数学上相等（例如 5.0 和 5 是一致的）。
    
    请务必只返回 JSON 格式结果，不要包含 Markdown 标记或其他废话。
    格式如下：
    {
        "text_value": "识别到的文本数值",
        "table_value": "识别到的表格数值",
        "is_consistent": true/false,
        "reason": "简短的比对说明"
    }
    如果找不到数值，请在 value 字段填 null。
    """

    try:
        response = client.chat.completions.create(
            model="deepseek-chat",  # 或者 deepseek-v3
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"请分析以下文档内容：\n\n{content}"}
            ],
            temperature=0.1, # 低温度以保证输出结果的确定性
            response_format={ "type": "json_object" } # 强制 JSON 输出（如果模型支持）
        )
        
        result_content = response.choices[0].message.content
        result_json = json.loads(result_content)
        return result_json
        
    except Exception as e:
        print(f"调用 API 出错: {e}")
        return None

def run_external_exe(exe_path, args=[]):
    """
    调用外部 EXE 程序
    """
    if not os.path.exists(exe_path):
        print(f"错误: 找不到文件 {exe_path}")
        return

    try:
        print(f"正在启动程序: {exe_path} 参数: {args}")
        
        # subprocess.run 是同步调用，会等待 exe 执行完毕
        # 如果需要异步（不等待），可以使用 subprocess.Popen
        result = subprocess.run(
            [exe_path] + args, 
            capture_output=True, # 捕获输出
            text=True,           # 以文本形式处理输出
            check=True           # 如果 exe 返回错误码则抛出异常
        )
        
        print("程序执行成功！")
        print("输出内容:", result.stdout)
        
    except subprocess.CalledProcessError as e:
        print(f"程序执行失败，返回码: {e.returncode}")
        print("错误输出:", e.stderr)
    except Exception as e:
        print(f"调用发生未知错误: {e}")

# ================= 模拟测试 =================

if __name__ == "__main__":
    # 假设这是你从文件中读取到的内容（包含文字和 Markdown/文本格式的表格）
    # 如果你的源文件是 PDF 或 Word，需要先用 python-docx 或 pdfplumber 转为这种字符串
    document_content = """
    项目报告：
    在本次水利测试中，我们对管道进行了详细检测。
    经过多次测量，我们确认当前的平均流速是 5.2 m/s，符合预期标准。
    
    详细数据表：
    | 参数名称 | 测量值 | 单位 |
    | :--- | :--- | :--- |
    | 温度 | 25 | C |
    | 流速 | 5.2 | m/s |
    | 压力 | 101 | kPa |
    """

    # 1. 执行第一步：比对数据
    print("正在进行 DeepSeek 一致性校验...")
    check_result = check_consistency_with_deepseek(document_content)
    
    if check_result:
        print(f"校验结果: {json.dumps(check_result, indent=2, ensure_ascii=False)}")
        
        # 逻辑判断：例如，只有当数据一致时才运行 EXE，或者无论如何都运行
        if check_result.get("is_consistent"):
            print("数据一致，准备调用外部程序...")
            
            # 2. 执行第二步：调用 EXE
            # 请替换为你的实际 exe 路径
            target_exe = r"C:\Windows\System32\ping.exe" 
            exe_arguments = ["127.0.0.1", "-n", "2"] # 示例参数
            
            run_external_exe(target_exe, exe_arguments)
        else:
            print("警告：文档数据不一致，停止后续操作。")
    else:
        print("分析失败。")
```

### 代码详解

#### 1. 关于 DeepSeek API 的使用技巧
*   **Prompt 设计**：为了让 AI 准确对比，Prompt 中明确了三个步骤（找文字、找表格、对比）。
*   **结构化输出**：要求 AI 返回 `JSON` 格式。这是关键，因为我们需要在代码中用 `if check_result["is_consistent"]` 这样的逻辑来判断下一步操作，而不是去解析一段自然语言文本。
*   **Temperature**：设置为 `0.1`，这会让模型的回答非常严谨、由事实驱动，减少“幻觉”或创造性发挥，适合数据提取任务。

#### 2. 关于调用 EXE (subprocess)
*   **`subprocess.run`**: 这是现代 Python 推荐的方式。
*   **参数传递**: `[exe_path] + args`，将路径和参数作为一个列表传入，避免了命令行注入攻击的问题，也处理了路径中包含空格的情况。
*   **`capture_output=True`**: 这样你可以捕获 exe 打印到控制台的内容（stdout），如果你的 exe 运行完会输出一些结果供 Python 读取，这个很有用。

### 补充：关于“识别”的前置处理

如果你的输入文件是 PDF、Word 或图片，DeepSeek 不能直接“看”文件（除非使用其多模态功能，但纯文本 API 更便宜且稳定）。你需要先提取文本：

1.  **Word (.docx)**: 使用 `python-docx` 库提取所有文本。
2.  **PDF**: 使用 `pdfplumber` 库。它不仅能提取文字，还能很好地提取表格结构转为列表或 Markdown，这不仅对 LLM 更友好，也能提高识别准确率。
3.  **图片**: 需要使用 OCR 技术（如 `PaddleOCR` 或 `Tesseract`）先转为文字，再传给 DeepSeek。

如果你需要关于 **“如何读取 PDF/Word 并提取表格传给 API”** 的代码，请告诉我，我可以补充这一部分。