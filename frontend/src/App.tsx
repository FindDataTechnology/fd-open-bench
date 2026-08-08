import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import Layout from './components/Layout'
import Leaderboard from './pages/Leaderboard'
import Benchmarks from './pages/Benchmarks'
import BenchmarkDetail from './pages/BenchmarkDetail'
import BatchDetail from './pages/BatchDetail'
import Agents from './pages/Agents'
import AgentDetail from './pages/AgentDetail'
import Datasets from './pages/Datasets'
import DatasetDetail from './pages/DatasetDetail'
import EvaluationDetail from './pages/EvaluationDetail'
import Settings from './pages/Settings'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
})

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Router>
        <Layout>
          <Routes>
            <Route path="/" element={<Leaderboard />} />
            <Route path="/benchmarks" element={<Benchmarks />} />
            <Route path="/benchmarks/:id" element={<BenchmarkDetail />} />
            <Route path="/runs/:batchId" element={<BatchDetail />} />
            <Route path="/agents" element={<Agents />} />
            <Route path="/agents/:id" element={<AgentDetail />} />
            <Route path="/datasets" element={<Datasets />} />
            <Route path="/datasets/:id" element={<DatasetDetail />} />
            <Route path="/evaluations/:id" element={<EvaluationDetail />} />
            <Route path="/settings" element={<Settings />} />
          </Routes>
        </Layout>
      </Router>
    </QueryClientProvider>
  )
}

export default App