#!/usr/bin/env python3
"""
Pinecone Integration for Notes Summarizer

Processes PDFs with advanced OCR and stores in Pinecone vector database
for semantic search and RAG applications.
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from typing import List, Dict, Any
import hashlib

# Add backend to path for direct imports if needed
sys.path.append('backend')

class NotesToPinecone:
    """Integrate OCR-processed notes with Pinecone vector database"""
    
    def __init__(self, pinecone_api_key: str, pinecone_environment: str, index_name: str = "notes-index"):
        """
        Initialize Pinecone integration
        
        Args:
            pinecone_api_key: Your Pinecone API key
            pinecone_environment: Your Pinecone environment
            index_name: Name for the Pinecone index
        """
        self.api_key = pinecone_api_key
        self.environment = pinecone_environment
        self.index_name = index_name
        self.notes_dir = Path("processed_notes")
        self.notes_dir.mkdir(exist_ok=True)
        
        # Initialize Pinecone (you'll need to install: pip install pinecone-client)
        try:
            import pinecone
            from pinecone import Pinecone, ServerlessSpec
            
            self.pc = Pinecone(api_key=pinecone_api_key)
            self.pinecone = pinecone
            print("✅ Pinecone initialized successfully")
        except ImportError:
            print("❌ Pinecone not installed. Run: pip install pinecone-client")
            sys.exit(1)
    
    def process_pdf_to_text(self, pdf_path: Path, output_format: str = "rag") -> Path:
        """
        Process PDF using the notes summarizer backend
        
        Args:
            pdf_path: Path to PDF file
            output_format: 'rag' or 'text' format
            
        Returns:
            Path to processed text file
        """
        print(f"📄 Processing PDF: {pdf_path.name}")
        
        # Generate output path
        output_path = self.notes_dir / f"{pdf_path.stem}.txt"
        
        # Run the backend main.py
        backend_main = Path("backend/main.py")
        
        cmd = [
            sys.executable, 
            str(backend_main),
            str(pdf_path),
            "-f", output_format,
            "-o", str(output_path)
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            print(f"✅ Processed successfully: {output_path}")
            return output_path
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to process {pdf_path}: {e.stderr}")
            raise
    
    def chunk_text(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> List[Dict[str, Any]]:
        """
        Split text into overlapping chunks for better semantic search
        
        Args:
            text: Input text to chunk
            chunk_size: Size of each chunk in characters
            overlap: Overlap between chunks
            
        Returns:
            List of text chunks with metadata
        """
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            
            # Try to break at sentence boundary
            if end < len(text):
                sentence_end = text.rfind('.', start, end)
                if sentence_end != -1 and sentence_end > start + chunk_size // 2:
                    end = sentence_end + 1
            
            chunk_text = text[start:end].strip()
            
            if chunk_text:
                chunks.append({
                    'text': chunk_text,
                    'start_char': start,
                    'end_char': end,
                    'chunk_id': len(chunks)
                })
            
            start = end - overlap
        
        return chunks
    
    def create_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Create embeddings using OpenAI (or your preferred embedding model)
        
        Args:
            texts: List of text chunks to embed
            
        Returns:
            List of embedding vectors
        """
        try:
            import openai
            from openai import OpenAI
            
            client = OpenAI()  # Uses OPENAI_API_KEY from environment
            
            embeddings = []
            batch_size = 100  # Process in batches to handle rate limits
            
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i + batch_size]
                
                response = client.embeddings.create(
                    model="text-embedding-ada-002",
                    input=batch
                )
                
                batch_embeddings = [item.embedding for item in response.data]
                embeddings.extend(batch_embeddings)
            
            print(f"✅ Created {len(embeddings)} embeddings")
            return embeddings
            
        except ImportError:
            print("❌ OpenAI not installed. Run: pip install openai")
            raise
        except Exception as e:
            print(f"❌ Failed to create embeddings: {e}")
            raise
    
    def setup_pinecone_index(self, dimension: int = 1536):
        """
        Create or connect to Pinecone index
        
        Args:
            dimension: Embedding dimension (1536 for text-embedding-ada-002)
        """
        try:
            # Check if index exists
            if self.index_name not in [index.name for index in self.pc.list_indexes()]:
                print(f"📊 Creating Pinecone index: {self.index_name}")
                
                self.pc.create_index(
                    name=self.index_name,
                    dimension=dimension,
                    metric="cosine",
                    spec=self.pinecone.ServerlessSpec(
                        cloud="aws",
                        region=self.environment
                    )
                )
            
            # Connect to index
            self.index = self.pc.Index(self.index_name)
            print(f"✅ Connected to Pinecone index: {self.index_name}")
            
        except Exception as e:
            print(f"❌ Failed to setup Pinecone index: {e}")
            raise
    
    def upload_to_pinecone(self, pdf_path: Path, namespace: str = None):
        """
        Complete pipeline: PDF → OCR → Embeddings → Pinecone
        
        Args:
            pdf_path: Path to PDF file
            namespace: Pinecone namespace (optional)
        """
        try:
            # Step 1: Process PDF to text
            text_path = self.process_pdf_to_text(pdf_path)
            
            # Step 2: Read processed text
            with open(text_path, 'r', encoding='utf-8') as f:
                full_text = f.read()
            
            # Step 3: Chunk the text
            chunks = self.chunk_text(full_text)
            print(f"📑 Split into {len(chunks)} chunks")
            
            # Step 4: Create embeddings
            chunk_texts = [chunk['text'] for chunk in chunks]
            embeddings = self.create_embeddings(chunk_texts)
            
            # Step 5: Prepare vectors for Pinecone
            vectors = []
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                vector_id = f"{pdf_path.stem}_{i}"
                
                vectors.append({
                    'id': vector_id,
                    'values': embedding,
                    'metadata': {
                        'source_file': pdf_path.name,
                        'chunk_id': chunk['chunk_id'],
                        'text': chunk['text'][:1000],  # Truncate for metadata
                        'start_char': chunk['start_char'],
                        'end_char': chunk['end_char']
                    }
                })
            
            # Step 6: Upload to Pinecone
            batch_size = 100
            for i in range(0, len(vectors), batch_size):
                batch = vectors[i:i + batch_size]
                self.index.upsert(vectors=batch, namespace=namespace)
            
            print(f"✅ Uploaded {len(vectors)} vectors to Pinecone")
            
        except Exception as e:
            print(f"❌ Failed to upload to Pinecone: {e}")
            raise
    
    def search_notes(self, query: str, namespace: str = None, top_k: int = 5) -> List[Dict]:
        """
        Search processed notes using semantic similarity
        
        Args:
            query: Search query
            namespace: Pinecone namespace to search
            top_k: Number of results to return
            
        Returns:
            List of matching note chunks
        """
        try:
            # Create embedding for query
            query_embedding = self.create_embeddings([query])[0]
            
            # Search Pinecone
            results = self.index.query(
                vector=query_embedding,
                top_k=top_k,
                namespace=namespace,
                include_metadata=True
            )
            
            # Format results
            matches = []
            for match in results.matches:
                matches.append({
                    'score': match.score,
                    'source_file': match.metadata.get('source_file'),
                    'text': match.metadata.get('text'),
                    'chunk_id': match.metadata.get('chunk_id')
                })
            
            return matches
            
        except Exception as e:
            print(f"❌ Search failed: {e}")
            raise

