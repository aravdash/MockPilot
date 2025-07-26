# 🎨 **Frontend Implementations**

Multiple frontend options for the **Notes Summarizer** project, demonstrating different approaches to integrate with the backend APIs.

## 📁 **Directory Structure**

```
frontend/
├── README.md                    # This file
├── react/                      # React + Vite implementation
│   ├── package.json
│   ├── src/
│   │   ├── App.jsx
│   │   ├── components/
│   │   │   ├── SearchPage.jsx
│   │   │   ├── SearchResults.jsx
│   │   │   ├── UploadPage.jsx
│   │   │   ├── DocumentsPage.jsx
│   │   │   ├── AnalyticsPage.jsx
│   │   │   └── Navbar.jsx
│   │   └── App.css
│   └── vite.config.js
├── vue/                        # Vue 3 + Vite implementation
│   ├── package.json
│   ├── src/
│   │   ├── App.vue
│   │   ├── components/
│   │   └── views/
│   └── vite.config.js
├── vanilla-js/                 # Pure JavaScript implementation
│   ├── index.html
│   ├── style.css
│   └── script.js
└── django-templates/           # Django template examples
    ├── base.html
    ├── search.html
    ├── upload.html
    └── results.html
```

## 🚀 **Quick Start**

### **Option 1: React Frontend (Recommended)**
```bash
cd frontend/react
npm install
npm run dev
# Opens http://localhost:3000
```

### **Option 2: Vue Frontend**
```bash
cd frontend/vue
npm install
npm run dev
# Opens http://localhost:5173
```

### **Option 3: Vanilla JavaScript**
```bash
cd frontend/vanilla-js
# Open index.html in browser or serve with:
python -m http.server 8080
# Opens http://localhost:8080
```

### **Option 4: Django Templates**
```bash
# Use with Django project
# Copy templates to your Django app's templates folder
```

## 🔧 **Backend Configuration**

All frontends are configured to work with these backend options:

### **FastAPI Server (Default)**
```bash
# Start the FastAPI server
python start_api.py
# API available at http://localhost:8000
```

### **Django REST Framework**
```bash
# Start Django development server
python manage.py runserver
# API available at http://localhost:8000/api/v1/notes/
```

## 🎨 **Frontend Features**

### **🔍 Search Page**
- **Semantic search** with natural language queries
- **Category filtering** by namespace (lecture-notes, research-papers, etc.)
- **Results count** selection (3, 5, 10, 20 results)
- **Real-time search** with loading states
- **Error handling** with user-friendly messages

### **📄 Upload Page**
- **Drag & drop** PDF upload
- **Category selection** for document organization
- **Progress tracking** during upload and processing
- **Status updates** (pending, processing, completed, failed)

### **📚 Documents Page**
- **List all processed documents** for the user
- **Filter by status** (completed, processing, failed)
- **Search documents** by filename
- **View processing statistics** (pages, tables, equations found)
- **Reprocess failed documents**

### **📊 Analytics Page**
- **Search query history** with timestamps
- **Most searched terms** analytics
- **Search performance** metrics
- **Usage statistics** by category

## 🌐 **API Integration**

### **React Example**
```javascript
// Search API call
const searchNotes = async (query, namespace = '', topK = 5) => {
  const response = await axios.post('/api/search/', {
    query,
    namespace: namespace || undefined,
    top_k: topK
  })
  return response.data
}

// Upload API call
const uploadPDF = async (file, namespace = 'general') => {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('namespace', namespace)
  
  const response = await axios.post('/api/upload/', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
  return response.data
}
```

### **Vue Example**
```vue
<script setup>
import { ref } from 'vue'

const searchQuery = ref('')
const searchResults = ref([])

const performSearch = async () => {
  try {
    const response = await fetch('/api/search/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        query: searchQuery.value,
        top_k: 5
      })
    })
    
    const data = await response.json()
    searchResults.value = data.results
  } catch (error) {
    console.error('Search failed:', error)
  }
}
</script>
```

### **Vanilla JavaScript Example**
```javascript
// Simple search function
async function searchNotes() {
  const query = document.getElementById('searchInput').value
  
  try {
    const response = await fetch('/api/search/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        query: query,
        top_k: 5
      })
    })
    
    const data = await response.json()
    displayResults(data.results)
  } catch (error) {
    console.error('Search failed:', error)
  }
}
```

