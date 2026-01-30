import json
import os
import networkx as nx

class GraphStore:
    def __init__(self, storage_path="knowledge_graph.json"):
        # Put the json in the rag folder by default
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.storage_path = os.path.join(base_dir, storage_path)
        self.graph = nx.MultiDiGraph()
        self.load()

    def add_triplet(self, source, relation, target):
        self.graph.add_edge(source, target, relation=relation)

    def save(self):
        data = nx.node_link_data(self.graph)
        with open(self.storage_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def load(self):
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.graph = nx.node_link_graph(data)
            except Exception as e:
                print(f"Failed to load graph: {e}. Starting new.")
                self.graph = nx.MultiDiGraph()

    def search(self, query):
        """Search for nodes that contain the query string (case-insensitive)"""
        results = []
        if not query:
            return results
        for node in self.graph.nodes():
            if str(query).lower() in str(node).lower():
                results.append(node)
        return results
