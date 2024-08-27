from flask import Flask, request, jsonify
from neo4j import GraphDatabase
from llama_index import VectorStoreIndex, SimpleDirectoryReader
from llama_index.vector_stores import Neo4jVectorStore
from llama_index.storage.storage_context import StorageContext
from llama_index.embeddings import HuggingFaceEmbedding
from vllm import LLM, SamplingParams
import json
import os

app = Flask(__name__)

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://neo4j-service:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")
VLLM_MODEL = os.getenv("VLLM_MODEL", "your_vllm_model_name")

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
vllm_model = LLM(model=VLLM_MODEL)

def setup_llamaindex_with_neo4j():
    embed_model = HuggingFaceEmbedding(model_name="sentence-transformers/all-MiniLM-L6-v2")
    vector_store = Neo4jVectorStore(driver, index_name="item_index", embed_dim=384)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)
    return VectorStoreIndex.from_vector_store(vector_store, storage_context=storage_context)

index = setup_llamaindex_with_neo4j()

@app.route('/ingest', methods=['POST'])
def ingest():
    if 'files' not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    files = request.files.getlist('files')
    data = []
    for file in files:
        content = json.loads(file.read().decode('utf-8'))
        data.extend(content)
    
    with driver.session() as session:
        for item in data:
            session.run("""
                MERGE (n:Item {id: $id})
                SET n += $properties
            """, id=item.get('id'), properties=item)
    
    return jsonify({"message": "Files ingested successfully"}), 200

@app.route('/query', methods=['POST'])
def query():
    query_text = request.json.get('query')
    if not query_text:
        return jsonify({"error": "No query provided"}), 400
    
    query_engine = index.as_query_engine()
    response = query_engine.query(query_text)
    
    sampling_params = SamplingParams(temperature=0.7, top_p=0.95)
    vllm_output = vllm_model.generate([str(response)], sampling_params)
    
    return jsonify({"result": vllm_output[0].outputs[0].text}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)