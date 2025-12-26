已创建 3 个待办事项

读取 [](file:///c%3A/program1/git/MYGPTAIv2/mcp_server_shihua.py#1-1)，行 1 到 200

读取 [](file:///c%3A/program1/git/MYGPTAIv2/backend_shihua.py#1-1)，行 1 到 200

读取 [](file:///c%3A/program1/git/MYGPTAIv2/backend_shihua.py#201-201)，行 201 到 400

读取 [](file:///c%3A/program1/git/MYGPTAIv2/backend_shihua.py#401-401)，行 401 到 600

现在的 Agent 实现参数补全提醒的机制，是结合了 **Prompt 提示工程** 和 **后端代码逻辑拦截** 的混合模式。

简单来说，Agent（大模型）被指示即使参数不足也要发起工具调用，然后后端代码拦截这个调用，检查参数是否缺失。如果缺失，后端会构造一个特殊的 `need_params` 数据结构返回给前端，由前端渲染表单让用户填写。

具体流程如下：

### 1. Prompt 提示工程 (让模型主动发起调用)
在 backend_shihua.py 中，`SYSTEM_PROMPT` 明确指示了模型：
> "当你认为用户意图涉及到调用工具时，判断用户希望执行的工具，必要参数未提供或不完整时，也必须返回tool_calls，前端会渲染表单让用户填写。"

这意味着，即使你只说了“运行反演”，没有提供路径，模型也会尝试生成一个 `tool_calls`（例如调用 `run_MIP`），哪怕参数是空的。

### 2. 后端拦截与校验 (核心逻辑)
在 backend_shihua.py 的 `process_user_query` 函数中，当模型返回 `tool_calls` 时，代码并不会立即执行工具，而是先进行校验：

```python
# backend_shihua.py

# ... 获取模型返回的 tool_call ...
tool_name = tool_call["function"]["name"]
tool_args = json.loads(tool_call["function"]["arguments"])

# 调用校验函数
ok, args_or_need = _check_and_collect_args(tool_name, tool_args)

if not ok:
    # 缺少必填参数：把 need_params 返回给前端
    return {
        "final_response": "",
        **args_or_need  # 包含需要填写的字段信息
    }
```

### 3. 参数检查函数 `_check_and_collect_args`
这个函数定义了哪些参数是必须的。它读取 `REQUIRED_FIELDS` 字典：

```python
REQUIRED_FIELDS = {
    "run_MIP": ["query"],
    "run_Aifrac": ["query"],
    "run_Petrel2Aifrac": ["query", "file_name"],
    # ...
}
```

如果发现参数缺失（例如 `query` 为空），它会构造一个 `need_params` 对象，包含字段的 `label`、`placeholder` 等信息（从 `TOOLS` 定义中获取），以便前端生成表单。

### 4. 用户补全后的恢复执行
当你在前端填写完参数并提交后，后端会调用 `resume_with_tool_params` 函数：
1.  它会更新历史记录中那个“参数不全”的工具调用，将其参数替换为你填写的完整参数。
2.  然后真正执行 MCP 工具 (`execute_tool_with_mcp`)。
3.  最后将工具执行结果反馈给模型，生成最终回复。

### 总结
Agent 并不是通过“对话”来问你“请提供参数”，而是通过**触发一个未完成的工具调用**，由后端代码捕获这个意图，并强制要求前端显示参数填写界面。