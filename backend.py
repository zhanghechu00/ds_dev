import asyncio

import requests
import json
from dotenv import load_dotenv
import os

from mcp_client import MCPClient


def get_api_key() -> str:
    """Load the API key from an environment variable."""
    load_dotenv()
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise ValueError("未找到 OPENROUTER_API_KEY 环境变量，请在 .env 文件中设置。")
    return api_key


OPENROUTER_API_KEY = get_api_key()
# MODEL_NAME = "openai/gpt-4o-mini"
# MODEL_NAME = "deepseek/deepseek-chat-v3-0324:free"
MODEL_NAME = "deepseek-chat"
content=[]
TOOLS = [
    # {
    #     "type": "function",
    #     "function": {
    #         "name": "search",
    #         "description": "搜索网络",
    #         "parameters": {
    #             "type": "object",
    #             "properties": {
    #                 "query": {
    #                     "type": "string",
    #                     "description": "要搜索的内容"
    #                 }
    #             },
    #             "required": ["query"]
    #         }
    #     }
    # },
    {
        "type": "function",
        "function": {
            "name": "run_map2petrel",
            "description": "从高程数据建立Petrel地质模型",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "工作路径"
                    },
                    "file_name": {
                        "type": "string",
                        "description": "高程数据文件名"
                    }

                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "run_wellcalc",
            "description": "运行测井地应力计算",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "工作路径"
                    },
                    "file_name": {
                        "type": "string",
                        "description": "测井数据文件名"
                    }

                },
                "required": []
            }
        }
    },
    # {
    #     "type": "function",
    #     "function": {
    #         "name": "run_MIP",
    #         "description": "运行反演仿真模拟程序",
    #         "parameters": {
    #             "type": "object",
    #             "properties": {
    #                 "query": {
    #                     "type": "string",
    #                     "description": "工作路径"
    #                 }
    #             },
    #             "required": []
    #         }
    #     }
    # },
    {
        "type": "function",
        "function": {
            "name": "run_Aifrac",
            "description": "压裂仿真和四维地应力分析",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "工作路径"
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "run_Petrel2Aifrac",
            "description": "运行Petrel转Aifrac程序，将Petrel数据（.GRDECL格式）转换为Aifrac格式，地质模型转地质力学模型",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "工作路径"
                    },
                    "file_name": {
                        "type": "string",
                        "description": "Petrel文件名"
                    }
                },
            }
        }
    },
    # {
    #     "type": "function",
    #     "function": {
    #         "name": "run_crashsimulation",
    #         "description": "运行一个碰撞模拟程序",
    #         "parameters": {
    #             "type": "object",
    #             "properties": {
    #                 "query": {
    #                     "type": "string",
    #                     "description": "工作路径"
    #                 },
    #                 "file_name": {
    #                     "type": "string",
    #                     "description": "模型文件名"
    #                 }
    #             },
    #         }
    #     }
    # },
    {
        "type": "function",
        "function": {
            "name": "run_Aifrac2Petrel",
            "description": " 运行Aifrac转Petrel程序，将计算结果为Petrel格式",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "工作路径"
                    },

                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "run_boundary",
            "description": "自动设定边界条件，对转换后的模型施加力边界",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "工作路径"
                    },
                    "F": {
                        "type": "string",
                        "description": "上覆压力"
                    }
                },
                "required": []
           }
        }
    },
    #  {
    #     "type": "function",
    #     "function": {
    #         "name": "send_image",
    #         "description": "返回一个结果图片的 Markdown 链接，便于前端直接显示图片",
    #         "parameters": {
    #             "type": "object",
    #             "properties": {
    #                 "url": {
    #                     "type": "string",
    #                     "description": "图片的 URL（可选，不传则返回随机图）"
    #                 },
    #                 "alt": {
    #                     "type": "string",
    #                     "description": "图片描述（alt 文本），默认“结果图片”"
    #                 }
    #             },
    #             "required": []
    #         }
    #     }
    # },
    {
        "type": "function",
        "function": {
            "name": "search_result",
            "description": "查看其他数据结果（井周压裂模拟结果、四维压裂结果、地应力数据统计结果），返回一个结果的 Markdown 链接，便于前端直接显示",
            "parameters": {
                "type": "object",
                "properties": {
                    "alt": {
                        "type": "string",
                        "description": "结果描述（alt 文本），默认“压裂模拟结果”"
                    }
                },
                "required": []
            }
        }
    }

]
WELCOME_MD = (
    "👋 **您好！我是Aifrac智能体，很高兴为您服务！**\n"
    "我是由武汉大学联合武汉市鸿理科技有限公司开发的Aifrac智能体，能够协助您完成从地质力学建模、压裂仿真和四维地应力分析等工作。\n"
    "第一步，请您先提供整个项目的工作路径！\n\n"
)

