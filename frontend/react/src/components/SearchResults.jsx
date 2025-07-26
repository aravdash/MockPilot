import React from 'react'
import { DocumentTextIcon, ClockIcon, StarIcon } from '@heroicons/react/24/outline'

const SearchResults = ({ results, query }) => {
  if (!results || results.total_results === 0) {
    return (
      <div className="text-center py-8">
        <DocumentTextIcon className="mx-auto h-12 w-12 text-gray-400 mb-4" />
        <h3 className="text-lg font-medium text-gray-900 mb-2">No results found</h3>
        <p className="text-gray-500">
          Try adjusting your search query or browse different categories.
        </p>
      </div>
    )
  }

  const formatScore = (score) => Math.round(score * 100)
  const getScoreColor = (score) => {
    const percentage = score * 100
    if (percentage >= 80) return 'text-green-600 bg-green-100'
    if (percentage >= 60) return 'text-yellow-600 bg-yellow-100'
    return 'text-red-600 bg-red-100'
  }

  return (
    <div className="space-y-6">
      {/* Results Header */}
      <div className="bg-white rounded-lg shadow-sm border p-4">
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-semibold text-gray-900">
            Search Results for "{query}"
          </h2>
          <div className="flex items-center space-x-4 text-sm text-gray-500">
            <span className="flex items-center">
              <DocumentTextIcon className="h-4 w-4 mr-1" />
              {results.total_results} results
            </span>
            <span className="flex items-center">
              <ClockIcon className="h-4 w-4 mr-1" />
              {(results.search_time * 1000).toFixed(0)}ms
            </span>
          </div>
        </div>
      </div>

      {/* Results List */}
      <div className="space-y-4">
        {results.results.map((result, index) => (
          <div
            key={`${result.source_file}-${result.chunk_id}-${index}`}
            className="bg-white rounded-lg shadow-sm border hover:shadow-md transition-shadow duration-200"
          >
            <div className="p-6">
              {/* Header */}
              <div className="flex items-start justify-between mb-4">
                <div className="flex-1">
                  <h3 className="text-lg font-medium text-gray-900 mb-1">
                    📄 {result.source_file}
                  </h3>
                  <div className="flex items-center space-x-3 text-sm text-gray-500">
                    {result.page_number && (
                      <span>Page {result.page_number}</span>
                    )}
                    {result.content_type && (
                      <span className="capitalize">{result.content_type}</span>
                    )}
                    <span>Chunk {result.chunk_id}</span>
                  </div>
                </div>
                
                {/* Similarity Score */}
                <div className="flex-shrink-0">
                  <span
                    className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${getScoreColor(
                      result.score
                    )}`}
                  >
                    <StarIcon className="h-4 w-4 mr-1" />
                    {formatScore(result.score)}% match
                  </span>
                </div>
              </div>

              {/* Content */}
              <div className="prose max-w-none">
                <p className="text-gray-700 leading-relaxed">
                  {highlightSearchTerms(result.text, query)}
                </p>
              </div>

              {/* Footer */}
              <div className="mt-4 pt-4 border-t border-gray-100">
                <div className="flex items-center justify-between">
                  <span className="text-xs text-gray-400">
                    Relevance: {formatScore(result.score)}%
                  </span>
                  <button className="text-blue-600 hover:text-blue-800 text-sm font-medium">
                    View Full Document →
                  </button>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Results Summary */}
      <div className="bg-blue-50 rounded-lg p-4">
        <div className="flex items-center justify-between">
          <div className="text-sm text-blue-800">
            <strong>{results.total_results}</strong> results found in{' '}
            <strong>{(results.search_time * 1000).toFixed(0)}ms</strong>
          </div>
          <div className="text-xs text-blue-600">
            Powered by semantic search
          </div>
        </div>
      </div>
    </div>
  )
}

// Helper function to highlight search terms
const highlightSearchTerms = (text, query) => {
  if (!query || !text) return text

  // Simple highlighting - in a real app, you might want more sophisticated highlighting
  const terms = query.toLowerCase().split(' ').filter(term => term.length > 2)
  
  let highlightedText = text
  terms.forEach(term => {
    const regex = new RegExp(`(${term})`, 'gi')
    highlightedText = highlightedText.replace(
      regex,
      '<mark class="bg-yellow-200 px-1 rounded">$1</mark>'
    )
  })

  return <span dangerouslySetInnerHTML={{ __html: highlightedText }} />
}

export default SearchResults