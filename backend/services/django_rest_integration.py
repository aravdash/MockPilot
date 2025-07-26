#!/usr/bin/env python3
"""
Django REST Framework Integration for Notes Summarizer

Provides DRF serializers, viewsets, and API endpoints for the notes summarizer.
Alternative to FastAPI with native Django integration.
"""

import os
import sys
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

# Add backend to path
sys.path.append(str(Path(__file__).parent.parent))

try:
    # Django REST Framework imports
    from rest_framework import serializers, viewsets, status, permissions
    from rest_framework.decorators import action, api_view, permission_classes
    from rest_framework.response import Response
    from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
    from rest_framework.authentication import SessionAuthentication, TokenAuthentication
    from rest_framework.permissions import IsAuthenticated
    from rest_framework.pagination import PageNumberPagination
    from rest_framework.filters import SearchFilter, OrderingFilter
    from django_filters.rest_framework import DjangoFilterBackend
    
    # Django imports
    from django.core.files.storage import default_storage
    from django.core.files.base import ContentFile
    from django.conf import settings as django_settings
    from django.utils import timezone
    from django.db import transaction
    
    DRF_AVAILABLE = True
except ImportError:
    DRF_AVAILABLE = False
    # Mock classes for development without DRF
    class serializers:
        class ModelSerializer: pass
        class Serializer: pass
        class CharField: pass
        class IntegerField: pass
        class FloatField: pass
        class DateTimeField: pass
        class FileField: pass
        class ListField: pass
    class viewsets:
        class ModelViewSet: pass
        class ViewSet: pass
    class Response:
        def __init__(self, *args, **kwargs): pass
    class status:
        HTTP_200_OK = 200
        HTTP_201_CREATED = 201
        HTTP_400_BAD_REQUEST = 400
        HTTP_500_INTERNAL_SERVER_ERROR = 500

# Import our Django models and Pinecone integration
from services.django_integration import ProcessedDocument, SearchQuery, django_notes

# Set up logging
logger = logging.getLogger(__name__)

# ============================================================================
# DRF SERIALIZERS
# ============================================================================

if DRF_AVAILABLE:
    class ProcessedDocumentSerializer(serializers.ModelSerializer):
        """Serializer for ProcessedDocument model"""
        
        class Meta:
            model = ProcessedDocument
            fields = [
                'id', 'original_filename', 'namespace', 'status',
                'total_pages', 'text_regions', 'tables_found',
                'equations_found', 'diagrams_found', 'uploaded_at',
                'processed_at', 'error_message'
            ]
            read_only_fields = [
                'id', 'uploaded_at', 'processed_at', 'status',
                'total_pages', 'text_regions', 'tables_found',
                'equations_found', 'diagrams_found', 'error_message'
            ]

    class SearchQuerySerializer(serializers.ModelSerializer):
        """Serializer for SearchQuery model"""
        
        class Meta:
            model = SearchQuery
            fields = [
                'id', 'query_text', 'namespace', 'results_count',
                'search_time', 'timestamp'
            ]
            read_only_fields = ['id', 'timestamp']

    class SearchRequestSerializer(serializers.Serializer):
        """Serializer for search requests"""
        query = serializers.CharField(max_length=1000, required=True)
        namespace = serializers.CharField(max_length=100, required=False, allow_blank=True)
        top_k = serializers.IntegerField(min_value=1, max_value=50, default=5)

    class SearchResultSerializer(serializers.Serializer):
        """Serializer for individual search results"""
        score = serializers.FloatField()
        source_file = serializers.CharField()
        text = serializers.CharField()
        chunk_id = serializers.IntegerField()
        page_number = serializers.IntegerField(required=False)
        content_type = serializers.CharField(required=False)

    class SearchResponseSerializer(serializers.Serializer):
        """Serializer for search response"""
        results = SearchResultSerializer(many=True)
        query = serializers.CharField()
        total_results = serializers.IntegerField()
        search_time = serializers.FloatField()
        namespace = serializers.CharField(required=False, allow_blank=True)

    class PDFUploadSerializer(serializers.Serializer):
        """Serializer for PDF upload"""
        file = serializers.FileField(required=True)
        namespace = serializers.CharField(max_length=100, default='general')
        
        def validate_file(self, value):
            """Validate uploaded file"""
            if not value.name.endswith('.pdf'):
                raise serializers.ValidationError("Only PDF files are supported.")
            
            # Check file size (10MB limit)
            if value.size > 10 * 1024 * 1024:
                raise serializers.ValidationError("File size cannot exceed 10MB.")
            
            return value

    class UploadResponseSerializer(serializers.Serializer):
        """Serializer for upload response"""
        message = serializers.CharField()
        file_name = serializers.CharField()
        namespace = serializers.CharField()
        status = serializers.CharField()
        document_id = serializers.IntegerField(required=False)

