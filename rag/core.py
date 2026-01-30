from .graph_store import GraphStore
from .builder import GraphBuilder
from .llm import chat_completion
import os

store = GraphStore()
builder = GraphBuilder(store)

def query_graph_rag(query):
    """
    Query the Knowledge Graph for answers.
    1. Identify keywords in user query.
    2. Search graph for matching nodes.
    3. Retrieve 1-hop subgraphs.
    4. Generate answer.
    """
    print(f"RAG Query: {query}")
    
    # 1. & 2. Node lookup
    # Simple strategy: Use the whole query as searching text, or ask LLM to extract keywords
    keywords_prompt = f"Extract 1 to 3 main technical keywords from this query, separated by commas: {query}"
    keywords_resp = chat_completion([{"role": "user", "content": keywords_prompt}])
    keywords = [k.strip() for k in keywords_resp.split(",")]
    
    related_nodes = set()
    for k in keywords:
        found = store.search(k)
        related_nodes.update(found)
    
    # Also try direct search query tokens
    for token in query.split():
        if len(token) > 3: # Ignore short words
            related_nodes.update(store.search(token))

    if not related_nodes:
        return "Knowledge Graph: No related entities found to answer this question."

    # 3. Retrieve Context
    context_lines = []
    seen_edges = set()
    
    # Limit nodes to check
    for node in list(related_nodes)[:10]:
        if node in store.graph:
            # Outgoing edges
            for nbr, edict in store.graph[node].items():
                for k, attrs in edict.items():
                    rel = attrs.get('relation', 'related')
                    edge = f"{node} --[{rel}]--> {nbr}"
                    if edge not in seen_edges:
                        context_lines.append(edge)
                        seen_edges.add(edge)
            
            # Incoming edges (networkx predecessor check)
            # Depending on graph size this might be expensive, skipping for now or use undirected view
            
    context_str = "\n".join(context_lines[:30]) # Limit context size
    
    if not context_str:
        return "Knowledge Graph: Found entities but no relationships recorded."

    # 4. Generate Answer
    system_prompt = "You are a helpful assistant augmented with a Knowledge Graph. Use the provided Context to answer the user's question."
    user_prompt = f"""
    Context (Graph Triplets):
    {context_str}
    
    Question: {query}
    
    Please answer based on the context above. If the context doesn't contain the answer, say so, but try to infer from the relationships.
    """
    
    answer = chat_completion([
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ])
    
    return answer

def build_knowledge_base():
    # Helper to scan Q&A
    import os
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    qa_dir = os.path.join(base_dir, "Q&A")
    print(f"Building Knowledge Base from {qa_dir}...")
    builder.build_from_directory(qa_dir)
    print("Knowledge Graph built.")

if __name__ == "__main__":
    # Test run
    # build_knowledge_base()
    pass