def main():
    """Example usage"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Upload PDFs to Pinecone via OCR processing")
    parser.add_argument("pdf_files", nargs="+", help="PDF files to process")
    parser.add_argument("--pinecone-key", required=True, help="Pinecone API key")
    parser.add_argument("--pinecone-env", required=True, help="Pinecone environment")
    parser.add_argument("--namespace", help="Pinecone namespace")
    parser.add_argument("--search", help="Search query to test")
    
    args = parser.parse_args()
    
    # Initialize integration
    notes_to_pinecone = NotesToPinecone(
        pinecone_api_key=args.pinecone_key,
        pinecone_environment=args.pinecone_env
    )
    
    # Setup Pinecone index
    notes_to_pinecone.setup_pinecone_index()
    
    # Process and upload PDFs
    for pdf_file in args.pdf_files:
        pdf_path = Path(pdf_file)
        if pdf_path.exists():
            print(f"\n🚀 Processing: {pdf_path}")
            notes_to_pinecone.upload_to_pinecone(pdf_path, args.namespace)
        else:
            print(f"❌ File not found: {pdf_path}")
    
    # Test search if provided
    if args.search:
        print(f"\n🔍 Searching for: '{args.search}'")
        results = notes_to_pinecone.search_notes(args.search, args.namespace)
        
        for i, result in enumerate(results, 1):
            print(f"\n{i}. Score: {result['score']:.3f}")
            print(f"   Source: {result['source_file']}")
            print(f"   Text: {result['text'][:200]}...")

if __name__ == "__main__":
    main()