import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import api from '../services/api'
import { Link } from 'react-router-dom'

export default function Evaluations() {
  const [showCreateModal, setShowCreateModal] = useState(false)
  const queryClient = useQueryClient()

  const { data: evaluations, isLoading } = useQuery({
    queryKey: ['evaluations'],
    queryFn: () => api.get('/evaluations').then(res => res.data),
  })

  const { data: agents } = useQuery({
    queryKey: ['agents'],
    queryFn: () => api.get('/agents').then(res => res.data),
  })

  const { data: datasets } = useQuery({
    queryKey: ['datasets'],
    queryFn: () => api.get('/datasets').then(res => res.data),
  })

  const createMutation = useMutation({
    mutationFn: (data) => api.post('/evaluations', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['evaluations'] })
      setShowCreateModal(false)
    },
  })

  if (isLoading) {
    return <div className="text-center py-8">Loading evaluations...</div>
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Evaluations</h1>
          <p className="text-gray-500 dark:text-gray-400 mt-1">
            Run and monitor agent evaluations
          </p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          data-testid="create-evaluation-button"
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          + New Evaluation
        </button>
      </div>

      <div data-testid="evaluation-list" className="bg-white dark:bg-gray-800 rounded-lg shadow">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50 dark:bg-gray-700">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                  Run ID
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                  Agent
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                  Dataset
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                  Progress
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                  Cost
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                  Date
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
              {evaluations?.map((eval_run) => (
                <tr key={eval_run.id}>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                    {eval_run.id.substring(0, 8)}...
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                    {eval_run.agent_id.substring(0, 8)}...
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                    {eval_run.dataset_id.substring(0, 8)}...
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                      eval_run.status === 'completed' ? 'bg-green-100 text-green-800' :
                      eval_run.status === 'running' ? 'bg-blue-100 text-blue-800' :
                      eval_run.status === 'failed' ? 'bg-red-100 text-red-800' :
                      'bg-gray-100 text-gray-800'
                    }`}>
                      {eval_run.status}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                    {eval_run.tasks_completed} / {eval_run.tasks_total}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                    ${eval_run.current_cost?.toFixed(2) || '0.00'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                    {new Date(eval_run.created_at).toLocaleDateString()}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm">
                    <Link
                      to={`/evaluations/${eval_run.id}`}
                      className="text-blue-600 hover:text-blue-700"
                    >
                      View →
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {showCreateModal && (
        <CreateEvaluationModal
          agents={agents}
          datasets={datasets}
          onClose={() => setShowCreateModal(false)}
          onCreate={(data) => createMutation.mutate(data)}
        />
      )}
    </div>
  )
}

function CreateEvaluationModal({ agents, datasets, onClose, onCreate }) {
  const [agentId, setAgentId] = useState('')
  const [datasetId, setDatasetId] = useState('')
  const [evaluators] = useState([])

  const handleSubmit = (e) => {
    e.preventDefault()
    onCreate({
      agent_id: agentId,
      dataset_id: datasetId,
      evaluator_configs: evaluators,
    })
  }

  return (
    <div data-testid="create-evaluation-modal" className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white dark:bg-gray-800 rounded-lg p-6 w-full max-w-md">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">
          Create New Evaluation
        </h2>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Agent
            </label>
            <select
              data-testid="agent-selector"
              value={agentId}
              onChange={(e) => setAgentId(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              required
            >
              <option value="">Select an agent</option>
              {agents?.map((agent) => (
                <option key={agent.id} value={agent.id}>
                  {agent.name}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Dataset
            </label>
            <select
              data-testid="dataset-selector"
              value={datasetId}
              onChange={(e) => setDatasetId(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              required
            >
              <option value="">Select a dataset</option>
              {datasets?.map((dataset) => (
                <option key={dataset.id} value={dataset.id}>
                  {dataset.name} ({dataset.golden_count} test cases)
                </option>
              ))}
            </select>
          </div>
          <div className="flex gap-3 pt-4">
            <button
              type="button"
              data-testid="cancel-button"
              onClick={onClose}
              className="flex-1 px-4 py-2 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700"
            >
              Cancel
            </button>
            <button
              type="submit"
              data-testid="create-evaluation-submit-button"
              className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              Create
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
