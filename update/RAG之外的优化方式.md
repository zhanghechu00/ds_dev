# Agent 优化方法全景

除了 RAG，还有多种方法可以增强 Agent 的能力。以下是主流的优化技术：

---

## 1. 记忆系统 (Memory Systems)

### 短期记忆 (Short-term Memory)

```python
from langchain.memory import ConversationBufferMemory

# 简单对话缓存
memory = ConversationBufferMemory(
    memory_key="chat_history",
    return_messages=True
)

# 滑动窗口记忆（只保留最近N轮对话）
from langchain.memory import ConversationBufferWindowMemory

window_memory = ConversationBufferWindowMemory(k=5)  # 保留最近5轮
```

### 长期记忆 (Long-term Memory)

```python
from langchain.memory import VectorStoreRetrieverMemory
from langchain.vectorstores import FAISS

# 基于向量的长期记忆
embeddings = OpenAIEmbeddings()
vectorstore = FAISS.from_texts([], embeddings)

long_term_memory = VectorStoreRetrieverMemory(
    retriever=vectorstore.as_retriever(search_kwargs={"k": 3}),
    memory_key="history"
)

# Agent会从历史对话中检索相关信息
```

### 结构化记忆

```python
class StructuredMemory:
    """分类存储不同类型的信息"""
    
    def __init__(self):
        self.user_profile = {}      # 用户信息
        self.task_history = []      # 任务历史
        self.learned_facts = {}     # 学到的事实
        self.preferences = {}       # 用户偏好
    
    def update_user_profile(self, key, value):
        self.user_profile[key] = value
    
    def add_task(self, task):
        self.task_history.append({
            "task": task,
            "timestamp": datetime.now(),
            "status": "completed"
        })
    
    def learn_fact(self, category, fact):
        if category not in self.learned_facts:
            self.learned_facts[category] = []
        self.learned_facts[category].append(fact)
```

---

## 2. 反思机制 (Reflection)

让 Agent 能够评估和改进自己的输出。

```python
class ReflectiveAgent:
    """具有反思能力的Agent"""
    
    def __init__(self, llm):
        self.llm = llm
        self.reflection_history = []
    
    def execute_with_reflection(self, task: str, max_iterations: int = 3):
        """执行任务并进行反思改进"""
        
        current_output = None
        
        for i in range(max_iterations):
            # 1. 执行任务
            if i == 0:
                current_output = self.llm.predict(f"任务：{task}")
            else:
                # 基于反思改进
                current_output = self.llm.predict(
                    f"任务：{task}\n"
                    f"上一次输出：{current_output}\n"
                    f"反思意见：{reflection}\n"
                    f"请改进输出"
                )
            
            # 2. 反思评估
            reflection = self.reflect(task, current_output)
            
            self.reflection_history.append({
                "iteration": i,
                "output": current_output,
                "reflection": reflection
            })
            
            # 3. 判断是否满意
            if self.is_satisfactory(reflection):
                break
        
        return current_output
    
    def reflect(self, task: str, output: str) -> str:
        """对输出进行反思"""
        prompt = f"""
        任务：{task}
        输出：{output}
        
        请从以下角度评估输出质量：
        1. 是否完整回答了问题
        2. 逻辑是否清晰
        3. 有无事实错误
        4. 是否可以改进
        
        提供具体的改进建议。
        """
        return self.llm.predict(prompt)
    
    def is_satisfactory(self, reflection: str) -> bool:
        """判断输出是否令人满意"""
        return "无需改进" in reflection or "质量良好" in reflection
```

### Reflexion 架构

