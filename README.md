# 🔍 **Notes Summarizer with Semantic Search**

Transform your PDF documents into searchable knowledge with **OCR processing** and **semantic search** powered by Pinecone vector database.

## ⚡ **Quick Start**

### **1. Setup Backend**
```bash
# Clone and install dependencies
git clone <your-repo>
cd notes-summarizer
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Add your API keys to .env file

# Start the API server
python start_api.py
# API available at http://localhost:8000
```

### **2. Setup Frontend**
```bash
# In a new terminal
cd frontend/react
npm install
npm run dev
# Frontend available at http://localhost:3000
```

### **3. Start Processing PDFs**
1. **Upload PDFs** via the web interface or API
2. **Search your notes** using natural language queries
3. **Get semantic results** with similarity scores

## 🏗️ **Architecture**

```
📄 PDF Upload → 🔍 OCR Processing → ✂️ Text Chunking → 🧠 Embeddings → 🗄️ Pinecone → 🔍 Semantic Search
```

### **Technology Stack**
- **Backend**: FastAPI (high-performance Python API)
- **Frontend**: React + TailwindCSS (modern web interface)
- **OCR**: PaddleOCR, EasyOCR, OpenAI GPT-4V
- **Vector DB**: Pinecone (semantic search)
- **Embeddings**: OpenAI text-embedding-ada-002

## 📁 **Project Structure**

```
notes-summarizer/
├── backend/                     # FastAPI backend
│   ├── src/
│   │   ├── extractors/         # OCR modules (PaddleOCR, EasyOCR)
│   │   └── processors/         # Text formatting
│   ├── services/
│   │   ├── api_server.py       # FastAPI web server
│   │   └── pinecone_integration.py # Vector database
│   ├── main.py                 # Main OCR processor
│   └── convert_json_to_text.py # JSON to text converter
├── frontend/react/              # React frontend
│   ├── src/
│   │   ├── components/         # React components
│   │   └── App.jsx            # Main app
│   └── package.json
├── start_api.py                # Start web server
├── process_pdf.py              # Process PDFs via CLI
├── requirements.txt            # Python dependencies
└── README.md                   # This file
```

## 🚀 **Features**

### **📄 Advanced OCR Processing**
- **Text Extraction**: PaddleOCR + EasyOCR for maximum accuracy
- **Table Recognition**: PP-Structure for structured data
- **Equation Detection**: Specialized math processing
- **Diagram Analysis**: OpenAI GPT-4V for complex visuals
- **Multi-format Support**: PDF, images, documents

### **🔍 Semantic Search**
- **Natural Language Queries**: "Find concepts about machine learning"
- **Similarity Scoring**: See relevance percentages
- **Category Filtering**: Search within specific document types
- **Cross-Document Search**: Find related content across all notes
- **Real-time Results**: Sub-second search responses

### **🌐 Web Interface**
- **Search Page**: Intuitive search with filters
- **Upload Page**: Drag & drop PDF processing
- **Documents Page**: Manage processed files
- **Analytics Page**: Search insights and metrics
- **Responsive Design**: Works on desktop and mobile

## 🔧 **Configuration**

### **Environment Variables (.env)**
```bash
# Required
OPENAI_API_KEY=your_openai_key_here
PINECONE_API_KEY=your_pinecone_key_here
PINECONE_ENVIRONMENT=us-east-1

# Optional
USE_GPU=true
CONFIDENCE_THRESHOLD=0.8
```

### **API Endpoints**
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Web interface |
| `/api/search/` | POST | Search notes |
| `/api/upload/` | POST | Upload & process PDFs |
| `/api/health/` | GET | Health check |
| `/docs` | GET | Interactive API docs |

## 📊 **Usage Examples**

### **CLI Processing**
```bash
# Process a single PDF
python process_pdf.py document.pdf

# With custom output format
python process_pdf.py document.pdf -f rag -o output.txt

# Upload to Pinecone
python pinecone_notes.py document.pdf --namespace="course-notes"
```

### **Web Interface**
```javascript
// Search notes
const results = await fetch('/api/search/', {
  method: 'POST',
  body: JSON.stringify({
    query: "machine learning concepts",
    top_k: 5
  })
})

// Upload PDF
const formData = new FormData()
formData.append('file', pdfFile)
await fetch('/api/upload/', {
  method: 'POST',
  body: formData
})
```

## 🎯 **Real-World Use Cases**

- **📚 Students**: Search across course materials and textbooks
- **🔬 Researchers**: Find relevant papers and concepts
- **📖 Knowledge Workers**: Build searchable document libraries
- **🏢 Teams**: Create shared knowledge bases
- **📝 Note-takers**: Semantic search across all notes

## 🔒 **Security**

- **API Key Protection**: All keys secured on backend
- **CORS Configuration**: Restricted origins
- **Input Validation**: Pydantic models for all requests
- **File Size Limits**: Configurable upload restrictions

## 🚀 **Production Deployment**

### **Backend Deployment**
```bash
# Docker deployment
docker build -t notes-summarizer .
docker run -p 8000:8000 notes-summarizer

# Or with gunicorn
gunicorn backend.services.api_server:app -w 4 -k uvicorn.workers.UvicornWorker
```

### **Frontend Deployment**
```bash
# Build for production
cd frontend/react
npm run build

# Serve with nginx or any static server
# Files will be in dist/ folder
```

## 🛠️ **Development**

### **Backend Development**
```bash
# Install development dependencies
pip install -r requirements.txt

# Run with hot reload
uvicorn backend.services.api_server:app --reload

# Run tests
pytest
```

### **Frontend Development**
```bash
cd frontend/react

# Install dependencies
npm install

# Start development server
npm run dev

# Run linting
npm run lint
```

## 📈 **Performance**

- **FastAPI**: 11.95+ requests/second
- **Search Speed**: Sub-second semantic search
- **OCR Processing**: 2-5 seconds per page
- **Embedding**: 100ms per text chunk
- **Memory**: 1-2GB for typical workloads

## 🤝 **Contributing**

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📞 **Support**

- **📖 Documentation**: [FastAPI docs](http://localhost:8000/docs)
- **🐛 Issues**: GitHub Issues
- **💬 Discussions**: GitHub Discussions

## 📄 **License**

MIT License - see LICENSE file for details.

---

**Transform your PDFs into searchable knowledge! 🚀**