import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import api from '../services/api'

interface Benchmark {
  id: string
  name: string
  description: string
  dataset_id: string
  metric_suite: string[]
  value_formula: string
  time_value_rate: number
}

interface LeaderboardEntry {
  agent_id: string
  agent_name: string
  run_count: number
  task_count: number
  success_count: number
  success_rate: number
  avg_score: number | null
  stddev_score: number | null
  avg_cost: number | null
  avg_latency_s: number | null
  total_cost: number
  total_business_value: number
  cost_per_success: number | null
  human_replacement: number | null
  time_cost: number
  net_value: number
  roi: number | null
  tech_stats: Record<string, {
    avg: number
    stddev: number
    min: number
    max: number
    count: number
  }>
}

type SortField = 'cost_per_success' | 'roi' | 'human_replacement' | 'avg_score' | 'success_rate'
type SortOrder = 'asc' | 'desc'

export default function Leaderboard() {
  const navigate = useNavigate()
  const [selectedBenchmark, setSelectedBenchmark] = useState<string>('')
  const [sortBy, setSortBy] = useState<SortField>('cost_per_success')
  const [sortOrder, setSortOrder] = useState<SortOrder>('asc')

  // Fetch benchmarks
  const { data: benchmarks } = useQuery<Benchmark[]>({
    queryKey: ['benchmarks'],
    queryFn: async () => {
      const res = await api.get('/benchmarks/')
      return res.data
    },
  })

  // Fetch leaderboard for selected benchmark
  const { data: leaderboardData, isLoading } = useQuery({
    queryKey: ['leaderboard', selectedBenchmark, sortBy, sortOrder],
    queryFn: async () => {
      if (!selectedBenchmark) return null
      const res = await api.get(`/benchmarks/${selectedBenchmark}/leaderboard`, {
        params: { sort_by: sortBy, sort_order: sortOrder }
      })
      return res.data
    },
    enabled: !!selectedBenchmark,
  })

  const leaderboard: LeaderboardEntry[] = leaderboardData?.leaderboard || []

  const formatNumber = (value: number | null, decimals: number = 2) => {
    if (value === null || value === undefined) return '-'
    return value.toFixed(decimals)
  }

  const formatCurrency = (value: number | null) => {
    if (value === null || value === undefined) return '-'
    return `$${value.toFixed(2)}`
  }

  const formatPercent = (value: number | null) => {
    if (value === null || value === undefined) return '-'
    return `${(value * 100).toFixed(1)}%`
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
            Agent Leaderboard
          </h1>
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
            Compare agents on the same benchmark — technical + business metrics
          </p>
        </div>
        <button
          onClick={() => navigate('/benchmarks')}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          Manage Benchmarks
        </button>
      </div>

      {/* Benchmark Selector */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
          Select Benchmark
        </label>
        <select
          value={selectedBenchmark}
          onChange={(e) => setSelectedBenchmark(e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg dark:bg-gray-700 dark:border-gray-600 dark:text-white"
        >
          <option value="">Choose a benchmark...</option>
          {benchmarks?.map((b) => (
            <option key={b.id} value={b.id}>
              {b.name}
            </option>
          ))}
        </select>
        {selectedBenchmark && (
          <div className="mt-4 text-sm text-gray-600 dark:text-gray-400">
            {benchmarks?.find(b => b.id === selectedBenchmark)?.description}
          </div>
        )}
      </div>

      {/* Leaderboard Table */}
      {selectedBenchmark && (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                Results
              </h2>
              <div className="flex items-center space-x-4">
                <label className="text-sm text-gray-600 dark:text-gray-400">
                  Sort by:
                </label>
                <select
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value as SortField)}
                  className="px-3 py-1 border border-gray-300 rounded dark:bg-gray-700 dark:border-gray-600 dark:text-white text-sm"
                >
                  <option value="cost_per_success">Cost per Success</option>
                  <option value="roi">ROI</option>
                  <option value="human_replacement">Human Replacement</option>
                  <option value="avg_score">Avg Score</option>
                  <option value="success_rate">Success Rate</option>
                </select>
                <button
                  onClick={() => setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')}
                  className="px-3 py-1 border border-gray-300 rounded dark:bg-gray-700 dark:border-gray-600 dark:text-white text-sm"
                >
                  {sortOrder === 'asc' ? '↑' : '↓'}
                </button>
              </div>
            </div>
          </div>

          {isLoading ? (
            <div className="p-12 text-center text-gray-500 dark:text-gray-400">
              Loading leaderboard...
            </div>
          ) : leaderboard.length === 0 ? (
            <div className="p-12 text-center text-gray-500 dark:text-gray-400">
              No evaluation runs yet. Create a batch to see results.
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50 dark:bg-gray-900">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      Agent
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      Success Rate
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      Avg Score
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      Cost per Success
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      ROI
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      vs Human
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      Time Cost
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                  {leaderboard.map((entry) => (
                    <tr
                      key={entry.agent_id}
                      className="hover:bg-gray-50 dark:hover:bg-gray-700 cursor-pointer"
                      onClick={() => {
                        // TODO: Navigate to batch detail when we have batch_id
                        console.log('Clicked agent:', entry.agent_id)
                      }}
                    >
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm font-medium text-gray-900 dark:text-white">
                          {entry.agent_name}
                        </div>
                        <div className="text-sm text-gray-500 dark:text-gray-400">
                          {entry.run_count} run{entry.run_count !== 1 ? 's' : ''} · {entry.task_count} tasks
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                        {formatPercent(entry.success_rate)}
                        <div className="text-xs text-gray-500 dark:text-gray-400">
                          {entry.success_count}/{entry.task_count}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                        {formatNumber(entry.avg_score, 3)}
                        {entry.stddev_score !== null && (
                          <div className="text-xs text-gray-500 dark:text-gray-400">
                            ±{formatNumber(entry.stddev_score, 3)}
                          </div>
                        )}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                        {formatCurrency(entry.cost_per_success)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                        {entry.roi !== null ? `${formatNumber(entry.roi, 1)}%` : '-'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                        {entry.human_replacement !== null ? (
                          <span className={entry.human_replacement < 1 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}>
                            {formatNumber(entry.human_replacement, 2)}×
                          </span>
                        ) : (
                          <span className="text-xs text-gray-400 dark:text-gray-500" title="补全人工成本数据后可用">
                            需人工数据
                          </span>
                        )}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                        {formatCurrency(entry.time_cost)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </div>
  )
}