```python
from typing import List, Dict

class ReflexionAgent:
    """实现 Reflexion 论文中的方法"""
    
    def __init__(self, llm, evaluator):
        self.llm = llm
        self.evaluator = evaluator
        self.episodic_memory = []
    
    def solve_task(self, task: str, max_trials: int = 3) -> str:
        """通过试错和反思解决任务"""
        
        for trial in range(max_trials):
            # 1. 生成解决方案
            trajectory = self.generate_trajectory(task)
            
            # 2. 评估结果
            score, feedback = self.evaluator.evaluate(trajectory)
            
            # 3. 如果成功，返回
            if score >= 0.8:
                return trajectory[-1]["action"]
            
            # 4. 生成反思
            reflection = self.generate_reflection(
                task, trajectory, score, feedback
            )
            
            # 5. 存入记忆
            self.episodic_memory.append({
                "task": task,
                "trial": trial,
                "trajectory": trajectory,
                "reflection": reflection,
                "score": score
            })
        
        return "任务失败"
    
    def generate_trajectory(self, task: str) -> List[Dict]:
        """生成行动轨迹，利用过往反思"""
        
        # 检索相关的历史反思
        relevant_reflections = self.retrieve_reflections(task)
        
        prompt = f"""
        任务：{task}
        
        过往经验教训：
        {relevant_reflections}
        
        请一步步解决任务。
        """
        
        # 生成步骤序列
        return self.llm.generate_steps(prompt)
    
    def generate_reflection(self, task, trajectory, score, feedback):
        """生成高层次的反思"""
        prompt = f"""
        任务：{task}
        执行轨迹：{trajectory}
        得分：{score}
        反馈：{feedback}
        
        请分析失败原因，总结经验教训，为下次尝试提供指导。
        """
        return self.llm.predict(prompt)
```

---

## 3. 规划能力 (Planning)

### 分层规划 (Hierarchical Planning)

```python
class HierarchicalPlanner:
    """分层任务规划"""
    
    def __init__(self, llm):
        self.llm = llm
    
    def plan(self, goal: str) -> Dict:
        """将大目标分解为子任务"""
        
        # 高层规划
        high_level_plan = self.llm.predict(f"""
        目标：{goal}
        
        请将此目标分解为3-5个主要步骤（高层计划）。
        """)
        
        # 细化每个步骤
        detailed_plan = {}
        for step in parse_steps(high_level_plan):
            detailed_plan[step] = self.llm.predict(f"""
            步骤：{step}
            
            请将此步骤细化为具体的子任务列表。
            """)
        
        return {
            "high_level": high_level_plan,
            "detailed": detailed_plan
        }
    
    def execute_plan(self, plan: Dict):
        """按计划执行"""
        results = []
        
        for step, subtasks in plan["detailed"].items():
            print(f"执行步骤: {step}")
            
            for subtask in subtasks:
                result = self.execute_subtask(subtask)
                results.append(result)
                
                # 动态调整：如果子任务失败，重新规划
                if not result.success:
                    new_plan = self.replan(step, result.error)
                    results.extend(self.execute_plan(new_plan))
        
        return results
```

### Plan-and-Execute 模式

```python
from langchain.experimental.plan_and_execute import (
    PlanAndExecute,
    load_agent_executor,
    load_chat_planner
)

# 1. 创建规划器
planner = load_chat_planner(llm)

# 2. 创建执行器
executor = load_agent_executor(llm, tools, verbose=True)

# 3. 组合
agent = PlanAndExecute(
    planner=planner,
    executor=executor,
    verbose=True
)

# 使用
agent.run("帮我研究竞争对手的产品定价策略，并生成报告")

# Agent会：
# 1. 先制定计划（搜索竞品 → 收集价格 → 分析对比 → 生成报告）
# 2. 逐步执行每个步骤
# 3. 根据执行结果动态调整后续计划
```

---

## 4. 工具使用优化 (Tool Use Enhancement)

### 工具选择优化

```python
class SmartToolSelector:
    """智能工具选择器"""
    
    def __init__(self, llm, tools):
        self.llm = llm
        self.tools = tools
        self.tool_usage_stats = {}  # 工具使用统计
    
    def select_tool(self, task: str, context: str) -> str:
        """基于任务和历史选择最佳工具"""
        
        # 获取工具使用历史
        tool_performance = self.get_tool_performance(task)
        
        prompt = f"""
        任务：{task}
        上下文：{context}
        
        可用工具：
        {self.format_tools_with_stats(tool_performance)}
        
        根据任务类型和工具历史表现，选择最合适的工具。
        """
        
        selected_tool = self.llm.predict(prompt)
        return selected_tool
    
    def record_usage(self, tool_name: str, success: bool, latency: float):
        """记录工具使用情况"""
        if tool_name not in self.tool_usage_stats:
            self.tool_usage_stats[tool_name] = {
                "count": 0,
                "success_count": 0,
                "avg_latency": 0
            }
        
        stats = self.tool_usage_stats[tool_name]
        stats["count"] += 1
        if success:
            stats["success_count"] += 1
        stats["avg_latency"] = (
            (stats["avg_latency"] * (stats["count"] - 1) + latency) 
            / stats["count"]
        )
```

