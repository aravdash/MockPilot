#!/usr/bin/env python3
"""
Django Integration for Notes Summarizer

Provides Django views, models, and utilities for integrating
the notes summarizer with Django projects.
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

# Add backend to path
sys.path.append(str(Path(__file__).parent.parent))

try:
    from django.http import JsonResponse, HttpResponse
    from django.views.decorators.csrf import csrf_exempt
    from django.views.decorators.http import require_http_methods
    from django.core.files.storage import default_storage
    from django.core.files.base import ContentFile
    from django.conf import settings as django_settings
    from django.db import models
    from django.contrib.auth.models import User
    from django.utils import timezone
    DJANGO_AVAILABLE = True
except ImportError:
    DJANGO_AVAILABLE = False
    # Create mock classes for development without Django
    class JsonResponse:
        def __init__(self, *args, **kwargs): pass
    class HttpResponse:
        def __init__(self, *args, **kwargs): pass
    def csrf_exempt(func): return func
    def require_http_methods(methods): return lambda func: func
    class models:
        class Model: pass
        class CharField: pass
        class TextField: pass
        class DateTimeField: pass
        class ForeignKey: pass
        class FileField: pass
        class FloatField: pass
        class IntegerField: pass
        CASCADE = None

# Our Pinecone integration
from services.pinecone_integration import NotesToPinecone

# Set up logging
logger = logging.getLogger(__name__)

# Django Models (only if Django is available)
if DJANGO_AVAILABLE:
    class ProcessedDocument(models.Model):
        """Model to track processed PDF documents"""
        user = models.ForeignKey(User, on_delete=models.CASCADE)
        original_filename = models.CharField(max_length=255)
        file_path = models.CharField(max_length=500)
        namespace = models.CharField(max_length=100, default='general')
        
        # Processing results
        total_pages = models.IntegerField(default=0)
        text_regions = models.IntegerField(default=0)
        tables_found = models.IntegerField(default=0)
        equations_found = models.IntegerField(default=0)
        diagrams_found = models.IntegerField(default=0)
        
        # Timestamps
        uploaded_at = models.DateTimeField(auto_now_add=True)
        processed_at = models.DateTimeField(null=True, blank=True)
        
        # Status
        STATUS_CHOICES = [
            ('pending', 'Pending'),
            ('processing', 'Processing'),
            ('completed', 'Completed'),
            ('failed', 'Failed'),
        ]
        status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
        error_message = models.TextField(blank=True)
        
        class Meta:
            ordering = ['-uploaded_at']
            
        def __str__(self):
            return f"{self.original_filename} ({self.status})"

    class SearchQuery(models.Model):
        """Model to track search queries for analytics"""
        user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
        query_text = models.TextField()
        namespace = models.CharField(max_length=100, blank=True)
        results_count = models.IntegerField(default=0)
        search_time = models.FloatField()  # Time taken for search in seconds
        timestamp = models.DateTimeField(auto_now_add=True)
        
        class Meta:
            ordering = ['-timestamp']

class DjangoNotesIntegration:
    """Django-specific integration for Notes Summarizer"""
    
    def __init__(self):
        """Initialize Django integration"""
        self.pinecone_client = None
        
    def get_pinecone_client(self) -> NotesToPinecone:
        """Get or create Pinecone client using Django settings"""
        if self.pinecone_client is None:
            # Try to get from Django settings first
            api_key = getattr(django_settings, 'PINECONE_API_KEY', None) or os.getenv('PINECONE_API_KEY')
            environment = getattr(django_settings, 'PINECONE_ENVIRONMENT', 'us-east-1') or os.getenv('PINECONE_ENVIRONMENT', 'us-east-1')
            index_name = getattr(django_settings, 'PINECONE_INDEX_NAME', 'notes-index')
            
            if not api_key:
                raise ValueError("Pinecone API key not found. Set PINECONE_API_KEY in Django settings or environment.")
            
            self.pinecone_client = NotesToPinecone(
                pinecone_api_key=api_key,
                pinecone_environment=environment,
                index_name=index_name
            )
            self.pinecone_client.setup_pinecone_index()
            
        return self.pinecone_client

# Django integration instance
django_notes = DjangoNotesIntegration()

# Django Views
@csrf_exempt
@require_http_methods(["POST"])
def search_notes_view(request):
    """Django view for searching notes"""
    if not DJANGO_AVAILABLE:
        return JsonResponse({'error': 'Django not available'}, status=500)
    
    try:
        import time
        start_time = time.time()
        
        # Parse request
        data = json.loads(request.body)
        query = data.get('query', '')
        namespace = data.get('namespace')
        top_k = data.get('top_k', 5)
        
        if not query.strip():
            return JsonResponse({'error': 'Query cannot be empty'}, status=400)
        
        # Perform search
        client = django_notes.get_pinecone_client()
        results = client.search_notes(
            query=query,
            namespace=namespace,
            top_k=top_k
        )
        
        # Track search query
        search_time = time.time() - start_time
        if hasattr(request, 'user') and request.user.is_authenticated:
            SearchQuery.objects.create(
                user=request.user,
                query_text=query,
                namespace=namespace or '',
                results_count=len(results),
                search_time=search_time
            )
        
        return JsonResponse({
            'results': results,
            'query': query,
            'total_results': len(results),
            'search_time': search_time
        })
        
    except Exception as e:
        logger.error(f"Search failed: {e}")
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def upload_pdf_view(request):
    """Django view for uploading and processing PDFs"""
    if not DJANGO_AVAILABLE:
        return JsonResponse({'error': 'Django not available'}, status=500)
    
    try:
        # Check if file was uploaded
        if 'file' not in request.FILES:
            return JsonResponse({'error': 'No file uploaded'}, status=400)
        
        uploaded_file = request.FILES['file']
        namespace = request.POST.get('namespace', 'general')
        
        if not uploaded_file.name.endswith('.pdf'):
            return JsonResponse({'error': 'Only PDF files are supported'}, status=400)
        
        # Save file
        file_content = uploaded_file.read()
        file_path = default_storage.save(
            f"pdfs/{uploaded_file.name}",
            ContentFile(file_content)
        )
        
        # Create database record
        doc_record = None
        if hasattr(request, 'user') and request.user.is_authenticated:
            doc_record = ProcessedDocument.objects.create(
                user=request.user,
                original_filename=uploaded_file.name,
                file_path=file_path,
                namespace=namespace,
                status='pending'
            )
        
        # Process the PDF (this could be moved to a background task)
        try:
            full_file_path = default_storage.path(file_path)
            client = django_notes.get_pinecone_client()
            result = client.upload_to_pinecone(Path(full_file_path), namespace)
            
            # Update database record
            if doc_record:
                doc_record.status = 'completed'
                doc_record.processed_at = timezone.now()
                # Extract stats from result if available
                if isinstance(result, dict):
                    doc_record.total_pages = result.get('total_pages', 0)
                    doc_record.text_regions = result.get('text_regions', 0)
                    doc_record.tables_found = result.get('tables', 0)
                    doc_record.equations_found = result.get('equations', 0)
                    doc_record.diagrams_found = result.get('diagrams', 0)
                doc_record.save()
            
            return JsonResponse({
                'message': 'PDF uploaded and processed successfully',
                'file_name': uploaded_file.name,
                'namespace': namespace,
                'status': 'completed',
                'document_id': doc_record.id if doc_record else None
            })
            
        except Exception as e:
            if doc_record:
                doc_record.status = 'failed'
                doc_record.error_message = str(e)
                doc_record.save()
            raise e
            
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        return JsonResponse({'error': str(e)}, status=500)

@require_http_methods(["GET"])
def user_documents_view(request):
    """View to list user's processed documents"""
    if not DJANGO_AVAILABLE:
        return JsonResponse({'error': 'Django not available'}, status=500)
    
    if not (hasattr(request, 'user') and request.user.is_authenticated):
        return JsonResponse({'error': 'Authentication required'}, status=401)
    
    try:
        documents = ProcessedDocument.objects.filter(user=request.user)
        
        docs_data = []
        for doc in documents:
            docs_data.append({
                'id': doc.id,
                'filename': doc.original_filename,
                'namespace': doc.namespace,
                'status': doc.status,
                'uploaded_at': doc.uploaded_at.isoformat(),
                'processed_at': doc.processed_at.isoformat() if doc.processed_at else None,
                'stats': {
                    'total_pages': doc.total_pages,
                    'text_regions': doc.text_regions,
                    'tables_found': doc.tables_found,
                    'equations_found': doc.equations_found,
                    'diagrams_found': doc.diagrams_found,
                },
                'error_message': doc.error_message if doc.status == 'failed' else None
            })
        
        return JsonResponse({
            'documents': docs_data,
            'total_count': len(docs_data)
        })
        
    except Exception as e:
        logger.error(f"Failed to fetch user documents: {e}")
        return JsonResponse({'error': str(e)}, status=500)

