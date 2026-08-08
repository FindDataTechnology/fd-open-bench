import { useParams, Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import api from '../services/api'

export default function EvaluationDetail() {
  const { id } = useParams()

  const { data: evaluation, isLoading } = useQuery({
    queryKey: ['evaluation', id],
    queryFn: () => api.get(`/evaluations/${id}`).then(res => res.data),
  })

  const { data: results } = useQuery({
    queryKey: ['evaluation-results', id],
    queryFn: () => api.get(`/evaluations/${id}/results`).then(res => res.data),
  })

  if (isLoading) {
    return <div className="text-center py-8">Loading evaluation...</div>
  }

  if (!evaluation) {
    return <div className="text-center py-8">Evaluation not found</div>
  }

  const progress = evaluation.tasks_total > 0
    ? (evaluation.tasks_completed / evaluation.tasks_total) * 100
    : 0

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Link to="/evaluations" className="text-blue-600 hover:text-blue-700">
          ← Back to Evaluations
        </Link>
      </div>

      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
              Evaluation {evaluation.id.substring(0, 8)}
            </h1>
            <p className="text-gray-500 dark:text-gray-400 mt-1">
              Agent: {evaluation.agent_id.substring(0, 8)}... • Dataset: {evaluation.dataset_id.substring(0, 8)}...
            </p>
          </div>
          <span className={`px-3 py-1 text-sm font-semibold rounded-full ${
            evaluation.status === 'completed' ? 'bg-green-100 text-green-800' :
            evaluation.status === 'running' ? 'bg-blue-100 text-blue-800' :
            evaluation.status === 'failed' ? 'bg-red-100 text-red-800' :
            'bg-gray-100 text-gray-800'
          }`}>
            {evaluation.status}
          </span>
        </div>

        <div className="mt-6 grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-gray-50 dark:bg-gray-900 rounded-lg p-4">
            <p className="text-sm text-gray-500 dark:text-gray-400">Progress</p>
            <p className="text-2xl font-bold text-gray-900 dark:text-white mt-1">
              {evaluation.tasks_completed} / {evaluation.tasks_total}
            </p>
            <div className="mt-2 w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
              <div
                className="bg-blue-600 h-2 rounded-full"
                style={{ width: `${progress}%` }}
              />
            </div>
          </div>

          <div className="bg-gray-50 dark:bg-gray-900 rounded-lg p-4">
            <p className="text-sm text-gray-500 dark:text-gray-400">Total Cost</p>
            <p className="text-2xl font-bold text-gray-900 dark:text-white mt-1">
              ${evaluation.current_cost?.toFixed(2) || '0.00'}
            </p>
          </div>

          <div className="bg-gray-50 dark:bg-gray-900 rounded-lg p-4">
            <p className="text-sm text-gray-500 dark:text-gray-400">Successful</p>
            <p className="text-2xl font-bold text-green-600 mt-1">
              {results?.filter(r => r.status === 'success').length || 0}
            </p>
          </div>

          <div className="bg-gray-50 dark:bg-gray-900 rounded-lg p-4">
            <p className="text-sm text-gray-500 dark:text-gray-400">Failed</p>
            <p className="text-2xl font-bold text-red-600 mt-1">
              {results?.filter(r => r.status === 'error').length || 0}
            </p>
          </div>
        </div>

        <div className="mt-6">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
            Results Summary
          </h2>
          <pre className="bg-gray-50 dark:bg-gray-900 p-4 rounded-lg overflow-x-auto text-sm">
            {JSON.stringify(evaluation.results_summary, null, 2)}
          </pre>
        </div>
      </div>

      <div className="bg-white dark:bg-gray-800 rounded-lg shadow">
        <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
            Test Case Results
          </h2>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50 dark:bg-gray-700">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                  Golden ID
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                  Score
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                  Cost
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                  Business Value
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
              {results?.map((result) => (
                <tr key={result.id}>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                    {result.golden_id.substring(0, 8)}...
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                      result.status === 'success' ? 'bg-green-100 text-green-800' :
                      result.status === 'error' ? 'bg-red-100 text-red-800' :
                      'bg-gray-100 text-gray-800'
                    }`}>
                      {result.status}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                    {result.metric_scores?.overall?.toFixed(2) || '0.00'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                    ${result.total_cost?.toFixed(4) || '0.0000'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                    ${result.business_value_delivered?.toFixed(2) || '0.00'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm">
                    <button className="text-blue-600 hover:text-blue-700">
                      View Details →
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
