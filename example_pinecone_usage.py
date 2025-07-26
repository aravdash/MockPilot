#!/usr/bin/env python3
"""
Example: Using Notes Summarizer with Pinecone

This example shows how to:
1. Process PDFs with advanced OCR
2. Upload to Pinecone for semantic search
3. Search your processed notes
"""

import os
from pathlib import Path
from pinecone_integration import NotesToPinecone

def example_usage():
    """Example of processing PDFs and uploading to Pinecone"""
    
    # Set up your API keys (add these to your .env file)
    pinecone_api_key = os.getenv("PINECONE_API_KEY")
    pinecone_environment = os.getenv("PINECONE_ENVIRONMENT", "us-east-1")  # or your region
    openai_api_key = os.getenv("OPENAI_API_KEY")
    
    if not pinecone_api_key:
        print("❌ Please set PINECONE_API_KEY in your .env file")
        return
    
    if not openai_api_key:
        print("❌ Please set OPENAI_API_KEY in your .env file")
        return
    
    # Initialize the integration
    notes_processor = NotesToPinecone(
        pinecone_api_key=pinecone_api_key,
        pinecone_environment=pinecone_environment,
        index_name="my-notes"
    )
    
    # Setup Pinecone index
    notes_processor.setup_pinecone_index()
    
    # Example 1: Process a single PDF
    pdf_path = Path("example_document.pdf")
    if pdf_path.exists():
        print(f"🚀 Processing {pdf_path}...")
        notes_processor.upload_to_pinecone(pdf_path, namespace="lecture-notes")
    
    # Example 2: Batch process multiple PDFs
    pdf_directory = Path("my_pdfs/")
    if pdf_directory.exists():
        for pdf_file in pdf_directory.glob("*.pdf"):
            print(f"🚀 Processing {pdf_file}...")
            notes_processor.upload_to_pinecone(pdf_file, namespace="research-papers")
    
    # Example 3: Search your processed notes
    search_queries = [
        "machine learning algorithms",
        "data structures and algorithms", 
        "neural networks",
        "database design patterns"
    ]
    
    for query in search_queries:
        print(f"\n🔍 Searching for: '{query}'")
        results = notes_processor.search_notes(
            query=query, 
            namespace="lecture-notes",  # or None to search all
            top_k=3
        )
        
        for i, result in enumerate(results, 1):
            print(f"  {i}. Score: {result['score']:.3f}")
            print(f"     Source: {result['source_file']}")
            print(f"     Text: {result['text'][:150]}...")
            print()

def simple_workflow_example():
    """Simple step-by-step example"""
    
    print("📚 Simple Pinecone Workflow Example")
    print("=" * 40)
    
    # Step 1: Set environment variables
    print("1. Set up your API keys in .env:")
    print("   PINECONE_API_KEY=your_pinecone_key")
    print("   OPENAI_API_KEY=your_openai_key")
    print()
    
    # Step 2: Install dependencies
    print("2. Install Pinecone:")
    print("   pip install pinecone-client")
    print()
    
    # Step 3: Process documents
    print("3. Process your PDFs:")
    print("   python pinecone_integration.py document1.pdf document2.pdf \\")
    print("     --pinecone-key YOUR_KEY --pinecone-env us-east-1")
    print()
    
    # Step 4: Search
    print("4. Search your notes:")
    print("   python pinecone_integration.py document1.pdf \\")
    print("     --pinecone-key YOUR_KEY --pinecone-env us-east-1 \\")
    print("     --search 'machine learning concepts'")
    print()
    
    print("✨ Your PDFs are now searchable with semantic similarity!")

if __name__ == "__main__":
    print("Choose an example:")
    print("1. Full workflow example (requires API keys)")
    print("2. Simple command-line examples")
    
    choice = input("Enter choice (1 or 2): ").strip()
    
    if choice == "1":
        example_usage()
    else:
        simple_workflow_example()