@require_http_methods(["GET"])
def search_analytics_view(request):
    """View to get search analytics for the user"""
    if not DJANGO_AVAILABLE:
        return JsonResponse({'error': 'Django not available'}, status=500)
    
    if not (hasattr(request, 'user') and request.user.is_authenticated):
        return JsonResponse({'error': 'Authentication required'}, status=401)
    
    try:
        queries = SearchQuery.objects.filter(user=request.user)[:50]  # Last 50 queries
        
        analytics_data = []
        for query in queries:
            analytics_data.append({
                'query': query.query_text,
                'namespace': query.namespace,
                'results_count': query.results_count,
                'search_time': query.search_time,
                'timestamp': query.timestamp.isoformat()
            })
        
        return JsonResponse({
            'recent_queries': analytics_data,
            'total_queries': SearchQuery.objects.filter(user=request.user).count()
        })
        
    except Exception as e:
        logger.error(f"Failed to fetch analytics: {e}")
        return JsonResponse({'error': str(e)}, status=500)

# Django Template Tags (optional)
if DJANGO_AVAILABLE:
    from django import template
    
    register = template.Library()
    
    @register.simple_tag
    def notes_search_form():
        """Template tag to render a search form"""
        return '''
        <form id="notes-search-form" method="post" action="/notes/search/">
            <input type="text" name="query" placeholder="Search your notes..." required>
            <select name="namespace">
                <option value="">All categories</option>
                <option value="lecture-notes">Lecture Notes</option>
                <option value="research-papers">Research Papers</option>
                <option value="textbooks">Textbooks</option>
                <option value="study-guides">Study Guides</option>
            </select>
            <button type="submit">Search</button>
        </form>
        
        <script>
        document.getElementById('notes-search-form').addEventListener('submit', function(e) {
            e.preventDefault();
            const formData = new FormData(this);
            
            fetch('/notes/search/', {
                method: 'POST',
                body: JSON.stringify({
                    query: formData.get('query'),
                    namespace: formData.get('namespace'),
                    top_k: 5
                }),
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                }
            })
            .then(response => response.json())
            .then(data => {
                // Handle search results
                console.log('Search results:', data);
                // You can customize this to display results in your template
            });
        });
        </script>
        '''

