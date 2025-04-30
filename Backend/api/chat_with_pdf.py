from flask import Blueprint, jsonify, request   
import os
from uuid import uuid4
from api.common import QdrantService, PromptService, DocumentProcessor
from api.retrieval import retriever
from config import config

# Blueprint for the chat routes
chat_blueprint = Blueprint('chat_with_pdf', __name__)

qdrant_service = QdrantService(url=config.QDRANT_URL, api_key=config.QDRANT_API_KEY, collection_name=config.TEMP_COLLECTION_NAME)

@chat_blueprint.route('/generate', methods=['POST'])
def generate():
    """
    Endpoint to process a PDF file and query, then generate a response.
    """
    try:
        if not request.is_json:
            return jsonify({"error": "Request must be JSON"}), 415

        data = request.get_json()
        file_path = data.get("file")
        query = data.get("query")
        print(file_path)

        if not query:
            return jsonify({"error": "No query provided"}), 400

        if file_path and not os.path.exists(file_path):
            return jsonify({"error": "File not found or path invalid"}), 400

        qdrant_service.create_collection_if_not_exists()

        if file_path:
            processed_data = DocumentProcessor.process_file_data(file_path)
            qdrant_service.add_documents(processed_data)
            print(f"File {file_path} processed and data added to the collection.")

        vector_store = qdrant_service.vector_store
        collection_retriever = vector_store.as_retriever(
            search_type="similarity_score_threshold",
            search_kwargs={"k": 3, "score_threshold": 0.5}
        )
        pdf_results = collection_retriever.get_relevant_documents(query)
        pdf_context = PromptService.format_docs(pdf_results)
        print(pdf_context)

        chatbot_results = retriever.get_relevant_documents(query)
        chatbot_context = PromptService.format_docs(chatbot_results)

        combined_context = f"""
            [PDF Collection Context]:
            {pdf_context}

            [Chatbot Collection Context]:
            {chatbot_context}
        """
        final_inputs = {
            "context": combined_context,
            "question": query,
            "query": query
        }
        final_prompt_template = PromptService.get_prompt_template("chat_with_pdf")
        final_answer = PromptService.run_chain(final_prompt_template, final_inputs)

        return jsonify({"response": final_answer}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

