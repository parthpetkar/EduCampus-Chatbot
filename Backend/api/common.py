from langchain_groq import ChatGroq  
from langchain.prompts import PromptTemplate 
from langchain.schema.output_parser import StrOutputParser 
from langchain.schema.runnable import RunnablePassthrough  
from config import config

# Initialize Groq model with API key
groq_chat = ChatGroq(groq_api_key=config.GROQ_API_KEY, model_name=config.MODEL_NAME)

class QdrantService:
    def __init__(self, url, api_key, collection_name):
        from qdrant_client import QdrantClient
        from langchain_qdrant import QdrantVectorStore
        from langchain_community.embeddings import FastEmbedEmbeddings
        self.client = QdrantClient(url=url, api_key=api_key)
        self.embeddings = FastEmbedEmbeddings()
        self.collection_name = collection_name
        self.vector_store = QdrantVectorStore(client=self.client, collection_name=collection_name, embedding=self.embeddings)

    def create_collection_if_not_exists(self, size=384, distance=None):
        from qdrant_client.http.models import Distance, VectorParams
        if distance is None:
            distance = Distance.COSINE
        collections = self.client.get_collections().collections
        if self.collection_name not in [col.name for col in collections]:
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=size, distance=distance)
            )
            print(f"Collection {self.collection_name} created successfully.")
        else:
            print(f"Collection {self.collection_name} already exists.")

    def delete_old_chunks(self, pdf_file_name):
        try:
            self.client.delete(
                collection_name=self.collection_name,
                filter={
                    "must": [
                        {"key": "pdf_file_name", "match": {"value": pdf_file_name}}
                    ]
                }
            )
            print(f"Deleted old chunks for {pdf_file_name}")
        except Exception as e:
            print(f"Failed to delete old chunks for {pdf_file_name}: {e}")

    def get_retriever(self, k=5, score_threshold=0.4):
        return self.vector_store.as_retriever(search_type="similarity_score_threshold", search_kwargs={"k": k, "score_threshold": score_threshold})

    def add_documents(self, documents):
        self.vector_store.add_documents(documents)

class DocumentProcessor:
    @staticmethod
    def process_file_data(file_path):
        from langchain_community.document_loaders import PyPDFLoader
        from langchain.docstore.document import Document
        documents = []
        try:
            docs = PyPDFLoader(file_path=file_path).load()
            for i, doc in enumerate(docs):
                if doc.page_content:
                    documents.append(Document(
                        page_content=doc.page_content.strip(),
                        metadata={"source": file_path, "page": i + 1}
                    ))
        except Exception as e:
            raise ValueError(f"Error processing file: {e}")
        return documents

    @staticmethod
    def get_pdf_last_modified_time(pdf_file_path):
        import os
        return os.path.getmtime(pdf_file_path)

class PromptService:
    @staticmethod
    def format_docs(docs):
        return "\n\n".join(doc.page_content for doc in docs)

    @staticmethod
    def run_chain(prompt_template, inputs):
        from langchain.schema.runnable import RunnablePassthrough
        from langchain.schema.output_parser import StrOutputParser
        chain = RunnablePassthrough() | prompt_template | groq_chat | StrOutputParser()
        return chain.invoke(inputs)

    @staticmethod
    def get_prompt_template(use_case):
        from langchain.prompts import PromptTemplate
        if use_case == "generation":
            return PromptTemplate(
                input_variables=["context", "question"],
                template="""
                <s> [INST] You are an expert assistant providing detailed information specifically about Vishwakarma Institute of Technology (VIT), Pune. 
                Please ensure that your response follows these rules:
                Rules:
                1. Only provide information about Vishwakarma Institute of Technology(VIT), Pune.
                2. Always answer in polite and professional manner.
                3. Answer the user query in structured format and make sure the answer is clear, concise and easy to read.

                Guidelines:
                2. Always base your responses on the provided documents. If the documents lack relevant information, politely inform the user that the information is not available and do not specify the internal working of the application.
                3. Identify what the user whats to do and always provide a link in the response based on the query.
                4. When a user provides their MHT-CET percentile, compare it with the cutoff percentiles for MHTCET for various branches and inform them whether they are eligible for admission.
                5. If the user requests steps, guidance for a precedure such as admission then respond in point wise manner.

                Response format:
                Details: [Provide a friendly and helpful response based on the context.]

                [/INST] </s>
                [INST] 
                Question: {question}
                Context: {context}
                Answer: [/INST]
                """
            )
        
        if use_case == "chat_with_pdf":
            return PromptTemplate(
                input_variables=["context", "question", "query"],
                template="""
                <s> [INST] You are an expert assistant specialized in providing detailed and accurate information about Vishwakarma Institute of Technology (VIT), Pune. Users may upload their marks documents containing Merit Rank and CET Percentile Scores. You will assist them with queries related to admissions based on their scores. Please adhere to the following guidelines:

                Guidelines:
                1. Scope: Provide information exclusively related to Vishwakarma Institute of Technology (VIT), Pune, focusing on admissions criteria, cutoff scores, branch allocations, percentiles, ranks, and related queries based on the user's uploaded marks.
                2. Source of Information: Base your responses solely on the provided documents, which include the user's Merit Rank and CET Percentile Scores, as well as VIT's admission details. If the necessary information is not available within the documents, politely inform the user that the information is unavailable without disclosing any internal processes.
                3. Length: Keep your response concise, not exceeding 80 words.
                4. User Intent & Links: Understand the user's intent (e.g., seeking branch allocation based on marks) and include relevant links or resources from the provided documents in your response based on the query.
                5. Data Interpretation: Accurately interpret the user's Merit Rank and Percentile Scores from the uploaded documents to provide precise and relevant information.
                6. Branch Suggestion: Use the Percentile Scores to suggest possible branches the user is eligible for, referencing the latest cutoff percentiles for each branch.
                7. If user doesnt specify the examination for cutoffs, provide the cutoffs for both MHTCET and JEE.

                Response Format:
                Details: [Provide a clear, friendly, and helpful response based on the context.]

                Original User Question: {question}
                Query: {query}
                Context: {context}

                Answer: [/INST]
            """
        )

class AudioService:
    @staticmethod
    def convert_audio_to_text(file_path):
        from groq import Groq
        import os
        if not file_path or not os.path.exists(file_path):
            raise FileNotFoundError("File not found.")
        client = Groq()
        with open(file_path, "rb") as file:
            transcription = client.audio.transcriptions.create(
                file=(file_path, file.read()),
                model="whisper-large-v3",
                response_format="verbose_json",
            )
        return transcription.get("text", "")