# Django URLs configuration helper
def get_urls():
    """Get URL patterns for Django integration"""
    if not DJANGO_AVAILABLE:
        return []
    
    from django.urls import path
    
    return [
        path('search/', search_notes_view, name='notes_search'),
        path('upload/', upload_pdf_view, name='notes_upload'),
        path('documents/', user_documents_view, name='user_documents'),
        path('analytics/', search_analytics_view, name='search_analytics'),
    ]

# Django settings helper
DJANGO_SETTINGS_TEMPLATE = """
# Add to your Django settings.py

# Notes Summarizer Configuration
PINECONE_API_KEY = os.getenv('PINECONE_API_KEY')
PINECONE_ENVIRONMENT = os.getenv('PINECONE_ENVIRONMENT', 'us-east-1')
PINECONE_INDEX_NAME = 'notes-index'

# Add to INSTALLED_APPS if creating a Django app
INSTALLED_APPS = [
    # ... your other apps
    'notes_summarizer',  # If you create a Django app
]

# File upload settings
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Optional: Configure file storage for production
# DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
"""

if __name__ == "__main__":
    print("Django Integration for Notes Summarizer")
    print("=" * 40)
    print()
    
    if DJANGO_AVAILABLE:
        print("✅ Django is available")
        print("🔧 Available components:")
        print("   - ProcessedDocument model")
        print("   - SearchQuery model") 
        print("   - search_notes_view")
        print("   - upload_pdf_view")
        print("   - user_documents_view")
        print("   - search_analytics_view")
        print("   - Template tags")
        print("   - URL patterns")
    else:
        print("❌ Django not installed")
        print("💡 Install Django: pip install django")
    
    print()
    print("📝 Usage in Django:")
    print("   1. Add to urls.py: include('notes.urls')")
    print("   2. Run migrations: python manage.py makemigrations && python manage.py migrate")
    print("   3. Use views in your templates")
    
    print()
    print("🔗 Example URLs:")
    print("   POST /notes/search/     - Search notes")
    print("   POST /notes/upload/     - Upload PDF")
    print("   GET  /notes/documents/  - List user docs")
    print("   GET  /notes/analytics/  - Search analytics")