from typing import List, Dict, Any
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from config.settings import settings

class DocumentProcessor:
    """Handles document processing, chunking, and embedding generation."""

    def __init__(self):
        self.embeddings = OpenAIEmbeddings(model=settings.embedding_model)
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=800,
            chunk_overlap=100,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""]
        )

    def process_text(self, text: str, source: str, tenant_id: str) -> List[Document]:
        """
        Process text content into document chunks.

        Args:
            text: Raw text content
            source: Source identifier (URL, filename, etc.)
            tenant_id: Tenant identifier

        Returns:
            List of Document objects with metadata
        """
        documents = [Document(
            page_content=text,
            metadata={
                "source": source,
                "tenant_id": tenant_id
            }
        )]

        chunks = self.text_splitter.split_documents(documents)
        return chunks

    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a list of texts.

        Args:
            texts: List of text strings

        Returns:
            List of embedding vectors
        """
        try:
            embeddings = await self.embeddings.aembed_documents(texts)
            return embeddings
        except Exception as e:
            print(f"Error generating embeddings: {e}")
            return []

    def extract_file_content(self, file_content: bytes, file_name: str) -> str:
        """
        Extract text content from file bytes.

        Args:
            file_content: File content in bytes
            file_name: Name of the file

        Returns:
            Extracted text content
        """
        try:
            if file_name.endswith('.txt'):
                return file_content.decode('utf-8')
            elif file_name.endswith('.md'):
                return file_content.decode('utf-8')
            else:
                return file_content.decode('utf-8', errors='ignore')
        except Exception as e:
            print(f"Error extracting file content: {e}")
            return ""

document_processor = DocumentProcessor()
