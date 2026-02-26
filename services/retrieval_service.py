import os
import sys
import shutil
from typing import List, Dict, Any, Optional
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import Chroma
from langchain_community.retrievers import BM25Retriever
from langchain.retrievers import EnsembleRetriever
from langchain.prompts import ChatPromptTemplate
from langchain.schema import Document

# Fix SQLite for ChromaDB compatibility
try:
    __import__('pysqlite3')
    sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
except ImportError:
    pass

from config.settings import settings
from .data_loader import data_loader

class RetrievalService:
    """Handles document retrieval and answer generation."""
    
    def __init__(self):
        self.embeddings = OpenAIEmbeddings(model=settings.embedding_model)
        self.llm = ChatOpenAI(model=settings.chat_model, temperature=settings.temperature)
        self.chroma_path = settings.chroma_path
        self.vector_db = None
        self.sparse_retriever = None
        self.prompt_template = """You are a helpful assistant. Answer the user's question using only the provided context.
If the answer is not contained in the context, say you don't know the answer and refer to contact page.

# Context:
{context}

# Question:
{question}

# Answer:"""
        self.prompt = ChatPromptTemplate.from_template(self.prompt_template)
    
    def initialize_database(self, force_rebuild: bool = False) -> bool:
        """Initialize or reload the vector database."""
        try:
            # Clean existing database if force rebuild
            if force_rebuild and os.path.exists(self.chroma_path):
                shutil.rmtree(self.chroma_path)
                print(f"Removed existing Chroma DB at {self.chroma_path}")
            
            # Load and process documents
            tenant_mapping = {
                "london.txt": "tenant_a",
                "manchester.txt": "tenant_b", 
                "birmingham.txt": "tenant_c",
                "glasgow.txt": "tenant_d",
                "midlands.txt": "tenant_e",
                "all-services.txt": "tenant_all"
            }
            
            all_documents = data_loader.load_all_tenants_data(tenant_mapping)
            
            if not all_documents:
                print("No documents found. Cannot initialize database.")
                return False
            
            # Split documents
            dense_docs = data_loader.split_documents_dense(all_documents)
            sparse_docs = data_loader.split_documents_sparse(all_documents)
            
            print(f"Split into {len(dense_docs)} dense chunks and {len(sparse_docs)} sparse chunks.")
            
            # Create vector database
            if dense_docs:
                self.vector_db = Chroma.from_documents(
                    documents=dense_docs,
                    embedding=self.embeddings,
                    persist_directory=self.chroma_path
                )
                self.vector_db.persist()
                print(f"Created Chroma DB with {len(dense_docs)} documents")
            
            # Create sparse retriever
            if sparse_docs:
                self.sparse_retriever = BM25Retriever.from_documents(sparse_docs)
                self.sparse_retriever.k = settings.retrieval_k
                print("Created BM25 retriever")
            
            return True
            
        except Exception as e:
            print(f"Error initializing database: {e}")
            return False
    
    def load_existing_database(self) -> bool:
        """Load existing persisted database."""
        try:
            if not os.path.exists(self.chroma_path):
                print(f"Chroma database not found at {self.chroma_path}")
                return False
            
            self.vector_db = Chroma(
                persist_directory=self.chroma_path,
                embedding_function=self.embeddings
            )
            print(f"Loaded existing Chroma DB with {len(self.vector_db.get(include=[])['ids'])} documents")
            return True
            
        except Exception as e:
            print(f"Error loading existing database: {e}")
            return False
    
    def answer_question(self, question: str, tenant_id: str) -> Dict[str, Any]:
        """Generate answer for a question using tenant-filtered retrieval."""
        if not self.vector_db:
            return {
                "answer": "Error: Vector database not available.",
                "sources": [],
                "tenant_id": tenant_id
            }
        
        try:
            # Create tenant filter for Chroma
            chroma_filter = {
                "$or": [
                    {"tenant_id": tenant_id},
                    {"tenant_id": "tenant_all"}
                ]
            }
            
            # Create dense retriever with tenant filter
            dense_retriever = self.vector_db.as_retriever(
                search_kwargs={"k": settings.retrieval_k, "filter": chroma_filter}
            )
            
            # Create ensemble retriever
            retrievers = [dense_retriever]
            weights = [1.0]
            
            if self.sparse_retriever:
                retrievers.append(self.sparse_retriever)
                weights = [0.5, 0.5]
            
            ensemble_retriever = EnsembleRetriever(
                retrievers=retrievers,
                weights=weights
            )
            
            # Get relevant documents
            docs = ensemble_retriever.get_relevant_documents(question)
            
            # Post-retrieval filtering for tenant isolation
            filtered_docs = []
            for doc in docs:
                doc_tenant_id = doc.metadata.get("tenant_id")
                if doc_tenant_id == tenant_id or doc_tenant_id == "tenant_all":
                    filtered_docs.append(doc)
            
            if not filtered_docs:
                return {
                    "answer": "I don't have information relevant to your tenant for this question.",
                    "sources": [],
                    "tenant_id": tenant_id
                }
            
            # Prepare context and sources
            context_text = "\n\n".join(doc.page_content for doc in filtered_docs)
            sources = [
                f"{doc.metadata.get('source', 'Unknown')} (tenant: {doc.metadata.get('tenant_id', 'N/A')})"
                for doc in filtered_docs
            ]
            
            # Generate answer
            final_prompt = self.prompt.format(context=context_text, question=question)
            response = self.llm.invoke(final_prompt)
            
            return {
                "answer": response.content.strip(),
                "sources": sources,
                "tenant_id": tenant_id
            }
            
        except Exception as e:
            print(f"Error answering question: {e}")
            return {
                "answer": f"Error processing question: {str(e)}",
                "sources": [],
                "tenant_id": tenant_id
            }

# Global retrieval service instance
retrieval_service = RetrievalService()