### 工具组合 (Tool Composition)

```python
class CompositeToolAgent:
    """能够组合多个工具完成复杂任务"""
    
    def __init__(self, llm, tools):
        self.llm = llm
        self.tools = {tool.name: tool for tool in tools}
    
    def execute_composite_task(self, task: str):
        """识别需要组合多个工具的任务"""
        
        # 1. 分析任务需要哪些工具
        plan = self.llm.predict(f"""
        任务：{task}
        
        可用工具：{list(self.tools.keys())}
        
        请设计一个工具调用链来完成此任务。
        格式：tool1(input) -> tool2(tool1的输出) -> ...
        """)
        
        # 2. 按顺序执行工具链
        result = None
        for step in parse_tool_chain(plan):
            tool_name = step["tool"]
            tool_input = step["input"] if result is None else result
            
            result = self.tools[tool_name].run(tool_input)
        
        return result

# 示例：组合工具完成复杂任务
tools = [
    web_search_tool,
    summarization_tool,
    translation_tool,
    email_tool
]

agent = CompositeToolAgent(llm, tools)

# 这个任务需要组合多个工具
agent.execute_composite_task(
    "搜索最新的AI新闻，总结要点，翻译成中文，然后发送给我"
)
# 执行链：web_search -> summarize -> translate -> send_email
```

---

## 5. 多智能体协作 (Multi-Agent Systems)

```python
from langchain.agents import Agent

class MultiAgentSystem:
    """多智能体协作系统"""
    
    def __init__(self):
        self.agents = {}
    
    def add_agent(self, name: str, agent: Agent, role: str):
        """添加专门的智能体"""
        self.agents[name] = {
            "agent": agent,
            "role": role,
            "expertise": []
        }
    
    def collaborate(self, task: str) -> str:
        """多个Agent协作完成任务"""
        
        # 1. 任务分配
        assignments = self.assign_tasks(task)
        
        # 2. 并行或顺序执行
        results = {}
        for agent_name, subtask in assignments.items():
            agent = self.agents[agent_name]["agent"]
            results[agent_name] = agent.run(subtask)
        
        # 3. 结果整合
        final_result = self.synthesize_results(task, results)
        
        return final_result
    
    def assign_tasks(self, task: str) -> Dict[str, str]:
        """根据Agent专长分配任务"""
        # 使用协调者LLM决定任务分配
        pass

# 示例：创建专门的Agent团队
research_agent = create_agent(
    llm, 
    [web_search, academic_search],
    "负责信息搜集和研究"
)

analysis_agent = create_agent(
    llm,
    [data_analysis, visualization],
    "负责数据分析和可视化"
)

writing_agent = create_agent(
    llm,
    [document_generation, formatting],
    "负责文档撰写和格式化"
)

system = MultiAgentSystem()
system.add_agent("researcher", research_agent, "研究员")
system.add_agent("analyst", analysis_agent, "分析师")
system.add_agent("writer", writing_agent, "作家")

# 协作完成复杂报告
result = system.collaborate("撰写一份关于AI行业发展趋势的研究报告")
```

### 辩论式多智能体

```python
class DebateAgents:
    """通过辩论提升答案质量"""
    
    def __init__(self, llm):
        self.llm = llm
    
    def debate(self, question: str, rounds: int = 3) -> str:
        """多个Agent通过辩论达成共识"""
        
        # 初始答案
        agent_a_answer = self.llm.predict(f"问题：{question}\n请给出你的答案。")
        agent_b_answer = self.llm.predict(f"问题：{question}\n请给出你的答案。")
        
        # 辩论轮次
        for round in range(rounds):
            # Agent A 反驳 B
            agent_a_answer = self.llm.predict(f"""
            问题：{question}
            你的立场：{agent_a_answer}
            对方立场：{agent_b_answer}
            
            请指出对方的问题并完善你的答案。
            """)
            
            # Agent B 反驳 A
            agent_b_answer = self.llm.predict(f"""
            问题：{question}
            你的立场：{agent_b_answer}
            对方立场：{agent_a_answer}
            
            请指出对方的问题并完善你的答案。
            """)
        
        # 达成共识
        consensus = self.llm.predict(f"""
        问题：{question}
        Agent A 的最终观点：{agent_a_answer}
        Agent B 的最终观点：{agent_b_answer}
        
        请综合双方观点，给出最终的最佳答案。
        """)
        
        return consensus
```

