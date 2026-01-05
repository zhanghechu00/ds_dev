# RAG (Retrieval-Augmented Generation) 详解

RAG 是**检索增强生成**技术，是一种结合了信息检索和生成式AI的混合架构。

## 核心概念

RAG 通过以下方式增强大语言模型（LLM）的能力：

```
用户问题 → 检索相关文档 → 将文档作为上下文 → LLM生成答案
```

## 工作流程

```python
# RAG 的基本工作流程示意
def rag_pipeline(user_query):
    # 1. 检索阶段 (Retrieval)
    relevant_docs = retrieve_documents(user_query)
    
    # 2. 增强阶段 (Augmentation)
    context = build_context(relevant_docs)
    
    # 3. 生成阶段 (Generation)
    prompt = f"基于以下信息回答问题：\n{context}\n\n问题：{user_query}"
    answer = llm.generate(prompt)
    
    return answer
```

## 主要优势

### 1. **解决知识时效性问题**
- LLM的训练数据有截止日期
- RAG可以检索最新的外部信息

### 2. **减少幻觉（Hallucination）**
- 基于实际文档生成答案
- 提供可追溯的信息来源

### 3. **领域专业化**
- 无需重新训练模型
- 通过检索特定领域知识库即可

### 4. **成本效益**
- 比微调大模型成本更低
- 易于更新和维护知识库

## 典型架构

```python
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from langchain.llms import OpenAI
from langchain.chains import RetrievalQA

# 1. 构建向量数据库
embeddings = OpenAIEmbeddings()
vector_store = FAISS.from_documents(documents, embeddings)

# 2. 创建检索器
retriever = vector_store.as_retriever(
    search_type="similarity",
    search_kwargs={"k": 3}  # 检索top-3相关文档
)

# 3. 构建RAG链
qa_chain = RetrievalQA.from_chain_type(
    llm=OpenAI(),
    retriever=retriever,
    return_source_documents=True
)

# 4. 使用
result = qa_chain({"query": "用户的问题"})
print(result['result'])  # 答案
print(result['source_documents'])  # 引用来源
```

## 关键技术组件

### 1. **文档处理**
- 文本分割（Chunking）
- 清洗和预处理

### 2. **向量化（Embedding）**
- 将文本转换为向量表示
- 常用模型：OpenAI Embeddings, Sentence-BERT等

### 3. **向量数据库**
- 存储和检索向量
- 常用工具：FAISS, Pinecone, Milvus, Weaviate

### 4. **检索策略**
- 语义相似度检索
- 混合检索（语义+关键词）
- 重排序（Re-ranking）

## 应用场景

1. **企业知识库问答**：客服机器人、内部文档查询
2. **法律/医疗咨询**：基于专业文献的辅助决策
3. **教育辅导**：基于教材内容的智能答疑
4. **研究助手**：文献检索和总结

## 局限性

- 依赖检索质量，检索不准确会影响答案
- 上下文窗口限制（能输入的文档量有限）
- 对实时性要求极高的场景可能不适用

RAG 是当前最实用的 LLM 应用模式之一，特别适合需要结合私有数据和通用AI能力的场景。