import React, { useState } from 'react'
import { MagnifyingGlassIcon, DocumentTextIcon, ClockIcon } from '@heroicons/react/24/outline'
import { useQuery } from 'react-query'
import axios from 'axios'
import SearchResults from './SearchResults'
import LoadingSpinner from './LoadingSpinner'

const SearchPage = ({ apiEndpoint }) => {
  const [query, setQuery] = useState('')
  const [namespace, setNamespace] = useState('')
  const [topK, setTopK] = useState(5)
  const [searchTrigger, setSearchTrigger] = useState(null)

  // Fetch available namespaces
  const { data: namespacesData } = useQuery(
    'namespaces',
    async () => {
      const response = await axios.get(`${apiEndpoint}/api/namespaces/`)
      return response.data
    },
    {
      staleTime: 10 * 60 * 1000, // 10 minutes
    }
  )

  // Search query
  const {
    data: searchResults,
    isLoading: isSearching,
    error: searchError,
    refetch: performSearch,
  } = useQuery(
    ['search', searchTrigger],
    async () => {
      if (!searchTrigger) return null
      
      const response = await axios.post(`${apiEndpoint}/api/search/`, {
        query: searchTrigger.query,
        namespace: searchTrigger.namespace || undefined,
        top_k: searchTrigger.topK,
      })
      return response.data
    },
    {
      enabled: !!searchTrigger,
      staleTime: 2 * 60 * 1000, // 2 minutes
    }
  )

  const handleSearch = (e) => {
    e.preventDefault()
    if (!query.trim()) return

    setSearchTrigger({
      query: query.trim(),
      namespace,
      topK,
    })
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      handleSearch(e)
    }
  }

  return (
    <div className="max-w-4xl mx-auto">
      {/* Header */}
      <div className="text-center mb-8">
        <h1 className="text-4xl font-bold text-gray-900 mb-4">
          🔍 Notes Search
        </h1>
        <p className="text-xl text-gray-600">
          Search your processed notes using semantic similarity
        </p>
      </div>

      {/* Search Form */}
      <div className="bg-white rounded-lg shadow-md p-6 mb-8">
        <form onSubmit={handleSearch} className="space-y-4">
          {/* Query Input */}
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <MagnifyingGlassIcon className="h-5 w-5 text-gray-400" />
            </div>
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Search your notes... (e.g., 'machine learning concepts')"
              className="block w-full pl-10 pr-3 py-3 border border-gray-300 rounded-md leading-5 bg-white placeholder-gray-500 focus:outline-none focus:placeholder-gray-400 focus:ring-1 focus:ring-blue-500 focus:border-blue-500 text-lg"
            />
          </div>

          {/* Filters */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Namespace Filter */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Category
              </label>
              <select
                value={namespace}
                onChange={(e) => setNamespace(e.target.value)}
                className="block w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="">All categories</option>
                {namespacesData?.namespaces?.map((ns) => (
                  <option key={ns} value={ns}>
                    {ns.replace('-', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                  </option>
                ))}
              </select>
            </div>

            {/* Results Count */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Results
              </label>
              <select
                value={topK}
                onChange={(e) => setTopK(parseInt(e.target.value))}
                className="block w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
              >
                <option value={3}>3 results</option>
                <option value={5}>5 results</option>
                <option value={10}>10 results</option>
                <option value={20}>20 results</option>
              </select>
            </div>

            {/* Search Button */}
            <div className="flex items-end">
              <button
                type="submit"
                disabled={!query.trim() || isSearching}
                className="w-full bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
              >
                {isSearching ? (
                  <LoadingSpinner size="sm" />
                ) : (
                  <>
                    <MagnifyingGlassIcon className="h-5 w-5 mr-2" />
                    Search
                  </>
                )}
              </button>
            </div>
          </div>
        </form>
      </div>

      {/* Search Results */}
      {searchError && (
        <div className="bg-red-50 border border-red-200 rounded-md p-4 mb-6">
          <div className="flex">
            <div className="ml-3">
              <h3 className="text-sm font-medium text-red-800">
                Search Failed
              </h3>
              <p className="mt-1 text-sm text-red-700">
                {searchError.response?.data?.error || searchError.message}
              </p>
            </div>
          </div>
        </div>
      )}

      {searchResults && (
        <SearchResults 
          results={searchResults}
          query={searchTrigger?.query}
        />
      )}

      {/* Help Text */}
      {!searchResults && !isSearching && (
        <div className="text-center py-12">
          <DocumentTextIcon className="mx-auto h-12 w-12 text-gray-400 mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            Ready to search your notes?
          </h3>
          <p className="text-gray-500 mb-4">
            Enter a search query above to find relevant content across all your processed documents.
          </p>
          
          <div className="bg-blue-50 rounded-lg p-4 max-w-2xl mx-auto">
            <h4 className="font-medium text-blue-900 mb-2">💡 Search Tips:</h4>
            <ul className="text-sm text-blue-800 space-y-1 text-left">
              <li>• Use natural language: "machine learning algorithms"</li>
              <li>• Ask questions: "what is neural network backpropagation?"</li>
              <li>• Search concepts: "linear algebra applications"</li>
              <li>• Filter by category to narrow results</li>
            </ul>
          </div>
        </div>
      )}
    </div>
  )
}

export default SearchPage