import os
import shutil
from typing import List, Dict, Any
from langchain_community.document_loaders import DirectoryLoader
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter

from config.settings import settings

class DataLoader:
    """Handles loading and processing documents for tenants."""
    
    def __init__(self):
        self.data_path = settings.data_path
        self.dense_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.dense_chunk_size,
            chunk_overlap=settings.dense_chunk_overlap,
            length_function=len,
            separators=[". ", "\n\n", "\n\n\n", "\n\n\n\n", " ", ""]
        )
        self.sparse_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.sparse_chunk_size,
            chunk_overlap=settings.sparse_chunk_overlap,
            length_function=len,
            separators=[". ", "\n\n", "\n\n\n", "\n\n\n\n", " ", ""]
        )
    
    def load_tenant_data(self, tenant_id: str) -> List[Document]:
        """Load documents for a specific tenant."""
        tenant_data_path = os.path.join(self.data_path, tenant_id)
        
        if not os.path.exists(tenant_data_path):
            print(f"Tenant data directory not found: {tenant_data_path}")
            return []
        
        try:
            loader = DirectoryLoader(tenant_data_path, glob="*.txt")
            documents = loader.load()
            
            # Add tenant_id to metadata
            for doc in documents:
                doc.metadata["tenant_id"] = tenant_id
            
            print(f"Loaded {len(documents)} documents for tenant '{tenant_id}'")
            return documents
        except Exception as e:
            print(f"Error loading documents for tenant '{tenant_id}': {e}")
            return []
    
    def load_all_tenants_data(self, tenant_mapping: Dict[str, str]) -> List[Document]:
        """Load documents for all tenants based on mapping."""
        all_documents = []
        
        for file_name, tenant_id in tenant_mapping.items():
            tenant_data_path = os.path.join(self.data_path, tenant_id)
            file_path = os.path.join(tenant_data_path, file_name)
            
            if os.path.exists(tenant_data_path) and os.path.exists(file_path):
                try:
                    loader = DirectoryLoader(tenant_data_path, glob=file_name)
                    documents = loader.load()
                    
                    # Add tenant_id to metadata
                    for doc in documents:
                        doc.metadata["tenant_id"] = tenant_id
                    
                    all_documents.extend(documents)
                    print(f"Loaded {len(documents)} documents for tenant '{tenant_id}'")
                except Exception as e:
                    print(f"Error loading documents for tenant '{tenant_id}': {e}")
            else:
                print(f"Data path or file not found for tenant '{tenant_id}': {file_path}")
        
        return all_documents
    
    def split_documents_dense(self, documents: List[Document]) -> List[Document]:
        """Split documents into dense chunks for semantic retrieval."""
        return self.dense_splitter.split_documents(documents)
    
    def split_documents_sparse(self, documents: List[Document]) -> List[Document]:
        """Split documents into sparse chunks for keyword retrieval."""
        return self.sparse_splitter.split_documents(documents)
    
    def create_tenant_directory(self, tenant_id: str) -> bool:
        """Create directory structure for a new tenant."""
        tenant_data_path = os.path.join(self.data_path, tenant_id)
        
        try:
            os.makedirs(tenant_data_path, exist_ok=True)
            print(f"Created data directory for tenant '{tenant_id}': {tenant_data_path}")
            return True
        except Exception as e:
            print(f"Error creating directory for tenant '{tenant_id}': {e}")
            return False

# Global data loader instance
data_loader = DataLoader()