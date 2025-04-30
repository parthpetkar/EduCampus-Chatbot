from flask import Blueprint, jsonify, request   
import os
from api.retrieval import retriever  # Assuming retriever is already set up for the chatbot collection
from api.common import format_docs, run_chain, get_prompt_template
from qdrant_client import QdrantClient   
from langchain_qdrant import QdrantVectorStore   
from qdrant_client.http.models import Distance, VectorParams   
from langchain_community.embeddings import FastEmbedEmbeddings   
from langchain_community.document_loaders import PyPDFLoader   
from config import config
from uuid import uuid4
from langchain.docstore.document import Document    # Add this import

# Blueprint for the chat routes
chat_blueprint = Blueprint('chat_with_pdf', __name__)

@chat_blueprint.route('/generate', methods=['POST'])
def generate():
    """
    Endpoint to process a PDF file and query, then generate a response.
    """
    try:
        # Ensure the request is JSON
        if not request.is_json:
            return jsonify({"error": "Request must be JSON"}), 415

        data = request.get_json()
        file_path = data.get("file")
        query = data.get("query")
        print(file_path)

        # Validate inputs
        if not query:
            return jsonify({"error": "No query provided"}), 400

        if file_path and not os.path.exists(file_path):
            return jsonify({"error": "File not found or path invalid"}), 400

        # Initialize Qdrant client
        client = QdrantClient(url=config.QDRANT_URL, api_key=config.QDRANT_API_KEY, timeout=120)
        embeddings = FastEmbedEmbeddings()

        # Ensure the temporary collection exists
        create_collection_if_not_exists(client)

        # If a new file is uploaded, process and ingest its content
        if file_path:
            processed_data = process_file_data(file_path)
            vector_store = QdrantVectorStore(
                client=client,
                collection_name=config.TEMP_COLLECTION_NAME,
                embedding=embeddings
            )
            vector_store.add_documents(processed_data)
            print(f"File {file_path} processed and data added to the collection.")

        # Step 1: Query the PDF collection
        vector_store = QdrantVectorStore(
            client=client,
            collection_name=config.TEMP_COLLECTION_NAME,
            embedding=embeddings
        )
        collection_retriever = vector_store.as_retriever(
            search_type="similarity_score_threshold",
            search_kwargs={"k": 3, "score_threshold": 0.5}
        )
        pdf_results = collection_retriever.get_relevant_documents(query)
        pdf_context = format_docs(pdf_results)
        print(pdf_context)

        # Step 3: Use the refined query to fetch information from the chatbot collection
        chatbot_results = retriever.get_relevant_documents(query)
        chatbot_context = format_docs(chatbot_results)

        # Step 4: Combine all contexts and generate the final response
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
        final_prompt_template = get_prompt_template("chat_with_pdf")
        final_answer = run_chain(final_prompt_template, final_inputs)

        # Return the response
        return jsonify({"response": final_answer}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

def create_collection_if_not_exists(client):
    """
    Creates the collection in Qdrant if it does not exist, or ensures its correct configuration.
    """
    try:
        collections = client.get_collections().collections
        if config.TEMP_COLLECTION_NAME not in [col.name for col in collections]:
            client.create_collection(
                collection_name=config.TEMP_COLLECTION_NAME,
                vectors_config=VectorParams(size=384, distance=Distance.COSINE)
            )
            print(f"Collection {config.TEMP_COLLECTION_NAME} created successfully.")
        else:
            print(f"Collection {config.TEMP_COLLECTION_NAME} already exists.")
    except Exception as e:
        print(f"Failed to create collection: {e}")

def process_file_data(file_path):
    """
    Process the uploaded PDF file and convert its content to documents for vectorization.

    Args:
        file_path (str): Path to the uploaded file.

    Returns:
        List[Document]: A list of Document objects with fields like `page_content` and `metadata`.
    """
    documents = []
    try:
        # Read the PDF file
        docs = PyPDFLoader(file_path=file_path).load()
        for i, doc in enumerate(docs):
            if doc.page_content:  # Add only non-empty pages
                documents.append(Document(
                    page_content=doc.page_content.strip(),
                    metadata={"source": file_path, "page": i + 1}
                ))
    except Exception as e:
        raise ValueError(f"Error processing file: {e}")

    return documents

