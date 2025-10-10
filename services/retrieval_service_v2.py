import os
import sys
from typing import List, Dict, Any
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import Chroma
from langchain.prompts import ChatPromptTemplate
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter

# Fix SQLite for ChromaDB compatibility
try:
    __import__('pysqlite3')
    sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
except ImportError:
    pass

from config.settings import settings


class RetrievalServiceV2:
    """Enhanced retrieval service with dynamic knowledge management."""

    def __init__(self):
        self.embeddings = OpenAIEmbeddings(model=settings.embedding_model)
        self.llm = ChatOpenAI(model=settings.chat_model, temperature=settings.temperature)
        self.chroma_path = settings.chroma_path
        self.vector_db = None
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.dense_chunk_size,
            chunk_overlap=settings.dense_chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        self.prompt_template = """You are a helpful AI assistant. Answer the user's question using only the provided context.
If the answer is not in the context, politely say you don't have that information.

Context:
{context}

Question: {question}

Answer:"""
        self.prompt = ChatPromptTemplate.from_template(self.prompt_template)

    def initialize_database(self) -> bool:
        """Initialize or load the vector database."""
        try:
            self.vector_db = Chroma(
                persist_directory=self.chroma_path,
                embedding_function=self.embeddings
            )
            print(f"Loaded/Created Chroma DB at {self.chroma_path}")
            return True
        except Exception as e:
            print(f"Error initializing database: {e}")
            return False

    async def add_documents_to_index(self, text: str, source: str, tenant_id: str) -> bool:
        """Add documents to the vector index."""
        try:
            if not self.vector_db:
                self.initialize_database()

            # Convert UUID to string for metadata
            tenant_id_str = str(tenant_id)

            document = Document(
                page_content=text,
                metadata={
                    "source": source,
                    "tenant_id": tenant_id_str
                }
            )

            chunks = self.text_splitter.split_documents([document])
            if chunks:
                self.vector_db.add_documents(chunks)
                self.vector_db.persist()
                print(f"Added {len(chunks)} chunks for tenant {tenant_id_str} from {source}")
                return True

            return False
        except Exception as e:
            print(f"Error adding documents to index: {e}")
            return False

    def clear_tenant_documents(self, tenant_id: str) -> bool:
        """Clear all documents for a specific tenant."""
        try:
            if not self.vector_db:
                return False

            tenant_id_str = str(tenant_id)
            results = self.vector_db.get(where={"tenant_id": tenant_id_str})

            if results and results['ids']:
                self.vector_db.delete(ids=results['ids'])
                self.vector_db.persist()
                print(f"Cleared {len(results['ids'])} documents for tenant {tenant_id_str}")

            return True
        except Exception as e:
            print(f"Error clearing tenant documents: {e}")
            return False

    def answer_question(self, question: str, tenant_id: str) -> Dict[str, Any]:
        """Generate answer for a question using tenant-filtered retrieval."""
        if not self.vector_db:
            self.initialize_database()

        if not self.vector_db:
            return {
                "answer": "Error: Knowledge base not available. Please add some content first.",
                "sources": [],
                "tenant_id": str(tenant_id)
            }

        try:
            tenant_id_str = str(tenant_id)
            tenant_filter = {"tenant_id": tenant_id_str}

            retriever = self.vector_db.as_retriever(
                search_kwargs={
                    "k": settings.retrieval_k,
                    "filter": tenant_filter
                }
            )

            docs = retriever.get_relevant_documents(question)
            if not docs:
                return {
                    "answer": "I don't have any information to answer that question. Please add relevant content to the knowledge base.",
                    "sources": [],
                    "tenant_id": tenant_id_str
                }

            context_text = "\n\n".join([doc.page_content for doc in docs])
            sources = [doc.metadata.get("source", "Unknown") for doc in docs]

            final_prompt = self.prompt.format(context=context_text, question=question)
            response = self.llm.invoke(final_prompt)

            return {
                "answer": response.content.strip(),
                "sources": list(set(sources)),
                "tenant_id": tenant_id_str
            }
        except Exception as e:
            print(f"Error answering question: {e}")
            return {
                "answer": f"Error processing question: {str(e)}",
                "sources": [],
                "tenant_id": str(tenant_id)
            }

    def get_tenant_document_count(self, tenant_id: str) -> int:
        """Get the number of documents for a tenant."""
        try:
            if not self.vector_db:
                return 0

            tenant_id_str = str(tenant_id)
            results = self.vector_db.get(where={"tenant_id": tenant_id_str})
            return len(results['ids']) if results and results['ids'] else 0
        except Exception as e:
            print(f"Error getting document count: {e}")
            return 0


# Singleton instance
retrieval_service = RetrievalServiceV2()
