from .llm import chat_completion
from .graph_store import GraphStore
import os
import json

PROMPT_TEMPLATE = """
你需要作为一个专业的石油地质工程领域的知识图谱构建者。
请从以下文本中提取实体（Entities）和关系（Relationships）。
只关注关键的技术概念、工具名称、文件格式、操作步骤和物理参数。
返回格式必须是合法的 JSON 列表，包含对象：[{"source": "实体1", "relation": "关系描述", "target": "实体2"}, ...]。
请不要输出任何 Markdown 格式（如 ```json），只输出纯 JSON 字符串。

文本内容:
{text}
"""

class GraphBuilder:
    def __init__(self, store: GraphStore):
        self.store = store

    def process_document(self, text, filename=""):
        # Basic chunking if too large, simplified here to take first 4000 chars
        # Ideally we should chunk properly
        chunk = text[:4000] 
        prompt = PROMPT_TEMPLATE.format(text=chunk)
        
        print(f"Extracting knowledge from {filename}...")
        response = chat_completion([{"role": "user", "content": prompt}])
        
        try:
            # Clean response
            json_str = response.replace("```json", "").replace("```", "").strip()
            # Find the first [ and last ]
            p1 = json_str.find("[")
            p2 = json_str.rfind("]")
            if p1 != -1 and p2 != -1:
                json_str = json_str[p1:p2+1]
                
            triplets = json.loads(json_str)
            count = 0
            for t in triplets:
                if "source" in t and "relation" in t and "target" in t:
                    self.store.add_triplet(t["source"], t["relation"], t["target"])
                    count += 1
            
            # Also link document to entities? Maybe later.
            self.store.save()
            print(f"Extracted {count} triplets from {filename}.")
            return True
        except Exception as e:
            print(f"Error parsing triplets for {filename}: {e}")
            print(f"LLM Response was: {response}")
            return False

    def build_from_directory(self, directory):
        if not os.path.exists(directory):
            print(f"Directory {directory} does not exist.")
            return

        for root, _, files in os.walk(directory):
            for file in files:
                if file.endswith(".md") or file.endswith(".txt"):
                    path = os.path.join(root, file)
                    with open(path, 'r', encoding='utf-8') as f:
                        text = f.read()
                        self.process_document(text, filename=file)