---

## 6. 自我改进 (Self-Improvement)

### 在线学习

```python
class SelfImprovingAgent:
    """能够从反馈中学习的Agent"""
    
    def __init__(self, llm):
        self.llm = llm
        self.success_cases = []
        self.failure_cases = []
    
    def learn_from_feedback(self, task: str, action: str, 
                           outcome: str, feedback: str):
        """从执行结果中学习"""
        
        case = {
            "task": task,
            "action": action,
            "outcome": outcome,
            "feedback": feedback,
            "timestamp": datetime.now()
        }
        
        if "成功" in outcome or "良好" in feedback:
            self.success_cases.append(case)
        else:
            self.failure_cases.append(case)
        
        # 定期总结经验
        if len(self.success_cases) + len(self.failure_cases) % 10 == 0:
            self.synthesize_learnings()
    
    def synthesize_learnings(self):
        """总结经验教训"""
        
        prompt = f"""
        分析以下成功和失败案例，总结规律：
        
        成功案例：
        {self.success_cases[-5:]}
        
        失败案例：
        {self.failure_cases[-5:]}
        
        提取可复用的策略和应避免的错误。
        """
        
        learnings = self.llm.predict(prompt)
        self.update_strategy(learnings)
```

### Few-shot Learning

```python
class FewShotAgent:
    """动态构建示例以改进性能"""
    
    def __init__(self, llm):
        self.llm = llm
        self.example_pool = []
    
    def run(self, task: str) -> str:
        """使用相关示例增强性能"""
        
        # 1. 检索相似的历史任务
        relevant_examples = self.retrieve_examples(task, k=3)
        
        # 2. 构建 few-shot prompt
        prompt = self.build_few_shot_prompt(task, relevant_examples)
        
        # 3. 执行
        result = self.llm.predict(prompt)
        
        return result
    
    def build_few_shot_prompt(self, task: str, examples: List) -> str:
        """构建包含示例的提示"""
        
        examples_text = "\n\n".join([
            f"示例 {i+1}:\n输入: {ex['input']}\n输出: {ex['output']}"
            for i, ex in enumerate(examples)
        ])
        
        return f"""
        以下是一些类似任务的示例：
        
        {examples_text}
        
        现在请处理这个新任务：
        {task}
        """
    
    def add_example(self, input_text: str, output_text: str, quality_score: float):
        """添加高质量示例到池中"""
        if quality_score > 0.8:
            self.example_pool.append({
                "input": input_text,
                "output": output_text,
                "embedding": self.embed(input_text),
                "score": quality_score
            })
```

---

## 7. 约束和安全性 (Constraints & Safety)

### 宪法AI (Constitutional AI)

```python
class ConstitutionalAgent:
    """遵循预定义原则的Agent"""
    
    def __init__(self, llm, constitution: List[str]):
        self.llm = llm
        self.constitution = constitution  # 行为准则列表
    
    def run(self, task: str) -> str:
        """执行任务但需符合宪法约束"""
        
        # 1. 生成初始响应
        response = self.llm.predict(task)
        
        # 2. 检查是否违反宪法
        for principle in self.constitution:
            if self.violates_principle(response, principle):
                # 3. 修正响应
                response = self.revise_response(response, principle)
        
        return response
    
    def violates_principle(self, response: str, principle: str) -> bool:
        """检查是否违反原则"""
        check_prompt = f"""
        原则：{principle}
        响应：{response}
        
        此响应是否违反了上述原则？回答"是"或"否"。
        """
        result = self.llm.predict(check_prompt)
        return "是" in result
    
    def revise_response(self, response: str, principle: str) -> str:
        """修正违反原则的响应"""
        revision_prompt = f"""
        原始响应：{response}
        违反的原则：{principle}
        
        请修改响应使其符合原则，同时保持有用性。
        """
        return self.llm.predict(revision_prompt)

# 定义宪法
constitution = [
    "不得提供有害或危险的建议",
    "必须尊重用户隐私",
    "不得生成误导性信息",
    "保持中立，不偏袒任何立场"
]

agent = ConstitutionalAgent(llm, constitution)
```