SYSTEM_PROMPT   = (
    "你是由武汉大学联合武汉市鸿理科技有限公司开发的Aifrac智能体，你能够调用一些工具和解答相关专业问题 。你的回复都非常专业简洁\n"
    "你需要对用户的提示操作步骤：step1.提示用户先设定工作路径；step2.提示用户将高程数据map.txt人工放到工作目录下面，用户回复后，执行从高程数据建立Petrel地质模型,提示用户建模完成；step3.提示用户将测井数据放到工作目录后，可以运行测井地应力计算，反馈运行结果；step4.提示用户可以进行Aifrac仿真模拟，询问用户是否进行仿真模拟，用户确认，反馈运行情况；step5.如果用户是否需要查看其他信息（如井周压裂模拟结果、四维压裂结果、地应力数据统计结果），将调取其他数据进行查看。\n"
    "当你认为用户意图涉及到调用工具时，判断用户希望执行的工具，必要参数未提供或不完整时，也必须返回tool_calls，前端会渲染表单让用户填写。\n"
    "！当你使用的工具返回了一个图片链接时，你必须将这个链接放在你接下来的回复中，必须显示为图片。\n"
)
REQUIRED_FIELDS = {
    "run_MIP": ["query"],
    "run_Aifrac": ["query"],
    "run_Petrel2Aifrac": ["query", "file_name"],
    "run_Aifrac2Petrel": ["query"],
    "run_boundary": ["query", "F"],
    "run_crashsimulation": ["query", "file_name"],
}
class AppLogger:
    def __init__(self):
        """Initialize the logger with a file that will be cleared on startup."""
        self.log_file = "model.log"
        # Clear the log file on startup
        with open(self.log_file, 'w', encoding='utf-8', errors='ignore') as f:
            f.write("")

    def log(self, message):
        """Log a message to both file and console."""

        # Log to file
        with open(self.log_file, 'a', encoding='utf-8', errors='ignore') as f:
            f.write((message or "") + "\n")


logger = AppLogger()
def _schema_by_tool(tool_name: str):
    for t in TOOLS:
        fn = t.get("function", {})
        if fn.get("name") == tool_name:
            return fn.get("parameters", {}) or {}
    return {}
def _required_by_backend(tool_name: str):
    return REQUIRED_FIELDS.get(tool_name, [])
def _check_and_collect_args(tool_name: str, args: dict):
    """
    返回 (ok, args_or_needparams)
    ok=True: 参数齐全（依据 REQUIRED_FIELDS）
    ok=False: 返回 need_params 结构，前端应渲染表单
    """
    args = args or {}
    required = _required_by_backend(tool_name)
    # 空字符串也视为缺失
    missing = [k for k in required if not str(args.get(k, "")).strip()]

    if not missing:
        return True, args

    # 用 schema.properties 提供 label/placeholder 以提升表单可用性
    schema = _schema_by_tool(tool_name)
    props = schema.get("properties", {}) or {}
    fields = []
    for k in required:
        p = props.get(k, {})
        fields.append({
            "name": k,
            "label": p.get("title", k),
            "placeholder": p.get("description", ""),
            "type": "text" if p.get("type") in (None, "string") else p.get("type"),
            "value": (args or {}).get(k, "")
        })

    need = {
        "need_params": {
            "tool": tool_name,
            "message": "请填写所需参数后继续",
            "fields": fields,
            "schema": schema,
        }
    }
    logger.log(f"缺少参数：{missing}，需要返回 need_params 结构。")
    return False, need
def _check_and_collect_args1(tool_name: str, args: dict):
    """
    返回 (ok, args_or_needparams)
    ok=True: args 已满足需求
    ok=False: 返回 need_params 结构，前端应渲染表单
    """
    schema = _schema_by_tool(tool_name)
    props = schema.get("properties", {}) or {}
    required = schema.get("required", []) or []

    missing = [k for k in required if not (args or {}).get(k)]
    if not missing:
        return True, args

    fields = []
    for k in required:
        p = props.get(k, {})
        fields.append({
            "name": k,
            "label": p.get("title", k),
            "placeholder": p.get("description", ""),
            "type": "text" if p.get("type") in (None, "string") else p.get("type"),
            "value": (args or {}).get(k, "")
        })

    need = {
        "need_params": {
            "tool": tool_name,
            "message": "请填写所需参数后继续",
            "fields": fields,
            "schema": schema,
        }
    }
    return False, need
