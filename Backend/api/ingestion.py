from qdrant_client import QdrantClient  
from qdrant_client.http.models import Distance, VectorParams  
from langchain_qdrant import QdrantVectorStore  
from langchain_community.document_loaders import PyPDFLoader  
from langchain.text_splitter import RecursiveCharacterTextSplitter  
from langchain_community.embeddings import FastEmbedEmbeddings  
import os
from config import config
from concurrent.futures import ThreadPoolExecutor
import time
from functools import wraps
from api.common import QdrantService, DocumentProcessor
from api.common import PromptService

def create_collection_if_not_exists(client):
    # Deprecated: Use QdrantService.create_collection_if_not_exists instead
    pass

def retry(exceptions, tries=3, delay=2, backoff=2):
    """
    Retry decorator to handle exceptions and retry the operation.
    """
    def deco_retry(f):
        @wraps(f)
        def f_retry(*args, **kwargs):
            mtries, mdelay = tries, delay
            while mtries > 0:
                try:
                    return f(*args, **kwargs)
                except exceptions as e:
                    print(f"Retrying due to {e}. Attempts left: {mtries - 1}")
                    mtries -= 1
                    time.sleep(mdelay)
                    mdelay *= backoff
            raise Exception("Maximum retries reached")
        return f_retry
    return deco_retry

def get_pdf_last_modified_time(pdf_file_path):
    return DocumentProcessor.get_pdf_last_modified_time(pdf_file_path)

def delete_old_chunks(client, pdf_file_name):
    # Deprecated: Use QdrantService.delete_old_chunks instead
    pass

@retry((Exception,), tries=10, delay=5, backoff=2)
def process_pdf(pdf_file, client, embeddings, text_splitter):
    # Deprecated: Refactor to use QdrantService and DocumentProcessor
    pass

def ingest():
    """
    Ingests all PDF files from the 'data' folder into the Qdrant collection.
    """
    data_folder = "data"
    if not os.path.exists(data_folder):
        raise FileNotFoundError(f"Folder {data_folder} does not exist.")

    qdrant_service = QdrantService(url=config.QDRANT_URL, api_key=config.QDRANT_API_KEY, collection_name=config.COLLECTION_NAME)
    qdrant_service.create_collection_if_not_exists()

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    embeddings = qdrant_service.embeddings

    pdf_files = [f for f in os.listdir(data_folder) if f.endswith(".pdf")]
    batch_size = 3  # Adjust this according to your server's capacity

    for i in range(0, len(pdf_files), batch_size):
        batch = pdf_files[i:i + batch_size]
        for pdf_file in batch:
            file_path = os.path.join(data_folder, pdf_file)
            documents = DocumentProcessor.process_file_data(file_path)
            qdrant_service.add_documents(documents)
            print(f"Document {pdf_file} ingested successfully.")