### 输出验证

```python
class ValidatedAgent:
    """带输出验证的Agent"""
    
    def __init__(self, llm, validators: List):
        self.llm = llm
        self.validators = validators
    
    def run_with_validation(self, task: str, max_retries: int = 3) -> str:
        """执行任务并验证输出"""
        
        for attempt in range(max_retries):
            # 生成输出
            output = self.llm.predict(task)
            
            # 验证
            validation_results = []
            for validator in self.validators:
                is_valid, feedback = validator.validate(output)
                validation_results.append((is_valid, feedback))
            
            # 如果全部通过，返回
            if all(result[0] for result in validation_results):
                return output
            
            # 否则，提供反馈让LLM改进
            feedback_text = "\n".join([
                f"- {fb}" for valid, fb in validation_results if not valid
            ])
            
            task = f"""
            原始任务：{task}
            上次输出：{output}
            
            问题：
            {feedback_text}
            
            请修正上述问题并重新生成。
            """
        
        raise Exception("验证失败次数过多")

# 定义验证器
class FactValidator:
    def validate(self, text: str) -> Tuple[bool, str]:
        # 检查事实准确性
        pass

class FormatValidator:
    def validate(self, text: str) -> Tuple[bool, str]:
        # 检查格式规范
        pass

agent = ValidatedAgent(llm, [FactValidator(), FormatValidator()])
```

---

## 8. 提示工程优化 (Prompt Engineering)

### 思维链 (Chain-of-Thought)

```python
def chain_of_thought_agent(llm, task: str) -> str:
    """使用思维链提升推理能力"""
    
    cot_prompt = f"""
    {task}
    
    请一步一步思考并解决这个问题。
    在每一步说明你的思考过程。
    
    格式：
    步骤1: [思考过程]
    步骤2: [思考过程]
    ...
    最终答案: [答案]
    """
    
    return llm.predict(cot_prompt)
```

### 思维树 (Tree-of-Thoughts)

```python
class TreeOfThoughtsAgent:
    """探索多个思考路径"""
    
    def __init__(self, llm):
        self.llm = llm
    
    def solve(self, problem: str, branches: int = 3, depth: int = 3) -> str:
        """通过树状搜索找到最佳解决方案"""
        
        # 1. 生成多个初始想法
        initial_thoughts = []
        for i in range(branches):
            thought = self.llm.predict(
                f"{problem}\n\n提供第{i+1}个解决思路："
            )
            initial_thoughts.append(thought)
        
        # 2. 评估每个想法
        best_path = self.explore_tree(
            problem, initial_thoughts, depth
        )
        
        # 3. 基于最佳路径生成最终答案
        final_answer = self.llm.predict(f"""
        问题：{problem}
        最佳思考路径：{best_path}
        
        基于以上路径，给出最终答案。
        """)
        
        return final_answer
    
    def explore_tree(self, problem: str, thoughts: List[str], 
                     remaining_depth: int) -> List[str]:
        """递归探索思维树"""
        
        if remaining_depth == 0:
            # 评估叶节点
            scores = [self.evaluate_thought(problem, t) for t in thoughts]
            best_idx = scores.index(max(scores))
            return [thoughts[best_idx]]
        
        # 对每个想法继续展开
        best_score = -float('inf')
        best_path = None
        
        for thought in thoughts:
            # 生成下一层想法
            next_thoughts = self.generate_next_thoughts(problem, thought)
            
            # 递归探索
            path = self.explore_tree(problem, next_thoughts, remaining_depth - 1)
            
            # 评估整条路径
            path_score = self.evaluate_path(problem, [thought] + path)
            
            if path_score > best_score:
                best_score = path_score
                best_path = [thought] + path
        
        return best_path
```

---

## 9. 混合架构

### RAG + Reflection

