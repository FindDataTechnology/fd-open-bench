import { useState } from 'react'
import { Link, useLocation } from 'react-router-dom'

interface LayoutProps {
  children: React.ReactNode
}

export default function Layout({ children }: LayoutProps) {
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const location = useLocation()

  const navigation = [
    { name: 'Dashboard', href: '/', icon: '📊' },
    { name: 'Agents', href: '/agents', icon: '🤖' },
    { name: 'Datasets', href: '/datasets', icon: '📁' },
    { name: 'Evaluations', href: '/evaluations', icon: '🧪' },
    { name: 'Evaluators', href: '/evaluators', icon: '⚖️' },
    { name: 'Cost Analyzer', href: '/cost-analyzer', icon: '💰' },
    { name: 'Settings', href: '/settings', icon: '⚙️' },
  ]

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Sidebar */}
      <aside
        className={`fixed top-0 left-0 z-40 h-screen transition-transform ${
          sidebarOpen ? 'translate-x-0' : '-translate-x-full'
        } w-64 bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700`}
      >
        <div className="h-full px-3 py-4 overflow-y-auto">
          <div className="mb-5 px-3 py-2">
            <h1 className="text-xl font-bold text-gray-900 dark:text-white">
              FD Open Bench
            </h1>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              Agent Evaluation Platform
            </p>
          </div>
          <ul className="space-y-2 font-medium">
            {navigation.map((item) => {
              const isActive = location.pathname === item.href
              return (
                <li key={item.name}>
                  <Link
                    to={item.href}
                    className={`flex items-center p-2 text-gray-900 rounded-lg dark:text-white hover:bg-gray-100 dark:hover:bg-gray-700 group ${
                      isActive ? 'bg-gray-100 dark:bg-gray-700' : ''
                    }`}
                  >
                    <span className="mr-3 text-xl">{item.icon}</span>
                    <span>{item.name}</span>
                  </Link>
                </li>
              )
            })}
          </ul>
        </div>
      </aside>

      {/* Main content */}
      <div className={`${sidebarOpen ? 'ml-64' : ''} transition-all duration-300`}>
        {/* Top navbar */}
        <nav className="fixed top-0 z-30 w-full bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
          <div className="px-3 py-3 lg:px-5 lg:pl-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center">
                <button
                  onClick={() => setSidebarOpen(!sidebarOpen)}
                  className="p-2 text-gray-600 rounded-lg hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-700"
                >
                  <span className="sr-only">Toggle sidebar</span>
                  <svg
                    className="w-6 h-6"
                    fill="currentColor"
                    viewBox="0 0 20 20"
                  >
                    <path
                      fillRule="evenodd"
                      d="M3 5a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zM3 10a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zM3 15a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1z"
                      clipRule="evenodd"
                    />
                  </svg>
                </button>
              </div>
              <div className="flex items-center">
                <span className="text-xs text-gray-400 dark:text-gray-500 mr-2">
                  local · internal tool
                </span>
              </div>
            </div>
          </div>
        </nav>

        {/* Page content */}
        <main className="p-4 mt-16">
          {children}
        </main>
      </div>
    </div>
  )
}
