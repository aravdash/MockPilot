#!/usr/bin/env python3
"""
FastAPI server for frontend Pinecone integration

Provides secure API endpoints for frontend applications to search processed notes
without exposing Pinecone API keys to the client.
"""

import os
import sys
from pathlib import Path
from typing import List, Dict, Optional, Any
from pydantic import BaseModel
import logging

# Add backend to path
sys.path.append(str(Path(__file__).parent.parent))

# FastAPI imports
from fastapi import FastAPI, HTTPException, File, UploadFile, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse

# Our Pinecone integration
from services.pinecone_integration import NotesToPinecone

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Pydantic models for API
class SearchRequest(BaseModel):
    query: str
    namespace: Optional[str] = None
    top_k: int = 5

class SearchResult(BaseModel):
    score: float
    source_file: str
    text: str
    chunk_id: int

class SearchResponse(BaseModel):
    results: List[SearchResult]
    query: str
    total_results: int

class UploadResponse(BaseModel):
    message: str
    file_name: str
    status: str

# Initialize FastAPI app
app = FastAPI(
    title="Notes Summarizer API",
    description="API for processing PDFs and searching notes with Pinecone",
    version="1.0.0"
)

# Add CORS middleware for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "http://localhost:8080"],  # React, Vite, Vue dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global Pinecone instance
pinecone_client: Optional[NotesToPinecone] = None

def get_pinecone_client() -> NotesToPinecone:
    """Get or create Pinecone client"""
    global pinecone_client
    
    if pinecone_client is None:
        # Get credentials from environment
        api_key = os.getenv("PINECONE_API_KEY")
        environment = os.getenv("PINECONE_ENVIRONMENT", "us-east-1")
        
        if not api_key:
            raise HTTPException(
                status_code=500,
                detail="Pinecone API key not configured. Set PINECONE_API_KEY environment variable."
            )
        
        try:
            pinecone_client = NotesToPinecone(
                pinecone_api_key=api_key,
                pinecone_environment=environment,
                index_name="notes-index"
            )
            pinecone_client.setup_pinecone_index()
            logger.info("Pinecone client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Pinecone: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to initialize Pinecone: {e}")
    
    return pinecone_client

@app.on_event("startup")
async def startup_event():
    """Initialize Pinecone on startup"""
    try:
        get_pinecone_client()
        logger.info("API server started successfully")
    except Exception as e:
        logger.error(f"Failed to start API server: {e}")

# API Endpoints

@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve a simple frontend interface"""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Notes Summarizer</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
            .search-box { width: 100%; padding: 10px; margin: 10px 0; font-size: 16px; }
            .result { border: 1px solid #ddd; padding: 15px; margin: 10px 0; border-radius: 5px; }
            .score { color: #666; font-size: 12px; }
            .source { color: #0066cc; font-weight: bold; }
            button { padding: 10px 20px; font-size: 16px; background: #0066cc; color: white; border: none; border-radius: 5px; cursor: pointer; }
            button:hover { background: #0052a3; }
        </style>
    </head>
    <body>
        <h1>🔍 Notes Summarizer Search</h1>
        <p>Search your processed notes using semantic similarity</p>
        
        <div>
            <input type="text" id="searchQuery" class="search-box" placeholder="Enter your search query..." />
            <button onclick="searchNotes()">Search</button>
        </div>
        
        <div id="results"></div>
        
        <script>
            async function searchNotes() {
                const query = document.getElementById('searchQuery').value;
                if (!query.trim()) return;
                
                const resultsDiv = document.getElementById('results');
                resultsDiv.innerHTML = '<p>Searching...</p>';
                
                try {
                    const response = await fetch('/api/search', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ query: query, top_k: 5 })
                    });
                    
                    const data = await response.json();
                    
                    if (data.results.length === 0) {
                        resultsDiv.innerHTML = '<p>No results found.</p>';
                        return;
                    }
                    
                    let html = `<h3>Found ${data.total_results} results for "${data.query}"</h3>`;
                    
                    data.results.forEach((result, index) => {
                        html += `
                            <div class="result">
                                <div class="source">📄 ${result.source_file}</div>
                                <div class="score">Similarity: ${(result.score * 100).toFixed(1)}%</div>
                                <p>${result.text}</p>
                            </div>
                        `;
                    });
                    
                    resultsDiv.innerHTML = html;
                    
                } catch (error) {
                    resultsDiv.innerHTML = `<p>Error: ${error.message}</p>`;
                }
            }
            
            // Allow Enter key to search
            document.getElementById('searchQuery').addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    searchNotes();
                }
            });
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.post("/api/search", response_model=SearchResponse)
async def search_notes(request: SearchRequest):
    """Search processed notes using semantic similarity"""
    try:
        client = get_pinecone_client()
        
        # Perform search
        results = client.search_notes(
            query=request.query,
            namespace=request.namespace,
            top_k=request.top_k
        )
        
        # Convert to response format
        search_results = [
            SearchResult(
                score=result['score'],
                source_file=result['source_file'],
                text=result['text'],
                chunk_id=result['chunk_id']
            )
            for result in results
        ]
        
        return SearchResponse(
            results=search_results,
            query=request.query,
            total_results=len(search_results)
        )
        
    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {e}")

@app.post("/api/upload", response_model=UploadResponse)
async def upload_pdf(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    namespace: Optional[str] = None
):
    """Upload and process a PDF file"""
    
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    try:
        # Save uploaded file
        upload_dir = Path("uploads")
        upload_dir.mkdir(exist_ok=True)
        
        file_path = upload_dir / file.filename
        
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Process in background
        background_tasks.add_task(process_pdf_background, file_path, namespace)
        
        return UploadResponse(
            message="PDF uploaded successfully. Processing in background.",
            file_name=file.filename,
            status="processing"
        )
        
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {e}")

async def process_pdf_background(file_path: Path, namespace: Optional[str]):
    """Background task to process PDF and upload to Pinecone"""
    try:
        client = get_pinecone_client()
        client.upload_to_pinecone(file_path, namespace)
        logger.info(f"Successfully processed {file_path.name}")
    except Exception as e:
        logger.error(f"Background processing failed for {file_path.name}: {e}")

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "message": "Notes Summarizer API is running"}

@app.get("/api/namespaces")
async def list_namespaces():
    """List available namespaces (document categories)"""
    # This would require additional Pinecone API calls to get namespace info
    # For now, return common categories
    return {
        "namespaces": [
            "lecture-notes",
            "research-papers", 
            "textbooks",
            "study-guides",
            "general"
        ]
    }

if __name__ == "__main__":
    import uvicorn
    
    # Run the server
    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )