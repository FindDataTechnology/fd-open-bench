import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import Agents from './pages/Agents'
import AgentDetail from './pages/AgentDetail'
import Datasets from './pages/Datasets'
import DatasetDetail from './pages/DatasetDetail'
import Evaluations from './pages/Evaluations'
import EvaluationDetail from './pages/EvaluationDetail'
import Evaluators from './pages/Evaluators'
import CostAnalyzer from './pages/CostAnalyzer'
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
            <Route path="/" element={<Dashboard />} />
            <Route path="/agents" element={<Agents />} />
            <Route path="/agents/:id" element={<AgentDetail />} />
            <Route path="/datasets" element={<Datasets />} />
            <Route path="/datasets/:id" element={<DatasetDetail />} />
            <Route path="/evaluations" element={<Evaluations />} />
            <Route path="/evaluations/:id" element={<EvaluationDetail />} />
            <Route path="/evaluators" element={<Evaluators />} />
            <Route path="/cost-analyzer" element={<CostAnalyzer />} />
            <Route path="/settings" element={<Settings />} />
          </Routes>
        </Layout>
      </Router>
    </QueryClientProvider>
  )
}

export default App
