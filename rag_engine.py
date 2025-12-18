import os
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
import uuid
from typing import List, Dict

# Configuration
CHROMA_DB_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "db"))
COLLECTION_NAME = "legal_docs"

class RAGEngine:
    def __init__(self):
        print("Initializing RAG Engine...")
        self.client = chromadb.PersistentClient(path=CHROMA_DB_DIR)
        self.collection = self.client.get_or_create_collection(name=COLLECTION_NAME)
        
        # Load embedding model (runs on CPU/GPU automatically)
        print("Loading Embedding Model...")
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        print("RAG Engine Ready.")

    def split_text(self, text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
        """
        Simple recursive-like text splitter.
        """
        chunks = []
        start = 0
        text_len = len(text)

        while start < text_len:
            end = start + chunk_size
            if end >= text_len:
                chunks.append(text[start:])
                break
            
            # Try to find the last period or newline to break cleanly
            # Look back from 'end' to find a split point
            split_point = -1
            for i in range(end, start + overlap, -1):
                if text[i] in ['.', '\n']:
                    split_point = i + 1
                    break
            
            if split_point != -1:
                chunks.append(text[start:split_point])
                start = split_point
            else:
                # Hard split if no punctuation found
                chunks.append(text[start:end])
                start = end - overlap
        
        return chunks

    def ingest_document(self, filename: str, text: str):
        """
        Chunks document and saves to ChromaDB.
        """
        chunks = self.split_text(text)
        if not chunks:
            return

        print(f"Embedding {len(chunks)} chunks for {filename}...")
        embeddings = self.embedding_model.encode(chunks).tolist()
        
        ids = [str(uuid.uuid4()) for _ in chunks]
        metadatas = [{"source": filename, "chunk_index": i} for i in range(len(chunks))]

        self.collection.add(
            documents=chunks,
            embeddings=embeddings,
            metadatas=metadatas,
            ids=ids
        )
        print(f"Ingested {filename} successfully.")

    def search(self, query: str, n_results: int = 3) -> List[str]:
        """
        Retrieves most relevant chunks for a query.
        """
        query_embedding = self.embedding_model.encode([query]).tolist()
        
        results = self.collection.query(
            query_embeddings=query_embedding,
            n_results=n_results
        )
        
        # Flatten results
        documents = results['documents'][0] if results['documents'] else []
        return documents

rag_engine = RAGEngine()
