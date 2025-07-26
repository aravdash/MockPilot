# 🚀 Django Integration Guide

Complete guide for integrating the **Notes Summarizer** with your Django project.

## 📋 Quick Setup

### **1. Install Dependencies**
```bash
pip install django
pip install -r requirements.txt  # Our notes summarizer dependencies
```

### **2. Add to Django Project**

**In your `settings.py`:**
```python
import os

# Notes Summarizer Configuration
PINECONE_API_KEY = os.getenv('PINECONE_API_KEY')
PINECONE_ENVIRONMENT = os.getenv('PINECONE_ENVIRONMENT', 'us-east-1')
PINECONE_INDEX_NAME = 'notes-index'

# File upload settings (if not already configured)
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Optional: Add as Django app
INSTALLED_APPS = [
    # ... your other apps
    'notes_summarizer',  # If you create a dedicated app
]
```

**In your main `urls.py`:**
```python
from django.urls import path, include

urlpatterns = [
    # ... your existing URLs
    path('notes/', include('backend.services.django_integration')),
]
```

### **3. Create Models (Optional)**
If you want to track processed documents:

```bash
# Create migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate
```

## 🔧 **Usage in Django Views**

### **Search Notes in Your Views**
```python
from backend.services.django_integration import django_notes

def my_search_view(request):
    if request.method == 'POST':
        query = request.POST.get('query')
        
        try:
            client = django_notes.get_pinecone_client()
            results = client.search_notes(query=query, top_k=5)
            
            return render(request, 'search_results.html', {
                'results': results,
                'query': query
            })
        except Exception as e:
            messages.error(request, f"Search failed: {e}")
    
    return render(request, 'search.html')
```

### **Upload PDFs in Your Views**
```python
from backend.services.django_integration import ProcessedDocument

def upload_pdf_view(request):
    if request.method == 'POST' and request.FILES.get('pdf_file'):
        pdf_file = request.FILES['pdf_file']
        namespace = request.POST.get('namespace', 'general')
        
        # Save file
        file_path = default_storage.save(f"pdfs/{pdf_file.name}", pdf_file)
        
        # Create record
        doc = ProcessedDocument.objects.create(
            user=request.user,
            original_filename=pdf_file.name,
            file_path=file_path,
            namespace=namespace
        )
        
        # Process in background (recommended)
        from django_rq import get_queue
        queue = get_queue('default')
        queue.enqueue(process_pdf_task, doc.id)
        
        messages.success(request, "PDF uploaded! Processing in background.")
        return redirect('document_list')
    
    return render(request, 'upload.html')
```

## 🎨 **Templates**

### **Search Template (`search.html`)**
```html
<form method="post">
    {% csrf_token %}
    <input type="text" name="query" placeholder="Search your notes..." required>
    <select name="namespace">
        <option value="">All categories</option>
        <option value="lecture-notes">Lecture Notes</option>
        <option value="research-papers">Research Papers</option>
        <option value="textbooks">Textbooks</option>
    </select>
    <button type="submit">Search</button>
</form>

<!-- Use the template tag for auto-generated form -->
{% load notes_tags %}
{% notes_search_form %}
```

### **Search Results Template (`search_results.html`)**
```html
<h2>Search Results for "{{ query }}"</h2>

{% for result in results %}
<div class="result">
    <h4>📄 {{ result.source_file }}</h4>
    <p class="score">Similarity: {{ result.score|floatformat:1 }}%</p>
    <p>{{ result.text|truncatewords:50 }}</p>
</div>
{% empty %}
<p>No results found.</p>
{% endfor %}
```

### **Upload Template (`upload.html`)**
```html
<form method="post" enctype="multipart/form-data">
    {% csrf_token %}
    <input type="file" name="pdf_file" accept=".pdf" required>
    <select name="namespace">
        <option value="general">General</option>
        <option value="lecture-notes">Lecture Notes</option>
        <option value="research-papers">Research Papers</option>
    </select>
    <button type="submit">Upload & Process PDF</button>
</form>
```

## 🌐 **API Endpoints**

The Django integration provides these API endpoints:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/notes/search/` | POST | Search notes API |
| `/notes/upload/` | POST | Upload PDF API |
| `/notes/documents/` | GET | List user documents |
| `/notes/analytics/` | GET | Search analytics |

### **AJAX Search Example**
```javascript
// Search using AJAX
function searchNotes(query) {
    fetch('/notes/search/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
        },
        body: JSON.stringify({
            query: query,
            namespace: 'lecture-notes',
            top_k: 5
        })
    })
    .then(response => response.json())
    .then(data => {
        console.log('Search results:', data.results);
        // Display results in your UI
    });
}
```

## 🔄 **Background Processing (Recommended)**

For production use, process PDFs in the background:

### **Using Django-RQ**
```bash
pip install django-rq
```

**In `settings.py`:**
```python
INSTALLED_APPS = [
    # ...
    'django_rq',
]

