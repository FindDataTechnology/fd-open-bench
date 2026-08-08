import { useQuery } from '@tanstack/react-query'
import { useParams, useNavigate } from 'react-router-dom'
import api from '../services/api'

interface BatchRun {
  run_id: string
  agent_id: string
  agent_name: string
  status: string
  tasks_total: number
  tasks_completed: number
  tasks_failed: number
  progress: number
  current_cost: number
  results_count: number
  avg_score: number | null
}

interface BatchData {
  batch_id: string
  benchmark_id: string
  benchmark_name: string
  agents: BatchRun[]
}

export default function BatchDetail() {
  const { batchId } = useParams<{ batchId: string }>()
  const navigate = useNavigate()

  // Fetch batch comparison data
  const { data: batchData, isLoading } = useQuery<BatchData>({
    queryKey: ['batch', batchId],
    queryFn: async () => {
      const res = await api.get(`/batches/${batchId}`)
      return res.data
    },
    refetchInterval: (query) => {
      // Auto-refresh if any run is still running
      const data = query.state.data
      const hasRunning = data?.agents?.some((a: BatchRun) =>
        a.status === 'running' || a.status === 'pending'
      )
      return hasRunning ? 2000 : false
    },
  })

  const getStatusBadge = (status: string) => {
    const colors = {
      completed: 'bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200',
      running: 'bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200',
      failed: 'bg-red-100 dark:bg-red-900 text-red-800 dark:text-red-200',
      pending: 'bg-yellow-100 dark:bg-yellow-900 text-yellow-800 dark:text-yellow-200',
    }
    return colors[status as keyof typeof colors] || 'bg-gray-100 dark:bg-gray-900 text-gray-800 dark:text-gray-200'
  }

  if (isLoading) {
    return <div className="p-12 text-center text-gray-500">Loading batch...</div>
  }

  if (!batchData) {
    return <div className="p-12 text-center text-gray-500">Batch not found</div>
  }

  return (
    <div className="space-y-6">
      <div>
        <button
          onClick={() => navigate(`/benchmarks/${batchData.benchmark_id}`)}
          className="text-sm text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300 mb-2"
        >
          ← Back to Benchmark
        </button>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
          Batch {batchData.batch_id.substring(0, 8)}
        </h1>
        <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
          {batchData.benchmark_name}
        </p>
      </div>

      {/* Agent Runs */}
      <div className="grid gap-6">
        {batchData.agents.map((agent) => (
          <div
            key={agent.run_id}
            className="bg-white dark:bg-gray-800 rounded-lg shadow overflow-hidden"
          >
            <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                    {agent.agent_name}
                  </h3>
                  <div className="mt-1 flex items-center space-x-4 text-sm text-gray-500 dark:text-gray-400">
                    <span className={`px-2 py-1 rounded text-xs font-medium ${getStatusBadge(agent.status)}`}>
                      {agent.status}
                    </span>
                    <span>
                      {agent.tasks_completed} / {agent.tasks_total} tasks
                    </span>
                    {agent.avg_score !== null && (
                      <span>
                        Avg Score: {agent.avg_score.toFixed(3)}
                      </span>
                    )}
                    <span>
                      Cost: ${agent.current_cost.toFixed(2)}
                    </span>
                  </div>
                </div>
                <button
                  onClick={() => navigate(`/evaluations/${agent.run_id}`)}
                  className="px-4 py-2 text-sm border border-gray-300 rounded-lg text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700"
                >
                  View Details
                </button>
              </div>
            </div>

            {/* Progress Bar */}
            <div className="px-6 py-4">
              <div className="flex items-center justify-between text-sm text-gray-600 dark:text-gray-400 mb-2">
                <span>Progress</span>
                <span>{agent.progress.toFixed(0)}%</span>
              </div>
              <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                <div
                  className={`h-2 rounded-full transition-all duration-300 ${
                    agent.status === 'completed'
                      ? 'bg-green-600'
                      : agent.status === 'failed'
                      ? 'bg-red-600'
                      : 'bg-blue-600'
                  }`}
                  style={{ width: `${agent.progress}%` }}
                />
              </div>
              {agent.tasks_failed > 0 && (
                <div className="mt-2 text-sm text-red-600 dark:text-red-400">
                  {agent.tasks_failed} task{agent.tasks_failed !== 1 ? 's' : ''} failed
                </div>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Summary Stats */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          Batch Summary
        </h2>
        <div className="grid grid-cols-4 gap-4">
          <div>
            <div className="text-sm text-gray-500 dark:text-gray-400">Total Agents</div>
            <div className="text-2xl font-bold text-gray-900 dark:text-white">
              {batchData.agents.length}
            </div>
          </div>
          <div>
            <div className="text-sm text-gray-500 dark:text-gray-400">Completed</div>
            <div className="text-2xl font-bold text-green-600 dark:text-green-400">
              {batchData.agents.filter((a) => a.status === 'completed').length}
            </div>
          </div>
          <div>
            <div className="text-sm text-gray-500 dark:text-gray-400">Running</div>
            <div className="text-2xl font-bold text-blue-600 dark:text-blue-400">
              {batchData.agents.filter((a) => a.status === 'running').length}
            </div>
          </div>
          <div>
            <div className="text-sm text-gray-500 dark:text-gray-400">Failed</div>
            <div className="text-2xl font-bold text-red-600 dark:text-red-400">
              {batchData.agents.filter((a) => a.status === 'failed').length}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}