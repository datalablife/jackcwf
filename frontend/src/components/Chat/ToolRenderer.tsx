/**
 * ToolRenderer Component
 *
 * Renders tool-specific UI based on tool type:
 * - vector_search: Document cards with snippets and scores
 * - query_database: Tabular data display
 * - web_search: Search result cards with links
 * - generic: JSON data display
 *
 * Usage:
 * ```tsx
 * <ToolRenderer toolCall={toolCall} />
 * ```
 */

import React, { useState } from 'react';
import type { ToolCall, RAGSearchResult, DatabaseQueryResult, WebSearchResult } from '../../types';

interface ToolRendererProps {
  toolCall: ToolCall;
}

/**
 * Render vector search results
 */
const VectorSearchResults: React.FC<{ result: RAGSearchResult | RAGSearchResult[] }> = ({ result }) => {
  const [expandedIndex, setExpandedIndex] = useState<number | null>(null);

  // Ensure result is always an array
  const results = Array.isArray(result) ? result : [result];

  return (
    <div className="space-y-2">
      {results.map((doc: RAGSearchResult, index: number) => (
        <div key={index} className="bg-white border border-slate-200 rounded-lg p-3 hover:shadow-md transition-shadow">
          <div className="flex items-start justify-between gap-2 mb-2">
            <div className="flex-1 min-w-0">
              <h4 className="text-sm font-semibold text-slate-900 truncate">{doc.source || `Document ${index + 1}`}</h4>
              <p className="text-xs text-slate-600 mt-1 line-clamp-2">{doc.content}</p>
            </div>
            <div className="flex-shrink-0 text-right">
              <div className="inline-block px-2 py-1 bg-blue-100 text-blue-700 rounded text-xs font-semibold">
                {(doc.score * 100).toFixed(1)}%
              </div>
            </div>
          </div>

          {expandedIndex === index && (
            <div className="mt-2 pt-2 border-t border-slate-200">
              <p className="text-xs text-slate-700 text-justify">{doc.content}</p>
              <div className="mt-2 flex gap-2">
                <button
                  onClick={() => navigator.clipboard.writeText(doc.content)}
                  className="text-xs px-2 py-1 bg-slate-100 hover:bg-slate-200 rounded text-slate-700"
                >
                  📋 Copy
                </button>
                {doc.metadata && 'url' in doc.metadata && typeof doc.metadata.url === 'string' && (
                  <a
                    href={doc.metadata.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-xs px-2 py-1 bg-blue-100 hover:bg-blue-200 rounded text-blue-700"
                  >
                    🔗 Link
                  </a>
                )}
              </div>
            </div>
          )}

          <button
            onClick={() => setExpandedIndex(expandedIndex === index ? null : index)}
            className="mt-2 text-xs text-blue-600 hover:text-blue-700 font-medium"
          >
            {expandedIndex === index ? '▼ Collapse' : '▶ Expand'}
          </button>
        </div>
      ))}
    </div>
  );
};

/**
 * Render database query results
 */
const DatabaseQueryResults: React.FC<{ result: DatabaseQueryResult }> = ({ result }) => {
  if (!result.rows || result.rows.length === 0) {
    return <div className="text-xs text-slate-600 italic">No results returned</div>;
  }

  const columns = result.columns || Object.keys(result.rows[0] || {});
  const maxRows = 5;
  const hasMore = result.rows.length > maxRows;

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full text-xs border-collapse">
        <thead>
          <tr className="bg-slate-100 border-b border-slate-200">
            {columns.map((col) => (
              <th key={col} className="px-2 py-1 text-left font-semibold text-slate-700 whitespace-nowrap">
                {col}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {result.rows.slice(0, maxRows).map((row, rowIndex) => (
            <tr key={rowIndex} className={rowIndex % 2 === 0 ? 'bg-white' : 'bg-slate-50'}>
              {columns.map((col) => (
                <td key={`${rowIndex}-${col}`} className="px-2 py-1 border-b border-slate-200 truncate max-w-xs">
                  {typeof row[col as keyof typeof row] === 'object'
                    ? JSON.stringify(row[col as keyof typeof row]).substring(0, 50)
                    : String(row[col as keyof typeof row]).substring(0, 50)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
      {hasMore && (
        <div className="text-xs text-slate-600 italic mt-2">
          ... and {result.rows.length - maxRows} more rows
        </div>
      )}
    </div>
  );
};

/**
 * Render web search results
 */
const WebSearchResults: React.FC<{ result: WebSearchResult[] }> = ({ result }) => {
  return (
    <div className="space-y-2">
      {result.map((item, index) => (
        <a
          key={index}
          href={item.url}
          target="_blank"
          rel="noopener noreferrer"
          className="block p-3 bg-white border border-slate-200 rounded-lg hover:shadow-md hover:border-blue-300 transition-all group"
        >
          <h4 className="text-sm font-semibold text-blue-600 group-hover:text-blue-700 truncate">{item.title}</h4>
          <p className="text-xs text-slate-600 mt-1 truncate">{item.url}</p>
          <p className="text-xs text-slate-700 mt-2 line-clamp-2">{item.snippet}</p>
        </a>
      ))}
    </div>
  );
};

/**
 * ToolRenderer - Renders tool call results based on tool type
 *
 * Supports:
 * - vector_search: Document cards with similarity scores
 * - query_database: Tabular results display
 * - web_search: Search result links
 * - generic: JSON data display
 *
 * @param toolCall - Tool call object with type and result
 */
export const ToolRenderer: React.FC<ToolRendererProps> = ({ toolCall }) => {
  const { toolName, toolInput, status, result } = toolCall;

  // Icon and label mapping
  const toolConfig = {
    vector_search: { icon: '🔍', label: 'Vector Search', color: 'blue' },
    query_database: { icon: '🗄️', label: 'Database Query', color: 'purple' },
    web_search: { icon: '🌐', label: 'Web Search', color: 'green' },
    generic: { icon: '⚙️', label: 'Tool', color: 'slate' }
  };

  const config = toolConfig[toolName as keyof typeof toolConfig] || toolConfig.generic;

  return (
    <div className="bg-slate-50 border border-slate-200 rounded-lg p-3 text-xs">
      {/* Tool Header */}
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <span className="text-lg">{config.icon}</span>
          <span className="font-semibold text-slate-900">{config.label}</span>
        </div>
        <div className="flex items-center gap-2">
          {status === 'completed' && <span className="text-green-600">✓ Completed</span>}
          {status === 'pending' && <span className="text-yellow-600">⏳ Pending</span>}
          {status === 'failed' && <span className="text-red-600">✗ Failed</span>}
        </div>
      </div>

      {/* Tool Input */}
      {toolInput && (
        <div className="mb-2 p-2 bg-white border border-slate-200 rounded text-xs">
          <p className="font-mono text-slate-600">
            {JSON.stringify(toolInput).substring(0, 100)}
            {JSON.stringify(toolInput).length > 100 && '...'}
          </p>
        </div>
      )}

      {/* Tool Result */}
      {result ? (
        <div className="bg-white border border-slate-200 rounded p-2">
          {toolName === 'vector_search' && (
            <VectorSearchResults result={result as any} />
          )}

          {toolName === 'query_database' && (
            <DatabaseQueryResults result={result as any} />
          )}

          {toolName === 'web_search' && (
            <WebSearchResults result={result as any} />
          )}

          {/* Fallback: Generic JSON display */}
          {!['vector_search', 'query_database', 'web_search'].includes(toolName) && (
            <pre className="text-xs overflow-auto max-h-64 p-2 bg-slate-100 rounded font-mono">
              {JSON.stringify(result, null, 2).substring(0, 500)}
            </pre>
          )}
        </div>
      ) : (
        <div className="text-slate-600 italic">No results available</div>
      )}
    </div>
  );
};

export default ToolRenderer;