## 🎨 **Styling & UI**

### **React Implementation**
- **TailwindCSS** for modern, responsive design
- **Heroicons** for consistent iconography
- **React Query** for state management and caching
- **React Dropzone** for file uploads

### **Vue Implementation**
- **Vue 3 Composition API** for modern Vue patterns
- **TailwindCSS** for styling
- **Vue Router** for navigation
- **Pinia** for state management

### **Vanilla JavaScript**
- **Pure CSS** with modern CSS Grid and Flexbox
- **Responsive design** with mobile-first approach
- **CSS animations** for smooth interactions
- **No dependencies** - works anywhere

### **Django Templates**
- **Bootstrap 5** for responsive design
- **Django template tags** for dynamic content
- **CSRF protection** built-in
- **Django forms** integration

## 📱 **Responsive Design**

All frontend implementations are **fully responsive**:

- **Mobile-first** design approach
- **Tablet-optimized** layouts
- **Desktop** enhanced experience
- **Touch-friendly** interfaces
- **Keyboard navigation** support

## 🔐 **Authentication**

### **Token-based Authentication (React/Vue)**
```javascript
// Set up axios with token
axios.defaults.headers.common['Authorization'] = `Token ${userToken}`

// Or using fetch
const headers = {
  'Content-Type': 'application/json',
  'Authorization': `Token ${userToken}`
}
```

### **Session Authentication (Django Templates)**
```html
<!-- CSRF protection -->
{% csrf_token %}

<!-- User-specific content -->
{% if user.is_authenticated %}
  <p>Welcome, {{ user.username }}!</p>
{% endif %}
```

## 🚀 **Production Deployment**

### **React/Vue Production Build**
```bash
# Build for production
npm run build

# Serve with nginx, Apache, or CDN
# Files will be in dist/ folder
```

### **Environment Variables**
```bash
# .env file for React/Vue
VITE_API_ENDPOINT=https://your-api-domain.com
VITE_APP_NAME=Notes Summarizer

# For production
VITE_API_ENDPOINT=https://api.yourapp.com
```

### **Django Static Files**
```python
# settings.py
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Collect static files
python manage.py collectstatic
```

## 🧪 **Testing**

### **React Testing**
```bash
# Install testing dependencies
npm install --save-dev @testing-library/react vitest

# Run tests
npm run test
```

### **Vue Testing**
```bash
# Install testing dependencies
npm install --save-dev @vue/test-utils vitest

# Run tests
npm run test
```

## 📚 **Development Guide**

### **Adding New Features**

1. **Backend First**
   - Add API endpoint in `backend/services/api_server.py`
   - Or Django view in `backend/services/django_integration.py`

2. **Frontend Implementation**
   - Create new component in `src/components/`
   - Add API service function
   - Update navigation if needed

### **Customization**

1. **Styling**
   - Modify TailwindCSS classes
   - Update theme colors in config
   - Add custom CSS for specific needs

2. **API Endpoints**
   - Update `apiEndpoint` configuration
   - Modify API calls in service functions
   - Handle authentication tokens

3. **Features**
   - Add new pages/components
   - Integrate additional backend endpoints
   - Extend search functionality

## 🎯 **Recommendations**

### **For Most Users: React Frontend**
- **Modern React** with Hooks and functional components
- **Excellent performance** with React Query caching
- **Great developer experience** with Vite
- **Large ecosystem** of components and libraries

### **For Vue Developers: Vue Frontend**
- **Vue 3 Composition API** for modern patterns
- **Excellent TypeScript** support
- **Smooth learning curve** from Vue 2
- **Great documentation** and community

### **For Simple Use Cases: Vanilla JavaScript**
- **No build process** required
- **Fast loading** with minimal dependencies
- **Easy to understand** and modify
- **Works anywhere** without frameworks

### **For Django Projects: Django Templates**
- **Native Django** integration
- **Server-side rendering** for better SEO
- **Built-in security** features
- **Easy deployment** with existing Django apps

## 🔄 **Next Steps**

1. **Choose your frontend** based on your team's expertise
2. **Start the backend** API server (`python start_api.py`)
3. **Run the frontend** of your choice
4. **Customize** the styling and features for your use case
5. **Deploy** to production when ready

**All frontend options work seamlessly with both FastAPI and Django REST Framework backends!** 🎯