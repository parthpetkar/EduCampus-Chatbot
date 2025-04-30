from flask import Blueprint, jsonify, request  
from api.common import QdrantService, PromptService
from config import config

retrieval_blueprint = Blueprint('retrieval', __name__)

qdrant_service = QdrantService(url=config.QDRANT_URL, api_key=config.QDRANT_API_KEY, collection_name=config.COLLECTION_NAME)
retriever = qdrant_service.get_retriever(k=5, score_threshold=0.4)

@retrieval_blueprint.route('/retrieve', methods=['POST'])
def retrieve():
    """
    Endpoint to retrieve relevant documents from Qdrant based on a query.
    """
    data = request.get_json()
    query = data.get("query", "What is the purpose of this document?")
    results = retriever.get_relevant_documents(query)
    
    serialized_results = [{"page_content": doc.page_content, "metadata": doc.metadata} for doc in results]
    
    return jsonify({"query": query, "results": serialized_results})

