读取 [](file:///c%3A/program1/git/MYGPTAIv2/backend_shihua.py#1-1)，行 1 到 150

读取 [](file:///c%3A/program1/git/MYGPTAIv2/mcp_client.py)

读取 [](file:///c%3A/program1/git/MYGPTAIv2/backend_shihua.py#151-151)，行 151 到 250

这个项目中的“Agent”实现采用了 **前后端分离 + MCP (Model Context Protocol) 协议 + LLM 工具调用** 的各种分层架构。

核心原理可以概括为：**Backend (大脑/决策者) -> MCP Client (信使) -> MCP Server (工具箱) -> External Script (具体执行者)**。

以下是具体的实现流向：

### 1. 核心架构图解

```mermaid
graph LR
    User[用户/前端] -->|自然语言指令| Backend[Backend (Flask/Python)]
    Backend -->|调用 LLM API| LLM[LLM (DeepSeek/OpenAI)]
    LLM -->|返回 Tool Call 指令| Backend
    Backend -->|实例化| Client[MCP Client]
    Client -->|STDIO 管道通信| Server[MCP Server]
    Server -->|Subprocess 调用| Script[Extract Script (extract.py)]
    Script -->|处理结果| Server
    Server -->|返回结果| Client
    Client -->|返回结果| Backend
    Backend -->|最终回复| User
```

### 2. 各个组件的具体职责

#### A. Backend (backend_shihua.py)：大脑与决策
这是 Agent 的控制中心。
*   **工具定义**：在代码中定义了一个 `TOOLS` 列表（JSON Schema 格式），告诉 LLM 我具备哪些能力（例如：`extract_heights_from_image`, `run_map2petrel`）。
*   **LLM 交互**：它将用户的自然语言（例如“帮我从图片提取高程”）发送给 LLM。
*   **解析意图**：LLM 分析后返回一个结构化的指令：“请调用 `extract_heights_from_image`，参数是 `image_path=...`”。
*   **发起调用**：Backend 收到这个指令后，通过 `MCPClient` 去连接实际的工具服务器。

#### B. MCP Client (mcp_client.py)：通信管道
这是一个中间件，负责连接 Backend 和 MCP Server。
*   它使用 **标准输入输出 (Stdio)** 的方式启动并连接到 MCP Server。
*   它不包含业务逻辑，只负责“传话”，把 Backend 的函数调用请求发给 Server，并把 Server 的执行结果收回来。

#### C. MCP Server (mcp_server_shihua.py)：工具宿主
这是实际存放工具“函数”的地方。
*   **注册工具**：使用 `@mcp.tool()` 装饰器将 `extract_heights_from_image` 等 Python 函数注册为可调用的工具。
*   **执行逻辑**：当收到调用请求时，它会执行具体的 Python 代码。
*   **进程隔离**：对于 `extract` 这样的复杂任务，它不直接在 Server 进程内运行，而是使用 `subprocess.Popen` 启动一个**独立的子进程**来运行 `extract.py`。
    *   这样做的好处是：即使脚本崩了，Server 还能活；而且可以使用独立的环境（.venv）。

#### D. External Script (`extract.py`)：苦力
这是真正的业务逻辑执行者。
*   它是一个独立的 Python 脚本，只负责接收参数（图片路径），进行 OpenCV/OCR 处理，print 结果，生成文件。

### 3. "Agent" 目前的运行机理总结

当你在这个对话框里说“帮我提取高程”时，实际上发生了以下连锁反应：

1.  **意图识别**：`Backend` 把你的话发给 LLM，LLM 识别出你需要使用 `extract_heights_from_image` 工具。
2.  **工具路由**：`Backend` 激活 `MCPClient`，连接到 mcp_server_shihua.py。
3.  **命令下发**：`MCP Server` 接收到请求，构建了一条系统命令（类似 `python -u extract.py ...`）。
4.  **安全执行**：`Simple Stub` (Server) 启动子进程运行脚本，并接管了它的输入输出（防止死锁）。
5.  **结果回传**：脚本生成 TXT 文件 -> Server 确认成功 -> 消息层层回传 -> LLM 看到“提取成功”的结果 -> LLM 组织语言告诉你“高程数据已提取，文件在...”。

**关键点：** 这个 Agent 并不神秘，它就是一个**“甚至能看懂函数说明书的聊天机器人”**，配合一个**“能执行指定函数的服务器”**。