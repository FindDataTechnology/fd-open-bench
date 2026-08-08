import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import api from '../services/api'
import {
  LineChart, Line, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts'

export default function CostAnalyzer() {
  const [selectedAgent, setSelectedAgent] = useState('')
  const [dateRange, setDateRange] = useState('30')

  const { data: agents } = useQuery({
    queryKey: ['agents'],
    queryFn: () => api.get('/agents').then(res => res.data),
  })

  const { data: costBreakdown } = useQuery({
    queryKey: ['cost-breakdown', selectedAgent, dateRange],
    queryFn: () => api.get(`/agents/${selectedAgent}/cost-breakdown?days=${dateRange}`).then(res => res.data),
    enabled: !!selectedAgent,
  })

  const { data: roiTrends } = useQuery({
    queryKey: ['roi-trends', selectedAgent, dateRange],
    queryFn: () => api.get(`/agents/${selectedAgent}/roi-trends?days=${dateRange}`).then(res => res.data),
    enabled: !!selectedAgent,
  })

  const COLORS = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444']

  return (
    <div className="space-y-6">
      <div>
        <h1 data-testid="cost-analyzer-heading" className="text-3xl font-bold text-gray-900 dark:text-white">Cost Analyzer</h1>
        <p className="text-gray-500 dark:text-gray-400 mt-1">
          Analyze costs, ROI, and business value
        </p>
      </div>

      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Agent
            </label>
            <select
              data-testid="agent-selector"
              value={selectedAgent}
              onChange={(e) => setSelectedAgent(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
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
              Date Range
            </label>
            <select
              data-testid="date-range-selector"
              value={dateRange}
              onChange={(e) => setDateRange(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
            >
              <option value="7">Last 7 days</option>
              <option value="30">Last 30 days</option>
              <option value="90">Last 90 days</option>
            </select>
          </div>
        </div>
      </div>

      {selectedAgent && costBreakdown && (
        <>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
              <p className="text-sm text-gray-500 dark:text-gray-400">Total Cost</p>
              <p className="text-3xl font-bold text-gray-900 dark:text-white mt-2">
                ${costBreakdown.total_cost?.toFixed(2) || '0.00'}
              </p>
            </div>
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
              <p className="text-sm text-gray-500 dark:text-gray-400">Business Value</p>
              <p className="text-3xl font-bold text-green-600 mt-2">
                ${costBreakdown.total_business_value?.toFixed(2) || '0.00'}
              </p>
            </div>
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
              <p className="text-sm text-gray-500 dark:text-gray-400">ROI</p>
              <p className="text-3xl font-bold text-blue-600 mt-2">
                {costBreakdown.roi?.toFixed(1) || '0'}%
              </p>
            </div>
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
              <p className="text-sm text-gray-500 dark:text-gray-400">Cost per Task</p>
              <p className="text-3xl font-bold text-gray-900 dark:text-white mt-2">
                ${costBreakdown.cost_per_task?.toFixed(4) || '0.0000'}
              </p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
                Cost Breakdown
              </h2>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={costBreakdown.breakdown || []}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {costBreakdown.breakdown?.map((_entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </div>

            <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
                ROI Trends
              </h2>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={roiTrends || []}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Line type="monotone" dataKey="roi" stroke="#3B82F6" strokeWidth={2} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
              Daily Cost Breakdown
            </h2>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={costBreakdown.daily_costs || []}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Bar dataKey="token_cost" stackId="a" fill="#3B82F6" />
                <Bar dataKey="time_cost" stackId="a" fill="#10B981" />
                <Bar dataKey="infra_cost" stackId="a" fill="#F59E0B" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </>
      )}
    </div>
  )
}
