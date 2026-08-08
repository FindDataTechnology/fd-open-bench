import { useQuery } from '@tanstack/react-query'
import api from '../services/api'
import { Link } from 'react-router-dom'

export default function Dashboard() {
  // Fetch dashboard summary
  const { data: summary, isLoading: summaryLoading } = useQuery({
    queryKey: ['dashboard-summary'],
    queryFn: () => api.get('/dashboard/summary').then(res => res.data),
  })

  // Fetch recent evaluations
  const { data: evaluations, isLoading: evalsLoading } = useQuery({
    queryKey: ['recent-evaluations'],
    queryFn: () => api.get('/evaluations?limit=5').then(res => res.data),
  })

  // Fetch active agents
  const { data: agents, isLoading: agentsLoading } = useQuery({
    queryKey: ['agents'],
    queryFn: () => api.get('/agents').then(res => res.data),
  })

  if (summaryLoading || evalsLoading || agentsLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-xl text-gray-500">Loading dashboard...</div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 data-testid="dashboard-heading" className="text-3xl font-bold text-gray-900 dark:text-white">Dashboard</h1>
        <p className="text-gray-500 dark:text-gray-400 mt-1">
          Overview of your agent evaluation platform
        </p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500 dark:text-gray-400">Total Agents</p>
              <p className="text-3xl font-bold text-gray-900 dark:text-white mt-2">
                {agents?.length || 0}
              </p>
            </div>
            <div className="text-4xl">🤖</div>
          </div>
          <Link to="/agents" className="text-blue-600 hover:text-blue-700 text-sm mt-4 inline-block">
            View all →
          </Link>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500 dark:text-gray-400">Active Evaluations</p>
              <p className="text-3xl font-bold text-gray-900 dark:text-white mt-2">
                {evaluations?.filter(e => e.status === 'running').length || 0}
              </p>
            </div>
            <div className="text-4xl">🧪</div>
          </div>
          <Link to="/evaluations" className="text-blue-600 hover:text-blue-700 text-sm mt-4 inline-block">
            View all →
          </Link>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500 dark:text-gray-400">Total Cost (Today)</p>
              <p className="text-3xl font-bold text-gray-900 dark:text-white mt-2">
                ${summary?.today_cost?.toFixed(2) || '0.00'}
              </p>
            </div>
            <div className="text-4xl">💰</div>
          </div>
          <Link to="/cost-analyzer" className="text-blue-600 hover:text-blue-700 text-sm mt-4 inline-block">
            View details →
          </Link>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500 dark:text-gray-400">Avg ROI</p>
              <p className="text-3xl font-bold text-gray-900 dark:text-white mt-2">
                {summary?.avg_roi?.toFixed(1) || '0'}%
              </p>
            </div>
            <div className="text-4xl">📈</div>
          </div>
          <Link to="/cost-analyzer" className="text-blue-600 hover:text-blue-700 text-sm mt-4 inline-block">
            View analysis →
          </Link>
        </div>
      </div>

      {/* Recent Evaluations */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow">
        <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
            Recent Evaluations
          </h2>
        </div>
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
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                  Progress
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                  Cost
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

      {/* Quick Actions */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
          Quick Actions
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Link
            to="/agents"
            className="flex items-center p-4 border-2 border-gray-200 dark:border-gray-700 rounded-lg hover:border-blue-500 transition-colors"
          >
            <span className="text-3xl mr-4">🤖</span>
            <div>
              <h3 className="font-semibold text-gray-900 dark:text-white">Create Agent</h3>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                Set up a new agent for evaluation
              </p>
            </div>
          </Link>

          <Link
            to="/datasets"
            className="flex items-center p-4 border-2 border-gray-200 dark:border-gray-700 rounded-lg hover:border-blue-500 transition-colors"
          >
            <span className="text-3xl mr-4">📁</span>
            <div>
              <h3 className="font-semibold text-gray-900 dark:text-white">Import Dataset</h3>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                Upload test cases for evaluation
              </p>
            </div>
          </Link>

          <Link
            to="/evaluations"
            className="flex items-center p-4 border-2 border-gray-200 dark:border-gray-700 rounded-lg hover:border-blue-500 transition-colors"
          >
            <span className="text-3xl mr-4">🧪</span>
            <div>
              <h3 className="font-semibold text-gray-900 dark:text-white">Run Evaluation</h3>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                Start a new evaluation batch
              </p>
            </div>
          </Link>
        </div>
      </div>
    </div>
  )
}