class LLMProcessor:
    def __init__(self):
        # self.api_key = "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"
        # self.base_url = "https://openrouter.ai/api/v1/chat/completions"
        self.api_key = OPENROUTER_API_KEY
        self.base_url = "https://api.deepseek.com/v1/chat/completions"

        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        self.history = []
    def new_chat(self):
        """重置会话：写入 system + 欢迎语（assistant），并把欢迎语返回给前端显示。"""
        self.history = []
        self.history.append({"role": "system", "content": SYSTEM_PROMPT})
        self.history.append({"role": "assistant", "content": WELCOME_MD})
        return {"reply": WELCOME_MD}
    def _ensure_system_once(self):
        """仅当历史中还没有 system 时，补上 system 提示。"""
        if not any(m.get("role") == "system" for m in self.history):
            self.history.insert(0, {"role": "system", "content": SYSTEM_PROMPT})
    def process_user_query(self, query):

        # self.history.append({"role": "system", "content": "你是由武汉大学联合武汉市鸿理科技有限公司开发的Aifrac智能油气专家，你能够调用一些工具和解答相关专业问题 。"})
        # self.history.append({"role": "system", "content": "你需要对用户的提示操作步骤：step1.提供用户先设定工作路径；step2.提供用户将高程数据map.txt人工放到工作目录下面，运行高程数据Petrel建模,提示用户建模完成，让用户使用Petrel软件核对模型情况，用户确认无误执行下一步；step3.提示用户，可以运行Petrel转Aifrac程序，反馈转换结果；step4.提示用户是否执行自动设定边界条件，告诉运行情况；step5.提示用户可以进行Aifrac正演仿真模拟，反馈运行情况，或是提示用户将测井数据放到工作目录后，可以运行测井地应力约束，反馈运行结果，；step6.如果用户执行了测井地应力约束提示用户可以进行反演仿真模拟，反馈运行情况；step7.提示用户可以进行Aifrac转Petrel程序，将计算结果转换为Petrel格式，反馈转换结果，告诉用户可以在Petrel中查看结果。"})
        # self.history.append({"role": "system", "content": "当你认为用户意图涉及到调用工具时，判断用户希望执行的工具，必要参数未提供或不完整时，也必须返回tool_calls，前端会渲染表单让用户填写。"})
        self._ensure_system_once()
        self.history.append({"role": "user", "content": query})

        self.history.append({"role": "user", "content": query})

        first_model_response = self.call_model()

        first_model_message = first_model_response["choices"][0]["message"]
        self.history.append(first_model_message)
        # 检查模型是否需要调用工具
        if "tool_calls" in first_model_message and first_model_message["tool_calls"]:
            tool_call = first_model_message["tool_calls"][0]
            tool_name = tool_call["function"]["name"]
            tool_args = json.loads(tool_call["function"]["arguments"])

            # result = self.execute_tool(tool_name, tool_args)
            # result = self.execute_tool_with_mcp(tool_name, tool_args)
            ok, args_or_need = _check_and_collect_args(tool_name, tool_args)
            logger.log(f"Tool call: {tool_name}, args: {args_or_need}, ok: {ok}")
            if not ok:
    # 缺少必填参数：把 need_params 返回给 /chat → 前端渲染表单
                return {
                    "final_response": "",
                    **args_or_need  # 即 need_params
                }

            result = self.execute_tool_with_mcp(tool_name, args_or_need)

            self.history.append({
                "role": "tool",
                "tool_call_id": tool_call["id"],
                "name": tool_name,
                "content": result
            })

            second_response_data = self.call_model_after_tool_execution()

            final_message = second_response_data["choices"][0]["message"]
            self.history.append(final_message)

            return {
                "tool_name": tool_name,
                "tool_parameters": tool_args,
                "tool_executed": True,
                "tool_result": result,
                "final_response": final_message["content"],
            }
        else:
            return {
                "final_response": first_model_message["content"],
            }
    # === NEW: resume path when params are provided by the user ===
    def resume_with_tool_params(self, tool_name: str, params: dict):
        """
        用户在前端填写完参数后，从这里继续：
        1) 造一条 'assistant' tool_call（模拟模型刚刚决定调用）
        2) 真正执行 MCP 工具，写入 'tool' 消息
        3) 调用第二次补全，拿到最终回复
        """
        # 1) 造一条人工的 tool_call 消息，保证对话链条完整
        # import uuid, json as _json
        # call_id = f"manual_call_{uuid.uuid4().hex[:8]}"
        # manual_assistant_call = {
        #     "role": "assistant",
        #     "content": "",
        #     "tool_calls": [{
        #         "index": 0,
        #         "id": call_id,
        #         "type": "function",
        #         "function": {
        #             "name": tool_name,
        #             "arguments": _json.dumps(params, ensure_ascii=False)
        #         }
        #     }]
        # }
        logger.log(f"Resume with tool params: {tool_name}, params: {params}")

        logger.log(f"历史长度：{len(self.history)}")
        logger.log(f"历史最后一条：{self.history[-1] if self.history else '空'}")
        if self.history and self.history[-1].get("tool_calls"):
            self.history[-1]["tool_calls"][0]["function"]["arguments"] = json.dumps(params, ensure_ascii=False)
            tool_call =  self.history[-1]["tool_calls"][0]

        else:
            raise RuntimeError("历史中没有找到最近的 tool_call，无法追加 tool 消息。")
        # self.history.append(manual_assistant_call)

        # 2) 真正执行 MCP 工具
        result = self.execute_tool_with_mcp(tool_name, params)
        self.history.append({
                "role": "tool",
                "tool_call_id": tool_call.get("id"),
                "name": tool_name,
                "content": result + "\n注意：如果工具返回了一个链接，你需要将这个链接放在你接下来的回复中。"
            })
        logger.log(f"模拟的 tool_call 消息已添加到历史：{tool_name}, params: {params}")

        # self.history.append({
        #     "role": "tool",
        #     "tool_call_id": call_id,
        #     "name": tool_name,
        #     "content": result
        # })

        # 3) 二次补全


        second_response_data = self.call_model_after_tool_execution()
        final_message = second_response_data["choices"][0]["message"]
        self.history.append(final_message)

        return {
            "tool_name": tool_name,
            "tool_parameters": params,
            "tool_executed": True,
            "tool_result": result,
            "final_response": final_message["content"],
        }

    def execute_tool(self, function_name, args):
        if function_name == "search":
            # 正常情况下，这里应该调用相关 API 做搜索，为了减少代码的复杂度，
            # 这里我们返回一段假的工具执行结果，用以测试
            return "纽约市今天的天气是晴天，明天的天气是多云。"
        else:
            raise ValueError(f"未知的工具名称：{function_name}")

    def call_model(self):
        # force_tool_first = (len(self.history) <= 2)
        request_body = {
            "model": MODEL_NAME,
            "messages": self.history,
            "tools": TOOLS,
            "stream": False,
            # "tool_choice": "required" if force_tool_first else "auto"
            # "tool_choice": "required"  # 让模型决定是否调用工具
        }

        response = requests.post(
            self.base_url,
            headers=self.headers,
            json=request_body
        )

        logger.log(f"第一次模型请求：\n{json.dumps(request_body, indent=2, ensure_ascii=False)}\n")
        logger.log(f"第一次模型返回：\n{json.dumps(response.json(), indent=2, ensure_ascii=False)}\n")

        if response.status_code != 200:
            raise Exception(f"API request failed with status {response.status_code}: {response.text}")

        return response.json()

    def call_model_after_tool_execution(self):
        second_request_body = {
            "model": MODEL_NAME,
            "messages": self.history,
            "tools": TOOLS,
        }

        # Make the second POST request
        second_response = requests.post(
            self.base_url,
            headers=self.headers,
            json=second_request_body
        )

        logger.log(f"第二次模型请求：\n{json.dumps(second_request_body, indent=2, ensure_ascii=False)}\n")
        logger.log(f"第二次模型返回：\n{json.dumps(second_response.json(), indent=2, ensure_ascii=False)}\n")

        # Check if the request was successful
        if second_response.status_code != 200:
            raise Exception(f"API request failed with status {second_response.status_code}: {second_response.text}")

        # Parse the second response
        return second_response.json()

    # def execute_tool_with_mcp(self, function_name, args):
    #     loop = asyncio.new_event_loop()
    #     return loop.run_until_complete(self.execute_tool_with_mcp_async(function_name, args))
    def execute_tool_with_mcp(self, function_name, args):
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(self.execute_tool_with_mcp_async(function_name, args))
        finally:
            # 优雅关闭，避免 Proactor 未关闭管道的 warning
            try:
                loop.run_until_complete(asyncio.sleep(0))
                loop.run_until_complete(loop.shutdown_asyncgens())
            finally:
                loop.close()


    async def execute_tool_with_mcp_async(self, function_name, args):
        # 获取与当前脚本同目录下的 mcp_server.py 的绝对地址
        # mcp_server_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "mcp_server_haiyou.py"))
        mcp_server_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "mcp_server_shihua.py"))

        # 启动 MCP Client 并调用 MCP Tool
        async with MCPClient("uv", ["run", mcp_server_path]) as client:
            return await client.call_tool(function_name, args)