RQ_QUEUES = {
    'default': {
        'HOST': 'localhost',
        'PORT': 6379,
        'DB': 0,
    }
}
```

**Create `tasks.py`:**
```python
from backend.services.django_integration import django_notes, ProcessedDocument
from pathlib import Path
import django_rq

@django_rq.job
def process_pdf_task(document_id):
    """Background task to process PDF"""
    try:
        doc = ProcessedDocument.objects.get(id=document_id)
        doc.status = 'processing'
        doc.save()
        
        # Process the PDF
        client = django_notes.get_pinecone_client()
        file_path = Path(doc.file_path)
        result = client.upload_to_pinecone(file_path, doc.namespace)
        
        # Update status
        doc.status = 'completed'
        doc.processed_at = timezone.now()
        if isinstance(result, dict):
            doc.total_pages = result.get('total_pages', 0)
            # ... other stats
        doc.save()
        
    except Exception as e:
        doc.status = 'failed'
        doc.error_message = str(e)
        doc.save()
```

### **Using Celery**
```bash
pip install celery redis
```

**Create `celery.py`:**
```python
from celery import Celery
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')

app = Celery('myproject')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
```

## 🔒 **Security Considerations**

### **User Authentication**
```python
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin

@login_required
def search_view(request):
    # Your search logic
    pass

class DocumentListView(LoginRequiredMixin, ListView):
    model = ProcessedDocument
    
    def get_queryset(self):
        return ProcessedDocument.objects.filter(user=self.request.user)
```

### **File Upload Security**
```python
# In settings.py
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024

# Validate file types
def validate_pdf(file):
    if not file.name.endswith('.pdf'):
        raise ValidationError('Only PDF files are allowed.')
    if file.size > 10 * 1024 * 1024:  # 10MB limit
        raise ValidationError('File too large.')
```

## 📱 **Frontend Integration**

### **With Django + React**
```javascript
// In your React components
import axios from 'axios';

const SearchComponent = () => {
    const [query, setQuery] = useState('');
    const [results, setResults] = useState([]);
    
    const searchNotes = async () => {
        try {
            const response = await axios.post('/notes/search/', {
                query: query,
                top_k: 5
            }, {
                headers: {
                    'X-CSRFToken': getCookie('csrftoken')
                }
            });
            
            setResults(response.data.results);
        } catch (error) {
            console.error('Search failed:', error);
        }
    };
    
    return (
        <div>
            <input 
                value={query} 
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Search your notes..."
            />
            <button onClick={searchNotes}>Search</button>
            
            {results.map((result, index) => (
                <div key={index} className="result">
                    <h4>{result.source_file}</h4>
                    <p>{result.text}</p>
                    <span>Score: {result.score}</span>
                </div>
            ))}
        </div>
    );
};
```

### **With Django + Vue**
```vue
<template>
  <div>
    <input v-model="query" placeholder="Search your notes..." />
    <button @click="searchNotes">Search</button>
    
    <div v-for="result in results" :key="result.chunk_id" class="result">
      <h4>{{ result.source_file }}</h4>
      <p>{{ result.text }}</p>
      <span>Score: {{ result.score }}</span>
    </div>
  </div>
</template>

<script>
export default {
  data() {
    return {
      query: '',
      results: []
    };
  },
  methods: {
    async searchNotes() {
      try {
        const response = await fetch('/notes/search/', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': this.getCsrfToken()
          },
          body: JSON.stringify({
            query: this.query,
            top_k: 5
          })
        });
        
        const data = await response.json();
        this.results = data.results;
      } catch (error) {
        console.error('Search failed:', error);
      }
    }
  }
};
</script>
```

## 🚀 **Production Deployment**

### **Environment Variables**
```bash
# .env file
PINECONE_API_KEY=your_pinecone_key
PINECONE_ENVIRONMENT=us-east-1
OPENAI_API_KEY=your_openai_key
DJANGO_SECRET_KEY=your_secret_key
DEBUG=False
```

### **Settings for Production**
```python
# settings/production.py
import os

# Security
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# File storage (use AWS S3 in production)
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
AWS_STORAGE_BUCKET_NAME = 'your-bucket'
AWS_S3_REGION_NAME = 'us-east-1'

# Cache (for better performance)
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
    }
}
```

## 🎯 **Complete Example Project**

Here's a minimal Django project structure:

```
myproject/
├── myproject/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── notes/
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── models.py      # Import from django_integration
│   ├── views.py       # Your custom views
│   ├── urls.py        # Include django_integration URLs
│   └── templates/
│       ├── search.html
│       ├── results.html
│       └── upload.html
├── backend/           # Our notes summarizer
│   └── services/
│       └── django_integration.py
└── manage.py
```

## 📞 **Support**

If you encounter issues:

1. **Check Django version compatibility** (tested with Django 3.2+)
2. **Verify environment variables** are set correctly
3. **Run migrations** if using the database models
4. **Check logs** for detailed error messages

**Ready to integrate!** 🚀

Your Django app now has full **semantic search capabilities** powered by the Notes Summarizer!