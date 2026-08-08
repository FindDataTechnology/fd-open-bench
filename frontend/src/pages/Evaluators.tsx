import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import api from '../services/api'

export default function Evaluators() {
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [showTestModal, setShowTestModal] = useState(false)
  const [selectedEvaluator, setSelectedEvaluator] = useState(null)
  const queryClient = useQueryClient()

  const { data: evaluators, isLoading } = useQuery({
    queryKey: ['evaluators'],
    queryFn: () => api.get('/evaluators').then(res => res.data),
  })

  const createMutation = useMutation({
    mutationFn: (data) => api.post('/evaluators', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['evaluators'] })
      setShowCreateModal(false)
    },
  })

  if (isLoading) {
    return <div className="text-center py-8">Loading evaluators...</div>
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Evaluators</h1>
          <p className="text-gray-500 dark:text-gray-400 mt-1">
            Configure evaluation metrics and validators
          </p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          data-testid="create-evaluator-button"
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          + Create Evaluator
        </button>
      </div>

      <div data-testid="evaluator-list" className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {evaluators?.map((evaluator) => (
          <div
            key={evaluator.id}
            data-testid={`evaluator-card-${evaluator.id}`}
            className="bg-white dark:bg-gray-800 rounded-lg shadow p-6"
          >
            <div className="flex items-start justify-between">
              <div>
                <h3 className="text-xl font-semibold text-gray-900 dark:text-white">
                  {evaluator.name}
                </h3>
                <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                  {evaluator.type}
                </p>
              </div>
              <span className="text-3xl">
                {evaluator.type === 'validator' ? '✓' :
                 evaluator.type === 'llm_judge' ? '🤖' : '⚙️'}
              </span>
            </div>
            <div className="mt-4">
              <pre className="bg-gray-50 dark:bg-gray-900 p-3 rounded-lg overflow-x-auto text-xs">
                {JSON.stringify(evaluator.config, null, 2)}
              </pre>
            </div>
            <div className="mt-4 flex gap-2">
              <button
                onClick={() => {
                  setSelectedEvaluator(evaluator)
                  setShowTestModal(true)
                }}
                data-testid={`test-evaluator-button-${evaluator.id}`}
                className="flex-1 px-3 py-2 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700"
              >
                Test
              </button>
              <button className="flex-1 px-3 py-2 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 text-sm rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700">
                Edit
              </button>
            </div>
          </div>
        ))}
      </div>

      {showCreateModal && (
        <CreateEvaluatorModal
          onClose={() => setShowCreateModal(false)}
          onCreate={(data) => createMutation.mutate(data)}
        />
      )}

      {showTestModal && selectedEvaluator && (
        <TestEvaluatorModal
          evaluator={selectedEvaluator}
          onClose={() => {
            setShowTestModal(false)
            setSelectedEvaluator(null)
          }}
        />
      )}
    </div>
  )
}

function CreateEvaluatorModal({ onClose, onCreate }) {
  const [name, setName] = useState('')
  const [type, setType] = useState('validator')
  const [config, setConfig] = useState('{}')

  const handleSubmit = (e) => {
    e.preventDefault()
    try {
      const parsedConfig = JSON.parse(config)
      onCreate({ name, type, config: parsedConfig })
    } catch (error) {
      alert('Invalid JSON configuration')
    }
  }

  return (
    <div data-testid="create-evaluator-modal" className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white dark:bg-gray-800 rounded-lg p-6 w-full max-w-md">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">
          Create New Evaluator
        </h2>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Name
            </label>
            <input
              type="text"
              data-testid="evaluator-name-input"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Type
            </label>
            <select
              data-testid="evaluator-type-select"
              value={type}
              onChange={(e) => setType(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
            >
              <option value="validator">Validator</option>
              <option value="llm_judge">LLM Judge</option>
              <option value="executor">Executor</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Configuration (JSON)
            </label>
            <textarea
              data-testid="evaluator-config-input"
              value={config}
              onChange={(e) => setConfig(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white font-mono text-sm"
              rows={8}
              required
            />
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
              data-testid="create-evaluator-submit-button"
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

function TestEvaluatorModal({ evaluator, onClose }) {
  const [input, setInput] = useState('')
  const [output, setOutput] = useState('')
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)

  const handleTest = async () => {
    setLoading(true)
    try {
      const response = await api.post(`/evaluators/${evaluator.id}/test`, {
        input_text: input,
        output_text: output,
      })
      setResult(response.data)
    } catch (error) {
      alert('Test failed: ' + (error as Error).message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div data-testid="test-evaluator-modal" className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white dark:bg-gray-800 rounded-lg p-6 w-full max-w-2xl">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">
          Test Evaluator: {evaluator.name}
        </h2>
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Input
            </label>
            <textarea
              data-testid="test-input"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              rows={3}
              placeholder="Enter test input..."
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Output
            </label>
            <textarea
              data-testid="test-output"
              value={output}
              onChange={(e) => setOutput(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              rows={3}
              placeholder="Enter agent output to evaluate..."
            />
          </div>
          <button
            data-testid="run-test-button"
            onClick={handleTest}
            disabled={loading}
            className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
          >
            {loading ? 'Testing...' : 'Run Test'}
          </button>
          {result && (
            <div data-testid="test-result" className="bg-gray-50 dark:bg-gray-900 p-4 rounded-lg">
              <h3 className="font-semibold text-gray-900 dark:text-white mb-2">
                Test Result
              </h3>
              <pre className="text-sm overflow-x-auto">
                {JSON.stringify(result, null, 2)}
              </pre>
            </div>
          )}
          <button
            data-testid="close-button"
            onClick={onClose}
            className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  )
}