# ============================================================================
# DRF PAGINATION
# ============================================================================

if DRF_AVAILABLE:
    class StandardResultsSetPagination(PageNumberPagination):
        page_size = 20
        page_size_query_param = 'page_size'
        max_page_size = 100

# ============================================================================
# DRF VIEWSETS
# ============================================================================

if DRF_AVAILABLE:
    class ProcessedDocumentViewSet(viewsets.ModelViewSet):
        """ViewSet for managing processed documents"""
        
        serializer_class = ProcessedDocumentSerializer
        permission_classes = [IsAuthenticated]
        authentication_classes = [SessionAuthentication, TokenAuthentication]
        pagination_class = StandardResultsSetPagination
        filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
        filterset_fields = ['namespace', 'status']
        search_fields = ['original_filename', 'namespace']
        ordering_fields = ['uploaded_at', 'processed_at', 'original_filename']
        ordering = ['-uploaded_at']
        
        def get_queryset(self):
            """Return documents for the current user only"""
            return ProcessedDocument.objects.filter(user=self.request.user)
        
        def perform_create(self, serializer):
            """Set the user when creating a document"""
            serializer.save(user=self.request.user)
        
        @action(detail=False, methods=['get'])
        def stats(self, request):
            """Get user's document statistics"""
            queryset = self.get_queryset()
            
            stats = {
                'total_documents': queryset.count(),
                'completed_documents': queryset.filter(status='completed').count(),
                'processing_documents': queryset.filter(status='processing').count(),
                'failed_documents': queryset.filter(status='failed').count(),
                'total_pages': sum(doc.total_pages for doc in queryset),
                'namespaces': list(queryset.values_list('namespace', flat=True).distinct()),
            }
            
            return Response(stats)
        
        @action(detail=True, methods=['post'])
        def reprocess(self, request, pk=None):
            """Reprocess a failed document"""
            document = self.get_object()
            
            if document.status != 'failed':
                return Response(
                    {'error': 'Only failed documents can be reprocessed'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Reset status and clear error message
            document.status = 'pending'
            document.error_message = ''
            document.save()
            
            # TODO: Trigger background reprocessing task
            # process_pdf_task.delay(document.id)
            
            return Response({'message': 'Document queued for reprocessing'})

    class SearchQueryViewSet(viewsets.ReadOnlyModelViewSet):
        """ViewSet for viewing search query analytics"""
        
        serializer_class = SearchQuerySerializer
        permission_classes = [IsAuthenticated]
        authentication_classes = [SessionAuthentication, TokenAuthentication]
        pagination_class = StandardResultsSetPagination
        filter_backends = [DjangoFilterBackend, OrderingFilter]
        filterset_fields = ['namespace']
        ordering_fields = ['timestamp', 'search_time', 'results_count']
        ordering = ['-timestamp']
        
        def get_queryset(self):
            """Return search queries for the current user only"""
            return SearchQuery.objects.filter(user=self.request.user)
        
        @action(detail=False, methods=['get'])
        def analytics(self, request):
            """Get search analytics"""
            queryset = self.get_queryset()
            
            analytics = {
                'total_searches': queryset.count(),
                'average_search_time': queryset.aggregate(
                    avg_time=models.Avg('search_time')
                )['avg_time'] or 0,
                'most_searched_terms': list(
                    queryset.values('query_text')
                    .annotate(count=models.Count('query_text'))
                    .order_by('-count')[:10]
                ),
                'searches_by_namespace': list(
                    queryset.values('namespace')
                    .annotate(count=models.Count('namespace'))
                    .order_by('-count')
                ),
            }
            
            return Response(analytics)

    class NotesSearchViewSet(viewsets.ViewSet):
        """ViewSet for searching notes"""
        
        permission_classes = [IsAuthenticated]
        authentication_classes = [SessionAuthentication, TokenAuthentication]
        
        @action(detail=False, methods=['post'])
        def search(self, request):
            """Search notes using semantic similarity"""
            import time
            start_time = time.time()
            
            # Validate request data
            serializer = SearchRequestSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
            try:
                # Get search parameters
                query = serializer.validated_data['query']
                namespace = serializer.validated_data.get('namespace')
                top_k = serializer.validated_data['top_k']
                
                # Perform search
                client = django_notes.get_pinecone_client()
                results = client.search_notes(
                    query=query,
                    namespace=namespace,
                    top_k=top_k
                )
                
                # Track search query
                search_time = time.time() - start_time
                SearchQuery.objects.create(
                    user=request.user,
                    query_text=query,
                    namespace=namespace or '',
                    results_count=len(results),
                    search_time=search_time
                )
                
                # Prepare response
                response_data = {
                    'results': results,
                    'query': query,
                    'total_results': len(results),
                    'search_time': search_time,
                    'namespace': namespace
                }
                
                # Validate response
                response_serializer = SearchResponseSerializer(data=response_data)
                if response_serializer.is_valid():
                    return Response(response_serializer.validated_data)
                else:
                    return Response(response_data)  # Return raw data if serializer fails
                
            except Exception as e:
                logger.error(f"Search failed: {e}")
                return Response(
                    {'error': f'Search failed: {str(e)}'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        @action(detail=False, methods=['post'])
        def upload(self, request):
            """Upload and process a PDF file"""
            # Validate upload data
            serializer = PDFUploadSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
            try:
                uploaded_file = serializer.validated_data['file']
                namespace = serializer.validated_data['namespace']
                
                # Save file
                file_content = uploaded_file.read()
                file_path = default_storage.save(
                    f"pdfs/{uploaded_file.name}",
                    ContentFile(file_content)
                )
                
                # Create database record
                with transaction.atomic():
                    doc_record = ProcessedDocument.objects.create(
                        user=request.user,
                        original_filename=uploaded_file.name,
                        file_path=file_path,
                        namespace=namespace,
                        status='pending'
                    )
                
                # Process the PDF (this should be moved to a background task)
                try:
                    full_file_path = default_storage.path(file_path)
                    client = django_notes.get_pinecone_client()
                    result = client.upload_to_pinecone(Path(full_file_path), namespace)
                    
                    # Update database record
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
                    
                    response_data = {
                        'message': 'PDF uploaded and processed successfully',
                        'file_name': uploaded_file.name,
                        'namespace': namespace,
                        'status': 'completed',
                        'document_id': doc_record.id
                    }
                    
                    response_serializer = UploadResponseSerializer(data=response_data)
                    if response_serializer.is_valid():
                        return Response(response_serializer.validated_data, status=status.HTTP_201_CREATED)
                    else:
                        return Response(response_data, status=status.HTTP_201_CREATED)
                
                except Exception as e:
                    doc_record.status = 'failed'
                    doc_record.error_message = str(e)
                    doc_record.save()
                    raise e
                
            except Exception as e:
                logger.error(f"Upload failed: {e}")
                return Response(
                    {'error': f'Upload failed: {str(e)}'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

# ============================================================================
# API VIEWS (Function-based alternative)
# ============================================================================

if DRF_AVAILABLE:
    @api_view(['GET'])
    @permission_classes([IsAuthenticated])
    def health_check(request):
        """Health check endpoint"""
        return Response({
            'status': 'healthy',
            'message': 'Notes Summarizer DRF API is running',
            'user': request.user.username,
            'timestamp': timezone.now().isoformat()
        })
    
    @api_view(['GET'])
    @permission_classes([IsAuthenticated])
    def namespaces_list(request):
        """List available namespaces"""
        # Get namespaces from user's documents
        user_namespaces = ProcessedDocument.objects.filter(
            user=request.user
        ).values_list('namespace', flat=True).distinct()
        
        # Common namespace suggestions
        suggested_namespaces = [
            'lecture-notes',
            'research-papers',
            'textbooks',
            'study-guides',
            'general'
        ]
        
        # Combine user namespaces with suggestions
        all_namespaces = list(set(list(user_namespaces) + suggested_namespaces))
        
        return Response({
            'namespaces': sorted(all_namespaces),
            'user_namespaces': list(user_namespaces),
            'suggested_namespaces': suggested_namespaces
        })

# ============================================================================
# URL CONFIGURATION
# ============================================================================

def get_drf_urls():
    """Get URL patterns for Django REST Framework integration"""
    if not DRF_AVAILABLE:
        return []
    
    from django.urls import path, include
    from rest_framework.routers import DefaultRouter
    
    # Create router and register viewsets
    router = DefaultRouter()
    router.register(r'documents', ProcessedDocumentViewSet, basename='document')
    router.register(r'queries', SearchQueryViewSet, basename='query')
    router.register(r'search', NotesSearchViewSet, basename='search')
    
    # Additional URL patterns
    urlpatterns = [
        path('', include(router.urls)),
        path('health/', health_check, name='health_check'),
        path('namespaces/', namespaces_list, name='namespaces_list'),
    ]
    
    return urlpatterns

# ============================================================================
# DRF SETTINGS TEMPLATE
# ============================================================================

DRF_SETTINGS_TEMPLATE = """
# Add to your Django settings.py

# Django REST Framework Configuration
INSTALLED_APPS = [
    # ... your other apps
    'rest_framework',
    'rest_framework.authtoken',
    'django_filters',
    'corsheaders',  # For frontend integration
]

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ],
}

# CORS settings for frontend integration
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",  # React
    "http://localhost:5173",  # Vite
    "http://localhost:8080",  # Vue
]

CORS_ALLOW_CREDENTIALS = True

# Notes Summarizer Configuration (same as before)
PINECONE_API_KEY = os.getenv('PINECONE_API_KEY')
PINECONE_ENVIRONMENT = os.getenv('PINECONE_ENVIRONMENT', 'us-east-1')
PINECONE_INDEX_NAME = 'notes-index'
"""

if __name__ == "__main__":
    print("Django REST Framework Integration for Notes Summarizer")
    print("=" * 55)
    print()
    
    if DRF_AVAILABLE:
        print("✅ Django REST Framework is available")
        print("🔧 Available components:")
        print("   - ProcessedDocumentViewSet (CRUD for documents)")
        print("   - SearchQueryViewSet (Analytics)")
        print("   - NotesSearchViewSet (Search & Upload)")
        print("   - Comprehensive serializers")
        print("   - Token authentication")
        print("   - Pagination and filtering")
        print("   - API documentation (Browsable API)")
    else:
        print("❌ Django REST Framework not installed")
        print("💡 Install DRF: pip install djangorestframework django-filter django-cors-headers")
    
    print()
    print("📝 Usage in Django:")
    print("   1. Add DRF to INSTALLED_APPS")
    print("   2. Include DRF URLs: path('api/v1/notes/', include(get_drf_urls()))")
    print("   3. Configure REST_FRAMEWORK settings")
    print("   4. Run migrations: python manage.py migrate")
    
    print()
    print("🔗 API Endpoints:")
    print("   GET    /api/v1/notes/documents/     - List documents")
    print("   POST   /api/v1/notes/documents/     - Upload document")
    print("   GET    /api/v1/notes/documents/{id}/ - Get document details")
    print("   POST   /api/v1/notes/search/search/ - Search notes")
    print("   POST   /api/v1/notes/search/upload/ - Upload PDF")
    print("   GET    /api/v1/notes/queries/       - Search analytics")
    print("   GET    /api/v1/notes/health/        - Health check")
    print("   GET    /api/v1/notes/namespaces/    - List namespaces")