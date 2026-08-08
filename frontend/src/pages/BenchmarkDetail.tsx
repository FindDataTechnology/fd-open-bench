import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useParams, useNavigate } from 'react-router-dom'
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

interface Golden {
  id: string
  input: string
  expected_output: string | null
  business_value: number | null
  human_cost: number | null
  human_minutes: number | null
}

interface Agent {
  id: string
  name: string
  description: string
}

interface Dataset {
  id: string
  name: string
  goldens: Golden[]
}

export default function BenchmarkDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [showRunBatchForm, setShowRunBatchForm] = useState(false)
  const [selectedAgents, setSelectedAgents] = useState<string[]>([])

  // Fetch benchmark
  const { data: benchmark } = useQuery<Benchmark>({
    queryKey: ['benchmark', id],
    queryFn: async () => {
      const res = await api.get(`/benchmarks/${id}`)
      return res.data
    },
  })

  // Fetch dataset with goldens
  const { data: dataset } = useQuery<Dataset>({
    queryKey: ['dataset', benchmark?.dataset_id],
    queryFn: async () => {
      const res = await api.get(`/datasets/${benchmark?.dataset_id}`)
      return res.data
    },
    enabled: !!benchmark?.dataset_id,
  })

  // Fetch agents
  const { data: agents } = useQuery<Agent[]>({
    queryKey: ['agents'],
    queryFn: async () => {
      const res = await api.get('/agents/')
      return res.data
    },
  })

  // Fetch batches (runs with this benchmark_id)
  const { data: runs } = useQuery({
    queryKey: ['runs', 'benchmark', id],
    queryFn: async () => {
      const res = await api.get('/evaluations/', {
        params: { benchmark_id: id }
      })
      return res.data
    },
  })

  // Create batch mutation
  const createBatchMutation = useMutation({
    mutationFn: async (data: { benchmark_id: string; agent_ids: string[] }) => {
      const res = await api.post('/batches/', data)
      return res.data
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['runs'] })
      setShowRunBatchForm(false)
      setSelectedAgents([])
      // Navigate to batch detail
      navigate(`/runs/${data.batch_id}`)
    },
  })

  const handleRunBatch = () => {
    if (selectedAgents.length === 0) {
      alert('Please select at least one agent')
      return
    }
    createBatchMutation.mutate({
      benchmark_id: id!,
      agent_ids: selectedAgents,
    })
  }

  // Group runs by batch_id
  const batches = runs?.reduce((acc: any, run: any) => {
    if (!run.batch_id) return acc
    if (!acc[run.batch_id]) {
      acc[run.batch_id] = []
    }
    acc[run.batch_id].push(run)
    return acc
  }, {}) || {}

  if (!benchmark) {
    return <div className="p-12 text-center text-gray-500">Loading...</div>
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <button
            onClick={() => navigate('/benchmarks')}
            className="text-sm text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300 mb-2"
          >
            ← Back to Benchmarks
          </button>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
            {benchmark.name}
          </h1>
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
            {benchmark.description}
          </p>
        </div>
        <button
          onClick={() => setShowRunBatchForm(!showRunBatchForm)}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          {showRunBatchForm ? 'Cancel' : 'Run New Batch'}
        </button>
      </div>

      {/* Benchmark Info */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          Configuration
        </h2>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <div className="text-sm text-gray-500 dark:text-gray-400">Dataset</div>
            <div className="text-sm font-medium text-gray-900 dark:text-white">
              {dataset?.name || 'Loading...'}
            </div>
          </div>
          <div>
            <div className="text-sm text-gray-500 dark:text-gray-400">Metrics</div>
            <div className="flex flex-wrap gap-1 mt-1">
              {benchmark.metric_suite.map((metric) => (
                <span
                  key={metric}
                  className="px-2 py-1 text-xs bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 rounded"
                >
                  {metric}
                </span>
              ))}
            </div>
          </div>
          <div>
            <div className="text-sm text-gray-500 dark:text-gray-400">Value Formula</div>
            <div className="text-sm font-mono text-gray-900 dark:text-white">
              {benchmark.value_formula}
            </div>
          </div>
          <div>
            <div className="text-sm text-gray-500 dark:text-gray-400">Time Value Rate</div>
            <div className="text-sm font-medium text-gray-900 dark:text-white">
              ${benchmark.time_value_rate}/hour
            </div>
          </div>
        </div>
      </div>

      {/* Run Batch Form */}
      {showRunBatchForm && (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            Run New Batch
          </h2>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Select Agents
              </label>
              <div className="space-y-2">
                {agents?.map((agent) => (
                  <label key={agent.id} className="flex items-center">
                    <input
                      type="checkbox"
                      checked={selectedAgents.includes(agent.id)}
                      onChange={(e) => {
                        if (e.target.checked) {
                          setSelectedAgents([...selectedAgents, agent.id])
                        } else {
                          setSelectedAgents(selectedAgents.filter((id) => id !== agent.id))
                        }
                      }}
                      className="mr-2"
                    />
                    <span className="text-sm text-gray-700 dark:text-gray-300">
                      {agent.name}
                    </span>
                  </label>
                ))}
              </div>
            </div>
            <div className="flex justify-end space-x-3">
              <button
                onClick={() => setShowRunBatchForm(false)}
                className="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700"
              >
                Cancel
              </button>
              <button
                onClick={handleRunBatch}
                disabled={createBatchMutation.isPending || selectedAgents.length === 0}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
              >
                {createBatchMutation.isPending ? 'Starting...' : 'Start Batch'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Goldens */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
            Test Cases ({dataset?.goldens?.length || 0})
          </h2>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50 dark:bg-gray-900">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Input
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Business Value
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Human Cost
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Human Time
                </th>
              </tr>
            </thead>
            <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
              {dataset?.goldens?.slice(0, 10).map((golden) => (
                <tr key={golden.id}>
                  <td className="px-6 py-4 text-sm text-gray-900 dark:text-white">
                    {golden.input.substring(0, 100)}
                    {golden.input.length > 100 && '...'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                    {golden.business_value !== null ? `$${golden.business_value}` : '-'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                    {golden.human_cost !== null ? `$${golden.human_cost}` : '-'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                    {golden.human_minutes !== null ? `${golden.human_minutes} min` : '-'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {dataset?.goldens && dataset.goldens.length > 10 && (
            <div className="px-6 py-3 text-sm text-gray-500 dark:text-gray-400 text-center">
              Showing 10 of {dataset.goldens.length} test cases
            </div>
          )}
        </div>
      </div>

      {/* Batch History */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
            Batch History
          </h2>
        </div>
        {Object.keys(batches).length === 0 ? (
          <div className="p-12 text-center text-gray-500 dark:text-gray-400">
            No batches yet. Run your first batch to see results.
          </div>
        ) : (
          <div className="divide-y divide-gray-200 dark:divide-gray-700">
            {Object.entries(batches).map(([batchId, batchRuns]: [string, any]) => (
              <div
                key={batchId}
                className="px-6 py-4 hover:bg-gray-50 dark:hover:bg-gray-700 cursor-pointer"
                onClick={() => navigate(`/runs/${batchId}`)}
              >
                <div className="flex items-center justify-between">
                  <div>
                    <div className="text-sm font-medium text-gray-900 dark:text-white">
                      Batch {batchId.substring(0, 8)}
                    </div>
                    <div className="text-sm text-gray-500 dark:text-gray-400">
                      {batchRuns.length} agent{batchRuns.length !== 1 ? 's' : ''}
                    </div>
                  </div>
                  <div className="text-sm text-gray-500 dark:text-gray-400">
                    {new Date(batchRuns[0].created_at).toLocaleString()}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}