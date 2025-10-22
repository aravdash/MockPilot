import React, { useState } from 'react'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from 'react-query'
import SearchPage from './components/SearchPage'
import UploadPage from './components/UploadPage'
import DocumentsPage from './components/DocumentsPage'
import AnalyticsPage from './components/AnalyticsPage'
import Navbar from './components/Navbar'
import './App.css'

// Create a client for React Query
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
      staleTime: 5 * 60 * 1000, // 5 minutes
    },
  },
})

function App() {
  const [apiEndpoint] = useState(
    import.meta.env.VITE_API_ENDPOINT || 'http://localhost:8000'
  )

  return (
    <QueryClientProvider client={queryClient}>
      <Router>
        <div className="min-h-screen bg-gray-50">
          <Navbar />
          
          <main className="container mx-auto px-4 py-8">
            <Routes>
              <Route path="/" element={<SearchPage apiEndpoint={apiEndpoint} />} />
              <Route path="/search" element={<SearchPage apiEndpoint={apiEndpoint} />} />
              <Route path="/upload" element={<UploadPage apiEndpoint={apiEndpoint} />} />
              <Route path="/documents" element={<DocumentsPage apiEndpoint={apiEndpoint} />} />
              <Route path="/analytics" element={<AnalyticsPage apiEndpoint={apiEndpoint} />} />
            </Routes>
          </main>
        </div>
      </Router>
    </QueryClientProvider>
  )
}

export default App