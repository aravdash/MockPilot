# 🎨 **React Frontend for Notes Summarizer**

Modern React application for searching and managing your processed notes with semantic search capabilities.

## 🚀 **Quick Start**

```bash
cd frontend/react
npm install
npm run dev
# Frontend available at http://localhost:3000
```

## 🏗️ **Architecture**

- **Framework**: React 18 with functional components and hooks
- **Build Tool**: Vite for fast development and optimized builds
- **Styling**: TailwindCSS for modern, responsive design
- **State Management**: React Query for server state and caching
- **Icons**: Heroicons for consistent iconography
- **File Uploads**: React Dropzone for drag & drop functionality

## 📁 **Project Structure**

```
frontend/react/
├── src/
│   ├── components/
│   │   ├── SearchPage.jsx      # Main search interface
│   │   ├── SearchResults.jsx   # Display search results
│   │   ├── UploadPage.jsx      # PDF upload interface
│   │   ├── DocumentsPage.jsx   # Document management
│   │   ├── AnalyticsPage.jsx   # Search analytics
│   │   ├── Navbar.jsx          # Navigation bar
│   │   └── LoadingSpinner.jsx  # Loading states
│   ├── App.jsx                 # Main application
│   └── App.css                 # Global styles
├── package.json                # Dependencies
├── vite.config.js             # Vite configuration
└── tailwind.config.js         # TailwindCSS configuration
```

## 🎨 **Features**

### **🔍 Search Interface**
- **Semantic Search**: Natural language queries with real-time results
- **Category Filtering**: Filter by document namespaces
- **Results Count**: Configurable number of results (3, 5, 10, 20)
- **Loading States**: Smooth loading indicators
- **Error Handling**: User-friendly error messages

### **📄 Upload Interface**
- **Drag & Drop**: Intuitive file upload experience
- **Progress Tracking**: Real-time upload and processing status
- **Category Selection**: Organize documents by namespace
- **File Validation**: PDF-only uploads with size limits

### **📚 Document Management**
- **Document List**: View all processed documents
- **Status Tracking**: See processing status (pending, completed, failed)
- **Statistics**: View document metrics (pages, tables, equations)
- **Search Filter**: Find documents by filename

### **📊 Analytics Dashboard**
- **Search History**: Recent search queries with timestamps
- **Performance Metrics**: Search times and result counts
- **Usage Statistics**: Popular search terms and categories
- **Trends**: Search patterns over time

## 🌐 **API Integration**

### **Backend Configuration**
The frontend is configured to work with the FastAPI backend:

```javascript
// Environment configuration
const apiEndpoint = import.meta.env.VITE_API_ENDPOINT || 'http://localhost:8000'

// Search API call
const searchNotes = async (query, namespace = '', topK = 5) => {
  const response = await axios.post(`${apiEndpoint}/api/search/`, {
    query,
    namespace: namespace || undefined,
    top_k: topK
  })
  return response.data
}
```

### **Available API Endpoints**
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/search/` | POST | Semantic search |
| `/api/upload/` | POST | Upload and process PDFs |
| `/api/health/` | GET | Health check |
| `/api/namespaces/` | GET | Available categories |

## 🎯 **Component Highlights**

### **SearchPage.jsx**
- Comprehensive search interface with filters
- Real-time query validation
- React Query integration for caching
- Responsive design for all devices

### **SearchResults.jsx**
- Beautiful result cards with similarity scores
- Syntax highlighting for search terms
- Source file and page information
- Performance metrics display

### **UploadPage.jsx**
- React Dropzone for file uploads
- Progress tracking and status updates
- Category organization
- Error handling and validation

## 🔧 **Development**

### **Environment Variables**
Create a `.env` file in `frontend/react/`:

```bash
VITE_API_ENDPOINT=http://localhost:8000
VITE_APP_NAME=Notes Summarizer
```

### **Development Commands**
```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Run linting
npm run lint
```

### **TailwindCSS Configuration**
The project uses TailwindCSS for styling with a custom configuration:

```javascript
// tailwind.config.js
module.exports = {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: '#2563eb',
        secondary: '#64748b',
      }
    },
  },
  plugins: [],
}
```

## 📱 **Responsive Design**

The application is fully responsive with:
- **Mobile-first** approach
- **Tablet optimization** for medium screens
- **Desktop enhancement** for large displays
- **Touch-friendly** interfaces
- **Keyboard navigation** support

## 🚀 **Production Deployment**

### **Build for Production**
```bash
npm run build
```

This creates optimized files in the `dist/` folder.

### **Environment Configuration**
For production, update the API endpoint:

```bash
# Production .env
VITE_API_ENDPOINT=https://your-api-domain.com
```

### **Deployment Options**
- **Netlify**: Connect your Git repository for automatic deployments
- **Vercel**: Zero-config deployment for React applications
- **AWS S3 + CloudFront**: Static hosting with CDN
- **Nginx**: Serve static files with a reverse proxy to your API

## 🧪 **Testing**

### **Component Testing**
```bash
# Install testing dependencies
npm install --save-dev @testing-library/react vitest

# Run tests
npm run test
```

### **Example Test**
```javascript
import { render, screen } from '@testing-library/react'
import SearchPage from './components/SearchPage'

test('renders search input', () => {
  render(<SearchPage apiEndpoint="http://localhost:8000" />)
  const searchInput = screen.getByPlaceholderText(/search your notes/i)
  expect(searchInput).toBeInTheDocument()
})
```

## 🎨 **Customization**

### **Styling**
Modify TailwindCSS classes throughout the components:

```javascript
// Change primary color
className="bg-blue-600 hover:bg-blue-700"
// to
className="bg-green-600 hover:bg-green-700"
```

### **API Endpoints**
Update the API configuration in components:

```javascript
// In SearchPage.jsx
const { data: namespacesData } = useQuery(
  'namespaces',
  async () => {
    const response = await axios.get(`${apiEndpoint}/api/namespaces/`)
    return response.data
  }
)
```

## 📞 **Support**

- **📖 React Documentation**: [React.dev](https://react.dev)
- **🎨 TailwindCSS**: [TailwindCSS.com](https://tailwindcss.com)
- **⚡ Vite**: [Vitejs.dev](https://vitejs.dev)
- **🔄 React Query**: [TanStack Query](https://tanstack.com/query)

## 🤝 **Contributing**

1. Follow the existing code style
2. Use functional components with hooks
3. Implement proper error boundaries
4. Add TypeScript types if contributing TS features
5. Test components thoroughly

---

**Beautiful, fast, and responsive frontend for your notes search! 🎨**