```python
class RAGReflectiveAgent:
    """结合RAG和反思的Agent"""
    
    def __init__(self, llm, retriever):
        self.llm = llm
        self.retriever = retriever
    
    def answer_with_reflection(self, question: str) -> str:
        # 1. 检索
        docs = self.retriever.get_relevant_documents(question)
        context = "\n".join([doc.page_content for doc in docs])
        
        # 2. 初始回答
        answer = self.llm.predict(f"""
        基于以下信息回答问题：
        {context}
        
        问题：{question}
        """)
        
        # 3. 反思检查
        reflection = self.llm.predict(f"""
        问题：{question}
        参考资料：{context}
        生成的答案：{answer}
        
        请检查答案是否：
        1. 完全基于提供的资料
        2. 准确回答了问题
        3. 没有添加资料中不存在的信息
        
        如有问题，请指出并提供改进建议。
        """)
        
        # 4. 如果有问题，改进答案
        if "问题" in reflection or "改进" in reflection:
            answer = self.llm.predict(f"""
            原答案：{answer}
            反思意见：{reflection}
            参考资料：{context}
            
            请根据反思意见改进答案。
            """)
        
        return answer
```

### Multi-Agent + Planning

```python
class PlanningMultiAgentSystem:
    """具有规划能力的多智能体系统"""
    
    def __init__(self, coordinator_llm):
        self.coordinator = coordinator_llm
        self.specialist_agents = {}
    
    def execute_complex_task(self, task: str) -> str:
        # 1. 制定总体计划
        plan = self.coordinator.predict(f"""
        任务：{task}
        可用专家：{list(self.specialist_agents.keys())}
        
        请制定执行计划，指定哪个专家负责哪个子任务。
        """)
        
        # 2. 分配并执行
        results = {}
        for step in parse_plan(plan):
            agent_name = step["agent"]
            subtask = step["task"]
            
            agent = self.specialist_agents[agent_name]
            results[step["id"]] = agent.run(subtask)
        
        # 3. 整合结果
        final_result = self.coordinator.predict(f"""
        任务：{task}
        各部分结果：{results}
        
        请整合所有结果，生成最终输出。
        """)
        
        return final_result
```

---

## 10. 性能优化

### 缓存机制

```python
from functools import lru_cache
import hashlib

class CachedAgent:
    """带缓存的Agent，避免重复计算"""
    
    def __init__(self, llm):
        self.llm = llm
        self.cache = {}
    
    def run(self, task: str) -> str:
        # 计算任务哈希
        task_hash = hashlib.md5(task.encode()).hexdigest()
        
        # 检查缓存
        if task_hash in self.cache:
            print("从缓存返回")
            return self.cache[task_hash]
        
        # 执行并缓存
        result = self.llm.predict(task)
        self.cache[task_hash] = result
        
        return result
```

### 异步执行

```python
import asyncio
from typing import List

class AsyncAgent:
    """支持异步执行的Agent"""
    
    def __init__(self, llm):
        self.llm = llm
    
    async def run_async(self, task: str) -> str:
        """异步执行单个任务"""
        return await self.llm.apredict(task)
    
    async def run_batch(self, tasks: List[str]) -> List[str]:
        """并行执行多个任务"""
        results = await asyncio.gather(*[
            self.run_async(task) for task in tasks
        ])
        return results

# 使用
agent = AsyncAgent(llm)
results = asyncio.run(agent.run_batch([
    "总结这篇文章...",
    "翻译这段文字...",
    "分析这组数据..."
]))
```

---

## 总结对比

| 优化方法 | 主要优势 | 适用场景 | 实现难度 |
|---------|---------|---------|---------|
| RAG | 知识增强、时效性 | 需要专业知识的任务 | 中 |
| Memory | 上下文连贯性 | 多轮对话、个性化 | 低 |
| Reflection | 输出质量提升 | 需要高质量输出 | 中 |
| Planning | 复杂任务分解 | 多步骤任务 | 中 |
| Multi-Agent | 专业分工协作 | 复杂综合任务 | 高 |
| Self-Improvement | 持续优化 | 长期运行系统 | 高 |
| Constitutional AI | 安全性保障 | 面向用户的应用 | 中 |
| Chain-of-Thought | 推理能力 | 逻辑推理任务 | 低 |

这些方法可以**组合使用**，构建更强大的 Agent 系统。选择哪些方法取决于具体应用场景和需求。