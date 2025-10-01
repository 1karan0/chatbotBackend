from typing import List, Dict, Any
import io
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from config.settings import settings

try:
    import nltk
    nltk.download('punkt', quiet=True)
    nltk.download('averaged_perceptron_tagger', quiet=True)
except Exception as e:
    print(f"Warning: NLTK download failed: {e}")

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
            if file_name.endswith('.txt') or file_name.endswith('.md'):
                return file_content.decode('utf-8')
            elif file_name.endswith('.pdf'):
                try:
                    from pypdf import PdfReader
                    pdf_file = io.BytesIO(file_content)
                    pdf_reader = PdfReader(pdf_file)
                    text = ""
                    for page in pdf_reader.pages:
                        text += page.extract_text() + "\n"
                    return text
                except Exception as e:
                    print(f"Error extracting PDF: {e}")
                    return file_content.decode('utf-8', errors='ignore')
            elif file_name.endswith('.docx'):
                try:
                    from docx import Document as DocxDocument
                    doc_file = io.BytesIO(file_content)
                    doc = DocxDocument(doc_file)
                    text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
                    return text
                except Exception as e:
                    print(f"Error extracting DOCX: {e}")
                    return file_content.decode('utf-8', errors='ignore')
            else:
                return file_content.decode('utf-8', errors='ignore')
        except Exception as e:
            print(f"Error extracting file content: {e}")
            return ""

document_processor = DocumentProcessor()
